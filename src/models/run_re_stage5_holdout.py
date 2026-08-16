"""User-operated one-time RE5 LightGBM Quantile holdout evaluator.

Dry-run and status modes never materialize the 2025Q2 holdout targets. The
irreversible access record is written before 2025Q3-Q4 outcomes are read. Once
opened, only the already-approved LightGBM contract may resume; model reselection
is prohibited.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import joblib
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml
from scipy import sparse
from sklearn.preprocessing import OneHotEncoder

from src.data.build_re_stage5_baseline import build_targets
from src.models.run_re_stage5_quantile import compute_metrics, sha256_file


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "re_stage5.yaml"
PREPARED_MANIFEST_PATH = ROOT / "reports" / "re_stage5" / "manifest.json"
FEATURE_SET_PATH = ROOT / "reports" / "stage5" / "feature_sets.json"
CV_CHECKPOINT_DIR = ROOT / "reports" / "re_stage5" / "cv" / "checkpoints"
CV_METRICS_PATH = ROOT / "reports" / "re_stage5" / "cv" / "fold_metrics.csv"
PREPARATION_LOCK_PATH = ROOT / "reports" / "re_stage5" / "holdout_lock.json"

HOLDOUT_DIR = ROOT / "reports" / "re_stage5" / "holdout"
CHECKPOINT_DIR = HOLDOUT_DIR / "checkpoints"
ACCESS_PATH = HOLDOUT_DIR / "access.json"
PROGRESS_PATH = HOLDOUT_DIR / "progress.json"
LOG_PATH = HOLDOUT_DIR / "evaluation.log"
METRICS_PATH = HOLDOUT_DIR / "holdout_metrics.csv"
INDUSTRY_METRICS_PATH = HOLDOUT_DIR / "holdout_industry_metrics.csv"
PREDICTIONS_PATH = HOLDOUT_DIR / "holdout_predictions.parquet"
REPORT_PATH = HOLDOUT_DIR / "holdout_report.md"
MANIFEST_PATH = HOLDOUT_DIR / "holdout_manifest.json"
ARTIFACT_DIR = ROOT / "artifacts" / "re_stage5_lightgbm_quantile"

ROW_ID = "re5_row_id"
PERIOD = "기준_년분기_코드"
AREA = "상권_코드"
INDUSTRY = "서비스_업종_코드"
SALES = "당월_매출_금액"
TARGETS = [
    "target_a_next_quarter_yoy",
    "target_b_next_two_quarters_yoy",
    "target_aux_min_next_two_quarters_yoy",
]
QUANTILES = (0.1, 0.5, 0.9)
MODEL_NAME = "lightgbm"


def now_kst() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="minutes")


def atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)


def atomic_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_parquet(temporary, index=False, compression="zstd")
    temporary.replace(path)


def atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False, encoding="utf-8-sig")
    temporary.replace(path)


def configure_logging() -> logging.Logger:
    HOLDOUT_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("re5.holdout")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | RE5 HOLDOUT | %(message)s")
    terminal = logging.StreamHandler(sys.stdout)
    terminal.setFormatter(formatter)
    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(terminal)
    logger.addHandler(file_handler)
    return logger


@dataclass
class HoldoutContract:
    config: dict[str, object]
    manifest: dict[str, object]
    features: list[str]
    contract_sha256: str
    cv_contract_sha256: str


@dataclass
class FittedSparsePreprocessor:
    numeric_columns: list[str]
    categorical_columns: list[str]
    numeric_medians: np.ndarray
    numeric_scales: np.ndarray
    encoder: OneHotEncoder | None

    def transform(self, frame: pd.DataFrame) -> sparse.csr_matrix:
        numeric_values = np.empty(
            (len(frame), len(self.numeric_columns)), dtype=np.float32
        )
        for index, column in enumerate(self.numeric_columns):
            values = pd.to_numeric(frame[column], errors="coerce").to_numpy(
                dtype=np.float64, copy=True
            )
            values[~np.isfinite(values)] = np.nan
            values[np.isnan(values)] = self.numeric_medians[index]
            numeric_values[:, index] = (
                values / self.numeric_scales[index]
            ).astype(np.float32)
        parts: list[sparse.spmatrix] = [sparse.csr_matrix(numeric_values)]
        if self.categorical_columns:
            if self.encoder is None:  # pragma: no cover - defensive
                raise RuntimeError("Categorical encoder is missing.")
            categorical = (
                frame[self.categorical_columns]
                .astype("string")
                .fillna("__MISSING__")
            )
            parts.append(self.encoder.transform(categorical))
        return sparse.hstack(parts, format="csr").astype(np.float32)


def fit_sparse_preprocessor(
    train: pd.DataFrame, columns: list[str]
) -> tuple[FittedSparsePreprocessor, sparse.csr_matrix]:
    categorical = [
        column
        for column in columns
        if pd.api.types.is_string_dtype(train[column].dtype)
        or isinstance(train[column].dtype, pd.CategoricalDtype)
        or pd.api.types.is_object_dtype(train[column].dtype)
    ]
    numeric = [column for column in columns if column not in categorical]
    medians = np.empty(len(numeric), dtype=np.float64)
    scales = np.empty(len(numeric), dtype=np.float64)
    numeric_values = np.empty((len(train), len(numeric)), dtype=np.float32)
    for index, column in enumerate(numeric):
        values = pd.to_numeric(train[column], errors="coerce").to_numpy(
            dtype=np.float64, copy=True
        )
        values[~np.isfinite(values)] = np.nan
        finite = values[np.isfinite(values)]
        median = float(np.median(finite)) if finite.size else 0.0
        values[np.isnan(values)] = median
        scale = float(np.std(values))
        if not math.isfinite(scale) or scale == 0:
            scale = 1.0
        medians[index] = median
        scales[index] = scale
        numeric_values[:, index] = (values / scale).astype(np.float32)

    encoder: OneHotEncoder | None = None
    parts: list[sparse.spmatrix] = [sparse.csr_matrix(numeric_values)]
    if categorical:
        encoder = OneHotEncoder(
            handle_unknown="ignore", sparse_output=True, dtype=np.float32
        )
        categorical_values = (
            train[categorical].astype("string").fillna("__MISSING__")
        )
        parts.append(encoder.fit_transform(categorical_values))
    preprocessor = FittedSparsePreprocessor(
        numeric_columns=numeric,
        categorical_columns=categorical,
        numeric_medians=medians,
        numeric_scales=scales,
        encoder=encoder,
    )
    matrix = sparse.hstack(parts, format="csr").astype(np.float32)
    return preprocessor, matrix


def target_valid_column(target: str) -> str:
    if target.startswith("target_a_"):
        return "target_a_valid"
    if target.startswith("target_b_"):
        return "target_b_valid"
    if target.startswith("target_aux_"):
        return "target_aux_valid"
    raise ValueError(f"Unsupported target: {target}")


def target_reason_column(target: str) -> str:
    return target_valid_column(target).replace("_valid", "_reason")


def verify_selected_cv_checkpoints() -> tuple[str, list[dict[str, object]]]:
    checkpoints: list[dict[str, object]] = []
    expected = {
        (target, fold) for target in TARGETS for fold in range(1, 5)
    }
    seen: set[tuple[str, int]] = set()
    contract_hashes: set[str] = set()
    for path in sorted(CV_CHECKPOINT_DIR.glob(f"*__{MODEL_NAME}.json")):
        item = json.loads(path.read_text(encoding="utf-8"))
        key = (str(item.get("target")), int(item.get("fold", -1)))
        if item.get("model") != MODEL_NAME or key not in expected:
            continue
        if item.get("status") != "completed":
            raise RuntimeError(f"Incomplete selected CV checkpoint: {path}")
        prediction_path = ROOT / str(item["prediction_path"])
        if not prediction_path.exists():
            raise RuntimeError(f"Missing selected CV prediction: {prediction_path}")
        if sha256_file(prediction_path) != item.get("prediction_sha256"):
            raise RuntimeError(f"Selected CV prediction hash mismatch: {prediction_path}")
        if key in seen:
            raise RuntimeError(f"Duplicate selected CV checkpoint: {key}")
        seen.add(key)
        contract_hashes.add(str(item["contract_sha256"]))
        checkpoints.append(item)
    if seen != expected:
        raise RuntimeError(
            f"Selected LightGBM CV checkpoints are incomplete: missing={sorted(expected-seen)}"
        )
    if len(contract_hashes) != 1:
        raise RuntimeError("Selected LightGBM CV checkpoints use multiple contracts.")
    return next(iter(contract_hashes)), checkpoints


def holdout_contract_hash(
    config: dict[str, object],
    manifest: dict[str, object],
    features: list[str],
    cv_contract_sha256: str,
) -> str:
    payload = {
        "contract_version": config["contract_version"],
        "selected_model": config["status"]["selected_model"],
        "selected_model_scope": config["status"]["selected_model_scope"],
        "data": config["data"],
        "targets": config["targets"],
        "time_split": config["time_split"],
        "quantiles": config["quantiles"],
        "model_settings": config["models"][MODEL_NAME],
        "random_seed": config["models"]["random_seed"],
        "features": features,
        "prepared_manifest_sha256": sha256_file(PREPARED_MANIFEST_PATH),
        "development_sha256": manifest["outputs"]["development"]["sha256"],
        "holdout_features_sha256": manifest["outputs"]["holdout_features"][
            "sha256"
        ],
        "feature_set_sha256": sha256_file(FEATURE_SET_PATH),
        "cv_metrics_sha256": sha256_file(CV_METRICS_PATH),
        "cv_contract_sha256": cv_contract_sha256,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def load_contract() -> HoldoutContract:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    status = config["status"]
    if config["contract_version"] != "re5-v1":
        raise RuntimeError("Unsupported RE5 contract version.")
    if status.get("selected_model") != MODEL_NAME:
        raise RuntimeError("The approved RE5 holdout model must be lightgbm.")
    if status.get("selected_model_approved") is not True:
        raise RuntimeError("The selected RE5 model is not approved.")
    if status.get("selected_model_scope") != "internal_holdout_candidate":
        raise RuntimeError("Unexpected selected-model scope.")
    if status.get("holdout_execution_authorized") is not True:
        raise RuntimeError("User-operated holdout execution is not authorized.")
    if status.get("stage6_final_status_approved") is not True:
        raise RuntimeError("The frozen Stage 6 service status is unresolved.")

    manifest = json.loads(PREPARED_MANIFEST_PATH.read_text(encoding="utf-8"))
    lock = json.loads(PREPARATION_LOCK_PATH.read_text(encoding="utf-8"))
    if manifest["status"] != "baseline_prepared_training_not_run":
        raise RuntimeError("Unexpected RE5 preparation manifest state.")
    if lock.get("target_opened") is not False:
        raise RuntimeError("Preparation lock already reports an opened target.")

    feature_sets = json.loads(FEATURE_SET_PATH.read_text(encoding="utf-8"))
    feature_id = config["data"]["feature_set"]
    features = feature_sets["feature_sets"][feature_id]["columns"]
    if len(features) != 197:
        raise RuntimeError("Approved common baseline must contain 197 features.")

    development_path = ROOT / config["data"]["development"]
    holdout_path = ROOT / config["data"]["holdout_features"]
    source_path = ROOT / config["data"]["source_panel"]
    if sha256_file(source_path) != manifest["source"]["sha256"]:
        raise RuntimeError("Stage 3 source Panel hash mismatch.")
    if sha256_file(development_path) != manifest["outputs"]["development"]["sha256"]:
        raise RuntimeError("Development data hash mismatch.")
    if sha256_file(holdout_path) != lock["features_sha256"]:
        raise RuntimeError("Holdout feature hash mismatch.")
    if sha256_file(holdout_path) != manifest["outputs"]["holdout_features"]["sha256"]:
        raise RuntimeError("Holdout feature/manifest hash mismatch.")
    development_schema = set(pq.read_schema(development_path).names)
    holdout_schema = set(pq.read_schema(holdout_path).names)
    if not set(features).issubset(development_schema):
        raise RuntimeError("Development data is missing approved features.")
    if not set(features).issubset(holdout_schema):
        raise RuntimeError("Holdout data is missing approved features.")
    if set(TARGETS).intersection(holdout_schema):
        raise RuntimeError("Holdout feature file unexpectedly contains targets.")

    cv_contract_sha256, _ = verify_selected_cv_checkpoints()
    expected_hash = holdout_contract_hash(
        config, manifest, features, cv_contract_sha256
    )
    return HoldoutContract(
        config=config,
        manifest=manifest,
        features=features,
        contract_sha256=expected_hash,
        cv_contract_sha256=cv_contract_sha256,
    )


def access_resume_state(
    access: dict[str, object] | None, expected_hash: str
) -> str:
    if access is None:
        return "new"
    if access.get("contract_sha256") != expected_hash:
        raise RuntimeError("Holdout was opened under a different frozen contract.")
    if access.get("selected_model") != MODEL_NAME:
        raise RuntimeError("Holdout access belongs to a different selected model.")
    if access.get("status") == "completed":
        raise RuntimeError("The one-time holdout evaluation is already completed.")
    if access.get("target_opened") is not True:
        raise RuntimeError("Malformed holdout access record.")
    return "resume_same_model_only"


def dry_run() -> None:
    contract = load_contract()
    access = None
    if ACCESS_PATH.exists():
        access = json.loads(ACCESS_PATH.read_text(encoding="utf-8"))
    if access is not None and access.get("status") == "completed":
        state = "already_completed"
    else:
        state = access_resume_state(access, contract.contract_sha256)
    payload = {
        "status": "ready_for_user_operated_holdout",
        "selected_model": MODEL_NAME,
        "targets": TARGETS,
        "quantiles": QUANTILES,
        "target_tasks": len(TARGETS),
        "lightgbm_estimators": len(TARGETS) * len(QUANTILES),
        "approved_features": len(contract.features),
        "selected_cv_checkpoints_verified": 12,
        "holdout_feature_period": contract.config["time_split"][
            "holdout_feature_period"
        ],
        "holdout_outcome_periods": contract.config["time_split"][
            "holdout_outcome_periods"
        ],
        "holdout_rows": contract.manifest["rows"]["holdout_features"],
        "access_state": state,
        "holdout_target_opened_by_dry_run": False,
        "training_executed_by_dry_run": False,
        "contract_sha256": contract.contract_sha256,
        "required_command": (
            ".\\scripts\\run_re_stage5_holdout.ps1 -ConfirmOpenHoldout"
        ),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def status() -> None:
    payload: dict[str, object] = {
        "status": "not_started",
        "holdout_target_opened": False,
        "selected_model": MODEL_NAME,
    }
    if PROGRESS_PATH.exists():
        payload = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
    if ACCESS_PATH.exists():
        payload["access"] = json.loads(ACCESS_PATH.read_text(encoding="utf-8"))
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def materialize_holdout_targets(contract: HoldoutContract) -> pd.DataFrame:
    source_path = ROOT / contract.config["data"]["source_panel"]
    source = pd.read_parquet(
        source_path, columns=[PERIOD, AREA, INDUSTRY, SALES]
    )
    source.insert(0, ROW_ID, np.arange(1, len(source) + 1, dtype=np.int64))
    targets = build_targets(source)
    target_frame = pd.concat(
        [source[[ROW_ID, PERIOD, AREA, INDUSTRY]], targets], axis=1
    )
    feature_period = int(contract.config["time_split"]["holdout_feature_period"])
    target_frame = target_frame.loc[
        target_frame[PERIOD].astype(int) == feature_period
    ].copy()
    expected_rows = int(contract.manifest["rows"]["holdout_features"])
    if len(target_frame) != expected_rows:
        raise RuntimeError(
            f"Holdout target row mismatch: {len(target_frame)} != {expected_rows}"
        )
    if target_frame[[ROW_ID, PERIOD, AREA, INDUSTRY]].duplicated().any():
        raise RuntimeError("Holdout target keys are not unique.")
    return target_frame


def artifact_path(target: str) -> Path:
    return ARTIFACT_DIR / f"{target}__lightgbm_quantile.joblib"


def checkpoint_paths(target: str) -> tuple[Path, Path]:
    return (
        CHECKPOINT_DIR / f"{target}__lightgbm.json",
        CHECKPOINT_DIR / f"{target}__lightgbm.parquet",
    )


def artifact_predictions(
    artifact: dict[str, object], frame: pd.DataFrame
) -> np.ndarray:
    preprocessor = artifact["preprocessor"]
    matrix = preprocessor.transform(frame)
    models = artifact["models"]
    return np.column_stack(
        [models[f"p{int(q * 100)}"].predict(matrix) for q in QUANTILES]
    )


def fit_target(
    target: str,
    train: pd.DataFrame,
    holdout: pd.DataFrame,
    contract: HoldoutContract,
    logger: logging.Logger,
) -> tuple[pd.DataFrame, dict[str, object], float, Path]:
    import lightgbm as lgb

    started = time.perf_counter()
    logger.info("    Train-only 전처리 시작 | features=%d", len(contract.features))
    preprocessor, train_matrix = fit_sparse_preprocessor(train, contract.features)
    holdout_matrix = preprocessor.transform(holdout)
    logger.info(
        "    Train-only 전처리 완료 | train_matrix=%s holdout_matrix=%s",
        train_matrix.shape,
        holdout_matrix.shape,
    )
    train_y = train[target].to_numpy(dtype=np.float64, copy=True)
    models: dict[str, object] = {}
    predictions: list[np.ndarray] = []
    seed = int(contract.config["models"]["random_seed"]) + 10_000
    threads = max(
        1,
        min(
            int(contract.config["models"]["max_threads"]),
            max(1, (os.cpu_count() or 2) - 1),
        ),
    )
    for index, quantile in enumerate(QUANTILES, start=1):
        logger.info(
            "    [%d/3] LightGBM quantile %.1f 학습 시작", index, quantile
        )
        model = lgb.LGBMRegressor(
            objective="quantile",
            alpha=quantile,
            random_state=seed + index - 1,
            n_jobs=threads,
            verbosity=-1,
            **contract.config["models"][MODEL_NAME],
        )
        model.fit(
            train_matrix,
            train_y,
            eval_set=[(train_matrix, train_y)],
            eval_names=["train_only"],
            eval_metric="quantile",
            callbacks=[lgb.log_evaluation(period=50)],
        )
        prediction = np.asarray(model.predict(holdout_matrix), dtype=np.float64)
        if not np.isfinite(prediction).all():
            raise RuntimeError(f"Non-finite prediction: {target}, q={quantile}")
        models[f"p{int(quantile * 100)}"] = model
        predictions.append(prediction)
        logger.info("    [%d/3] LightGBM quantile %.1f 완료", index, quantile)

    raw_prediction = np.column_stack(predictions)
    corrected = np.sort(raw_prediction, axis=1)
    valid = holdout[target].notna().to_numpy()
    if not valid.any():
        raise RuntimeError(f"No valid holdout target rows: {target}")
    actual = holdout.loc[valid, target].to_numpy(dtype=np.float64, copy=True)
    metrics, _ = compute_metrics(actual, raw_prediction[valid])

    artifact = {
        "artifact_version": "re5-lightgbm-quantile-v1",
        "created_at_kst": now_kst(),
        "contract_sha256": contract.contract_sha256,
        "selected_model": MODEL_NAME,
        "target": target,
        "quantiles": QUANTILES,
        "feature_columns": contract.features,
        "train_rows": len(train),
        "holdout_rows": len(holdout),
        "preprocessor": preprocessor,
        "models": models,
        "service_boundary": contract.config["service_boundary"],
    }
    model_path = artifact_path(target)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = model_path.with_suffix(model_path.suffix + ".tmp")
    joblib.dump(artifact, temporary, compress=3)
    temporary.replace(model_path)
    reloaded = joblib.load(model_path)
    reloaded_prediction = artifact_predictions(reloaded, holdout)
    if not np.allclose(raw_prediction, reloaded_prediction, atol=1e-7, rtol=0):
        raise RuntimeError(f"Reloaded model prediction mismatch: {target}")

    result = pd.DataFrame(
        {
            ROW_ID: holdout[ROW_ID].to_numpy(dtype=np.int64),
            PERIOD: holdout[PERIOD].to_numpy(dtype=np.int32),
            AREA: holdout[AREA].astype("string").to_numpy(),
            INDUSTRY: holdout[INDUSTRY].astype("string").to_numpy(),
            "target": target,
            "target_valid": valid,
            "target_reason": holdout[target_reason_column(target)]
            .astype("string")
            .to_numpy(),
            "actual": holdout[target].to_numpy(dtype=np.float64, copy=True),
            "raw_p10": raw_prediction[:, 0],
            "raw_p50": raw_prediction[:, 1],
            "raw_p90": raw_prediction[:, 2],
            "p10": corrected[:, 0],
            "p50": corrected[:, 1],
            "p90": corrected[:, 2],
        }
    )
    elapsed = time.perf_counter() - started
    return result, metrics, elapsed, model_path


def industry_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    valid = predictions.loc[predictions["target_valid"]].copy()
    for (target, industry), group in valid.groupby(
        ["target", INDUSTRY], observed=True
    ):
        metrics, _ = compute_metrics(
            group["actual"].to_numpy(dtype=np.float64),
            group[["p10", "p50", "p90"]].to_numpy(dtype=np.float64),
        )
        rows.append(
            {
                "target": target,
                INDUSTRY: industry,
                "rows": len(group),
                **metrics,
            }
        )
    return pd.DataFrame(rows)


def write_report(metrics: pd.DataFrame) -> None:
    lines = [
        "# RE5 LightGBM Quantile 내부 Holdout 평가",
        "",
        "- 기준 Feature 분기: 2025Q2",
        "- 결과 분기: Target A=2025Q3, Target B·보조=2025Q3~Q4",
        "- 이 평가는 새 독립 감사가 아닌 사전 승인된 내부 시간 Holdout이다.",
        "- 결과를 본 뒤 모델을 재선택하지 않는다.",
        "- 기존 Stage 5·6 이진모델은 재학습·서비스 사용하지 않는다.",
        "",
        "## Target별 결과",
        "",
        "| Target | 유효행 | MAE | Median AE | Coverage | 구간 폭 | Interval Score | Spearman | 방향 일치율 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in metrics.to_dict(orient="records"):
        lines.append(
            "| `{target}` | {valid_rows:,} | {mae:.6f} | "
            "{median_absolute_error:.6f} | {coverage_p10_p90:.4f} | "
            "{mean_interval_width:.6f} | {interval_score_80:.6f} | "
            "{spearman:.4f} | {direction_accuracy:.4f} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## 상태 경계",
            "",
            "이 결과는 RE5 LightGBM의 고정된 1회 내부 Holdout이다. "
            "2026Q1·Q2 결과를 사용하는 새 독립 감사가 확보되기 전에는 "
            "독립검증 완료라고 표현하지 않는다.",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_holdout(confirm_model: str, confirm_open: bool) -> None:
    if confirm_model != MODEL_NAME or not confirm_open:
        raise RuntimeError(
            "Explicit confirmation is required: selected model=lightgbm and open holdout."
        )
    logger = configure_logging()
    contract = load_contract()
    existing_access = None
    if ACCESS_PATH.exists():
        existing_access = json.loads(ACCESS_PATH.read_text(encoding="utf-8"))
    resume_state = access_resume_state(existing_access, contract.contract_sha256)

    if resume_state == "new":
        access = {
            "status": "opened_same_model_resume_only",
            "opened_at_kst": now_kst(),
            "updated_at_kst": now_kst(),
            "target_opened": True,
            "selected_model": MODEL_NAME,
            "contract_sha256": contract.contract_sha256,
            "feature_period": contract.config["time_split"][
                "holdout_feature_period"
            ],
            "outcome_periods": contract.config["time_split"][
                "holdout_outcome_periods"
            ],
            "model_reselection_prohibited": True,
            "stage6_reactivation_prohibited": True,
        }
        atomic_json(ACCESS_PATH, access)
        logger.info(
            "HOLDOUT TARGET OPENED | model=lightgbm | 이후 동일 계약 재개만 허용"
        )
    else:
        access = existing_access
        logger.info("동일 LightGBM 계약 Holdout 평가 재개")

    try:
        logger.info("개발자료·Holdout Feature 읽기")
        development = pd.read_parquet(
            ROOT / contract.config["data"]["development"]
        )
        holdout_features = pd.read_parquet(
            ROOT / contract.config["data"]["holdout_features"]
        )
        logger.info("2025Q3·Q4 결과로 Holdout Target v2 계산")
        target_frame = materialize_holdout_targets(contract)
        target_columns = [
            ROW_ID,
            PERIOD,
            AREA,
            INDUSTRY,
            *TARGETS,
            "target_a_valid",
            "target_a_reason",
            "target_b_valid",
            "target_b_reason",
            "target_aux_valid",
            "target_aux_reason",
        ]
        holdout = holdout_features.merge(
            target_frame[target_columns],
            on=[ROW_ID, PERIOD, AREA, INDUSTRY],
            how="left",
            validate="one_to_one",
        )
        if len(holdout) != len(holdout_features):
            raise RuntimeError("Holdout feature/target merge changed row count.")

        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        metric_rows: list[dict[str, object]] = []
        prediction_frames: list[pd.DataFrame] = []
        completed = 0
        for task_index, target in enumerate(TARGETS, start=1):
            checkpoint_path, prediction_path = checkpoint_paths(target)
            if checkpoint_path.exists():
                checkpoint = json.loads(
                    checkpoint_path.read_text(encoding="utf-8")
                )
                model_path = ROOT / checkpoint["artifact_path"]
                if (
                    checkpoint.get("status") != "completed"
                    or checkpoint.get("contract_sha256")
                    != contract.contract_sha256
                    or not prediction_path.exists()
                    or not model_path.exists()
                    or sha256_file(prediction_path)
                    != checkpoint.get("prediction_sha256")
                    or sha256_file(model_path) != checkpoint.get("artifact_sha256")
                ):
                    raise RuntimeError(
                        f"Invalid holdout checkpoint: {checkpoint_path}"
                    )
                logger.info(
                    "[%d/3] SKIP 완료 checkpoint | target=%s",
                    task_index,
                    target,
                )
                metric_rows.append(
                    {
                        "target": target,
                        "train_rows": checkpoint["train_rows"],
                        "holdout_rows": checkpoint["holdout_rows"],
                        "valid_rows": checkpoint["valid_rows"],
                        "fit_seconds": checkpoint["fit_seconds"],
                        **checkpoint["metrics"],
                    }
                )
                prediction_frames.append(pd.read_parquet(prediction_path))
                completed += 1
                continue

            train = development.loc[development[target].notna()].copy()
            if train.empty:
                raise RuntimeError(f"No development rows for target: {target}")
            logger.info(
                "[%d/3] START | target=%s train=%d holdout=%d",
                task_index,
                target,
                len(train),
                len(holdout),
            )
            atomic_json(
                PROGRESS_PATH,
                {
                    "status": "running_same_model_only",
                    "updated_at_kst": now_kst(),
                    "selected_model": MODEL_NAME,
                    "contract_sha256": contract.contract_sha256,
                    "completed_targets": completed,
                    "total_targets": len(TARGETS),
                    "percent_complete": round(100 * completed / len(TARGETS), 2),
                    "current_target": target,
                    "holdout_target_opened": True,
                    "model_reselection_prohibited": True,
                },
            )
            predictions, metrics, elapsed, model_path = fit_target(
                target, train, holdout, contract, logger
            )
            atomic_parquet(predictions, prediction_path)
            checkpoint = {
                "status": "completed",
                "completed_at_kst": now_kst(),
                "contract_sha256": contract.contract_sha256,
                "selected_model": MODEL_NAME,
                "target": target,
                "train_rows": len(train),
                "holdout_rows": len(holdout),
                "valid_rows": int(predictions["target_valid"].sum()),
                "fit_seconds": elapsed,
                "metrics": metrics,
                "prediction_path": str(prediction_path.relative_to(ROOT)),
                "prediction_sha256": sha256_file(prediction_path),
                "artifact_path": str(model_path.relative_to(ROOT)),
                "artifact_sha256": sha256_file(model_path),
                "holdout_target_opened": True,
                "model_reselection_prohibited": True,
            }
            atomic_json(checkpoint_path, checkpoint)
            metric_rows.append(
                {
                    "target": target,
                    "train_rows": len(train),
                    "holdout_rows": len(holdout),
                    "valid_rows": checkpoint["valid_rows"],
                    "fit_seconds": elapsed,
                    **metrics,
                }
            )
            prediction_frames.append(predictions)
            completed += 1
            logger.info(
                "[%d/3] DONE | target=%s MAE=%.6f Coverage=%.4f elapsed=%.1fs",
                task_index,
                target,
                metrics["mae"],
                metrics["coverage_p10_p90"],
                elapsed,
            )

        metrics_frame = pd.DataFrame(metric_rows).sort_values("target")
        predictions_frame = pd.concat(prediction_frames, ignore_index=True)
        industries = industry_metrics(predictions_frame)
        atomic_csv(metrics_frame, METRICS_PATH)
        atomic_csv(industries, INDUSTRY_METRICS_PATH)
        atomic_parquet(predictions_frame, PREDICTIONS_PATH)
        write_report(metrics_frame)

        artifacts = sorted(ARTIFACT_DIR.glob("*.joblib"))
        outputs = [
            METRICS_PATH,
            INDUSTRY_METRICS_PATH,
            PREDICTIONS_PATH,
            REPORT_PATH,
            *artifacts,
        ]
        manifest = {
            "status": "holdout_completed_model_frozen",
            "completed_at_kst": now_kst(),
            "contract_sha256": contract.contract_sha256,
            "cv_contract_sha256": contract.cv_contract_sha256,
            "selected_model": MODEL_NAME,
            "targets": TARGETS,
            "quantiles": QUANTILES,
            "feature_period": contract.config["time_split"][
                "holdout_feature_period"
            ],
            "outcome_periods": contract.config["time_split"][
                "holdout_outcome_periods"
            ],
            "holdout_rows": len(holdout),
            "independent_audit": False,
            "model_reselection_prohibited": True,
            "stage6_service_status": "archived_evidence_only",
            "outputs": {
                str(path.relative_to(ROOT)): {
                    "sha256": sha256_file(path),
                    "bytes": path.stat().st_size,
                }
                for path in outputs
            },
        }
        atomic_json(MANIFEST_PATH, manifest)
        access.update(
            {
                "status": "completed",
                "updated_at_kst": now_kst(),
                "completed_at_kst": now_kst(),
                "target_opened": True,
                "manifest_path": str(MANIFEST_PATH.relative_to(ROOT)),
                "manifest_sha256": sha256_file(MANIFEST_PATH),
            }
        )
        atomic_json(ACCESS_PATH, access)
        atomic_json(
            PROGRESS_PATH,
            {
                "status": "holdout_completed_model_frozen",
                "completed_at_kst": now_kst(),
                "updated_at_kst": now_kst(),
                "selected_model": MODEL_NAME,
                "contract_sha256": contract.contract_sha256,
                "completed_targets": len(TARGETS),
                "total_targets": len(TARGETS),
                "percent_complete": 100.0,
                "holdout_target_opened": True,
                "model_reselection_prohibited": True,
                "report": str(REPORT_PATH.relative_to(ROOT)),
                "manifest": str(MANIFEST_PATH.relative_to(ROOT)),
            },
        )
        logger.info(
            "HOLDOUT 완료 | targets=3/3 | model=lightgbm 고정 | 모델 재선택 금지"
        )
    except Exception as error:
        failed = {
            "status": "failed_same_model_resume_only",
            "failed_at_kst": now_kst(),
            "updated_at_kst": now_kst(),
            "selected_model": MODEL_NAME,
            "contract_sha256": contract.contract_sha256,
            "error_type": type(error).__name__,
            "error": str(error)[:2000],
            "holdout_target_opened": True,
            "model_reselection_prohibited": True,
            "resume_command": (
                ".\\scripts\\run_re_stage5_holdout.ps1 -ConfirmOpenHoldout"
            ),
        }
        atomic_json(PROGRESS_PATH, failed)
        access.update(
            {
                "status": "failed_same_model_resume_only",
                "updated_at_kst": now_kst(),
                "last_error_type": type(error).__name__,
                "target_opened": True,
            }
        )
        atomic_json(ACCESS_PATH, access)
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--confirm-selected-model")
    parser.add_argument("--confirm-open-holdout", action="store_true")
    args = parser.parse_args()
    selected = sum([args.dry_run, args.status, args.run])
    if selected != 1:
        parser.error("Choose exactly one of --dry-run, --status, or --run.")
    if args.dry_run:
        dry_run()
    elif args.status:
        status()
    else:
        run_holdout(args.confirm_selected_model, args.confirm_open_holdout)


if __name__ == "__main__":
    main()
