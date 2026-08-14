"""Build the Stage 3 commercial-district × industry × quarter panel.

Processing is disk-backed through SQLite and exported to Parquet in chunks.
Raw files remain unchanged. No target is created here; that belongs to Stage 4.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import shapefile


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
INTERIM_DIR = PROJECT_ROOT / "data" / "interim"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORT_DIR = PROJECT_ROOT / "reports" / "stage3"
DATABASE_PATH = INTERIM_DIR / "stage3_panel.sqlite"
PANEL_PATH = PROCESSED_DIR / "stage3_panel.parquet"
CHUNK_SIZE = 20_000
CSV_ENCODING = "cp949"

PERIOD = "기준_년분기_코드"
AREA = "상권_코드"
INDUSTRY = "서비스_업종_코드"
CORE_KEY = ("기준_연도", "기준_분기", AREA, INDUSTRY)
QUALITY_FEATURES = (
    "전분기_매출_증감률",
    "전년동기_매출_증감률",
    "최근_2분기_매출_변화액",
    "최근_4분기_매출_선형기울기",
    "점포_증감률",
    "프랜차이즈_점포_비율",
)

STORE_2025_MAPPING = {
    "stdr_yyqu_cd": PERIOD,
    "trdar_se_cd": "상권_구분_코드",
    "trdar_se_cd_nm": "상권_구분_코드_명",
    "trdar_cd": AREA,
    "trdar_cd_nm": "상권_코드_명",
    "svc_induty_cd": INDUSTRY,
    "svc_induty_cd_nm": "서비스_업종_코드_명",
    "stor_co": "점포_수",
    "similr_induty_stor_co": "유사_업종_점포_수",
    "opbiz_rt": "개업_율",
    "opbiz_stor_co": "개업_점포_수",
    "clsbiz_rt": "폐업_률",
    "clsbiz_stor_co": "폐업_점포_수",
    "frc_stor_co": "프랜차이즈_점포_수",
}

AUXILIARY = {
    "flow": ("길단위인구-상권", "유동"),
    "change": ("상권변화지표-상권", "변화"),
    "resident": ("상주인구-상권", "상주"),
    "worker": ("직장인구-상권", "직장"),
    "facility": ("집객시설-상권", "시설"),
    "apartment": ("아파트-상권", "아파트"),
}

DIMENSION_COLUMNS = {
    PERIOD,
    "상권_구분_코드",
    "상권_구분_코드_명",
    AREA,
    "상권_코드_명",
    INDUSTRY,
    "서비스_업종_코드_명",
}


def quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def normalize_code(series: pd.Series) -> pd.Series:
    result = series.astype("string").str.strip()
    return result.str.replace(r"\.0$", "", regex=True)


def is_numeric_column(column: str) -> bool:
    if column in DIMENSION_COLUMNS or column in {
        "상권_변화_지표",
        "상권_변화_지표_명",
    }:
        return False
    return any(
        token in column
        for token in (
            "금액",
            "건수",
            "점포_수",
            "인구_수",
            "시설_수",
            "_수",
            "_율",
            "_률",
            "개월_평균",
            "평균_면적",
            "평균_시가",
        )
    )


def standardize_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    if set(STORE_2025_MAPPING).issubset(chunk.columns):
        chunk = chunk.rename(columns=STORE_2025_MAPPING)
    for column in chunk.columns:
        if column in DIMENSION_COLUMNS or column in {
            "상권_변화_지표",
            "상권_변화_지표_명",
            "자치구_코드",
            "상권배후지_코드",
        }:
            chunk[column] = normalize_code(chunk[column])
        elif is_numeric_column(column):
            chunk[column] = pd.to_numeric(chunk[column], errors="coerce")
        else:
            chunk[column] = chunk[column].astype("string").str.strip()
    return chunk


def iter_csv(path: Path):
    for chunk in pd.read_csv(
        path,
        encoding=CSV_ENCODING,
        dtype=str,
        keep_default_na=False,
        chunksize=CHUNK_SIZE,
        low_memory=False,
    ):
        yield standardize_chunk(chunk)


def find_one(fragment: str) -> Path:
    matches = [
        path
        for path in RAW_DIR.glob(f"*{fragment}*.csv")
        if "자치구" not in path.name and "상권배후지" not in path.name
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one file for {fragment!r}; found {len(matches)}")
    return matches[0]


def load_csv_table(
    connection: sqlite3.Connection,
    table: str,
    paths: list[Path],
) -> tuple[int, list[str]]:
    connection.execute(f"DROP TABLE IF EXISTS {quote(table)}")
    row_count = 0
    expected_columns: list[str] | None = None
    first = True
    for path in paths:
        for chunk in iter_csv(path):
            columns = chunk.columns.tolist()
            if expected_columns is None:
                expected_columns = columns
            elif columns != expected_columns:
                raise RuntimeError(f"Standardized schema mismatch in {path.name}")
            chunk.to_sql(
                table,
                connection,
                if_exists="replace" if first else "append",
                index=False,
                chunksize=1_000,
            )
            first = False
            row_count += len(chunk)
    if first or expected_columns is None:
        raise RuntimeError(f"No rows loaded for {table}")
    connection.commit()
    return row_count, expected_columns


def load_spatial_attributes(connection: sqlite3.Connection) -> int:
    shp_path = next(RAW_DIR.rglob("*.shp"))
    encoding = shp_path.with_suffix(".cpg").read_text(encoding="ascii").strip()
    reader = shapefile.Reader(str(shp_path), encoding=encoding)
    fields = [field[0] for field in reader.fields if field[0] != "DeletionFlag"]
    mapping = {
        "TRDAR_SE_C": "공간__상권_구분_코드",
        "TRDAR_SE_1": "공간__상권_구분_코드_명",
        "TRDAR_CD": AREA,
        "TRDAR_CD_N": "공간__상권_코드_명",
        "XCNTS_VALU": "공간__중심_X",
        "YDNTS_VALU": "공간__중심_Y",
        "SIGNGU_CD": "공간__자치구_코드",
        "SIGNGU_CD_": "공간__자치구_명",
        "ADSTRD_CD": "공간__행정동_코드",
        "ADSTRD_CD_": "공간__행정동_명",
        "RELM_AR": "공간__면적",
    }
    records = []
    for record in reader.iterRecords():
        row = dict(zip(fields, record))
        records.append({mapping[column]: row[column] for column in mapping})
    frame = pd.DataFrame(records)
    for column in frame.columns:
        if column in {"공간__중심_X", "공간__중심_Y", "공간__면적"}:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        else:
            frame[column] = normalize_code(frame[column])
    connection.execute("DROP TABLE IF EXISTS spatial")
    frame.to_sql("spatial", connection, if_exists="replace", index=False, chunksize=1_000)
    connection.execute(f"CREATE UNIQUE INDEX idx_spatial_key ON spatial ({quote(AREA)})")
    connection.commit()
    return len(frame)


def table_columns(connection: sqlite3.Connection, table: str) -> list[str]:
    return [row[1] for row in connection.execute(f"PRAGMA table_info({quote(table)})")]


def create_indexes(connection: sqlite3.Connection) -> None:
    connection.execute(
        f"CREATE UNIQUE INDEX idx_sales_key ON sales ({quote(PERIOD)}, {quote(AREA)}, {quote(INDUSTRY)})"
    )
    connection.execute(
        f"CREATE UNIQUE INDEX idx_store_key ON store ({quote(PERIOD)}, {quote(AREA)}, {quote(INDUSTRY)})"
    )
    for table in AUXILIARY:
        connection.execute(
            f"CREATE UNIQUE INDEX idx_{table}_key ON {quote(table)} ({quote(PERIOD)}, {quote(AREA)})"
        )
    connection.commit()


def create_core_feature_table(connection: sqlite3.Connection) -> None:
    connection.execute("DROP TABLE IF EXISTS core_base")
    sales_feature_columns = [
        column
        for column in table_columns(connection, "sales")
        if column not in DIMENSION_COLUMNS
    ]
    store_feature_columns = [
        column
        for column in table_columns(connection, "store")
        if column not in DIMENSION_COLUMNS
    ]
    sales_select = ",\n        ".join(
        f"s.{quote(column)} AS {quote(column)}" for column in sales_feature_columns
    )
    store_select = ",\n        ".join(
        f"t.{quote(column)} AS {quote(column)}" for column in store_feature_columns
    )
    connection.execute(
        f"""
        CREATE TABLE core_base AS
        SELECT
            CAST(substr(s.{quote(PERIOD)}, 1, 4) AS INTEGER) AS {quote('기준_연도')},
            CAST(substr(s.{quote(PERIOD)}, 5, 1) AS INTEGER) AS {quote('기준_분기')},
            s.{quote(PERIOD)} AS {quote(PERIOD)},
            s.{quote('상권_구분_코드')} AS {quote('상권_구분_코드')},
            s.{quote('상권_구분_코드_명')} AS {quote('상권_구분_코드_명')},
            s.{quote(AREA)} AS {quote(AREA)},
            s.{quote('상권_코드_명')} AS {quote('상권_코드_명')},
            s.{quote(INDUSTRY)} AS {quote(INDUSTRY)},
            s.{quote('서비스_업종_코드_명')} AS {quote('서비스_업종_코드_명')},
            {sales_select},
            {store_select},
            CASE WHEN t.{quote(PERIOD)} IS NULL THEN 0 ELSE 1 END AS {quote('점포_결합_여부')}
        FROM sales s
        LEFT JOIN store t
          ON s.{quote(PERIOD)} = t.{quote(PERIOD)}
         AND s.{quote(AREA)} = t.{quote(AREA)}
         AND s.{quote(INDUSTRY)} = t.{quote(INDUSTRY)}
        """
    )
    connection.execute(
        f"CREATE UNIQUE INDEX idx_core_key ON core_base ({quote(PERIOD)}, {quote(AREA)}, {quote(INDUSTRY)})"
    )
    connection.commit()

    connection.execute("DROP TABLE IF EXISTS core_features")
    connection.execute(
        f"""
        CREATE TABLE core_features AS
        WITH history AS (
            SELECT
                c.*,
                LAG({quote(PERIOD)}, 1) OVER w AS lag1_period,
                LAG({quote(PERIOD)}, 2) OVER w AS lag2_period,
                LAG({quote(PERIOD)}, 3) OVER w AS lag3_period,
                LAG({quote(PERIOD)}, 4) OVER w AS lag4_period,
                LAG({quote('당월_매출_금액')}, 1) OVER w AS lag1_sales,
                LAG({quote('당월_매출_금액')}, 2) OVER w AS lag2_sales,
                LAG({quote('당월_매출_금액')}, 3) OVER w AS lag3_sales,
                LAG({quote('당월_매출_금액')}, 4) OVER w AS lag4_sales,
                LAG({quote('점포_수')}, 1) OVER w AS lag1_store
            FROM core_base c
            WINDOW w AS (PARTITION BY {quote(AREA)}, {quote(INDUSTRY)} ORDER BY {quote(PERIOD)})
        ), marked AS (
            SELECT
                h.*,
                ({quote('기준_연도')} * 4 + {quote('기준_분기')} - 1) AS period_index,
                CASE WHEN lag1_period IS NULL THEN NULL
                     ELSE CAST(substr(lag1_period,1,4) AS INTEGER)*4 + CAST(substr(lag1_period,5,1) AS INTEGER)-1 END AS lag1_index,
                CASE WHEN lag2_period IS NULL THEN NULL
                     ELSE CAST(substr(lag2_period,1,4) AS INTEGER)*4 + CAST(substr(lag2_period,5,1) AS INTEGER)-1 END AS lag2_index,
                CASE WHEN lag3_period IS NULL THEN NULL
                     ELSE CAST(substr(lag3_period,1,4) AS INTEGER)*4 + CAST(substr(lag3_period,5,1) AS INTEGER)-1 END AS lag3_index,
                CASE WHEN lag4_period IS NULL THEN NULL
                     ELSE CAST(substr(lag4_period,1,4) AS INTEGER)*4 + CAST(substr(lag4_period,5,1) AS INTEGER)-1 END AS lag4_index
            FROM history h
        )
        SELECT
            {', '.join(quote(column) for column in table_columns(connection, 'core_base'))},
            CASE WHEN lag1_index = period_index - 1 THEN 1 ELSE 0 END AS {quote('전분기_연속_여부')},
            CASE WHEN lag1_index = period_index - 1 AND lag2_index = period_index - 2
                       AND lag3_index = period_index - 3 THEN 1 ELSE 0 END AS {quote('최근_4분기_연속_여부')},
            CASE WHEN lag1_index = period_index - 1 AND lag1_sales <> 0
                 THEN ({quote('당월_매출_금액')} - lag1_sales) * 1.0 / lag1_sales END AS {quote('전분기_매출_증감률')},
            CASE WHEN lag4_index = period_index - 4 AND lag4_sales <> 0
                 THEN ({quote('당월_매출_금액')} - lag4_sales) * 1.0 / lag4_sales END AS {quote('전년동기_매출_증감률')},
            CASE WHEN lag1_index = period_index - 1
                 THEN {quote('당월_매출_금액')} - lag1_sales END AS {quote('최근_2분기_매출_변화액')},
            CASE WHEN lag1_index = period_index - 1 AND lag2_index = period_index - 2
                       AND lag3_index = period_index - 3
                 THEN (3.0 * {quote('당월_매출_금액')} + lag1_sales - lag2_sales - 3.0 * lag3_sales) / 10.0
                 END AS {quote('최근_4분기_매출_선형기울기')},
            CASE WHEN {quote('당월_매출_금액')} > 0
                 THEN {quote('주말_매출_금액')} * 1.0 / {quote('당월_매출_금액')} END AS {quote('주말_매출_비중')},
            CASE WHEN lag1_index = period_index - 1 AND lag1_store <> 0
                 THEN ({quote('점포_수')} - lag1_store) * 1.0 / lag1_store END AS {quote('점포_증감률')},
            CASE WHEN {quote('유사_업종_점포_수')} > 0
                 THEN {quote('프랜차이즈_점포_수')} * 1.0 / {quote('유사_업종_점포_수')} END AS {quote('프랜차이즈_점포_비율')}
        FROM marked
        """
    )
    connection.execute(
        f"CREATE UNIQUE INDEX idx_core_features_key ON core_features ({quote(PERIOD)}, {quote(AREA)}, {quote(INDUSTRY)})"
    )
    connection.commit()


def auxiliary_selects(connection: sqlite3.Connection) -> tuple[list[str], list[str]]:
    selects: list[str] = []
    joins: list[str] = []
    excluded = {PERIOD, AREA, "상권_구분_코드", "상권_구분_코드_명", "상권_코드_명"}
    for table, (_, prefix) in AUXILIARY.items():
        feature_columns = [column for column in table_columns(connection, table) if column not in excluded]
        selects.extend(
            f"{quote(table)}.{quote(column)} AS {quote(prefix + '__' + column)}"
            for column in feature_columns
        )
        selects.append(
            f"CASE WHEN {quote(table)}.{quote(PERIOD)} IS NULL THEN 0 ELSE 1 END AS {quote(prefix + '__결합_여부')}"
        )
        joins.append(
            f"LEFT JOIN {quote(table)} ON c.{quote(PERIOD)}={quote(table)}.{quote(PERIOD)} "
            f"AND c.{quote(AREA)}={quote(table)}.{quote(AREA)}"
        )
    spatial_columns = [column for column in table_columns(connection, "spatial") if column != AREA]
    selects.extend(f"spatial.{quote(column)} AS {quote(column)}" for column in spatial_columns)
    selects.append(
        f"CASE WHEN spatial.{quote(AREA)} IS NULL THEN 0 ELSE 1 END AS {quote('공간__결합_여부')}"
    )
    joins.append(f"LEFT JOIN spatial ON c.{quote(AREA)}=spatial.{quote(AREA)}")
    return selects, joins


def create_final_table(connection: sqlite3.Connection) -> None:
    selects, joins = auxiliary_selects(connection)
    connection.execute("DROP TABLE IF EXISTS panel_final")
    connection.execute(
        "CREATE TABLE panel_final AS SELECT c.*,\n"
        + ",\n".join(selects)
        + "\nFROM core_features c\n"
        + "\n".join(joins)
    )
    connection.execute(
        f"CREATE UNIQUE INDEX idx_panel_final_key ON panel_final ({quote('기준_연도')}, {quote('기준_분기')}, {quote(AREA)}, {quote(INDUSTRY)})"
    )
    connection.commit()


def arrow_type(column: str) -> pa.DataType:
    text_columns = {
        PERIOD,
        "상권_구분_코드",
        "상권_구분_코드_명",
        AREA,
        "상권_코드_명",
        INDUSTRY,
        "서비스_업종_코드_명",
        "변화__상권_변화_지표",
        "변화__상권_변화_지표_명",
        "공간__상권_구분_코드",
        "공간__상권_구분_코드_명",
        "공간__상권_코드_명",
        "공간__자치구_코드",
        "공간__자치구_명",
        "공간__행정동_코드",
        "공간__행정동_명",
    }
    if column in text_columns:
        return pa.string()
    if column in {"기준_연도", "기준_분기"} or column.endswith("결합_여부") or column.endswith("연속_여부"):
        return pa.int64()
    return pa.float64()


def export_parquet(connection: sqlite3.Connection) -> tuple[int, list[str], str]:
    columns = table_columns(connection, "panel_final")
    schema = pa.schema([(column, arrow_type(column)) for column in columns])
    cursor = connection.execute(
        f"SELECT * FROM panel_final ORDER BY {quote('기준_연도')}, {quote('기준_분기')}, {quote(AREA)}, {quote(INDUSTRY)}"
    )
    writer = pq.ParquetWriter(PANEL_PATH, schema=schema, compression="zstd")
    row_count = 0
    try:
        while True:
            records = cursor.fetchmany(CHUNK_SIZE)
            if not records:
                break
            arrays = []
            frame = pd.DataFrame.from_records(records, columns=columns)
            for column, field in zip(columns, schema):
                if pa.types.is_string(field.type):
                    arrays.append(pa.array(frame[column].astype("string"), type=field.type, from_pandas=True))
                else:
                    arrays.append(pa.array(pd.to_numeric(frame[column], errors="coerce"), type=field.type, from_pandas=True))
            writer.write_table(pa.Table.from_arrays(arrays, schema=schema))
            row_count += len(records)
    finally:
        writer.close()
    digest = hashlib.sha256()
    with PANEL_PATH.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return row_count, columns, digest.hexdigest()


def write_feature_quality() -> None:
    """Summarize selected derived features without loading the panel in full."""
    sample_limit = 50_000
    rng = np.random.default_rng(20260814)
    state = {
        column: {"seen": 0, "null": 0, "sample": [], "min": math.inf, "max": -math.inf}
        for column in QUALITY_FEATURES
    }
    parquet_file = pq.ParquetFile(PANEL_PATH)
    for batch in parquet_file.iter_batches(batch_size=CHUNK_SIZE, columns=list(QUALITY_FEATURES)):
        frame = batch.to_pandas()
        for column in QUALITY_FEATURES:
            values = pd.to_numeric(frame[column], errors="coerce")
            item = state[column]
            item["null"] += int(values.isna().sum())
            for value in values.dropna().to_numpy(dtype=float):
                item["seen"] += 1
                item["min"] = min(item["min"], value)
                item["max"] = max(item["max"], value)
                if len(item["sample"]) < sample_limit:
                    item["sample"].append(value)
                else:
                    position = int(rng.integers(0, item["seen"]))
                    if position < sample_limit:
                        item["sample"][position] = value
    rows = []
    for column in QUALITY_FEATURES:
        item = state[column]
        sample = np.asarray(item["sample"], dtype=float)
        quantiles = np.quantile(sample, [0.01, 0.05, 0.5, 0.95, 0.99]) if len(sample) else [None] * 5
        rows.append(
            {
                "feature": column,
                "non_null_count": item["seen"],
                "null_count": item["null"],
                "null_rate": item["null"] / parquet_file.metadata.num_rows,
                "min": None if item["seen"] == 0 else item["min"],
                "p01": quantiles[0],
                "p05": quantiles[1],
                "median": quantiles[2],
                "p95": quantiles[3],
                "p99": quantiles[4],
                "max": None if item["seen"] == 0 else item["max"],
                "quantile_sample_size": len(sample),
                "extreme_value_rule": "통계 요약만 기록, 자동 제거 없음",
            }
        )
    pd.DataFrame(rows).to_csv(
        REPORT_DIR / "feature_quality.csv", index=False, encoding="utf-8-sig"
    )


def verify_panel(connection: sqlite3.Connection, expected_rows: int) -> dict[str, object]:
    final_rows = connection.execute("SELECT COUNT(*) FROM panel_final").fetchone()[0]
    duplicate_keys = connection.execute(
        f"SELECT COUNT(*) FROM (SELECT {', '.join(quote(column) for column in CORE_KEY)}, COUNT(*) c "
        f"FROM panel_final GROUP BY {', '.join(quote(column) for column in CORE_KEY)} HAVING c > 1)"
    ).fetchone()[0]
    null_keys = connection.execute(
        "SELECT COUNT(*) FROM panel_final WHERE "
        + " OR ".join(f"{quote(column)} IS NULL" for column in CORE_KEY)
    ).fetchone()[0]
    join_flags = {}
    for column in [column for column in table_columns(connection, "panel_final") if column.endswith("결합_여부")]:
        join_flags[column] = connection.execute(
            f"SELECT SUM(CASE WHEN {quote(column)}=0 THEN 1 ELSE 0 END) FROM panel_final"
        ).fetchone()[0]
    if final_rows != expected_rows or duplicate_keys or null_keys:
        raise RuntimeError(
            f"Panel QA failed: expected={expected_rows}, final={final_rows}, duplicates={duplicate_keys}, null_keys={null_keys}"
        )
    return {
        "source_sales_rows": expected_rows,
        "final_rows": final_rows,
        "duplicate_key_count": duplicate_keys,
        "null_key_rows": null_keys,
        "join_unmatched_rows": join_flags,
    }


def spot_check(connection: sqlite3.Connection) -> pd.DataFrame:
    count = connection.execute("SELECT COUNT(*) FROM panel_final").fetchone()[0]
    offsets = [0, count // 2, count - 1]
    rows = []
    for case, offset in enumerate(offsets, 1):
        key = connection.execute(
            f"SELECT {quote(PERIOD)}, {quote(AREA)}, {quote(INDUSTRY)} FROM panel_final "
            f"ORDER BY {quote(PERIOD)}, {quote(AREA)}, {quote(INDUSTRY)} LIMIT 1 OFFSET ?",
            (offset,),
        ).fetchone()
        period, area, industry = key
        current = connection.execute(
            f"SELECT {quote('당월_매출_금액')}, {quote('점포_수')} FROM sales s "
            f"JOIN store t USING ({quote(PERIOD)}, {quote(AREA)}, {quote(INDUSTRY)}) "
            f"WHERE s.{quote(PERIOD)}=? AND s.{quote(AREA)}=? AND s.{quote(INDUSTRY)}=?",
            key,
        ).fetchone()
        panel = connection.execute(
            f"SELECT {quote('당월_매출_금액')}, {quote('점포_수')}, {quote('전분기_매출_증감률')} "
            f"FROM panel_final WHERE {quote(PERIOD)}=? AND {quote(AREA)}=? AND {quote(INDUSTRY)}=?",
            key,
        ).fetchone()
        previous_period = (
            f"{int(period[:4]) - 1}4" if period[4] == "1" else f"{period[:4]}{int(period[4]) - 1}"
        )
        previous = connection.execute(
            f"SELECT {quote('당월_매출_금액')} FROM sales WHERE {quote(PERIOD)}=? AND {quote(AREA)}=? AND {quote(INDUSTRY)}=?",
            (previous_period, area, industry),
        ).fetchone()
        manual_growth = None
        if previous and previous[0] not in (None, 0):
            manual_growth = (current[0] - previous[0]) / previous[0]
        growth_match = (
            manual_growth is None and panel[2] is None
        ) or (
            manual_growth is not None and panel[2] is not None and abs(manual_growth - panel[2]) < 1e-12
        )
        rows.append(
            {
                "case": case,
                PERIOD: period,
                AREA: area,
                INDUSTRY: industry,
                "원본_매출": current[0],
                "패널_매출": panel[0],
                "원본_점포": current[1],
                "패널_점포": panel[1],
                "이전분기_원본_매출": None if previous is None else previous[0],
                "수기계산_전분기_증감률": manual_growth,
                "패널_전분기_증감률": panel[2],
                "매출_일치": current[0] == panel[0],
                "점포_일치": current[1] == panel[1],
                "증감률_일치": growth_match,
            }
        )
    frame = pd.DataFrame(rows)
    if not frame[["매출_일치", "점포_일치", "증감률_일치"]].all().all():
        raise RuntimeError("Three-case source-to-panel spot check failed")
    return frame


def source_for_column(column: str) -> str:
    if column.startswith("유동__"):
        return "길단위인구-상권"
    if column.startswith("변화__"):
        return "상권변화지표-상권"
    if column.startswith("상주__"):
        return "상주인구-상권"
    if column.startswith("직장__"):
        return "직장인구-상권"
    if column.startswith("시설__"):
        return "집객시설-상권"
    if column.startswith("아파트__"):
        return "아파트-상권"
    if column.startswith("공간__"):
        return "영역-상권"
    if column in {
        "점포_수",
        "유사_업종_점포_수",
        "개업_율",
        "개업_점포_수",
        "폐업_률",
        "폐업_점포_수",
        "프랜차이즈_점포_수",
        "점포_증감률",
        "프랜차이즈_점포_비율",
        "점포_결합_여부",
    }:
        return "점포-상권 또는 파생"
    if column in CORE_KEY or column in DIMENSION_COLUMNS:
        return "추정매출-상권 기준키"
    return "추정매출-상권 또는 과거값 파생"


def write_documents(columns: list[str], manifest: dict[str, object]) -> None:
    dictionary_rows = []
    for position, column in enumerate(columns, 1):
        dictionary_rows.append(
            {
                "position": position,
                "column": column,
                "storage_type": str(arrow_type(column)),
                "source": source_for_column(column),
                "time_scope": "현재 분기 원본" if "증감" not in column and "최근_" not in column else "현재 및 과거 분기만 사용",
            }
        )
    pd.DataFrame(dictionary_rows).to_csv(
        REPORT_DIR / "data_dictionary.csv", index=False, encoding="utf-8-sig"
    )
    feature_lines = [
        "# Stage 3 Panel Feature 정의",
        "",
        "## 기준과 누수 방지",
        "",
        "- 한 행: 연도 × 분기 × 상권코드 × 서비스업종코드",
        "- 기준 테이블: 추정매출-상권",
        "- 기간: 2021Q1~2025Q4",
        "- 모든 변화·추세 Feature는 현재 분기와 과거 분기만 사용한다.",
        "- 관측 행의 직전 레코드가 실제 직전 분기가 아니면 변화율을 결측으로 둔다.",
        "- 분모가 0이면 변화율·비율을 결측으로 둔다.",
        "- 결측치 대체와 이상치 제거는 하지 않았다.",
        "- Target은 Stage 4에서 별도로 생성한다.",
        "",
        "## 주요 파생식",
        "",
        "| Feature | 계산식 |",
        "| --- | --- |",
        "| 전분기_매출_증감률 | `(현재 매출 - 실제 직전분기 매출) / 실제 직전분기 매출` |",
        "| 전년동기_매출_증감률 | `(현재 매출 - 4분기 전 매출) / 4분기 전 매출` |",
        "| 최근_2분기_매출_변화액 | `현재 매출 - 실제 직전분기 매출` |",
        "| 최근_4분기_매출_선형기울기 | 4개 연속 분기에 대한 OLS 기울기 `(-3*y[t-3]-y[t-2]+y[t-1]+3*y[t])/10` |",
        "| 주말_매출_비중 | `주말 매출금액 / 당월 매출금액` |",
        "| 점포_증감률 | `(현재 점포 수 - 실제 직전분기 점포 수) / 실제 직전분기 점포 수` |",
        "| 프랜차이즈_점포_비율 | `프랜차이즈 점포 수 / 유사업종 점포 수` |",
        "",
        "## 결합 규칙",
        "",
        "- 점포: 기준년분기+상권코드+서비스업종코드 1:1 left join",
        "- 4~9번 상권 공통 자료: 기준년분기+상권코드 many-to-one left join",
        "- 영역 속성: 상권코드 many-to-one left join, 좌표계 EPSG:5181",
        "- 자치구 변화지표와 상권배후지 직장인구는 집계 단위가 달라 제외",
        "",
    ]
    (REPORT_DIR / "feature_definitions.md").write_text("\n".join(feature_lines), encoding="utf-8")
    (REPORT_DIR / "panel_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> None:
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=NORMAL")
    connection.execute("PRAGMA temp_store=FILE")
    source_inventory = []
    try:
        sales_paths = sorted(RAW_DIR.glob("*추정매출-상권*20??년.csv"))
        store_paths = sorted(RAW_DIR.glob("*점포-상권*20??년.csv"))
        if len(sales_paths) != 5 or len(store_paths) != 5:
            raise RuntimeError("Five annual sales and store files are required")
        sales_rows, _ = load_csv_table(connection, "sales", sales_paths)
        store_rows, _ = load_csv_table(connection, "store", store_paths)
        auxiliary_rows = {}
        for table, (fragment, _) in AUXILIARY.items():
            path = find_one(fragment)
            row_count, _ = load_csv_table(connection, table, [path])
            auxiliary_rows[table] = row_count
        spatial_rows = load_spatial_attributes(connection)
        create_indexes(connection)
        create_core_feature_table(connection)
        create_final_table(connection)
        qa = verify_panel(connection, sales_rows)
        spot = spot_check(connection)
        spot.to_csv(REPORT_DIR / "manual_spot_check.csv", index=False, encoding="utf-8-sig")
        parquet_rows, columns, digest = export_parquet(connection)
        write_feature_quality()
        parquet_file = pq.ParquetFile(PANEL_PATH)
        if parquet_file.metadata.num_rows != sales_rows or parquet_file.metadata.num_columns != len(columns):
            raise RuntimeError("Parquet metadata does not match the verified SQLite panel")
        for path in [*sales_paths, *store_paths, *(find_one(value[0]) for value in AUXILIARY.values())]:
            source_inventory.append(
                {"file": str(path.relative_to(PROJECT_ROOT)), "size_bytes": path.stat().st_size, "modified": path.stat().st_mtime_ns}
            )
        manifest = {
            "created_at_kst": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="minutes"),
            "panel": str(PANEL_PATH.relative_to(PROJECT_ROOT)),
            "row_count": parquet_rows,
            "column_count": len(columns),
            "key": list(CORE_KEY),
            "period": {"min": "20211", "max": "20254", "quarters": 20},
            "sha256": digest,
            "chunk_size": CHUNK_SIZE,
            "raw_full_memory_load": False,
            "source_sales_rows": sales_rows,
            "source_store_rows": store_rows,
            "auxiliary_rows": auxiliary_rows,
            "spatial_rows": spatial_rows,
            "qa": qa,
            "source_inventory": source_inventory,
            "excluded": ["상권변화지표-자치구", "직장인구-상권배후지"],
            "target_created": False,
        }
        write_documents(columns, manifest)
        pd.DataFrame(
            [
                {"stage": "sales source", "rows": sales_rows},
                {"stage": "after store left join", "rows": connection.execute("SELECT COUNT(*) FROM core_base").fetchone()[0]},
                {"stage": "after auxiliary left joins", "rows": connection.execute("SELECT COUNT(*) FROM panel_final").fetchone()[0]},
                {"stage": "parquet", "rows": parquet_rows},
            ]
        ).to_csv(REPORT_DIR / "join_row_counts.csv", index=False, encoding="utf-8-sig")
        print(json.dumps({"status": "completed", "rows": parquet_rows, "columns": len(columns), "sha256": digest, "qa": qa}, ensure_ascii=False))
    finally:
        connection.close()


if __name__ == "__main__":
    main()
