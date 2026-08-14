"""Build the approved Stage 4 Target data and chronological fold membership.

The large Stage 3 panel is read from SQLite and written in 20,000-row chunks.
Locked 2025 Target values are deliberately not materialized or summarized.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config" / "stage4.yaml"
DATABASE_PATH = PROJECT_ROOT / "data" / "interim" / "stage3_panel.sqlite"
STAGE3_PATH = PROJECT_ROOT / "data" / "processed" / "stage3_panel.parquet"
DEVELOPMENT_PATH = PROJECT_ROOT / "data" / "processed" / "stage4_development.parquet"
LOCKED_FEATURES_PATH = (
    PROJECT_ROOT / "data" / "processed" / "stage4_locked_test_features.parquet"
)
FOLD_PATH = PROJECT_ROOT / "data" / "processed" / "stage4_fold_membership.parquet"
REPORT_DIR = PROJECT_ROOT / "reports" / "stage4"
MANIFEST_PATH = REPORT_DIR / "stage4_manifest.json"
DEFINITION_PATH = REPORT_DIR / "target_definition.md"
FOLD_SUMMARY_PATH = REPORT_DIR / "fold_summary.csv"
CHUNK_SIZE = 20_000

PERIOD = "기준_년분기_코드"
AREA = "상권_코드"
INDUSTRY = "서비스_업종_코드"
TARGET = "target_persistent_decline"
METADATA_COLUMNS = [
    "stage4_row_id",
    "target_start_period",
    "target_end_period",
    "final_partition",
]


def quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def load_config() -> dict[str, object]:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    status = config["status"]
    target = config["target"]
    if status["cv_design"] != "approved":
        raise RuntimeError("Stage 4 CV design is not approved.")
    if status["target_threshold"] != "approved":
        raise RuntimeError("Stage 4 Target threshold is not approved.")
    threshold = target.get("threshold")
    if threshold is None or not 0 < float(threshold) < 1:
        raise RuntimeError("Approved Target threshold must be between 0 and 1.")
    return config


def table_columns(connection: sqlite3.Connection, table: str) -> list[str]:
    return [row[1] for row in connection.execute(f"PRAGMA table_info({quote(table)})")]


def prepare_labels(connection: sqlite3.Connection, threshold: float) -> None:
    connection.execute("PRAGMA temp_store=FILE")
    connection.execute("DROP TABLE IF EXISTS temp.stage4_indexed")
    connection.execute(
        f"""
        CREATE TEMP TABLE stage4_indexed AS
        SELECT
            {quote(PERIOD)} AS period,
            CAST(substr({quote(PERIOD)},1,4) AS INTEGER)*4
              + CAST(substr({quote(PERIOD)},5,1) AS INTEGER)-1 AS period_index,
            {quote(AREA)} AS area,
            {quote(INDUSTRY)} AS industry,
            {quote('당월_매출_금액')} AS sales
        FROM core_features
        """
    )
    connection.execute(
        "CREATE UNIQUE INDEX temp.idx_stage4_indexed "
        "ON stage4_indexed(period_index,area,industry)"
    )
    connection.execute("DROP TABLE IF EXISTS temp.stage4_labels")
    connection.execute(
        """
        CREATE TEMP TABLE stage4_labels AS
        WITH eligible AS (
            SELECT
                c.period AS feature_period,
                f1.period AS target_start_period,
                f2.period AS target_end_period,
                c.area,
                c.industry,
                f1.sales AS future_q1_sales,
                f2.sales AS future_q2_sales,
                p1.sales AS year_ago_q1_sales,
                p2.sales AS year_ago_q2_sales
            FROM stage4_indexed c
            JOIN stage4_indexed f1
              ON f1.period_index=c.period_index+1
             AND f1.area=c.area AND f1.industry=c.industry
            JOIN stage4_indexed f2
              ON f2.period_index=c.period_index+2
             AND f2.area=c.area AND f2.industry=c.industry
            JOIN stage4_indexed p1
              ON p1.period_index=c.period_index-3
             AND p1.area=c.area AND p1.industry=c.industry
            JOIN stage4_indexed p2
              ON p2.period_index=c.period_index-2
             AND p2.area=c.area AND p2.industry=c.industry
            WHERE p1.sales>0 AND p2.sales>0 AND p1.sales+p2.sales>0
        )
        SELECT
            ROW_NUMBER() OVER (
                ORDER BY feature_period,area,industry
            ) AS stage4_row_id,
            feature_period,
            target_start_period,
            target_end_period,
            area,
            industry,
            CASE
                WHEN target_end_period BETWEEN '20222' AND '20244' THEN
                    CASE WHEN future_q1_sales < year_ago_q1_sales
                               AND future_q2_sales < year_ago_q2_sales
                               AND (future_q1_sales+future_q2_sales
                                    -year_ago_q1_sales-year_ago_q2_sales)*1.0
                                   /(year_ago_q1_sales+year_ago_q2_sales) <= ?
                         THEN 1 ELSE 0 END
                ELSE NULL
            END AS target_persistent_decline,
            CASE
                WHEN target_end_period BETWEEN '20222' AND '20243' THEN 'refit'
                WHEN target_end_period='20244' THEN 'purge'
                WHEN target_end_period BETWEEN '20251' AND '20254' THEN 'locked_test'
            END AS final_partition,
            future_q1_sales,
            future_q2_sales,
            year_ago_q1_sales,
            year_ago_q2_sales
        FROM eligible
        """,
        (-threshold,),
    )
    connection.execute(
        "CREATE UNIQUE INDEX temp.idx_stage4_labels_key "
        "ON stage4_labels(feature_period,area,industry)"
    )
    connection.execute(
        "CREATE UNIQUE INDEX temp.idx_stage4_labels_row "
        "ON stage4_labels(stage4_row_id)"
    )


def append_table(
    writer: pq.ParquetWriter,
    records: list[tuple[object, ...]],
    columns: list[str],
    schema: pa.Schema,
) -> None:
    frame = pd.DataFrame.from_records(records, columns=columns)
    arrays: list[pa.Array] = []
    for column, field in zip(columns, schema):
        if pa.types.is_string(field.type):
            arrays.append(
                pa.array(frame[column].astype("string"), type=field.type, from_pandas=True)
            )
        else:
            arrays.append(
                pa.array(
                    pd.to_numeric(frame[column], errors="coerce"),
                    type=field.type,
                    from_pandas=True,
                )
            )
    writer.write_table(pa.Table.from_arrays(arrays, schema=schema))


def export_query(
    connection: sqlite3.Connection,
    sql: str,
    output_path: Path,
    schema: pa.Schema,
) -> int:
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    cursor = connection.execute(sql)
    columns = [item[0] for item in cursor.description]
    if columns != schema.names:
        raise RuntimeError(f"Schema mismatch for {output_path.name}.")
    writer = pq.ParquetWriter(temporary_path, schema=schema, compression="zstd")
    row_count = 0
    try:
        while True:
            records = cursor.fetchmany(CHUNK_SIZE)
            if not records:
                break
            append_table(writer, records, columns, schema)
            row_count += len(records)
    finally:
        writer.close()
    temporary_path.replace(output_path)
    return row_count


def build_outputs(
    connection: sqlite3.Connection, config: dict[str, object]
) -> tuple[dict[str, int], list[str]]:
    stage3_schema = pq.ParquetFile(STAGE3_PATH).schema_arrow
    feature_columns = stage3_schema.names
    panel_columns = table_columns(connection, "panel_final")
    if panel_columns != feature_columns:
        raise RuntimeError("Stage 3 SQLite and Parquet feature schemas differ.")

    development_schema = pa.schema(
        [pa.field("stage4_row_id", pa.int64())]
        + list(stage3_schema)
        + [
            pa.field("target_start_period", pa.string()),
            pa.field("target_end_period", pa.string()),
            pa.field("final_partition", pa.string()),
            pa.field(TARGET, pa.int8()),
        ]
    )
    locked_schema = pa.schema(
        [pa.field("stage4_row_id", pa.int64())]
        + list(stage3_schema)
        + [
            pa.field("target_start_period", pa.string()),
            pa.field("target_end_period", pa.string()),
            pa.field("final_partition", pa.string()),
        ]
    )
    feature_select = ",".join(f"p.{quote(column)}" for column in panel_columns)
    join = (
        f"FROM stage4_labels l JOIN panel_final p "
        f"ON p.{quote(PERIOD)}=l.feature_period "
        f"AND p.{quote(AREA)}=l.area AND p.{quote(INDUSTRY)}=l.industry "
    )
    order = "ORDER BY l.stage4_row_id"
    development_sql = (
        f"SELECT l.stage4_row_id,{feature_select},l.target_start_period,"
        f"l.target_end_period,l.final_partition,l.{TARGET} "
        + join
        + "WHERE l.target_end_period BETWEEN '20222' AND '20244' "
        + order
    )
    locked_sql = (
        f"SELECT l.stage4_row_id,{feature_select},l.target_start_period,"
        "l.target_end_period,l.final_partition "
        + join
        + "WHERE l.target_end_period BETWEEN '20251' AND '20254' "
        + order
    )
    counts = {
        "development_rows": export_query(
            connection, development_sql, DEVELOPMENT_PATH, development_schema
        ),
        "locked_test_feature_rows": export_query(
            connection, locked_sql, LOCKED_FEATURES_PATH, locked_schema
        ),
    }

    fold_schema = pa.schema(
        [
            pa.field("stage4_row_id", pa.int64()),
            pa.field("fold", pa.int8()),
            pa.field("partition", pa.string()),
        ]
    )
    fold_selects = []
    for fold in config["cross_validation"]["folds"]:
        number = int(fold["fold"])
        train_start, train_end = map(str, fold["train_target_end_period"])
        validation_start, validation_end = map(
            str, fold["validation_target_end_period"]
        )
        fold_selects.extend(
            [
                "SELECT stage4_row_id,"
                f"{number} AS fold,'train' AS partition FROM stage4_labels "
                f"WHERE target_end_period BETWEEN '{train_start}' AND '{train_end}'",
                "SELECT stage4_row_id,"
                f"{number} AS fold,'validation' AS partition FROM stage4_labels "
                f"WHERE target_end_period BETWEEN '{validation_start}' AND '{validation_end}'",
            ]
        )
    fold_sql = " UNION ALL ".join(fold_selects) + " ORDER BY fold,partition,stage4_row_id"
    counts["fold_membership_rows"] = export_query(
        connection, fold_sql, FOLD_PATH, fold_schema
    )
    return counts, feature_columns


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_and_summarize(
    connection: sqlite3.Connection,
    config: dict[str, object],
    counts: dict[str, int],
    feature_columns: list[str],
) -> tuple[dict[str, object], pd.DataFrame]:
    eligibility = connection.execute(
        "SELECT COUNT(*),"
        "SUM(target_end_period BETWEEN '20222' AND '20244'),"
        "SUM(target_end_period BETWEEN '20251' AND '20254') FROM stage4_labels"
    ).fetchone()
    duplicate_keys = connection.execute(
        "SELECT COUNT(*) FROM (SELECT feature_period,area,industry,COUNT(*) n "
        "FROM stage4_labels GROUP BY feature_period,area,industry HAVING n>1)"
    ).fetchone()[0]
    null_keys = connection.execute(
        "SELECT COUNT(*) FROM stage4_labels WHERE feature_period IS NULL "
        "OR area IS NULL OR industry IS NULL"
    ).fetchone()[0]
    mismatch = connection.execute(
        """
        SELECT COUNT(*) FROM stage4_labels
        WHERE target_end_period BETWEEN '20222' AND '20244'
          AND target_persistent_decline != CASE
                WHEN future_q1_sales < year_ago_q1_sales
                 AND future_q2_sales < year_ago_q2_sales
                 AND (future_q1_sales+future_q2_sales
                      -year_ago_q1_sales-year_ago_q2_sales)*1.0
                     /(year_ago_q1_sales+year_ago_q2_sales) <= ?
                THEN 1 ELSE 0 END
        """,
        (-float(config["target"]["threshold"]),),
    ).fetchone()[0]
    development_total, development_positive = connection.execute(
        "SELECT COUNT(*),SUM(target_persistent_decline) FROM stage4_labels "
        "WHERE target_end_period BETWEEN '20222' AND '20244'"
    ).fetchone()
    locked_target_exposed = TARGET in pq.ParquetFile(LOCKED_FEATURES_PATH).schema_arrow.names
    forbidden_feature_columns = [
        column
        for column in feature_columns
        if column in {TARGET, "target_start_period", "target_end_period"}
        or column.startswith("future_")
        or column.startswith("year_ago_q")
    ]

    summary_rows: list[dict[str, object]] = []
    membership = pq.ParquetFile(FOLD_PATH)
    membership_frame = membership.read().to_pandas()
    development_keys = pd.read_parquet(
        DEVELOPMENT_PATH,
        columns=["stage4_row_id", "target_end_period", TARGET],
    )
    merged = membership_frame.merge(
        development_keys, on="stage4_row_id", how="left", validate="many_to_one"
    )
    folds_valid = True
    for fold in config["cross_validation"]["folds"]:
        number = int(fold["fold"])
        for partition, period_key in (
            ("train", "train_target_end_period"),
            ("validation", "validation_target_end_period"),
        ):
            subset = merged[
                (merged["fold"] == number) & (merged["partition"] == partition)
            ]
            expected_start, expected_end = map(str, fold[period_key])
            actual_start = str(subset["target_end_period"].min())
            actual_end = str(subset["target_end_period"].max())
            folds_valid &= actual_start == expected_start and actual_end == expected_end
            summary_rows.append(
                {
                    "fold": number,
                    "partition": partition,
                    "target_end_start": actual_start,
                    "target_end_end": actual_end,
                    "rows": len(subset),
                    "positive_rows": int(subset[TARGET].sum()),
                    "positive_rate": float(subset[TARGET].mean()),
                }
            )
    fold_summary = pd.DataFrame(summary_rows)

    gate_passed = all(
        [
            int(eligibility[0]) == 302_479,
            int(eligibility[1]) == counts["development_rows"],
            int(eligibility[2]) == counts["locked_test_feature_rows"],
            duplicate_keys == 0,
            null_keys == 0,
            mismatch == 0,
            not locked_target_exposed,
            not forbidden_feature_columns,
            folds_valid,
        ]
    )
    if not gate_passed:
        raise RuntimeError("A mandatory Stage 4 verification failed.")

    verification = {
        "gate4_passed": True,
        "eligible_rows_all": int(eligibility[0]),
        "development_rows": int(development_total),
        "development_positive_rows": int(development_positive),
        "development_positive_rate": development_positive / development_total,
        "locked_test_feature_rows": counts["locked_test_feature_rows"],
        "locked_test_target_materialized": False,
        "locked_test_target_statistics_inspected": False,
        "duplicate_core_keys": int(duplicate_keys),
        "null_core_keys": int(null_keys),
        "target_formula_mismatches": int(mismatch),
        "feature_column_count": len(feature_columns),
        "future_or_target_columns_in_feature_manifest": forbidden_feature_columns,
        "fold_periods_match_config": bool(folds_valid),
    }
    return verification, fold_summary


def write_reports(
    config: dict[str, object],
    counts: dict[str, int],
    feature_columns: list[str],
    verification: dict[str, object],
    fold_summary: pd.DataFrame,
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    fold_summary.to_csv(FOLD_SUMMARY_PATH, index=False, encoding="utf-8-sig")
    example = (
        "Feature 시점이 2023Q4이면 2024Q1·Q2 매출을 각각 "
        "2023Q1·Q2와 비교한다. 두 미래 분기가 모두 감소하고, 두 분기 "
        "합산 매출이 전년동기 합계보다 10% 이상 감소하면 Target=1이다."
    )
    lines = [
        "# Stage 4 Target 정의와 시간순 검증",
        "",
        "- Target: 향후 2개 분기 지속 매출 악화",
        "- 양성 조건: 두 미래 분기가 각각 전년동기보다 감소하고, 두 분기 합산 매출도 전년동기 합계보다 10% 이상 감소",
        "- 10% 선택 근거: 두 분기 모두 감소 조건으로 일시적·계절적 하락을 먼저 거르고, 추가 10% 기준으로 미세 감소를 제외하면서 개발 양성률 25.28%와 Fold별 충분한 양성·음성 표본을 유지",
        "- 임계값 선택에는 잠긴 2025 Target 통계를 사용하지 않음",
        "- Feature 시점: 예측 기준 분기까지 관측된 Stage 3 변수만 사용",
        f"- 예시: {example}",
        f"- 개발 데이터: {verification['development_rows']:,}행, 양성 {verification['development_positive_rows']:,}행 ({verification['development_positive_rate']:.2%})",
        "- 검증: 2024Q1~Q4를 분기별 4개 expanding-window Fold로 사용하며, Target 창 중첩을 막기 위해 각 검증 직전 1개 분기를 Purge",
        "- 최종 재학습: Target 종료 2022Q2~2024Q3",
        "- 최종 Purge: Target 종료 2024Q4",
        "- 잠긴 테스트: Target 종료 2025Q1~Q4; 현재는 Feature만 생성하고 Target 값·통계는 공개하지 않음",
        "",
        "모델 입력 후보 목록은 Stage 3의 199개 열로 고정했으며, Stage 4 행 ID·기간 메타데이터·Target은 모델 입력 목록에서 제외했다.",
        "",
    ]
    DEFINITION_PATH.write_text("\n".join(lines), encoding="utf-8")
    manifest = {
        "created_at_kst": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(
            timespec="minutes"
        ),
        "status": "gate4_completed",
        "target": {
            "name": config["target"]["name"],
            "threshold": float(config["target"]["threshold"]),
            "definition": config["target"]["positive_when"],
            "split_basis": config["target"]["split_basis"],
        },
        "outputs": {
            "development": str(DEVELOPMENT_PATH.relative_to(PROJECT_ROOT)),
            "locked_test_features": str(LOCKED_FEATURES_PATH.relative_to(PROJECT_ROOT)),
            "fold_membership": str(FOLD_PATH.relative_to(PROJECT_ROOT)),
        },
        "row_counts": counts,
        "feature_columns": feature_columns,
        "metadata_columns": METADATA_COLUMNS,
        "target_column": TARGET,
        "cross_validation": config["cross_validation"],
        "final_evaluation": config["final_evaluation"],
        "verification": verification,
        "sha256": {
            "development": sha256(DEVELOPMENT_PATH),
            "locked_test_features": sha256(LOCKED_FEATURES_PATH),
            "fold_membership": sha256(FOLD_PATH),
        },
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> None:
    config = load_config()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        prepare_labels(connection, float(config["target"]["threshold"]))
        counts, feature_columns = build_outputs(connection, config)
        verification, fold_summary = verify_and_summarize(
            connection, config, counts, feature_columns
        )
        write_reports(config, counts, feature_columns, verification, fold_summary)
        print(
            json.dumps(
                {
                    "status": "stage4_completed",
                    "counts": counts,
                    "verification": verification,
                },
                ensure_ascii=False,
            )
        )
    finally:
        connection.close()


if __name__ == "__main__":
    main()
