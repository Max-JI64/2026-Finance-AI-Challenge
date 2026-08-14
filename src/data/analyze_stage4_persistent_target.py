"""Analyze the approved persistent two-quarter sales-deterioration Target.

The Target threshold remains unselected. Statistics use development periods
only; locked 2025 outcomes are excluded from threshold selection.
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
THRESHOLDS = (0.05, 0.08, 0.10, 0.12, 0.15, 0.18, 0.20)
DEVELOPMENT_RANGE = ("20222", "20244")
BASE_TRAIN_RANGE = ("20222", "20234")
VALIDATION_2024_RANGE = ("20241", "20244")
FOLDS = (
    (1, "20222", "20233", "20241"),
    (2, "20222", "20234", "20242"),
    (3, "20222", "20241", "20243"),
    (4, "20222", "20242", "20244"),
)


def q(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def prepare(connection: sqlite3.Connection) -> dict[str, object]:
    connection.execute("PRAGMA temp_store=FILE")
    connection.execute("DROP TABLE IF EXISTS temp.persistent_indexed")
    connection.execute(
        f"""
        CREATE TEMP TABLE persistent_indexed AS
        SELECT
            {q('기준_년분기_코드')} AS period,
            CAST(substr({q('기준_년분기_코드')},1,4) AS INTEGER)*4
              + CAST(substr({q('기준_년분기_코드')},5,1) AS INTEGER)-1 AS period_index,
            {q('상권_코드')} AS area,
            {q('서비스_업종_코드')} AS industry,
            {q('서비스_업종_코드_명')} AS industry_name,
            {q('당월_매출_금액')} AS sales
        FROM core_features
        """
    )
    connection.execute(
        "CREATE UNIQUE INDEX temp.idx_persistent_indexed "
        "ON persistent_indexed(period_index,area,industry)"
    )
    connection.execute("DROP TABLE IF EXISTS temp.persistent_base")
    connection.execute(
        """
        CREATE TEMP TABLE persistent_base AS
        SELECT
            c.period AS feature_period,
            f1.period AS target_start_period,
            f2.period AS target_end_period,
            CAST(substr(f2.period,1,4) AS INTEGER) AS target_end_year,
            c.area,
            c.industry,
            c.industry_name,
            f1.sales AS future_q1_sales,
            f2.sales AS future_q2_sales,
            p1.sales AS year_ago_q1_sales,
            p2.sales AS year_ago_q2_sales,
            (f1.sales-p1.sales)*1.0/p1.sales AS future_q1_yoy_growth,
            (f2.sales-p2.sales)*1.0/p2.sales AS future_q2_yoy_growth,
            (f1.sales+f2.sales-p1.sales-p2.sales)*1.0/(p1.sales+p2.sales)
                AS future_two_quarter_yoy_growth
        FROM persistent_indexed c
        JOIN persistent_indexed f1
          ON f1.period_index=c.period_index+1
         AND f1.area=c.area AND f1.industry=c.industry
        JOIN persistent_indexed f2
          ON f2.period_index=c.period_index+2
         AND f2.area=c.area AND f2.industry=c.industry
        JOIN persistent_indexed p1
          ON p1.period_index=c.period_index-3
         AND p1.area=c.area AND p1.industry=c.industry
        JOIN persistent_indexed p2
          ON p2.period_index=c.period_index-2
         AND p2.area=c.area AND p2.industry=c.industry
        WHERE p1.sales>0 AND p2.sales>0 AND p1.sales+p2.sales>0
        """
    )
    connection.execute(
        "CREATE INDEX temp.idx_persistent_end ON persistent_base(target_end_period)"
    )
    total, minimum, maximum = connection.execute(
        "SELECT COUNT(*),MIN(target_end_period),MAX(target_end_period) "
        "FROM persistent_base"
    ).fetchone()
    development = connection.execute(
        "SELECT COUNT(*) FROM persistent_base "
        "WHERE target_end_period BETWEEN ? AND ?",
        DEVELOPMENT_RANGE,
    ).fetchone()[0]
    return {
        "eligible_rows_all": int(total),
        "eligible_rows_development": int(development),
        "target_end_period_min": minimum,
        "target_end_period_max": maximum,
    }


def target_condition() -> str:
    return (
        "future_q1_yoy_growth < 0 AND future_q2_yoy_growth < 0 "
        "AND future_two_quarter_yoy_growth <= ?"
    )


def count_result(
    connection: sqlite3.Connection,
    threshold: float,
    start: str,
    end: str,
) -> tuple[int, int, float]:
    total, positive = connection.execute(
        f"SELECT COUNT(*),SUM(CASE WHEN {target_condition()} THEN 1 ELSE 0 END) "
        "FROM persistent_base WHERE target_end_period BETWEEN ? AND ?",
        (-threshold, start, end),
    ).fetchone()
    positive = int(positive or 0)
    return int(total), positive, positive / total if total else math.nan


def industry_coverage(
    connection: sqlite3.Connection, threshold: float
) -> tuple[int, int, int]:
    rows = connection.execute(
        f"""
        SELECT industry,COUNT(*) AS total,
               SUM(CASE WHEN {target_condition()} THEN 1 ELSE 0 END) AS positive
        FROM persistent_base
        WHERE target_end_period BETWEEN ? AND ?
        GROUP BY industry
        """,
        (-threshold, *BASE_TRAIN_RANGE),
    ).fetchall()
    both = sum(0 < positive < total for _, total, positive in rows)
    minimum = sum(
        positive >= 100 and total-positive >= 100
        for _, total, positive in rows
    )
    return len(rows), both, minimum


def sensitivity(connection: sqlite3.Connection) -> pd.DataFrame:
    rows = []
    for threshold in THRESHOLDS:
        development = count_result(
            connection, threshold, *DEVELOPMENT_RANGE
        )
        train = count_result(connection, threshold, *BASE_TRAIN_RANGE)
        validation = count_result(
            connection, threshold, *VALIDATION_2024_RANGE
        )
        fold_rows = []
        for fold, train_start, train_end, validation_period in FOLDS:
            fold_train = count_result(
                connection, threshold, train_start, train_end
            )
            fold_validation = count_result(
                connection, threshold, validation_period, validation_period
            )
            fold_rows.append((fold, fold_train, fold_validation))
        industries, both, minimum = industry_coverage(
            connection, threshold
        )
        rows.append(
            {
                "decline_threshold": threshold,
                "development_rows": development[0],
                "development_positive_rows": development[1],
                "development_positive_rate": development[2],
                "base_train_rows": train[0],
                "base_train_positive_rate": train[2],
                "validation_2024_rows": validation[0],
                "validation_2024_positive_rate": validation[2],
                "validation_minus_train_pp": (
                    validation[2]-train[2]
                )*100,
                "minimum_fold_train_rows": min(
                    item[1][0] for item in fold_rows
                ),
                "minimum_fold_validation_positive_rows": min(
                    item[2][1] for item in fold_rows
                ),
                "minimum_fold_validation_negative_rows": min(
                    item[2][0]-item[2][1] for item in fold_rows
                ),
                "training_industries": industries,
                "training_industries_with_both_classes": both,
                "training_industries_with_at_least_100_each_class": minimum,
            }
        )
    return pd.DataFrame(rows)


def by_fold(connection: sqlite3.Connection) -> pd.DataFrame:
    rows = []
    for threshold in THRESHOLDS:
        for fold, train_start, train_end, validation_period in FOLDS:
            for partition, start, end in (
                ("train", train_start, train_end),
                ("validation", validation_period, validation_period),
            ):
                total, positive, rate = count_result(
                    connection, threshold, start, end
                )
                rows.append(
                    {
                        "decline_threshold": threshold,
                        "fold": fold,
                        "partition": partition,
                        "target_end_start": start,
                        "target_end_end": end,
                        "rows": total,
                        "positive_rows": positive,
                        "positive_rate": rate,
                    }
                )
    return pd.DataFrame(rows)


def write_report(
    eligibility: dict[str, object], frame: pd.DataFrame
) -> None:
    table = []
    for row in frame.itertuples(index=False):
        table.append(
            f"| {row.decline_threshold:.0%} | "
            f"{row.development_positive_rate:.2%} | "
            f"{row.base_train_positive_rate:.2%} | "
            f"{row.validation_2024_positive_rate:.2%} | "
            f"{row.validation_minus_train_pp:.2f}%p | "
            f"{row.minimum_fold_validation_positive_rows:,} / "
            f"{row.minimum_fold_validation_negative_rows:,} |"
        )
    lines = [
        "# Stage 4 향후 2개 분기 지속 악화 Target",
        "",
        "- 상태: Target 구조 승인 / 감소 임계값 미확정",
        "- Feature 시점 이후 두 분기를 모두 사용한다.",
        "- 두 미래 분기가 각각 전년동기보다 감소해야 한다.",
        "- 두 미래 분기 합산 매출의 전년동기 대비 감소율이 임계값 이하여야 한다.",
        "- 잠긴 2025 테스트 통계는 임계값 선택에서 제외했다.",
        "",
        f"- 전체 생성 가능 행: {eligibility['eligible_rows_all']:,}",
        f"- 개발기간 생성 가능 행: {eligibility['eligible_rows_development']:,}",
        f"- Target 종료기간: {eligibility['target_end_period_min']}~{eligibility['target_end_period_max']}",
        "",
        "| 합산 감소 기준 | 개발 양성률 | 2022~2023 양성률 | 2024 양성률 | 시기 차이 | Fold별 최소 양성/음성 행 |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
        *table,
        "",
        "## 시간순 Fold",
        "",
        "두 분기 Target 창이 학습과 검증에서 겹치지 않도록 한 분기 Purge를 적용한다.",
        "",
        "- Fold 1: 학습 Target 종료 2022Q2~2023Q3 → 검증 종료 2024Q1",
        "- Fold 2: 학습 Target 종료 2022Q2~2023Q4 → 검증 종료 2024Q2",
        "- Fold 3: 학습 Target 종료 2022Q2~2024Q1 → 검증 종료 2024Q3",
        "- Fold 4: 학습 Target 종료 2022Q2~2024Q2 → 검증 종료 2024Q4",
        "- 최종 재학습 종료: 2024Q3",
        "- 잠긴 최종 테스트 Target 종료: 2025Q1~2025Q4",
        "",
        "최종 임계값은 사용자 승인 전까지 설정하지 않는다.",
        "",
    ]
    (REPORT_DIR / "persistent_target_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        eligibility = prepare(connection)
        frame = sensitivity(connection)
        folds = by_fold(connection)
        frame.to_csv(
            REPORT_DIR / "persistent_target_sensitivity.csv",
            index=False,
            encoding="utf-8-sig",
        )
        folds.to_csv(
            REPORT_DIR / "persistent_target_by_fold.csv",
            index=False,
            encoding="utf-8-sig",
        )
        write_report(eligibility, frame)
        manifest = {
            "created_at_kst": datetime.now(
                ZoneInfo("Asia/Seoul")
            ).isoformat(timespec="minutes"),
            "target_structure_approved": True,
            "target_threshold_approved": False,
            "definition": {
                "future_quarters": 2,
                "both_quarters_yoy_negative": True,
                "combined_yoy_threshold": None,
            },
            "eligibility": eligibility,
            "locked_test_statistics_used_for_selection": False,
        }
        (REPORT_DIR / "persistent_target_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "status": "persistent_target_analysis_completed",
                    "eligibility": eligibility,
                    "threshold_rows": len(frame),
                },
                ensure_ascii=False,
            )
        )
    finally:
        connection.close()


if __name__ == "__main__":
    main()
