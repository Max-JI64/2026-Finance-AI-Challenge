"""Prepare Stage 4 target and chronological-split candidates for user approval.

This script does not select a final target, does not create model-ready labels,
and does not alter the Stage 3 panel. It uses a temporary disk-backed SQLite
table and publishes only aggregate comparison reports.
"""

from __future__ import annotations

import json
import math
import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "data" / "interim" / "stage3_panel.sqlite"
REPORT_DIR = PROJECT_ROOT / "reports" / "stage4"

PERIOD = "기준_년분기_코드"
AREA = "상권_코드"
INDUSTRY = "서비스_업종_코드"
INDUSTRY_NAME = "서비스_업종_코드_명"
SALES = "당월_매출_금액"


def q(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def exact_quantile(
    connection: sqlite3.Connection,
    probability: float,
    where: str = "1=1",
    parameters: tuple[object, ...] = (),
) -> float:
    count = connection.execute(
        f"SELECT COUNT(*) FROM candidate_base WHERE {where}", parameters
    ).fetchone()[0]
    if not count:
        raise RuntimeError("Cannot calculate a quantile for an empty partition")
    offset = math.floor((count - 1) * probability)
    value = connection.execute(
        f"SELECT target_yoy_growth FROM candidate_base WHERE {where} "
        "ORDER BY target_yoy_growth LIMIT 1 OFFSET ?",
        (*parameters, offset),
    ).fetchone()[0]
    return float(value)


def count_at_threshold(
    connection: sqlite3.Connection,
    threshold: float,
    where: str = "1=1",
    parameters: tuple[object, ...] = (),
) -> tuple[int, int, float]:
    total, positive = connection.execute(
        f"SELECT COUNT(*), SUM(CASE WHEN target_yoy_growth <= ? THEN 1 ELSE 0 END) "
        f"FROM candidate_base WHERE {where}",
        (threshold, *parameters),
    ).fetchone()
    positive = int(positive or 0)
    return int(total), positive, positive / total if total else float("nan")


def prepare_candidate_table(connection: sqlite3.Connection) -> dict[str, int]:
    connection.execute("PRAGMA temp_store=FILE")
    connection.execute("DROP TABLE IF EXISTS temp.stage4_indexed")
    connection.execute(
        f"""
        CREATE TEMP TABLE stage4_indexed AS
        SELECT
            {q(PERIOD)} AS period,
            CAST(substr({q(PERIOD)}, 1, 4) AS INTEGER) AS year,
            CAST(substr({q(PERIOD)}, 5, 1) AS INTEGER) AS quarter,
            CAST(substr({q(PERIOD)}, 1, 4) AS INTEGER) * 4
              + CAST(substr({q(PERIOD)}, 5, 1) AS INTEGER) - 1 AS period_index,
            {q(AREA)} AS area,
            {q(INDUSTRY)} AS industry,
            {q(INDUSTRY_NAME)} AS industry_name,
            {q(SALES)} AS sales
        FROM core_features
        """
    )
    connection.execute(
        "CREATE UNIQUE INDEX temp.idx_stage4_indexed "
        "ON stage4_indexed(period_index, area, industry)"
    )

    next_pair_count = connection.execute(
        "SELECT COUNT(*) FROM stage4_indexed c JOIN stage4_indexed n "
        "ON n.period_index=c.period_index+1 AND n.area=c.area AND n.industry=c.industry"
    ).fetchone()[0]
    yoy_history_count = connection.execute(
        "SELECT COUNT(*) FROM stage4_indexed c "
        "JOIN stage4_indexed n ON n.period_index=c.period_index+1 AND n.area=c.area AND n.industry=c.industry "
        "JOIN stage4_indexed p ON p.period_index=c.period_index-3 AND p.area=c.area AND p.industry=c.industry"
    ).fetchone()[0]
    zero_base_count = connection.execute(
        "SELECT COUNT(*) FROM stage4_indexed c "
        "JOIN stage4_indexed n ON n.period_index=c.period_index+1 AND n.area=c.area AND n.industry=c.industry "
        "JOIN stage4_indexed p ON p.period_index=c.period_index-3 AND p.area=c.area AND p.industry=c.industry "
        "WHERE p.sales=0"
    ).fetchone()[0]

    connection.execute("DROP TABLE IF EXISTS temp.candidate_base")
    connection.execute(
        """
        CREATE TEMP TABLE candidate_base AS
        SELECT
            c.period AS feature_period,
            n.period AS target_period,
            n.year AS target_year,
            n.quarter AS target_quarter,
            c.area AS area,
            c.industry AS industry,
            c.industry_name AS industry_name,
            n.sales AS next_quarter_sales,
            p.sales AS target_year_ago_sales,
            (n.sales - p.sales) * 1.0 / p.sales AS target_yoy_growth
        FROM stage4_indexed c
        JOIN stage4_indexed n
          ON n.period_index=c.period_index+1
         AND n.area=c.area
         AND n.industry=c.industry
        JOIN stage4_indexed p
          ON p.period_index=c.period_index-3
         AND p.area=c.area
         AND p.industry=c.industry
        WHERE p.sales > 0
        """
    )
    connection.execute(
        "CREATE INDEX temp.idx_candidate_growth ON candidate_base(target_yoy_growth)"
    )
    connection.execute(
        "CREATE INDEX temp.idx_candidate_period ON candidate_base(target_period)"
    )
    eligible_count = connection.execute("SELECT COUNT(*) FROM candidate_base").fetchone()[0]
    period_min, period_max = connection.execute(
        "SELECT MIN(target_period), MAX(target_period) FROM candidate_base"
    ).fetchone()
    return {
        "next_quarter_pair_rows": int(next_pair_count),
        "with_year_ago_rows": int(yoy_history_count),
        "zero_year_ago_sales_rows": int(zero_base_count),
        "eligible_rows": int(eligible_count),
        "target_period_min": period_min,
        "target_period_max": period_max,
    }


def candidate_definitions(connection: sqlite3.Connection) -> list[dict[str, object]]:
    q25 = exact_quantile(connection, 0.25)
    q30 = exact_quantile(connection, 0.30)
    definitions = [
        ("전년동기 대비 -5% 이하", -0.05, "고정 기준"),
        ("전년동기 대비 -10% 이하", -0.10, "고정 기준"),
        ("전체 하위 25%", q25, "전체기간 진단용 분위수"),
        ("전체 하위 30%", q30, "전체기간 진단용 분위수"),
    ]
    rows = []
    for name, threshold, kind in definitions:
        total, positive, rate = count_at_threshold(connection, threshold)
        rows.append(
            {
                "candidate": name,
                "threshold": threshold,
                "threshold_type": kind,
                "eligible_rows": total,
                "positive_rows": positive,
                "positive_rate": rate,
                "selection_status": "미확정",
            }
        )
    return rows


def grouped_summary(
    connection: sqlite3.Connection,
    definitions: list[dict[str, object]],
    group: str,
) -> pd.DataFrame:
    if group == "year":
        select = "target_year"
        group_columns = ["target_year"]
    elif group == "industry":
        select = "industry, MAX(industry_name) AS industry_name"
        group_columns = ["industry", "industry_name"]
    else:
        raise ValueError(group)
    threshold_columns = ", ".join(
        f"SUM(CASE WHEN target_yoy_growth <= {float(item['threshold'])!r} THEN 1 ELSE 0 END) "
        f"AS positive_{index}"
        for index, item in enumerate(definitions)
    )
    order = "target_year" if group == "year" else "industry"
    query = (
        f"SELECT {select}, COUNT(*) AS eligible_rows, {threshold_columns} "
        f"FROM candidate_base GROUP BY {order} ORDER BY {order}"
    )
    raw = pd.read_sql_query(query, connection)
    rows = []
    for _, source in raw.iterrows():
        for index, item in enumerate(definitions):
            row = {column: source[column] for column in group_columns}
            row.update(
                {
                    "candidate": item["candidate"],
                    "threshold": item["threshold"],
                    "eligible_rows": int(source["eligible_rows"]),
                    "positive_rows": int(source[f"positive_{index}"]),
                    "positive_rate": source[f"positive_{index}"] / source["eligible_rows"],
                }
            )
            rows.append(row)
    return pd.DataFrame(rows)


def split_comparison(connection: sqlite3.Connection) -> pd.DataFrame:
    options = {
        "A_3구간_최종테스트보존": {
            "train": ("20221", "20234"),
            "validation": ("20241", "20244"),
            "test_locked": ("20251", "20254"),
        },
        "B_2구간_학습확대": {
            "train": ("20221", "20244"),
            "validation": ("20251", "20254"),
        },
    }
    rows = []
    for option, partitions in options.items():
        train_start, train_end = partitions["train"]
        train_where = "target_period BETWEEN ? AND ?"
        train_parameters = (train_start, train_end)
        train_q25 = exact_quantile(connection, 0.25, train_where, train_parameters)
        train_q30 = exact_quantile(connection, 0.30, train_where, train_parameters)
        for partition, (start, end) in partitions.items():
            where = "target_period BETWEEN ? AND ?"
            parameters = (start, end)
            total = connection.execute(
                f"SELECT COUNT(*) FROM candidate_base WHERE {where}", parameters
            ).fetchone()[0]
            row = {
                "option": option,
                "partition": partition,
                "target_period_start": start,
                "target_period_end": end,
                "eligible_rows": int(total),
                "train_fitted_q25_threshold": train_q25,
                "train_fitted_q30_threshold": train_q30,
            }
            for label, threshold in (
                ("fixed_5", -0.05),
                ("fixed_10", -0.10),
                ("train_q25", train_q25),
                ("train_q30", train_q30),
            ):
                _, positive, rate = count_at_threshold(
                    connection, threshold, where, parameters
                )
                row[f"{label}_positive_rows"] = positive
                row[f"{label}_positive_rate"] = rate
            rows.append(row)
    return pd.DataFrame(rows)


def write_report(
    eligibility: dict[str, int],
    candidates: pd.DataFrame,
    splits: pd.DataFrame,
) -> None:
    candidate_lines = []
    for row in candidates.itertuples(index=False):
        candidate_lines.append(
            f"| {row.candidate} | {row.threshold:.6f} | {row.positive_rows:,} | {row.positive_rate:.2%} |"
        )
    split_lines = []
    for row in splits.itertuples(index=False):
        split_lines.append(
            f"| {row.option} | {row.partition} | {row.target_period_start}~{row.target_period_end} | "
            f"{row.eligible_rows:,} | {row.fixed_5_positive_rate:.2%} | {row.fixed_10_positive_rate:.2%} |"
        )
    lines = [
        "# Stage 4 Target 후보 비교",
        "",
        "- 상태: 후보 통계 작성 완료 / 최종 Target·시간 분할 미확정",
        "- Target 시점: Feature 분기의 실제 다음 분기",
        "- 변화율: `(다음 분기 매출 - 다음 분기의 전년 동기 매출) / 다음 분기의 전년 동기 매출`",
        "- 미래정보 누수 방지: 분위수 기준을 선택할 경우 학습 기간에서만 임계값을 Fit해야 한다.",
        "",
        "## 생성 가능 행",
        "",
        f"- 실제 다음 분기가 있는 행: {eligibility['next_quarter_pair_rows']:,}",
        f"- 다음 분기의 전년 동기까지 있는 행: {eligibility['with_year_ago_rows']:,}",
        f"- 전년 동기 매출 0으로 비율 계산이 불가능한 행: {eligibility['zero_year_ago_sales_rows']:,}",
        f"- 최종 후보 비교 가능 행: {eligibility['eligible_rows']:,}",
        f"- Target 기간: {eligibility['target_period_min']}~{eligibility['target_period_max']}",
        "",
        "## Target 후보",
        "",
        "| 후보 | 기준값 | 양성 행 | 양성 비율 |",
        "| --- | ---: | ---: | ---: |",
        *candidate_lines,
        "",
        "전체 하위 25%·30%의 기준값은 후보 비교용이다. 최종 분위수 Target을 선택하면 시간 분할 확정 후 학습 기간에서 다시 계산한다.",
        "",
        "## 시간 분할 선택지",
        "",
        "| 선택지 | 구간 | Target 기간 | 행 수 | -5% 양성률 | -10% 양성률 |",
        "| --- | --- | --- | ---: | ---: | ---: |",
        *split_lines,
        "",
        "- A: 2024년을 검증으로 사용하고 2025년을 잠긴 최종 테스트로 남긴다.",
        "- B: 2024년까지 학습해 학습량을 늘리고 2025년을 검증으로 사용한다. 별도의 잠긴 최종 테스트는 없다.",
        "",
        "## 사용자 결정 필요",
        "",
        "1. Target 후보 1개",
        "2. 시간 분할 선택지 A 또는 B",
        "",
        "선택 전에는 Target 열, 학습 세트, 검증 세트를 생성하지 않는다.",
        "",
    ]
    (REPORT_DIR / "candidate_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(DATABASE_PATH)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        eligibility = prepare_candidate_table(connection)
        candidate_rows = candidate_definitions(connection)
        candidates = pd.DataFrame(candidate_rows)
        by_year = grouped_summary(connection, candidate_rows, "year")
        by_industry = grouped_summary(connection, candidate_rows, "industry")
        splits = split_comparison(connection)

        candidates.to_csv(
            REPORT_DIR / "target_candidate_summary.csv", index=False, encoding="utf-8-sig"
        )
        by_year.to_csv(
            REPORT_DIR / "target_candidate_by_year.csv", index=False, encoding="utf-8-sig"
        )
        by_industry.to_csv(
            REPORT_DIR / "target_candidate_by_industry.csv", index=False, encoding="utf-8-sig"
        )
        splits.to_csv(
            REPORT_DIR / "time_split_comparison.csv", index=False, encoding="utf-8-sig"
        )
        write_report(eligibility, candidates, splits)
        manifest = {
            "created_at_kst": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="minutes"),
            "status": "candidate_analysis_only",
            "source": str(DATABASE_PATH.relative_to(PROJECT_ROOT)),
            "source_table": "core_features",
            "eligibility": eligibility,
            "final_target_selected": False,
            "final_split_selected": False,
            "model_ready_dataset_created": False,
        }
        (REPORT_DIR / "candidate_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(
            json.dumps(
                {
                    "status": "candidate_analysis_completed",
                    "eligibility": eligibility,
                    "candidates": candidate_rows,
                },
                ensure_ascii=False,
            )
        )
    finally:
        connection.close()


if __name__ == "__main__":
    main()
