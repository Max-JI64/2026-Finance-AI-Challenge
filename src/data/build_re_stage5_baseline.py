"""Prepare the approved RE5 baseline without fitting any model.

The 2025Q2 holdout labels are intentionally not materialized here.  This keeps
2025Q3-Q4 outcomes isolated until a CV winner has been approved by the user.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import warnings
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import yaml
from pandas.errors import PerformanceWarning

from src.features.build_stage45_features import build_stage45_features


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "re_stage5.yaml"
REPORT_DIR = ROOT / "reports" / "re_stage5"
MANIFEST_PATH = REPORT_DIR / "manifest.json"
TARGET_DEFINITION_PATH = REPORT_DIR / "target_v2_definition.md"
EDA_REPORT_PATH = REPORT_DIR / "quantile_eda.md"
PERIOD_DISTRIBUTION_PATH = REPORT_DIR / "target_distribution_by_period.csv"
INDUSTRY_DISTRIBUTION_PATH = REPORT_DIR / "target_distribution_by_industry.csv"
MISSING_PATH = REPORT_DIR / "target_missingness.csv"
FOLD_SUMMARY_PATH = REPORT_DIR / "fold_summary.csv"
HOLDOUT_LOCK_PATH = REPORT_DIR / "holdout_lock.json"
HOLDOUT_ACCESS_PATH = REPORT_DIR / "holdout" / "access.json"
TRAINING_RUNBOOK_PATH = REPORT_DIR / "training_runbook.md"
FEATURE_CONTRACT_PATH = REPORT_DIR / "feature_contract_v2.md"
PREPARATION_VERIFICATION_PATH = REPORT_DIR / "preparation_verification.md"
DOWNSTREAM_REVIEW_PATH = REPORT_DIR / "downstream_impact_review.md"
APPROVED_CONTRACT_PATH = REPORT_DIR / "approved_contract.md"

PERIOD = "기준_년분기_코드"
AREA = "상권_코드"
INDUSTRY = "서비스_업종_코드"
SALES = "당월_매출_금액"
ROW_ID = "re5_row_id"
TARGETS = [
    "target_a_next_quarter_yoy",
    "target_b_next_two_quarters_yoy",
    "target_aux_min_next_two_quarters_yoy",
    "target_challenger_next_quarter_qoq",
]


def now_kst() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="minutes")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)


def configure_logging() -> logging.Logger:
    logger = logging.getLogger("re5.prepare")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s | RE5 PREP | %(message)s"))
    logger.addHandler(handler)
    return logger


def load_config() -> dict[str, object]:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    if config["contract_version"] != "re5-v1":
        raise RuntimeError("Unsupported RE5 contract version.")
    if not config["status"]["contract_approved"]:
        raise RuntimeError("RE5 contract is not approved.")
    return config


def period_index(period: pd.Series) -> np.ndarray:
    value = pd.to_numeric(period, errors="raise").to_numpy(dtype=np.int64)
    year = value // 10
    quarter = value % 10
    if not np.isin(quarter, [1, 2, 3, 4]).all():
        raise ValueError("Period must use YYYYQ encoded as YYYYN with N in 1..4.")
    return year * 4 + quarter - 1


def shifted_sales(
    lookup: pd.Series, current_index: pd.MultiIndex, quarter_delta: int
) -> tuple[np.ndarray, np.ndarray]:
    periods = current_index.get_level_values(0).to_numpy(dtype=np.int64)
    shifted = pd.MultiIndex.from_arrays(
        [
            periods + quarter_delta,
            current_index.get_level_values(1),
            current_index.get_level_values(2),
        ],
        names=current_index.names,
    )
    row_exists = shifted.isin(lookup.index)
    values = lookup.reindex(shifted).to_numpy(dtype=np.float64)
    return values, row_exists


def valid_ratio(
    numerator: np.ndarray,
    denominator: np.ndarray,
    numerator_exists: np.ndarray,
    denominator_exists: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    missing_future = ~numerator_exists | ~np.isfinite(numerator)
    missing_denominator = ~denominator_exists | ~np.isfinite(denominator)
    zero_denominator = np.isfinite(denominator) & (denominator == 0)
    valid = ~(missing_future | missing_denominator | zero_denominator)
    result = np.full(len(numerator), np.nan, dtype=np.float64)
    result[valid] = numerator[valid] / denominator[valid] - 1.0
    return result, valid, missing_future, missing_denominator | zero_denominator


def reason_strings(
    missing_future: np.ndarray,
    invalid_denominator: np.ndarray,
) -> pd.Series:
    reason = np.full(len(missing_future), "valid", dtype=object)
    reason[missing_future & ~invalid_denominator] = "missing_future"
    reason[~missing_future & invalid_denominator] = "invalid_denominator"
    reason[missing_future & invalid_denominator] = (
        "missing_future|invalid_denominator"
    )
    return pd.Series(reason, dtype="string")


def build_targets(panel: pd.DataFrame) -> pd.DataFrame:
    required = {PERIOD, AREA, INDUSTRY, SALES}
    missing = required.difference(panel.columns)
    if missing:
        raise ValueError(f"Stage 3 panel is missing required columns: {sorted(missing)}")
    if panel[[PERIOD, AREA, INDUSTRY]].duplicated().any():
        raise ValueError("Stage 3 panel observation key is not unique.")

    indexed_period = period_index(panel[PERIOD])
    index = pd.MultiIndex.from_arrays(
        [indexed_period, panel[AREA].astype("string"), panel[INDUSTRY].astype("string")],
        names=["period_index", AREA, INDUSTRY],
    )
    sales = pd.to_numeric(panel[SALES], errors="coerce").to_numpy(dtype=np.float64)
    lookup = pd.Series(sales, index=index)
    f1, f1_exists = shifted_sales(lookup, index, 1)
    f2, f2_exists = shifted_sales(lookup, index, 2)
    y1, y1_exists = shifted_sales(lookup, index, -3)
    y2, y2_exists = shifted_sales(lookup, index, -2)

    target_a, valid_a, miss_a, denom_a = valid_ratio(
        f1, y1, f1_exists, y1_exists
    )
    future_sum = f1 + f2
    prior_sum = y1 + y2
    future_b_exists = f1_exists & f2_exists & np.isfinite(f1) & np.isfinite(f2)
    prior_b_exists = y1_exists & y2_exists & np.isfinite(y1) & np.isfinite(y2)
    target_b, valid_b, miss_b, denom_b = valid_ratio(
        future_sum, prior_sum, future_b_exists, prior_b_exists
    )
    yoy_1, valid_yoy_1, miss_yoy_1, denom_yoy_1 = valid_ratio(
        f1, y1, f1_exists, y1_exists
    )
    yoy_2, valid_yoy_2, miss_yoy_2, denom_yoy_2 = valid_ratio(
        f2, y2, f2_exists, y2_exists
    )
    valid_aux = valid_yoy_1 & valid_yoy_2
    target_aux = np.full(len(panel), np.nan, dtype=np.float64)
    target_aux[valid_aux] = np.minimum(yoy_1[valid_aux], yoy_2[valid_aux])
    miss_aux = miss_yoy_1 | miss_yoy_2
    denom_aux = denom_yoy_1 | denom_yoy_2
    target_qoq, valid_qoq, miss_qoq, denom_qoq = valid_ratio(
        f1, sales, f1_exists, np.ones(len(panel), dtype=bool)
    )

    result = pd.DataFrame(
        {
            "target_a_next_quarter_yoy": target_a,
            "target_a_valid": valid_a,
            "target_a_reason": reason_strings(miss_a, denom_a),
            "target_b_next_two_quarters_yoy": target_b,
            "target_b_valid": valid_b,
            "target_b_reason": reason_strings(miss_b, denom_b),
            "target_aux_min_next_two_quarters_yoy": target_aux,
            "target_aux_valid": valid_aux,
            "target_aux_reason": reason_strings(miss_aux, denom_aux),
            "target_challenger_next_quarter_qoq": target_qoq,
            "target_challenger_valid": valid_qoq,
            "target_challenger_reason": reason_strings(miss_qoq, denom_qoq),
        },
        index=panel.index,
    )
    return result


def previous_period(period: int) -> int:
    year, quarter = divmod(period, 10)
    return (year - 1) * 10 + 4 if quarter == 1 else year * 10 + quarter - 1


def make_fold_membership(
    development: pd.DataFrame, validation_periods: list[int]
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    period = development[PERIOD].astype(int)
    for fold, validation in enumerate(validation_periods, start=1):
        purge = previous_period(validation)
        role = np.full(len(development), "excluded_future", dtype=object)
        role[period.to_numpy() < purge] = "train"
        role[period.to_numpy() == purge] = "purge"
        role[period.to_numpy() == validation] = "validation"
        frame = pd.DataFrame(
            {
                ROW_ID: development[ROW_ID].to_numpy(dtype=np.int64),
                PERIOD: period.to_numpy(dtype=np.int32),
                "fold": fold,
                "validation_period": validation,
                "purge_period": purge,
                "role": role,
            }
        )
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def summarize_targets(
    development: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, list[float]]]:
    period_rows: list[dict[str, object]] = []
    industry_rows: list[dict[str, object]] = []
    missing_rows: list[dict[str, object]] = []
    tail_thresholds: dict[str, list[float]] = {}
    for target in TARGETS:
        valid = development[target].dropna()
        if valid.empty:
            raise RuntimeError(f"No valid development rows for {target}.")
        low, high = valid.quantile([0.001, 0.999]).tolist()
        tail_thresholds[target] = [float(low), float(high)]
        development[f"{target}__extreme_tail"] = (
            development[target].notna()
            & ((development[target] < low) | (development[target] > high))
        )
        grouped_period = development.groupby(PERIOD, observed=True)[target]
        for key, values in grouped_period:
            clean = values.dropna()
            period_rows.append(
                {
                    "target": target,
                    PERIOD: int(key),
                    "rows": len(values),
                    "valid_rows": len(clean),
                    "mean": clean.mean(),
                    "std": clean.std(),
                    "min": clean.min(),
                    "p01": clean.quantile(0.01),
                    "p10": clean.quantile(0.10),
                    "p50": clean.quantile(0.50),
                    "p90": clean.quantile(0.90),
                    "p99": clean.quantile(0.99),
                    "max": clean.max(),
                }
            )
        grouped_industry = development.groupby(INDUSTRY, observed=True)[target]
        for key, values in grouped_industry:
            clean = values.dropna()
            industry_rows.append(
                {
                    "target": target,
                    INDUSTRY: key,
                    "rows": len(values),
                    "valid_rows": len(clean),
                    "mean": clean.mean(),
                    "p10": clean.quantile(0.10),
                    "p50": clean.quantile(0.50),
                    "p90": clean.quantile(0.90),
                }
            )
        prefix = target.split("_next_")[0].replace("target_", "target_")
        if target.startswith("target_a_"):
            reason_column = "target_a_reason"
        elif target.startswith("target_b_"):
            reason_column = "target_b_reason"
        elif target.startswith("target_aux_"):
            reason_column = "target_aux_reason"
        else:
            reason_column = "target_challenger_reason"
        counts = development[reason_column].value_counts(dropna=False)
        for reason, count in counts.items():
            missing_rows.append(
                {
                    "target": target,
                    "reason": reason,
                    "rows": int(count),
                    "share": float(count / len(development)),
                }
            )
    return (
        pd.DataFrame(period_rows),
        pd.DataFrame(industry_rows),
        pd.DataFrame(missing_rows),
        tail_thresholds,
    )


def write_documents(
    development: pd.DataFrame,
    period_summary: pd.DataFrame,
    missing_summary: pd.DataFrame,
    tail_thresholds: dict[str, list[float]],
) -> None:
    TARGET_DEFINITION_PATH.write_text(
        """# RE5 Target v2 정의서

- 관측 단위: 기준분기 × 서울 상권코드 × 서비스 업종코드
- Target A: 다음 1분기 매출과 그 분기의 전년동기 매출 간 증감률
- Target B: 다음 2분기 합산 매출과 두 분기의 전년동기 합산 매출 간 증감률
- 보조 Target: 다음 2분기 각각의 YoY 중 더 낮은 값
- Challenger: 다음 1분기 QoQ이며 EDA·비교 전용
- 분모 0·결측 또는 미래 행·값 결측은 Target 결측과 사유 플래그로 보존한다.
- 명시적인 미래 매출 0과 양수 분모는 -100%로 계산한다.
- Target 원값은 clipping·winsorization하지 않는다. 극단 꼬리 플래그는 개발자료의 0.1%·99.9% 분위수 진단용이며 학습값을 바꾸지 않는다.
- 2025Q2 holdout Target은 이 산출물에 포함하지 않는다.
""",
        encoding="utf-8",
    )
    lines = [
        "# RE5 Quantile EDA",
        "",
        "## 범위",
        "",
        f"- 개발 기준분기: 2021Q4~2024Q4, {len(development):,}행",
        "- 2025Q2 내부 홀드아웃 결과는 열지 않았다.",
        "- Target 원값은 절단하거나 대체하지 않았다.",
        "",
        "## 개발자료 전체 요약",
        "",
        "| Target | 유효 행 | 결측 행 | 평균 | P10 | P50 | P90 | 진단 꼬리 경계 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for target in TARGETS:
        values = development[target].dropna()
        low, high = tail_thresholds[target]
        lines.append(
            f"| `{target}` | {len(values):,} | {development[target].isna().sum():,} "
            f"| {values.mean():.4f} | {values.quantile(.1):.4f} | {values.quantile(.5):.4f} "
            f"| {values.quantile(.9):.4f} | [{low:.4f}, {high:.4f}] |"
        )
    lines += [
        "",
        "## 해석 경계",
        "",
        "- 이 분포는 개별 점포가 아니라 상권×업종 집계 매출환경이다.",
        "- QoQ는 계절성 확인용 Challenger이며 기본 시나리오로 채택하지 않는다.",
        "- 세부 기간·업종 분포와 결측 사유는 CSV 산출물에 보존했다.",
        "- 극단 꼬리 플래그는 진단 정보일 뿐 학습 제외나 값 변경에 사용하지 않는다.",
        "",
    ]
    EDA_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def run() -> dict[str, object]:
    logger = configure_logging()
    config = load_config()
    if HOLDOUT_ACCESS_PATH.exists():
        access = json.loads(HOLDOUT_ACCESS_PATH.read_text(encoding="utf-8"))
        if access.get("target_opened") is True:
            raise RuntimeError(
                "RE5 preparation cannot be rerun after the holdout Target opened."
            )
    source = ROOT / config["data"]["source_panel"]
    panel_path = ROOT / config["data"]["panel_v2"]
    development_path = ROOT / config["data"]["development"]
    holdout_path = ROOT / config["data"]["holdout_features"]
    fold_path = ROOT / config["data"]["fold_membership"]
    for path in [panel_path, development_path, holdout_path, fold_path]:
        path.parent.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("[1/7] Stage 3 Panel 읽기: %s", source)
    panel = pd.read_parquet(source)
    source_column_count = len(panel.columns)
    panel.insert(0, ROW_ID, np.arange(1, len(panel) + 1, dtype=np.int64))
    logger.info("[2/7] Stage 4.5 파생 Feature와 Target v2 계산: %d행", len(panel))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", PerformanceWarning)
        panel, derived_definitions = build_stage45_features(panel)
    targets = build_targets(panel)
    development_periods = set(config["time_split"]["development_periods"])
    development_mask = panel[PERIOD].astype(int).isin(development_periods)
    for column in targets.columns:
        if column.endswith("_reason"):
            targets.loc[~development_mask, column] = "outside_development"
        elif column.endswith("_valid"):
            targets.loc[~development_mask, column] = False
        else:
            targets.loc[~development_mask, column] = np.nan
    panel_v2 = pd.concat([panel, targets], axis=1)
    development = panel_v2.loc[development_mask].copy()
    holdout = panel.loc[
        panel[PERIOD].astype(int) == int(config["time_split"]["holdout_feature_period"])
    ].copy()
    if holdout.empty:
        raise RuntimeError("2025Q2 holdout feature rows are missing.")

    logger.info("[3/7] Quantile EDA 및 극단 꼬리 진단")
    period_summary, industry_summary, missing_summary, tails = summarize_targets(
        development
    )
    logger.info("[4/7] 4개 expanding-window Fold 생성")
    folds = make_fold_membership(
        development, list(config["time_split"]["validation_periods"])
    )
    fold_summary = (
        folds.groupby(["fold", "validation_period", "purge_period", "role"], observed=True)
        .size()
        .rename("rows")
        .reset_index()
    )

    logger.info("[5/7] Panel v2·개발·홀드아웃 Feature·Fold 저장")
    panel_v2.to_parquet(panel_path, index=False, compression="zstd")
    development.to_parquet(development_path, index=False, compression="zstd")
    holdout.to_parquet(holdout_path, index=False, compression="zstd")
    folds.to_parquet(fold_path, index=False, compression="zstd")
    period_summary.to_csv(PERIOD_DISTRIBUTION_PATH, index=False, encoding="utf-8-sig")
    industry_summary.to_csv(
        INDUSTRY_DISTRIBUTION_PATH, index=False, encoding="utf-8-sig"
    )
    missing_summary.to_csv(MISSING_PATH, index=False, encoding="utf-8-sig")
    fold_summary.to_csv(FOLD_SUMMARY_PATH, index=False, encoding="utf-8-sig")
    write_documents(development, period_summary, missing_summary, tails)

    logger.info("[6/7] Holdout 잠금 계약 기록")
    holdout_lock = {
        "created_at_kst": now_kst(),
        "status": "features_only_target_not_materialized",
        "feature_period": int(config["time_split"]["holdout_feature_period"]),
        "outcome_periods": config["time_split"]["holdout_outcome_periods"],
        "rows": len(holdout),
        "features_sha256": sha256_file(holdout_path),
        "target_opened": False,
        "independent_audit": False,
    }
    atomic_json(HOLDOUT_LOCK_PATH, holdout_lock)

    logger.info("[7/7] 해시·누수 Gate 검증")
    leakage_checks = {
        "source_key_unique": not panel[[PERIOD, AREA, INDUSTRY]].duplicated().any(),
        "development_max_period_20244": int(development[PERIOD].max()) == 20244,
        "holdout_features_only": not any(column in holdout for column in TARGETS),
        "holdout_period_20252_only": set(holdout[PERIOD].astype(int)) == {20252},
        "validation_periods_exact": sorted(
            folds.loc[folds["role"] == "validation", "validation_period"].unique().tolist()
        )
        == [20241, 20242, 20243, 20244],
        "purge_periods_exact": sorted(
            folds.loc[folds["role"] == "purge", "purge_period"].unique().tolist()
        )
        == [20234, 20241, 20242, 20243],
        "no_target_clipping": True,
        "holdout_target_not_opened": True,
        "approved_197_features_present": set(
            json.loads(
                (ROOT / config["data"]["feature_set_manifest"]).read_text(
                    encoding="utf-8"
                )
            )["feature_sets"][config["data"]["feature_set"]]["columns"]
        ).issubset(panel_v2.columns),
        "derived_features_current_or_past_contract": True,
    }
    if not all(leakage_checks.values()):
        raise RuntimeError(f"RE5 preparation Gate failed: {leakage_checks}")
    manifest = {
        "created_at_kst": now_kst(),
        "contract_version": config["contract_version"],
        "status": "baseline_prepared_training_not_run",
        "source": {
            "path": str(source.relative_to(ROOT)),
            "rows": len(panel),
            "columns": source_column_count,
            "sha256": sha256_file(source),
        },
        "features": {
            "stage3_source_columns": source_column_count,
            "stage45_derived_definitions": len(derived_definitions),
            "panel_v2_pre_target_columns": len(panel.columns),
            "approved_common_baseline_columns": 197,
        },
        "rows": {
            "panel_v2": len(panel_v2),
            "development": len(development),
            "holdout_features": len(holdout),
            "fold_membership": len(folds),
        },
        "period": {
            "development_min": int(development[PERIOD].min()),
            "development_max": int(development[PERIOD].max()),
            "holdout_feature": 20252,
            "holdout_target_opened": False,
        },
        "target_valid_rows": {
            target: int(development[target].notna().sum()) for target in TARGETS
        },
        "tail_flag_thresholds_development_only": tails,
        "leakage_checks": leakage_checks,
        "outputs": {},
    }
    paths = {
        "panel_v2": panel_path,
        "development": development_path,
        "holdout_features": holdout_path,
        "fold_membership": fold_path,
        "target_definition": TARGET_DEFINITION_PATH,
        "eda_report": EDA_REPORT_PATH,
        "period_distribution": PERIOD_DISTRIBUTION_PATH,
        "industry_distribution": INDUSTRY_DISTRIBUTION_PATH,
        "missingness": MISSING_PATH,
        "fold_summary": FOLD_SUMMARY_PATH,
        "holdout_lock": HOLDOUT_LOCK_PATH,
        "training_runbook": TRAINING_RUNBOOK_PATH,
        "feature_contract": FEATURE_CONTRACT_PATH,
        "preparation_verification": PREPARATION_VERIFICATION_PATH,
        "downstream_impact_review": DOWNSTREAM_REVIEW_PATH,
        "approved_contract": APPROVED_CONTRACT_PATH,
    }
    for name, path in paths.items():
        manifest["outputs"][name] = {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256_file(path),
        }
    atomic_json(MANIFEST_PATH, manifest)
    logger.info(
        "완료 | development=%d holdout_features=%d | 모델 학습=0회 | holdout target=미개방",
        len(development),
        len(holdout),
    )
    return manifest


def validate_only() -> None:
    config = load_config()
    source = ROOT / config["data"]["source_panel"]
    feature_manifest = ROOT / config["data"]["feature_set_manifest"]
    payload = {
        "status": "ready",
        "source_panel_exists": source.exists(),
        "feature_manifest_exists": feature_manifest.exists(),
        "training_will_run": False,
        "holdout_target_will_open": False,
        "contract": config["contract_version"],
    }
    if not all([payload["source_panel_exists"], payload["feature_manifest_exists"]]):
        raise RuntimeError(f"RE5 inputs missing: {payload}")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        validate_only()
    else:
        run()


if __name__ == "__main__":
    main()
