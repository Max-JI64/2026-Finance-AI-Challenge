"""Stage 2 raw-data quality checks using bounded-memory chunk processing.

The raw CSV files are never modified and are never loaded into memory in full.
Only key columns are written to a temporary SQLite database for disk-backed
duplicate and join checks. All published results are aggregate QA artifacts.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import sqlite3
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

import numpy as np
import pandas as pd
import shapefile
from pyproj import CRS
from shapely.geometry import shape as shapely_shape


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
REPORT_DIR = PROJECT_ROOT / "reports" / "stage2"
CHUNK_SIZE = 20_000
CSV_ENCODING = "cp949"

PERIOD = "기준_년분기_코드"
AREA = "상권_코드"
AREA_NAME = "상권_코드_명"
INDUSTRY = "서비스_업종_코드"
INDUSTRY_NAME = "서비스_업종_코드_명"

STORE_2025_MAPPING = {
    "stdr_yyqu_cd": PERIOD,
    "trdar_se_cd": "상권_구분_코드",
    "trdar_se_cd_nm": "상권_구분_코드_명",
    "trdar_cd": AREA,
    "trdar_cd_nm": AREA_NAME,
    "svc_induty_cd": INDUSTRY,
    "svc_induty_cd_nm": INDUSTRY_NAME,
    "stor_co": "점포_수",
    "similr_induty_stor_co": "유사_업종_점포_수",
    "opbiz_rt": "개업_율",
    "opbiz_stor_co": "개업_점포_수",
    "clsbiz_rt": "폐업_률",
    "clsbiz_stor_co": "폐업_점포_수",
    "frc_stor_co": "프랜차이즈_점포_수",
}


@dataclass(frozen=True)
class DatasetSpec:
    name: str
    paths: tuple[Path, ...]
    key: tuple[str, ...]
    group: str


class Reservoir:
    """Deterministic bounded reservoir for approximate quantiles."""

    def __init__(self, size: int = 50_000, seed: int = 20260814) -> None:
        self.size = size
        self.values: list[float] = []
        self.seen = 0
        self.rng = np.random.default_rng(seed)
        self.minimum = math.inf
        self.maximum = -math.inf
        self.total = 0.0
        self.total_sq = 0.0

    def update(self, values: pd.Series) -> None:
        arr = pd.to_numeric(values, errors="coerce").dropna().to_numpy(dtype=float)
        for value in arr:
            self.seen += 1
            self.minimum = min(self.minimum, value)
            self.maximum = max(self.maximum, value)
            self.total += value
            self.total_sq += value * value
            if len(self.values) < self.size:
                self.values.append(value)
            else:
                position = int(self.rng.integers(0, self.seen))
                if position < self.size:
                    self.values[position] = value

    def summary(self) -> dict[str, float | int | None]:
        if not self.seen:
            return {
                "count": 0,
                "min": None,
                "p01": None,
                "p05": None,
                "median": None,
                "p95": None,
                "p99": None,
                "max": None,
                "mean": None,
                "std": None,
                "quantile_sample_size": 0,
            }
        sample = np.asarray(self.values, dtype=float)
        variance = max(0.0, self.total_sq / self.seen - (self.total / self.seen) ** 2)
        quantiles = np.quantile(sample, [0.01, 0.05, 0.5, 0.95, 0.99])
        return {
            "count": self.seen,
            "min": self.minimum,
            "p01": quantiles[0],
            "p05": quantiles[1],
            "median": quantiles[2],
            "p95": quantiles[3],
            "p99": quantiles[4],
            "max": self.maximum,
            "mean": self.total / self.seen,
            "std": math.sqrt(variance),
            "quantile_sample_size": len(sample),
        }


def normalize_scalar(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return None
    if text.endswith(".0") and text[:-2].isdigit():
        return text[:-2]
    return text


def period_to_index(period: str | None) -> int | None:
    if period is None or len(period) != 5 or not period.isdigit():
        return None
    year, quarter = int(period[:4]), int(period[4])
    if quarter not in {1, 2, 3, 4}:
        return None
    return year * 4 + quarter - 1


def next_period(period: str) -> str:
    year, quarter = int(period[:4]), int(period[4])
    return f"{year + (quarter == 4)}{1 if quarter == 4 else quarter + 1}"


def read_header(path: Path) -> list[str]:
    with path.open("r", encoding=CSV_ENCODING, newline="") as handle:
        return next(csv.reader(handle))


def iter_chunks(path: Path) -> Iterator[pd.DataFrame]:
    for chunk in pd.read_csv(
        path,
        encoding=CSV_ENCODING,
        dtype=str,
        keep_default_na=False,
        chunksize=CHUNK_SIZE,
        low_memory=False,
    ):
        if set(STORE_2025_MAPPING).issubset(chunk.columns):
            chunk = chunk.rename(columns=STORE_2025_MAPPING)
        yield chunk


def dataset_specs() -> list[DatasetSpec]:
    sales = tuple(sorted(RAW_DIR.glob("*추정매출-상권*20??년.csv")))
    stores = tuple(sorted(RAW_DIR.glob("*점포-상권*20??년.csv")))

    def one(fragment: str) -> tuple[Path, ...]:
        matches = tuple(
            path
            for path in RAW_DIR.glob(f"*{fragment}*.csv")
            if "자치구" not in path.name and "상권배후지" not in path.name
        )
        if len(matches) != 1:
            raise RuntimeError(f"Expected one raw file for {fragment!r}, found {len(matches)}")
        return matches

    specs = [
        DatasetSpec("추정매출-상권", sales, (PERIOD, AREA, INDUSTRY), "sales"),
        DatasetSpec("점포-상권", stores, (PERIOD, AREA, INDUSTRY), "store"),
        DatasetSpec("길단위인구-상권", one("길단위인구-상권"), (PERIOD, AREA), "area_quarter"),
        DatasetSpec("상권변화지표-상권", one("상권변화지표-상권"), (PERIOD, AREA), "area_quarter"),
        DatasetSpec("상주인구-상권", one("상주인구-상권"), (PERIOD, AREA), "area_quarter"),
        DatasetSpec("직장인구-상권", one("직장인구-상권"), (PERIOD, AREA), "area_quarter"),
        DatasetSpec("집객시설-상권", one("집객시설-상권"), (PERIOD, AREA), "area_quarter"),
        DatasetSpec("아파트-상권", one("아파트-상권"), (PERIOD, AREA), "area_quarter"),
        DatasetSpec(
            "상권변화지표-자치구",
            (RAW_DIR / "서울시 상권분석서비스(상권변화지표-자치구).csv",),
            (PERIOD, "자치구_코드"),
            "excluded_district",
        ),
        DatasetSpec(
            "직장인구-상권배후지",
            (RAW_DIR / "서울시 상권분석서비스(직장인구-상권배후지).csv",),
            (PERIOD, "상권배후지_코드"),
            "excluded_hinterland",
        ),
    ]
    for spec in specs:
        if not spec.paths or any(not path.exists() for path in spec.paths):
            raise FileNotFoundError(f"Missing raw input for {spec.name}")
    if len(sales) != 5 or len(stores) != 5:
        raise RuntimeError(f"Expected five sales and five store files; got {len(sales)} and {len(stores)}")
    return specs


def numeric_candidate(column: str) -> bool:
    return any(
        token in column
        for token in ("금액", "건수", "점포_수", "인구_수", "시설_수", "_수", "_율", "_률", "개월_평균", "평균_면적", "평균_시가")
    ) and column not in {PERIOD, AREA, "자치구_코드", "상권배후지_코드"}


def blank_mask(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().isin(["", "nan", "None", "null"])


def limited_example(chunk: pd.DataFrame, mask: pd.Series, key: Iterable[str]) -> str:
    columns = [column for column in key if column in chunk.columns]
    if not columns or not mask.any():
        return ""
    row = chunk.loc[mask, columns].head(1).iloc[0]
    return " | ".join(f"{column}={normalize_scalar(row[column])}" for column in columns)


def scan_csvs(specs: list[DatasetSpec], connection: sqlite3.Connection) -> dict[str, object]:
    period_counts: Counter[tuple[str, str]] = Counter()
    period_areas: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    period_industries: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    year_areas: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    year_industries: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    missing: Counter[tuple[str, str, str, str]] = Counter()
    totals: Counter[tuple[str, str, str]] = Counter()
    zeros: Counter[tuple[str, str, str]] = Counter()
    parse_failures: Counter[tuple[str, str]] = Counter()
    negative_counts: Counter[tuple[str, str]] = Counter()
    name_pairs: defaultdict[tuple[str, str], set[tuple[str, str]]] = defaultdict(set)
    logical: defaultdict[tuple[str, str], dict[str, object]] = defaultdict(
        lambda: {"checked_rows": 0, "issue_count": 0, "example": ""}
    )
    outlier_columns = {
        "추정매출-상권": ["당월_매출_금액", "당월_매출_건수"],
        "점포-상권": ["점포_수", "유사_업종_점포_수", "개업_율", "폐업_률"],
        "길단위인구-상권": ["총_유동인구_수"],
        "상주인구-상권": ["총_상주인구_수", "총_가구_수"],
        "직장인구-상권": ["총_직장_인구_수"],
        "집객시설-상권": ["집객시설_수"],
        "아파트-상권": ["아파트_단지_수", "아파트_평균_시가"],
    }
    reservoirs = {
        (dataset, column): Reservoir(seed=20260814 + index)
        for index, (dataset, columns) in enumerate(outlier_columns.items())
        for column in columns
    }
    headers: dict[str, list[dict[str, object]]] = defaultdict(list)

    for table in ("sales_keys", "store_keys", "area_quarter_keys", "other_keys"):
        connection.execute(f'DROP TABLE IF EXISTS "{table}"')
    connection.execute(
        "CREATE TABLE sales_keys (period TEXT, area TEXT, industry TEXT, area_name TEXT, industry_name TEXT)"
    )
    connection.execute(
        "CREATE TABLE store_keys (period TEXT, area TEXT, industry TEXT, area_name TEXT, industry_name TEXT)"
    )
    connection.execute(
        "CREATE TABLE area_quarter_keys (dataset TEXT, period TEXT, area TEXT, area_name TEXT)"
    )
    connection.execute("CREATE TABLE other_keys (dataset TEXT, key_json TEXT)")

    for spec in specs:
        for path in spec.paths:
            raw_header = read_header(path)
            standardized = [STORE_2025_MAPPING.get(column, column) for column in raw_header]
            headers[spec.name].append(
                {
                    "file": path.name,
                    "raw": raw_header,
                    "standardized": standardized,
                    "mapping_applied": raw_header != standardized,
                }
            )
            for chunk in iter_chunks(path):
                missing_key_columns = [column for column in spec.key if column not in chunk.columns]
                if missing_key_columns:
                    raise KeyError(f"{path.name}: missing key columns {missing_key_columns}")

                normalized_keys = pd.DataFrame(
                    {column: chunk[column].map(normalize_scalar) for column in spec.key}
                )
                periods = normalized_keys[PERIOD]
                years = periods.map(lambda value: value[:4] if value and len(value) == 5 else None)
                unique_periods = periods.dropna().unique().tolist()
                for period in unique_periods:
                    mask = periods == period
                    row_count = int(mask.sum())
                    period_counts[(spec.name, period)] += row_count
                    if AREA in normalized_keys:
                        period_areas[(spec.name, period)].update(normalized_keys.loc[mask, AREA].dropna())
                    if INDUSTRY in normalized_keys:
                        period_industries[(spec.name, period)].update(
                            normalized_keys.loc[mask, INDUSTRY].dropna()
                        )
                if AREA in normalized_keys:
                    for year in years.dropna().unique().tolist():
                        year_areas[(spec.name, year)].update(
                            normalized_keys.loc[years == year, AREA].dropna()
                        )
                if INDUSTRY in normalized_keys:
                    for year in years.dropna().unique().tolist():
                        year_industries[(spec.name, year)].update(
                            normalized_keys.loc[years == year, INDUSTRY].dropna()
                        )

                if spec.group in {"sales", "store"}:
                    key_frame = pd.DataFrame(
                        {
                            "period": periods,
                            "area": normalized_keys[AREA],
                            "industry": normalized_keys[INDUSTRY],
                            "area_name": chunk[AREA_NAME].map(normalize_scalar),
                            "industry_name": chunk[INDUSTRY_NAME].map(normalize_scalar),
                        }
                    )
                    key_frame.to_sql(
                        "sales_keys" if spec.group == "sales" else "store_keys",
                        connection,
                        if_exists="append",
                        index=False,
                        method="multi",
                        chunksize=2_000,
                    )
                elif spec.group == "area_quarter":
                    key_frame = pd.DataFrame(
                        {
                            "dataset": spec.name,
                            "period": periods,
                            "area": normalized_keys[AREA],
                            "area_name": chunk[AREA_NAME].map(normalize_scalar),
                        }
                    )
                    key_frame.to_sql(
                        "area_quarter_keys",
                        connection,
                        if_exists="append",
                        index=False,
                        method="multi",
                        chunksize=2_000,
                    )
                else:
                    key_frame = normalized_keys.apply(
                        lambda row: json.dumps(row.to_dict(), ensure_ascii=False, sort_keys=True), axis=1
                    )
                    pd.DataFrame({"dataset": spec.name, "key_json": key_frame}).to_sql(
                        "other_keys",
                        connection,
                        if_exists="append",
                        index=False,
                        method="multi",
                        chunksize=2_000,
                    )

                for code_column, name_column in (
                    (AREA, AREA_NAME),
                    (INDUSTRY, INDUSTRY_NAME),
                    ("상권_구분_코드", "상권_구분_코드_명"),
                    ("상권_변화_지표", "상권_변화_지표_명"),
                    ("자치구_코드", "자치구_코드_명"),
                    ("상권배후지_코드", "상권배후지_코드_명"),
                ):
                    if code_column in chunk and name_column in chunk:
                        pairs = zip(
                            chunk[code_column].map(normalize_scalar),
                            chunk[name_column].map(normalize_scalar),
                        )
                        name_pairs[(spec.name, code_column)].update(
                            (code, name) for code, name in pairs if code and name
                        )

                period_labels = periods.fillna("INVALID_OR_MISSING")
                for column in chunk.columns:
                    blanks = blank_mask(chunk[column])
                    for period in period_labels.unique().tolist():
                        mask = period_labels == period
                        key = (spec.name, period, column)
                        totals[key] += int(mask.sum())
                        missing[(spec.name, period, column, "blank_or_na")] += int((mask & blanks).sum())
                        if numeric_candidate(column):
                            numeric = pd.to_numeric(chunk[column], errors="coerce")
                            zeros[key] += int((mask & numeric.eq(0)).sum())

                for column in [column for column in chunk.columns if numeric_candidate(column)]:
                    numeric = pd.to_numeric(chunk[column], errors="coerce")
                    nonblank = ~blank_mask(chunk[column])
                    parse_failures[(spec.name, column)] += int((nonblank & numeric.isna()).sum())
                    negative_counts[(spec.name, column)] += int(numeric.lt(0).sum())
                    if (spec.name, column) in reservoirs:
                        reservoirs[(spec.name, column)].update(numeric)

                run_logical_checks(spec, chunk, logical)

    connection.commit()
    for table, columns in (
        ("sales_keys", "period, area, industry"),
        ("store_keys", "period, area, industry"),
        ("area_quarter_keys", "dataset, period, area"),
    ):
        connection.execute(f"CREATE INDEX IF NOT EXISTS idx_{table} ON {table} ({columns})")
    connection.commit()

    return {
        "period_counts": period_counts,
        "period_areas": period_areas,
        "period_industries": period_industries,
        "year_areas": year_areas,
        "year_industries": year_industries,
        "missing": missing,
        "totals": totals,
        "zeros": zeros,
        "parse_failures": parse_failures,
        "negative_counts": negative_counts,
        "name_pairs": name_pairs,
        "logical": logical,
        "reservoirs": reservoirs,
        "headers": headers,
    }


def record_check(
    logical: defaultdict[tuple[str, str], dict[str, object]],
    dataset: str,
    check: str,
    chunk: pd.DataFrame,
    mask: pd.Series,
    key: Iterable[str],
) -> None:
    result = logical[(dataset, check)]
    result["checked_rows"] = int(result["checked_rows"]) + len(chunk)
    issues = int(mask.fillna(False).sum())
    result["issue_count"] = int(result["issue_count"]) + issues
    if issues and not result["example"]:
        result["example"] = limited_example(chunk, mask.fillna(False), key)


def run_logical_checks(
    spec: DatasetSpec,
    chunk: pd.DataFrame,
    logical: defaultdict[tuple[str, str], dict[str, object]],
) -> None:
    key = spec.key
    if spec.group == "sales":
        total = pd.to_numeric(chunk["당월_매출_금액"], errors="coerce")
        weekday = pd.to_numeric(chunk["주중_매출_금액"], errors="coerce")
        weekend = pd.to_numeric(chunk["주말_매출_금액"], errors="coerce")
        valid = total.notna() & weekday.notna() & weekend.notna()
        record_check(logical, spec.name, "주중+주말 매출금액 != 당월 매출금액", chunk, valid & ((weekday + weekend - total).abs() > 1), key)
        total_count = pd.to_numeric(chunk["당월_매출_건수"], errors="coerce")
        weekday_count = pd.to_numeric(chunk["주중_매출_건수"], errors="coerce")
        weekend_count = pd.to_numeric(chunk["주말_매출_건수"], errors="coerce")
        valid_count = total_count.notna() & weekday_count.notna() & weekend_count.notna()
        record_check(logical, spec.name, "주중+주말 매출건수 != 당월 매출건수", chunk, valid_count & ((weekday_count + weekend_count - total_count).abs() > 1), key)
    elif spec.group == "store":
        similar = pd.to_numeric(chunk["유사_업종_점포_수"], errors="coerce")
        franchise = pd.to_numeric(chunk["프랜차이즈_점포_수"], errors="coerce")
        record_check(logical, spec.name, "프랜차이즈 점포 수 > 유사업종 점포 수", chunk, franchise.gt(similar), key)
        for column in ("개업_율", "폐업_률"):
            rate = pd.to_numeric(chunk[column], errors="coerce")
            record_check(logical, spec.name, f"{column} 범위 밖(0~100)", chunk, rate.lt(0) | rate.gt(100), key)
    elif spec.name == "길단위인구-상권":
        total = pd.to_numeric(chunk["총_유동인구_수"], errors="coerce")
        parts = chunk[["남성_유동인구_수", "여성_유동인구_수"]].apply(pd.to_numeric, errors="coerce").sum(axis=1, min_count=2)
        record_check(logical, spec.name, "성별 유동인구 합계 != 총 유동인구", chunk, total.notna() & parts.notna() & ((parts - total).abs() > 1), key)
    elif spec.name == "상주인구-상권":
        total = pd.to_numeric(chunk["총_상주인구_수"], errors="coerce")
        parts = chunk[["남성_상주인구_수", "여성_상주인구_수"]].apply(pd.to_numeric, errors="coerce").sum(axis=1, min_count=2)
        record_check(logical, spec.name, "성별 상주인구 합계 != 총 상주인구", chunk, total.notna() & parts.notna() & ((parts - total).abs() > 1), key)
        households = pd.to_numeric(chunk["총_가구_수"], errors="coerce")
        household_parts = chunk[["아파트_가구_수", "비_아파트_가구_수"]].apply(pd.to_numeric, errors="coerce").sum(axis=1, min_count=2)
        record_check(logical, spec.name, "아파트+비아파트 가구 != 총 가구", chunk, households.notna() & household_parts.notna() & ((household_parts - households).abs() > 1), key)
    elif spec.name in {"직장인구-상권", "직장인구-상권배후지"}:
        total = pd.to_numeric(chunk["총_직장_인구_수"], errors="coerce")
        parts = chunk[["남성_직장_인구_수", "여성_직장_인구_수"]].apply(pd.to_numeric, errors="coerce").sum(axis=1, min_count=2)
        record_check(logical, spec.name, "성별 직장인구 합계 != 총 직장인구", chunk, total.notna() & parts.notna() & ((parts - total).abs() > 1), key)


def duplicate_summary(connection: sqlite3.Connection) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    queries = [
        ("추정매출-상권", "sales_keys", "period, area, industry"),
        ("점포-상권", "store_keys", "period, area, industry"),
    ]
    area_datasets = [row[0] for row in connection.execute("SELECT DISTINCT dataset FROM area_quarter_keys")]
    for dataset in area_datasets:
        queries.append((dataset, "area_quarter_keys", "period, area"))
    for dataset, table, columns in queries:
        where = "" if table != "area_quarter_keys" else "WHERE dataset = ?"
        params = () if not where else (dataset,)
        total = connection.execute(f"SELECT COUNT(*) FROM {table} {where}", params).fetchone()[0]
        null_condition = " OR ".join(f"{column.strip()} IS NULL" for column in columns.split(","))
        null_keys = connection.execute(
            f"SELECT COUNT(*) FROM {table} {where} {'AND' if where else 'WHERE'} ({null_condition})",
            params,
        ).fetchone()[0]
        duplicate = connection.execute(
            f"SELECT COUNT(*), COALESCE(SUM(c - 1), 0) FROM ("
            f"SELECT {columns}, COUNT(*) c FROM {table} {where} GROUP BY {columns} HAVING c > 1)",
            params,
        ).fetchone()
        rows.append(
            {
                "dataset": dataset,
                "key_columns": columns,
                "row_count": total,
                "null_key_rows": null_keys,
                "duplicate_key_count": duplicate[0],
                "duplicate_extra_rows": duplicate[1],
            }
        )
    return pd.DataFrame(rows)


def mapping_quality(name_pairs: dict[tuple[str, str], set[tuple[str, str]]]) -> pd.DataFrame:
    rows = []
    for (dataset, code_column), pairs in sorted(name_pairs.items()):
        names_by_code: defaultdict[str, set[str]] = defaultdict(set)
        codes_by_name: defaultdict[str, set[str]] = defaultdict(set)
        for code, name in pairs:
            names_by_code[code].add(name)
            codes_by_name[name].add(code)
        rows.append(
            {
                "dataset": dataset,
                "check": f"{code_column}↔이름 관계",
                "unique_codes": len(names_by_code),
                "codes_with_multiple_names": sum(len(names) > 1 for names in names_by_code.values()),
                "names_with_multiple_codes": sum(len(codes) > 1 for codes in codes_by_name.values()),
                "example_code_with_multiple_names": next(
                    (f"{code}: {sorted(names)}" for code, names in names_by_code.items() if len(names) > 1),
                    "",
                ),
            }
        )
    return pd.DataFrame(rows)


def write_panel_gaps(connection: sqlite3.Connection, global_periods: list[str]) -> dict[str, float | int]:
    output = REPORT_DIR / "panel_gap_summary.csv"
    period_indices = [period_to_index(period) for period in global_periods]
    valid_indices = [value for value in period_indices if value is not None]
    global_expected = max(valid_indices) - min(valid_indices) + 1
    cursor = connection.execute(
        "SELECT area, industry, MIN(period), MAX(period), COUNT(DISTINCT period) "
        "FROM sales_keys WHERE period IS NOT NULL AND area IS NOT NULL AND industry IS NOT NULL "
        "GROUP BY area, industry ORDER BY area, industry"
    )
    combination_count = 0
    global_missing_sum = 0
    active_missing_sum = 0
    active_expected_sum = 0
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "상권_코드",
                "서비스_업종_코드",
                "최초_분기",
                "최종_분기",
                "관측_분기_수",
                "전체기간_기대_분기_수",
                "전체기간_누락률",
                "활성기간_기대_분기_수",
                "활성기간_누락률",
            ]
        )
        for area, industry, minimum, maximum, observed in cursor:
            minimum_index = period_to_index(minimum)
            maximum_index = period_to_index(maximum)
            active_expected = (
                maximum_index - minimum_index + 1
                if minimum_index is not None and maximum_index is not None
                else 0
            )
            global_missing = max(0, global_expected - observed)
            active_missing = max(0, active_expected - observed)
            writer.writerow(
                [
                    area,
                    industry,
                    minimum,
                    maximum,
                    observed,
                    global_expected,
                    global_missing / global_expected if global_expected else None,
                    active_expected,
                    active_missing / active_expected if active_expected else None,
                ]
            )
            combination_count += 1
            global_missing_sum += global_missing
            active_missing_sum += active_missing
            active_expected_sum += active_expected
    return {
        "combination_count": combination_count,
        "global_expected_quarters": global_expected,
        "global_missing_rate": global_missing_sum / (combination_count * global_expected),
        "active_window_missing_rate": active_missing_sum / active_expected_sum,
    }


def spatial_quality(connection: sqlite3.Connection) -> tuple[pd.DataFrame, set[str]]:
    shp_path = next(RAW_DIR.rglob("*.shp"))
    prj_path = shp_path.with_suffix(".prj")
    cpg_path = shp_path.with_suffix(".cpg")
    cpg_encoding = cpg_path.read_text(encoding="ascii").strip()
    reader = shapefile.Reader(str(shp_path), encoding=cpg_encoding)
    field_names = [field[0] for field in reader.fields if field[0] != "DeletionFlag"]
    area_index = field_names.index("TRDAR_CD")
    area_codes: list[str] = []
    blank_geometries = 0
    invalid_geometries = 0
    geometry_hashes: Counter[str] = Counter()
    for shape_record in reader.iterShapeRecords():
        code = normalize_scalar(shape_record.record[area_index])
        if code:
            area_codes.append(code)
        raw_shape = shape_record.shape
        if raw_shape.shapeType == shapefile.NULL or not raw_shape.points:
            blank_geometries += 1
            continue
        geometry = shapely_shape(raw_shape.__geo_interface__)
        if geometry.is_empty:
            blank_geometries += 1
        if not geometry.is_valid:
            invalid_geometries += 1
        digest = hashlib.sha256(geometry.wkb).hexdigest()
        geometry_hashes[digest] += 1
    area_set = set(area_codes)
    connection.execute("DROP TABLE IF EXISTS area_codes")
    connection.execute("CREATE TABLE area_codes (area TEXT PRIMARY KEY)")
    connection.executemany("INSERT OR IGNORE INTO area_codes(area) VALUES (?)", [(code,) for code in area_set])
    connection.commit()
    epsg = CRS.from_wkt(prj_path.read_text(encoding="utf-8")).to_epsg()
    rows = [
        {"check": "CPG 인코딩", "result": cpg_encoding, "status": "PASS" if cpg_encoding.upper() in {"UTF-8", "UTF8", "949", "CP949", "EUC-KR"} else "REVIEW"},
        {"check": "좌표계 EPSG", "result": epsg, "status": "PASS" if epsg == 5181 else "FAIL"},
        {"check": "DBF 레코드 수", "result": len(reader), "status": "PASS"},
        {"check": "SHP 도형 수", "result": reader.numRecords, "status": "PASS" if len(reader) == reader.numRecords else "FAIL"},
        {"check": "상권코드 중복 레코드", "result": len(area_codes) - len(area_set), "status": "PASS" if len(area_codes) == len(area_set) else "FAIL"},
        {"check": "빈 도형", "result": blank_geometries, "status": "PASS" if blank_geometries == 0 else "FAIL"},
        {"check": "유효하지 않은 도형", "result": invalid_geometries, "status": "PASS" if invalid_geometries == 0 else "REVIEW"},
        {"check": "중복 도형", "result": sum(count - 1 for count in geometry_hashes.values() if count > 1), "status": "PASS" if all(count == 1 for count in geometry_hashes.values()) else "REVIEW"},
        {"check": "도형 경계", "result": json.dumps(reader.bbox), "status": "PASS"},
    ]
    return pd.DataFrame(rows), area_set


def join_quality(connection: sqlite3.Connection) -> pd.DataFrame:
    rows = []
    sales_total = connection.execute("SELECT COUNT(*) FROM sales_keys").fetchone()[0]
    store_total = connection.execute("SELECT COUNT(*) FROM store_keys").fetchone()[0]
    sales_missing_store = connection.execute(
        "SELECT COUNT(*) FROM sales_keys s WHERE NOT EXISTS (SELECT 1 FROM store_keys t "
        "WHERE t.period=s.period AND t.area=s.area AND t.industry=s.industry)"
    ).fetchone()[0]
    store_missing_sales = connection.execute(
        "SELECT COUNT(*) FROM store_keys t WHERE NOT EXISTS (SELECT 1 FROM sales_keys s "
        "WHERE s.period=t.period AND s.area=t.area AND s.industry=t.industry)"
    ).fetchone()[0]
    sales_missing_area = connection.execute(
        "SELECT COUNT(*) FROM sales_keys s WHERE NOT EXISTS (SELECT 1 FROM area_codes a WHERE a.area=s.area)"
    ).fetchone()[0]
    rows.extend(
        [
            {"join": "추정매출→점포", "base_rows": sales_total, "unmatched_rows": sales_missing_store, "unmatched_rate": sales_missing_store / sales_total},
            {"join": "점포→추정매출", "base_rows": store_total, "unmatched_rows": store_missing_sales, "unmatched_rate": store_missing_sales / store_total},
            {"join": "추정매출→영역", "base_rows": sales_total, "unmatched_rows": sales_missing_area, "unmatched_rate": sales_missing_area / sales_total},
        ]
    )
    periods = [row[0] for row in connection.execute("SELECT DISTINCT period FROM sales_keys ORDER BY period")]
    for period in periods:
        base = connection.execute("SELECT COUNT(*) FROM sales_keys WHERE period=?", (period,)).fetchone()[0]
        unmatched = connection.execute(
            "SELECT COUNT(*) FROM sales_keys s WHERE s.period=? AND NOT EXISTS (SELECT 1 FROM store_keys t "
            "WHERE t.period=s.period AND t.area=s.area AND t.industry=s.industry)",
            (period,),
        ).fetchone()[0]
        rows.append({"join": f"추정매출→점포:{period}", "base_rows": base, "unmatched_rows": unmatched, "unmatched_rate": unmatched / base if base else None})
    return pd.DataFrame(rows)


def code_coverage_rows(scan: dict[str, object]) -> pd.DataFrame:
    rows = []
    for dimension, source in (("상권코드", scan["year_areas"]), ("서비스업종코드", scan["year_industries"])):
        datasets = sorted({dataset for dataset, _ in source})
        for dataset in datasets:
            previous: set[str] | None = None
            for year in sorted(year for ds, year in source if ds == dataset):
                current = source[(dataset, year)]
                rows.append(
                    {
                        "dataset": dataset,
                        "dimension": dimension,
                        "year": year,
                        "unique_count": len(current),
                        "new_from_previous_year": None if previous is None else len(current - previous),
                        "missing_from_previous_year": None if previous is None else len(previous - current),
                    }
                )
                previous = current
    return pd.DataFrame(rows)


def write_schema_mapping(headers: dict[str, list[dict[str, object]]]) -> None:
    lines = [
        "# Stage 2 스키마 매핑 결과",
        "",
        "- 원본 파일은 수정하지 않았다.",
        "- 점포 2025년 파일만 읽기 단계에서 아래 영문→표준 한글 매핑을 적용한다.",
        "- 나머지 파일은 원본 컬럼명을 표준 컬럼명으로 유지한다.",
        "",
        "## 점포 2025년 명시적 매핑",
        "",
        "| 원본 영문명 | 표준 컬럼명 |",
        "| --- | --- |",
    ]
    lines.extend(f"| `{raw}` | `{standard}` |" for raw, standard in STORE_2025_MAPPING.items())
    lines.extend(["", "## 파일별 헤더 검증", "", "| 데이터 | 파일 | 원본 열 수 | 표준 열 수 | 매핑 적용 |", "| --- | --- | ---: | ---: | --- |"])
    for dataset, records in headers.items():
        for record in records:
            lines.append(
                f"| {dataset} | `{record['file']}` | {len(record['raw'])} | {len(record['standardized'])} | "
                f"{'예' if record['mapping_applied'] else '아니오'} |"
            )
    lines.extend(
        [
            "",
            "## 집계 단위",
            "",
            "- 추정매출·점포: 기준년분기 × 상권코드 × 서비스업종코드",
            "- 길단위인구·상권변화지표·상주인구·직장인구·집객시설·아파트: 기준년분기 × 상권코드",
            "- 영역: 상권코드별 공간 Snapshot",
            "- 자치구 변화지표: 기준년분기 × 자치구코드이며 Stage 3에서 제외",
            "- 직장인구 상권배후지: 기준년분기 × 상권배후지코드이며 Stage 3에서 제외",
            "",
        ]
    )
    (REPORT_DIR / "schema_mapping.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    specs = dataset_specs()
    with tempfile.TemporaryDirectory(prefix="stage2_qa_") as temporary:
        connection = sqlite3.connect(Path(temporary) / "qa.sqlite")
        scan = scan_csvs(specs, connection)
        duplicate = duplicate_summary(connection)
        mapping = mapping_quality(scan["name_pairs"])
        key_quality = pd.concat([duplicate, mapping], ignore_index=True, sort=False)

        period_rows = []
        for (dataset, period), count in sorted(scan["period_counts"].items()):
            period_rows.append(
                {
                    "dataset": dataset,
                    "기준_년분기_코드": period,
                    "year": period[:4] if len(period) == 5 else None,
                    "quarter": period[4:] if len(period) == 5 else None,
                    "row_count": count,
                    "unique_area_count": len(scan["period_areas"].get((dataset, period), set())),
                    "unique_industry_count": len(scan["period_industries"].get((dataset, period), set())),
                }
            )
        period_frame = pd.DataFrame(period_rows)
        sales_periods = sorted(
            period for dataset, period in scan["period_counts"] if dataset == "추정매출-상권" and period.isdigit()
        )
        gap_stats = write_panel_gaps(connection, sales_periods)

        spatial_frame, _ = spatial_quality(connection)
        join_frame = join_quality(connection)

        missing_rows = []
        for (dataset, period, column), total in sorted(scan["totals"].items()):
            missing_count = scan["missing"][(dataset, period, column, "blank_or_na")]
            missing_rows.append(
                {
                    "dataset": dataset,
                    "period": period,
                    "column": column,
                    "row_count": total,
                    "missing_count": missing_count,
                    "missing_rate": missing_count / total if total else None,
                    "zero_count": scan["zeros"][(dataset, period, column)],
                    "parse_failure_count": scan["parse_failures"][(dataset, column)],
                }
            )
        missing_frame = pd.DataFrame(missing_rows)

        logical_rows = []
        for (dataset, check), result in sorted(scan["logical"].items()):
            logical_rows.append(
                {
                    "dataset": dataset,
                    "check": check,
                    **result,
                    "issue_rate": int(result["issue_count"]) / int(result["checked_rows"]),
                    "status": "PASS" if int(result["issue_count"]) == 0 else "REVIEW",
                }
            )
        for (dataset, column), count in sorted(scan["negative_counts"].items()):
            logical_rows.append(
                {
                    "dataset": dataset,
                    "check": f"{column} 음수",
                    "checked_rows": int(
                        sum(total for (ds, _, col), total in scan["totals"].items() if ds == dataset and col == column)
                    ),
                    "issue_count": count,
                    "example": "",
                    "issue_rate": None,
                    "status": "PASS" if count == 0 else "REVIEW",
                }
            )
        logical_frame = pd.DataFrame(logical_rows)

        outlier_rows = []
        for (dataset, column), reservoir in sorted(scan["reservoirs"].items()):
            outlier_rows.append({"dataset": dataset, "column": column, **reservoir.summary(), "quantiles": "deterministic reservoir approximation"})
        outlier_frame = pd.DataFrame(outlier_rows)

        period_frame.to_csv(REPORT_DIR / "period_coverage.csv", index=False, encoding="utf-8-sig")
        key_quality.to_csv(REPORT_DIR / "key_quality.csv", index=False, encoding="utf-8-sig")
        missing_frame.to_csv(REPORT_DIR / "missingness.csv", index=False, encoding="utf-8-sig")
        logical_frame.to_csv(REPORT_DIR / "logical_checks.csv", index=False, encoding="utf-8-sig")
        join_frame.to_csv(REPORT_DIR / "join_coverage.csv", index=False, encoding="utf-8-sig")
        outlier_frame.to_csv(REPORT_DIR / "outlier_summary.csv", index=False, encoding="utf-8-sig")
        spatial_frame.to_csv(REPORT_DIR / "spatial_quality.csv", index=False, encoding="utf-8-sig")
        code_coverage_rows(scan).to_csv(REPORT_DIR / "code_coverage.csv", index=False, encoding="utf-8-sig")
        write_schema_mapping(scan["headers"])

        target_possible = connection.execute(
            "SELECT COUNT(*) FROM sales_keys s WHERE EXISTS (SELECT 1 FROM sales_keys n "
            "WHERE n.area=s.area AND n.industry=s.industry AND n.period=CASE "
            "WHEN substr(s.period,5,1)='4' THEN printf('%d1', CAST(substr(s.period,1,4) AS INTEGER)+1) "
            "ELSE printf('%s%d', substr(s.period,1,4), CAST(substr(s.period,5,1) AS INTEGER)+1) END)"
        ).fetchone()[0]
        duplicate_sales = int(duplicate.loc[duplicate["dataset"] == "추정매출-상권", "duplicate_extra_rows"].iloc[0])
        duplicate_store = int(duplicate.loc[duplicate["dataset"] == "점포-상권", "duplicate_extra_rows"].iloc[0])
        join_sales_store = join_frame.loc[join_frame["join"] == "추정매출→점포"].iloc[0]
        join_sales_area = join_frame.loc[join_frame["join"] == "추정매출→영역"].iloc[0]
        sales_min, sales_max = min(sales_periods), max(sales_periods)
        store_periods = sorted(
            period for dataset, period in scan["period_counts"] if dataset == "점포-상권" and period.isdigit()
        )
        common_periods = sorted(set(sales_periods) & set(store_periods))
        invalid_geometry_count = int(spatial_frame.loc[spatial_frame["check"] == "유효하지 않은 도형", "result"].iloc[0])
        summary_lines = [
            "# Stage 2 품질검증 결과",
            "",
            "- 실행 방식: CSV `chunksize=20,000`, 전체 원본 메모리 로딩 없음, 원본 수정 없음",
            "- 점포 2025년: 영문 14개 헤더를 명시적 한글 표준명으로 읽기 시점에만 변환",
            f"- 추정매출 기간: {sales_min}~{sales_max} ({len(sales_periods)}개 분기)",
            f"- 점포 기간: {min(store_periods)}~{max(store_periods)} ({len(store_periods)}개 분기)",
            f"- Stage 3 공통 사용 기간: {min(common_periods)}~{max(common_periods)} ({len(common_periods)}개 분기)",
            "",
            "## Gate 핵심 결과",
            "",
            f"- 추정매출 기본키 중복 추가 행: {duplicate_sales:,}건",
            f"- 점포 기본키 중복 추가 행: {duplicate_store:,}건",
            f"- 추정매출→점포 미매칭: {int(join_sales_store['unmatched_rows']):,}건 ({join_sales_store['unmatched_rate']:.4%})",
            f"- 추정매출→영역 미매칭: {int(join_sales_area['unmatched_rows']):,}건 ({join_sales_area['unmatched_rate']:.4%})",
            f"- 상권×업종 전체 20분기 기준 누락률: {gap_stats['global_missing_rate']:.4%}",
            f"- 각 조합 활성기간 기준 내부 누락률: {gap_stats['active_window_missing_rate']:.4%}",
            f"- 다음 분기 Target 생성 가능한 현재 분기 행: {target_possible:,}건 (Target 값 자체는 Stage 4에서 생성)",
            f"- 공간 CRS: EPSG:{int(spatial_frame.loc[spatial_frame['check'] == '좌표계 EPSG', 'result'].iloc[0])}",
            f"- 유효하지 않은 도형: {invalid_geometry_count:,}건",
            "",
            "## 전처리 결정",
            "",
            "1. Stage 3 기준 테이블은 추정매출로 고정한다.",
            "2. 기본키는 `기준연도 + 기준분기 + 상권코드 + 서비스업종코드`로 분리 저장한다.",
            "3. 점포는 같은 키로 left join하고 미매칭 여부를 별도 플래그로 보존한다.",
            "4. 4~9번 상권 공통 데이터는 `기준년분기 + 상권코드` many-to-one으로 결합한다.",
            "5. 자치구·상권배후지 파일은 집계 단위가 달라 Stage 3 Panel에서 제외한다.",
            "6. 원본 결측·0·극단값은 삭제하거나 대체하지 않고 원값과 결측 플래그를 보존한다.",
            "7. 비율의 분모가 0이거나 과거 분기가 없으면 파생 변화율을 결측으로 둔다.",
            "8. 통계적 극단값은 자동 제거하지 않는다.",
            "",
            "## 세부 증거",
            "",
            "- `schema_mapping.md`: 파일별 헤더와 점포 2025 매핑",
            "- `period_coverage.csv`: 분기별 행·상권·업종 수",
            "- `key_quality.csv`: 키 결측·중복·코드명 관계",
            "- `missingness.csv`: 컬럼·분기별 결측·0·파싱 실패",
            "- `logical_checks.csv`: 음수·비율·구성 합계 검증",
            "- `join_coverage.csv`: 매출·점포·공간 연결률",
            "- `panel_gap_summary.csv`: 상권×업종별 분기 누락률",
            "- `outlier_summary.csv`: bounded reservoir 기반 분포 요약",
            "- `spatial_quality.csv`: CRS·레코드·도형 유효성",
            "- `code_coverage.csv`: 연도별 신규·소멸 상권·업종 코드",
            "",
        ]
        (REPORT_DIR / "qa_summary.md").write_text("\n".join(summary_lines), encoding="utf-8")
        connection.close()
        print(
            json.dumps(
                {
                    "status": "completed",
                    "sales_period": [sales_min, sales_max],
                    "common_period_count": len(common_periods),
                    "sales_duplicate_extra_rows": duplicate_sales,
                    "store_duplicate_extra_rows": duplicate_store,
                    "sales_store_unmatched": int(join_sales_store["unmatched_rows"]),
                    "sales_area_unmatched": int(join_sales_area["unmatched_rows"]),
                    "target_possible_rows": target_possible,
                    "reports": len(list(REPORT_DIR.glob("*"))),
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
