"""Run the single approved locked-2025 audit for final LightGBM Trial 10.

The final model and feature set are frozen before this script is authorized.
The audit reports only threshold-independent probability/ranking metrics.  It
does not search, select, or report a binary operating threshold.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import logging
import math
import os
import sqlite3
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import joblib
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import yaml
from scipy import sparse
from sklearn.preprocessing import OneHotEncoder

from src.data.build_stage4_dataset import DATABASE_PATH, prepare_labels
from src.features.build_stage45_features import build_stage45_features
from src.features.build_stage5_feature_sets import (
    build_feature_set_specs,
    read_contract_rows,
)
from src.models.run_stage5_base_comparison import (
    FEATURE_CONTRACT_PATH,
    RANDOM_SEED,
    TARGET,
)
from src.models.run_stage5_optuna import build_sparse_estimator, probability_metrics


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STAGE4_CONFIG_PATH = PROJECT_ROOT / "config" / "stage4.yaml"
STAGE5_CONFIG_PATH = PROJECT_ROOT / "config" / "stage5.yaml"
STAGE4_MANIFEST_PATH = PROJECT_ROOT / "reports" / "stage4" / "stage4_manifest.json"
TRIALS_PATH = PROJECT_ROOT / "reports" / "stage5" / "optuna_trials.csv"
REPORT_DIR = PROJECT_ROOT / "reports" / "stage5"
ARTIFACT_DIR = REPORT_DIR / "artifacts"
ACCESS_PATH = REPORT_DIR / "final_2025_access.json"
LOG_PATH = REPORT_DIR / "final_2025_run.log"
PREDICTIONS_PATH = REPORT_DIR / "final_2025_predictions.parquet"
METRICS_PATH = REPORT_DIR / "final_2025_metrics.json"
REPORT_PATH = REPORT_DIR / "final_2025_report.md"
MANIFEST_PATH = REPORT_DIR / "final_2025_manifest.json"
MODEL_PATH = ARTIFACT_DIR / "stage5_lightgbm_trial10.joblib"
MODEL_METADATA_PATH = ARTIFACT_DIR / "stage5_lightgbm_trial10_metadata.json"

APPROVED_MODEL = "lightgbm"
APPROVED_TRIAL = 10
APPROVED_FEATURE_SET = "common_baseline"
APPROVED_METRICS = ("average_precision", "roc_auc", "brier_score", "log_loss")
REFIT_PERIODS = (20222, 20243)
LOCKED_PERIODS = (20251, 20254)


def now_kst() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)


def configure_logger() -> logging.Logger:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("stage5_final_2025")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8", mode="a")
    file_handler.setFormatter(formatter)
    logger.addHandler(console)
    logger.addHandler(file_handler)
    return logger


def load_contract() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    stage4 = yaml.safe_load(STAGE4_CONFIG_PATH.read_text(encoding="utf-8"))
    stage5 = yaml.safe_load(STAGE5_CONFIG_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(STAGE4_MANIFEST_PATH.read_text(encoding="utf-8"))

    status = stage5["status"]
    if status.get("final_model") not in {
        "approved_lightgbm_trial10",
        "completed_lightgbm_trial10_artifact_verified",
    }:
        raise RuntimeError("Final LightGBM Trial 10 is not approved.")
    if status.get("locked_2025_evaluation") not in {
        "approved_threshold_independent_once",
        "completed_threshold_independent_once",
    }:
        raise RuntimeError("The one-time threshold-independent 2025 audit is not approved.")
    policy = stage5["metrics"]["locked_test_without_threshold"]
    if policy.get("status") not in {"approved_by_user", "completed"}:
        raise RuntimeError("Locked-test metric scope lacks explicit user approval.")
    if policy.get("recommended_scope") != [
        "average_precision_auprc",
        "roc_auc",
        "brier_score",
        "log_loss",
    ]:
        raise RuntimeError("Approved locked-test metrics changed.")
    if policy.get("exclude") != [
        "binary_classification_metrics",
        "threshold_search",
        "threshold_selection",
    ]:
        raise RuntimeError("Locked-test threshold exclusions changed.")
    selection = stage5["oof_ensemble"]["service_selection_policy"]
    if selection.get("current_final_choice") != "lightgbm_trial10":
        raise RuntimeError("Final model is not frozen to LightGBM Trial 10.")
    if selection.get("feature_set") != APPROVED_FEATURE_SET:
        raise RuntimeError("Final feature set differs from the approved common baseline.")
    if selection.get("frozen_before_locked_2025") is not True:
        raise RuntimeError("Final-model freeze is not recorded.")
    if manifest["verification"]["locked_test_target_materialized"] is not False:
        raise RuntimeError("Stage 4 manifest says locked Target was already materialized.")
    if manifest["verification"]["locked_test_target_statistics_inspected"] is not False:
        raise RuntimeError("Stage 4 manifest says locked Target was already inspected.")
    expected_refit = tuple(stage4["final_evaluation"]["refit_target_end_period"])
    expected_test = tuple(stage4["final_evaluation"]["locked_test_target_end_period"])
    if expected_refit != REFIT_PERIODS or expected_test != LOCKED_PERIODS:
        raise RuntimeError("Final refit or locked-test period differs from approval.")
    return stage4, stage5, manifest


def load_trial() -> tuple[dict[str, Any], str]:
    trials = pd.read_csv(TRIALS_PATH, encoding="utf-8-sig")
    selected = trials[
        (trials["model"] == APPROVED_MODEL)
        & (trials["feature_set"] == APPROVED_FEATURE_SET)
        & (trials["trial_number"] == APPROVED_TRIAL)
        & (trials["state"] == "COMPLETE")
    ]
    if len(selected) != 1:
        raise RuntimeError("Approved LightGBM Trial 10 is missing or duplicated.")
    params = json.loads(selected.iloc[0]["params_json"])
    digest = hashlib.sha256(
        json.dumps(params, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return params, digest


def read_feature_frame(
    path: Path,
    feature_columns: list[str],
    categorical_columns: list[str],
    extra_columns: list[str],
) -> pd.DataFrame:
    columns = ["stage4_row_id", *feature_columns, *extra_columns]
    table = pq.read_table(path, columns=columns)
    arrays: list[pa.Array | pa.ChunkedArray] = []
    fields: list[pa.Field] = []
    categorical = set(categorical_columns)
    for column in columns:
        values = table[column]
        if column == "stage4_row_id":
            values = values.cast(pa.int64(), safe=False)
        elif column == TARGET:
            values = values.cast(pa.int8(), safe=False)
        elif column == "target_end_period":
            values = values.cast(pa.int32(), safe=False)
        elif column in categorical:
            values = values.combine_chunks().dictionary_encode()
        else:
            values = values.cast(pa.float32(), safe=False)
        arrays.append(values)
        fields.append(pa.field(column, values.type))
    compressed = pa.Table.from_arrays(arrays, schema=pa.schema(fields))
    del table, arrays
    return compressed.to_pandas(split_blocks=True, self_destruct=True)


def prepare_model_frames(
    stage5: dict[str, Any], manifest: dict[str, Any]
) -> tuple[
    pd.DataFrame,
    np.ndarray,
    pd.DataFrame,
    np.ndarray,
    Any,
    list[str],
    list[str],
]:
    feature_columns = manifest["feature_columns"]
    development_path = PROJECT_ROOT / stage5["data"]["development"]
    locked_path = PROJECT_ROOT / manifest["outputs"]["locked_test_features"]
    development_schema = pq.ParquetFile(development_path).schema_arrow
    locked_schema = pq.ParquetFile(locked_path).schema_arrow
    categorical_columns = [
        column
        for column in feature_columns
        if pa.types.is_string(development_schema.field(column).type)
    ]
    for column in feature_columns:
        if development_schema.field(column).type != locked_schema.field(column).type:
            raise RuntimeError(f"Development/locked schema mismatch: {column}")

    development = read_feature_frame(
        development_path,
        feature_columns,
        categorical_columns,
        ["target_end_period", TARGET],
    )
    locked = read_feature_frame(
        locked_path,
        feature_columns,
        categorical_columns,
        ["target_end_period"],
    )
    if len(development) != manifest["row_counts"]["development_rows"]:
        raise RuntimeError("Unexpected development row count.")
    if len(locked) != manifest["row_counts"]["locked_test_feature_rows"]:
        raise RuntimeError("Unexpected locked-feature row count.")
    if development["stage4_row_id"].duplicated().any() or locked["stage4_row_id"].duplicated().any():
        raise RuntimeError("Duplicate Stage 4 row IDs.")
    if np.intersect1d(
        development["stage4_row_id"].to_numpy(), locked["stage4_row_id"].to_numpy()
    ).size:
        raise RuntimeError("Development and locked Stage 4 row IDs overlap.")

    development["_source"] = "development"
    locked["_source"] = "locked"
    combined = pd.concat([development, locked], ignore_index=True, sort=False)
    combined = combined.set_index("stage4_row_id", drop=False)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", pd.errors.PerformanceWarning)
        enriched, _ = build_stage45_features(combined[feature_columns])
    specs = build_feature_set_specs(
        read_contract_rows(FEATURE_CONTRACT_PATH), enriched.columns
    )
    spec = specs[APPROVED_FEATURE_SET]
    if len(spec.columns) != 197:
        raise RuntimeError(f"Expected 197 final features, got {len(spec.columns)}.")

    development_period = combined.loc[
        combined["_source"].eq("development"), "target_end_period"
    ]
    train_ids = development_period.index[
        development_period.between(*REFIT_PERIODS)
    ].to_numpy(dtype="int64")
    locked_period = combined.loc[
        combined["_source"].eq("locked"), "target_end_period"
    ]
    test_ids = locked_period.index[
        locked_period.between(*LOCKED_PERIODS)
    ].to_numpy(dtype="int64")
    if len(train_ids) == 0 or len(test_ids) != len(locked):
        raise RuntimeError("Final refit or locked-test membership is invalid.")
    target_by_id = development.set_index("stage4_row_id")[TARGET]
    train_target = target_by_id.loc[train_ids].to_numpy(dtype="int8")
    train_features = enriched.loc[train_ids, list(spec.columns)].copy()
    test_features = enriched.loc[test_ids, list(spec.columns)].copy()
    test_periods = locked.set_index("stage4_row_id").loc[
        test_ids, "target_end_period"
    ].to_numpy(dtype="int32")
    model_categorical = [
        column
        for column in spec.columns
        if isinstance(train_features[column].dtype, pd.CategoricalDtype)
        or pd.api.types.is_string_dtype(train_features[column].dtype)
        or pd.api.types.is_object_dtype(train_features[column].dtype)
    ]
    model_numeric = [
        column for column in spec.columns if column not in model_categorical
    ]
    del enriched, combined, development, locked
    gc.collect()
    return (
        train_features,
        train_target,
        test_features,
        test_periods,
        spec,
        model_numeric,
        model_categorical,
    )


def fit_preprocessor(
    train: pd.DataFrame,
    test: pd.DataFrame,
    numeric_columns: list[str],
    categorical_columns: list[str],
) -> tuple[sparse.csr_matrix, sparse.csr_matrix, dict[str, Any]]:
    train_numeric = np.empty((len(train), len(numeric_columns)), dtype=np.float32)
    test_numeric = np.empty((len(test), len(numeric_columns)), dtype=np.float32)
    medians: dict[str, float] = {}
    scales: dict[str, float] = {}
    for index, column in enumerate(numeric_columns):
        train_values = train[column].to_numpy(dtype=np.float32, copy=True)
        test_values = test[column].to_numpy(dtype=np.float32, copy=True)
        train_values[~np.isfinite(train_values)] = np.nan
        test_values[~np.isfinite(test_values)] = np.nan
        finite_train = train_values[np.isfinite(train_values)]
        median = float(np.median(finite_train)) if finite_train.size else 0.0
        train_values[np.isnan(train_values)] = median
        test_values[np.isnan(test_values)] = median
        scale = float(train_values.std(dtype=np.float64))
        if not math.isfinite(scale) or scale == 0:
            scale = 1.0
        train_numeric[:, index] = train_values / scale
        test_numeric[:, index] = test_values / scale
        medians[column] = median
        scales[column] = scale
    train_parts = [sparse.csr_matrix(train_numeric)]
    test_parts = [sparse.csr_matrix(test_numeric)]
    encoder: OneHotEncoder | None = None
    if categorical_columns:
        encoder = OneHotEncoder(
            handle_unknown="ignore", sparse_output=True, dtype=np.float32
        )
        train_categories = train[categorical_columns].astype("string").fillna("__MISSING__")
        test_categories = test[categorical_columns].astype("string").fillna("__MISSING__")
        train_parts.append(encoder.fit_transform(train_categories))
        test_parts.append(encoder.transform(test_categories))
    train_matrix = sparse.hstack(train_parts, format="csr").astype(np.float32)
    test_matrix = sparse.hstack(test_parts, format="csr").astype(np.float32)
    state = {
        "version": "stage5_train_only_median_scale_onehot_v1",
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "numeric_medians": medians,
        "numeric_scales": scales,
        "categorical_encoder": encoder,
        "output_feature_count": int(train_matrix.shape[1]),
    }
    return train_matrix, test_matrix, state


def materialize_locked_target(
    stage4: dict[str, Any], expected_ids: np.ndarray
) -> np.ndarray:
    threshold = float(stage4["target"]["threshold"])
    with sqlite3.connect(DATABASE_PATH) as connection:
        prepare_labels(connection, threshold)
        labels = pd.read_sql_query(
            """
            SELECT stage4_row_id,target_end_period,future_q1_sales,future_q2_sales,
                   year_ago_q1_sales,year_ago_q2_sales
            FROM stage4_labels
            WHERE target_end_period BETWEEN '20251' AND '20254'
            ORDER BY stage4_row_id
            """,
            connection,
        )
    if len(labels) != len(expected_ids):
        raise RuntimeError("Locked label count does not match locked features.")
    if not np.array_equal(
        labels["stage4_row_id"].to_numpy(dtype="int64"), expected_ids
    ):
        raise RuntimeError("Locked label row IDs do not match locked features.")
    denominator = labels["year_ago_q1_sales"] + labels["year_ago_q2_sales"]
    combined_growth = (
        labels["future_q1_sales"]
        + labels["future_q2_sales"]
        - labels["year_ago_q1_sales"]
        - labels["year_ago_q2_sales"]
    ) / denominator
    target = (
        (labels["future_q1_sales"] < labels["year_ago_q1_sales"])
        & (labels["future_q2_sales"] < labels["year_ago_q2_sales"])
        & (combined_growth <= -threshold)
    ).to_numpy(dtype="int8")
    if not set(np.unique(target)).issubset({0, 1}) or np.unique(target).size != 2:
        raise RuntimeError("Locked target must contain both binary classes.")
    return target


def contract_hash(params_hash: str, feature_hash: str) -> str:
    payload = {
        "model": APPROVED_MODEL,
        "trial": APPROVED_TRIAL,
        "params_sha256": params_hash,
        "feature_set": APPROVED_FEATURE_SET,
        "feature_set_sha256": feature_hash,
        "refit_periods": REFIT_PERIODS,
        "locked_periods": LOCKED_PERIODS,
        "metrics": APPROVED_METRICS,
        "threshold_metrics": False,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()


def write_report(metrics: dict[str, float], train_rows: int, test_rows: int) -> None:
    oof_ap = 0.6454
    oof_auc = 0.8108
    lines = [
        "# Stage 5 LightGBM 잠긴 2025 최종 평가",
        "",
        "## 평가 계약",
        "",
        "- 최종 모델: LightGBM Trial 10",
        "- Feature-set: 공통 기준선 197개",
        f"- 최종 Refit: Target 종료분기 {REFIT_PERIODS[0]}~{REFIT_PERIODS[1]}, {train_rows:,}행",
        f"- 잠긴 테스트: Target 종료분기 {LOCKED_PERIODS[0]}~{LOCKED_PERIODS[1]}, {test_rows:,}행",
        "- 2025를 열기 전에 모델과 Feature-set을 고정했으며 결과를 보고 다른 모델로 바꾸지 않는다.",
        "- 운영 임계값은 미정이다. 이 평가에서는 임계값 탐색·이진 위험 판정·Precision·Recall·F2를 계산하지 않았다.",
        "",
        "## 최종 성능",
        "",
        "| 지표 | 2024 OOF | 잠긴 2025 | 변화 |",
        "| --- | ---: | ---: | ---: |",
        f"| AUPRC / Average Precision | {oof_ap:.4f} | {metrics['average_precision']:.4f} | {metrics['average_precision'] - oof_ap:+.4f} |",
        f"| AUROC | {oof_auc:.4f} | {metrics['roc_auc']:.4f} | {metrics['roc_auc'] - oof_auc:+.4f} |",
        f"| Brier Score | 0.1565 | {metrics['brier_score']:.4f} | {metrics['brier_score'] - 0.1565:+.4f} |",
        f"| Log Loss | 0.4749 | {metrics['log_loss']:.4f} | {metrics['log_loss'] - 0.4749:+.4f} |",
        "",
        "## 해석 경계",
        "",
        "- 이 수치는 `상권 × 업종`의 향후 매출환경 악화 위험을 정렬하는 모델의 일반화 성능이다. 개별 점포의 폐업확률이나 인과효과가 아니다.",
        "- 위험표시율 50% 또는 F2 최대 임계값은 운영안으로 채택되지 않았다. 서비스의 위험등급·상위 지원비율은 실제 개입 가능 규모와 함께 별도로 결정한다.",
        "- 잠긴 2025 결과는 최종 모델이나 임계값을 재선택하는 자료로 사용하지 않는다.",
        "",
    ]
    temporary = REPORT_PATH.with_suffix(".md.tmp")
    temporary.write_text("\n".join(lines), encoding="utf-8")
    temporary.replace(REPORT_PATH)


def status() -> None:
    if not ACCESS_PATH.exists():
        print(json.dumps({"status": "not_started"}, ensure_ascii=False))
        return
    print(ACCESS_PATH.read_text(encoding="utf-8"))


def validate_only() -> None:
    _, stage5, manifest = load_contract()
    params, params_hash = load_trial()
    common = json.loads(
        (REPORT_DIR / "feature_sets.json").read_text(encoding="utf-8")
    )["feature_sets"][APPROVED_FEATURE_SET]
    payload = {
        "status": "validation_passed",
        "model": f"{APPROVED_MODEL}_trial{APPROVED_TRIAL}",
        "feature_set": APPROVED_FEATURE_SET,
        "feature_count": common["column_count"],
        "params_sha256": params_hash,
        "development_rows": manifest["row_counts"]["development_rows"],
        "locked_feature_rows": manifest["row_counts"]["locked_test_feature_rows"],
        "approved_metrics": list(APPROVED_METRICS),
        "threshold_metrics": False,
        "locked_target_opened": False,
        "current_execution_status": stage5["status"]["locked_2025_evaluation"],
    }
    if not params or common["column_count"] != 197:
        raise RuntimeError("Final model contract validation failed.")
    print(json.dumps(payload, ensure_ascii=False, indent=2), flush=True)


def run() -> None:
    logger = configure_logger()
    stage4, stage5, manifest = load_contract()
    if ACCESS_PATH.exists():
        prior = json.loads(ACCESS_PATH.read_text(encoding="utf-8"))
        if prior.get("status") == "completed":
            raise RuntimeError("Locked 2025 audit is already completed; rerun is prohibited.")
    params, params_hash = load_trial()
    logger.info("RUN START | FINAL LightGBM Trial 10 | locked 2025 one-time audit")
    logger.info("Metrics: AUPRC, AUROC, Brier Score, Log Loss | threshold metrics: FORBIDDEN")
    logger.info("Final model switching after result: FORBIDDEN")

    started = time.perf_counter()
    access: dict[str, Any] = {
        "status": "running",
        "started_at_kst": now_kst(),
        "updated_at_kst": now_kst(),
        "model": "lightgbm_trial10",
        "feature_set": APPROVED_FEATURE_SET,
        "locked_target_opened": False,
        "threshold_metrics_computed": False,
        "rerun_prohibited_after_completion": True,
    }
    atomic_json(ACCESS_PATH, access)
    try:
        (
            train_features,
            train_target,
            test_features,
            test_periods,
            feature_spec,
            numeric_columns,
            categorical_columns,
        ) = prepare_model_frames(stage5, manifest)
        final_contract_hash = contract_hash(params_hash, feature_spec.sha256)
        access["contract_sha256"] = final_contract_hash
        access["updated_at_kst"] = now_kst()
        atomic_json(ACCESS_PATH, access)
        logger.info(
            "DATA READY | refit=%d locked=%d features=%d",
            len(train_features),
            len(test_features),
            len(feature_spec.columns),
        )

        transform_started = time.perf_counter()
        train_matrix, test_matrix, preprocessor = fit_preprocessor(
            train_features,
            test_features,
            numeric_columns,
            categorical_columns,
        )
        transform_seconds = time.perf_counter() - transform_started
        logger.info(
            "PREPROCESS DONE | train=%s locked=%s seconds=%.1f",
            train_matrix.shape,
            test_matrix.shape,
            transform_seconds,
        )

        jobs = max(
            1,
            min(
                int(stage5["screen_budget"]["max_parallel_cpu_threads"]),
                max(1, (os.cpu_count() or 2) - 1),
            ),
        )
        estimator = build_sparse_estimator(APPROVED_MODEL, params, jobs)
        fit_started = time.perf_counter()
        estimator.fit(train_matrix, train_target)
        fit_seconds = time.perf_counter() - fit_started
        logger.info("MODEL FIT DONE | rows=%d seconds=%.1f", len(train_target), fit_seconds)

        test_ids = test_features.index.to_numpy(dtype="int64")
        locked_target = materialize_locked_target(stage4, test_ids)
        access["locked_target_opened"] = True
        access["target_opened_at_kst"] = now_kst()
        access["updated_at_kst"] = now_kst()
        atomic_json(ACCESS_PATH, access)
        logger.info("LOCKED TARGET OPENED | one-time audit is now irreversible")

        predict_started = time.perf_counter()
        probability = estimator.predict_proba(test_matrix)[:, 1]
        predict_seconds = time.perf_counter() - predict_started
        all_metrics = probability_metrics(locked_target, probability)
        metrics = {key: float(all_metrics[key]) for key in APPROVED_METRICS}
        logger.info(
            "FINAL METRIC | AP=%.6f AUC=%.6f Brier=%.6f LogLoss=%.6f",
            metrics["average_precision"],
            metrics["roc_auc"],
            metrics["brier_score"],
            metrics["log_loss"],
        )

        predictions = pd.DataFrame(
            {
                "stage4_row_id": test_ids,
                "target_end_period": test_periods,
                TARGET: locked_target,
                "risk_probability": np.asarray(probability, dtype="float32"),
            }
        )
        temporary_predictions = PREDICTIONS_PATH.with_suffix(".parquet.tmp")
        predictions.to_parquet(
            temporary_predictions, index=False, compression="zstd"
        )
        temporary_predictions.replace(PREDICTIONS_PATH)

        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        artifact = {
            "artifact_version": "stage5_lightgbm_trial10_v1",
            "model": estimator,
            "preprocessor": preprocessor,
            "source_feature_set": APPROVED_FEATURE_SET,
            "source_feature_columns": list(feature_spec.columns),
            "derived_feature_builder": "src.features.build_stage45_features.build_stage45_features",
            "target": TARGET,
            "refit_target_end_period": list(REFIT_PERIODS),
            "operating_threshold": None,
        }
        temporary_model = MODEL_PATH.with_suffix(".joblib.tmp")
        joblib.dump(artifact, temporary_model, compress=3)
        temporary_model.replace(MODEL_PATH)
        metadata = {
            "created_at_kst": now_kst(),
            "model": APPROVED_MODEL,
            "trial_number": APPROVED_TRIAL,
            "params": params,
            "params_sha256": params_hash,
            "feature_set": APPROVED_FEATURE_SET,
            "feature_count": len(feature_spec.columns),
            "feature_set_sha256": feature_spec.sha256,
            "preprocessed_feature_count": int(train_matrix.shape[1]),
            "refit_rows": len(train_features),
            "refit_target_end_period": list(REFIT_PERIODS),
            "operating_threshold": None,
            "locked_2025_metrics": list(APPROVED_METRICS),
            "binary_threshold_metrics_computed": False,
        }
        atomic_json(MODEL_METADATA_PATH, metadata)

        saved = pd.read_parquet(PREDICTIONS_PATH)
        verified = probability_metrics(
            saved[TARGET].to_numpy(dtype="int8"),
            saved["risk_probability"].to_numpy(dtype="float64"),
        )
        for key in APPROVED_METRICS:
            if not np.isclose(metrics[key], verified[key], atol=1e-7, rtol=0):
                raise RuntimeError(f"Saved prediction metric mismatch: {key}")
        reloaded = joblib.load(MODEL_PATH)
        reloaded_probability = reloaded["model"].predict_proba(test_matrix)[:, 1]
        if not np.allclose(probability, reloaded_probability, atol=1e-7, rtol=0):
            raise RuntimeError("Reloaded final model predictions differ.")

        metric_payload = {
            "created_at_kst": now_kst(),
            "model": "lightgbm_trial10",
            "feature_set": APPROVED_FEATURE_SET,
            "refit_target_end_period": list(REFIT_PERIODS),
            "locked_test_target_end_period": list(LOCKED_PERIODS),
            "metrics": metrics,
            "threshold_metrics_computed": False,
            "operating_threshold": None,
        }
        atomic_json(METRICS_PATH, metric_payload)
        write_report(metrics, len(train_features), len(test_features))

        manifest_payload = {
            "created_at_kst": now_kst(),
            "status": "completed_threshold_independent_once",
            "contract_sha256": final_contract_hash,
            "final_model_frozen_before_test": True,
            "model_switch_after_test_prohibited": True,
            "model": "lightgbm_trial10",
            "feature_set": APPROVED_FEATURE_SET,
            "feature_count": len(feature_spec.columns),
            "refit_rows": len(train_features),
            "locked_test_rows": len(test_features),
            "approved_metrics": list(APPROVED_METRICS),
            "threshold_search_performed": False,
            "binary_metrics_computed": False,
            "operating_threshold": None,
            "timing_seconds": {
                "transform": transform_seconds,
                "fit": fit_seconds,
                "predict": predict_seconds,
                "total": time.perf_counter() - started,
            },
            "outputs": {
                "metrics": str(METRICS_PATH.relative_to(PROJECT_ROOT)),
                "predictions": str(PREDICTIONS_PATH.relative_to(PROJECT_ROOT)),
                "report": str(REPORT_PATH.relative_to(PROJECT_ROOT)),
                "model": str(MODEL_PATH.relative_to(PROJECT_ROOT)),
                "model_metadata": str(MODEL_METADATA_PATH.relative_to(PROJECT_ROOT)),
                "log": str(LOG_PATH.relative_to(PROJECT_ROOT)),
            },
            "sha256": {
                "metrics": sha256_file(METRICS_PATH),
                "predictions": sha256_file(PREDICTIONS_PATH),
                "report": sha256_file(REPORT_PATH),
                "model": sha256_file(MODEL_PATH),
                "model_metadata": sha256_file(MODEL_METADATA_PATH),
            },
            "verification": {
                "saved_metrics_recomputed": True,
                "saved_model_reloaded": True,
                "prediction_rows_match_locked_features": len(saved) == len(test_features),
                "duplicate_prediction_row_ids": int(saved["stage4_row_id"].duplicated().sum()),
                "probabilities_finite_and_bounded": bool(
                    np.isfinite(saved["risk_probability"]).all()
                    and saved["risk_probability"].between(0, 1).all()
                ),
            },
        }
        atomic_json(MANIFEST_PATH, manifest_payload)
        access.update(
            {
                "status": "completed",
                "completed_at_kst": now_kst(),
                "updated_at_kst": now_kst(),
                "locked_target_opened": True,
                "threshold_metrics_computed": False,
                "metrics_file": str(METRICS_PATH.relative_to(PROJECT_ROOT)),
                "manifest_file": str(MANIFEST_PATH.relative_to(PROJECT_ROOT)),
            }
        )
        atomic_json(ACCESS_PATH, access)
        logger.info("RUN COMPLETE | locked 2025 audit completed once | rerun prohibited")
        print(json.dumps(metric_payload, ensure_ascii=False, indent=2), flush=True)
    except Exception as error:
        access.update(
            {
                "status": "failed",
                "updated_at_kst": now_kst(),
                "error_type": type(error).__name__,
                "error": str(error)[:1000],
            }
        )
        atomic_json(ACCESS_PATH, access)
        logger.exception("RUN FAILED")
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()
    if args.status:
        status()
    elif args.validate_only:
        validate_only()
    else:
        run()


if __name__ == "__main__":
    main()
