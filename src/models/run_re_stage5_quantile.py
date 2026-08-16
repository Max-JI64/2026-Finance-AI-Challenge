"""User-operated RE5 chronological quantile CV runner.

Codex prepares and validates this runner but does not execute model fitting.  It
prints durable progress to both the terminal and a log file, and resumes from
completed prediction/metric checkpoints.
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
from typing import Callable
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml
from scipy import sparse
from scipy.stats import spearmanr
from sklearn.preprocessing import OneHotEncoder


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "re_stage5.yaml"
REPORT_DIR = ROOT / "reports" / "re_stage5"
CV_DIR = REPORT_DIR / "cv"
CHECKPOINT_DIR = CV_DIR / "checkpoints"
PROGRESS_PATH = CV_DIR / "progress.json"
LOG_PATH = CV_DIR / "training.log"
SUMMARY_PATH = CV_DIR / "model_summary.csv"
FOLD_METRICS_PATH = CV_DIR / "fold_metrics.csv"
INDUSTRY_METRICS_PATH = CV_DIR / "industry_metrics.csv"
REPORT_PATH = CV_DIR / "comparison.md"
MANIFEST_PATH = REPORT_DIR / "manifest.json"
FEATURE_SET_PATH = ROOT / "reports" / "stage5" / "feature_sets.json"
HOLDOUT_ACCESS_PATH = REPORT_DIR / "holdout" / "access.json"

ROW_ID = "re5_row_id"
PERIOD = "기준_년분기_코드"
INDUSTRY = "서비스_업종_코드"
TARGETS = [
    "target_a_next_quarter_yoy",
    "target_b_next_two_quarters_yoy",
    "target_aux_min_next_two_quarters_yoy",
]
QUANTILES = (0.1, 0.5, 0.9)


def now_kst() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="minutes")


def atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def configure_logging() -> logging.Logger:
    CV_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("re5.training")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | RE5 TRAIN | %(message)s")
    terminal = logging.StreamHandler(sys.stdout)
    terminal.setFormatter(formatter)
    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(terminal)
    logger.addHandler(file_handler)
    return logger


def load_contract() -> tuple[dict[str, object], dict[str, object], list[str]]:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    if config["contract_version"] != "re5-v1":
        raise RuntimeError("Unsupported RE5 contract version.")
    if not MANIFEST_PATH.exists():
        raise RuntimeError("Run RE5 baseline preparation before training.")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest["status"] != "baseline_prepared_training_not_run":
        raise RuntimeError("RE5 preparation manifest is not in the expected state.")
    if manifest["period"]["holdout_target_opened"]:
        raise RuntimeError("CV must not run after opening the internal holdout Target.")
    if HOLDOUT_ACCESS_PATH.exists():
        access = json.loads(HOLDOUT_ACCESS_PATH.read_text(encoding="utf-8"))
        if access.get("target_opened") is True:
            raise RuntimeError("CV cannot run after the internal holdout Target opened.")
    feature_sets = json.loads(FEATURE_SET_PATH.read_text(encoding="utf-8"))
    feature_id = config["data"]["feature_set"]
    columns = feature_sets["feature_sets"][feature_id]["columns"]
    if len(columns) != 197:
        raise RuntimeError("Approved common baseline must contain exactly 197 features.")
    return config, manifest, columns


@dataclass
class PreparedMatrix:
    train: sparse.csr_matrix
    validation: sparse.csr_matrix
    numeric_columns: list[str]
    categorical_columns: list[str]


def prepare_matrix(
    train: pd.DataFrame, validation: pd.DataFrame, columns: list[str]
) -> PreparedMatrix:
    categorical = [
        column
        for column in columns
        if pd.api.types.is_string_dtype(train[column].dtype)
        or isinstance(train[column].dtype, pd.CategoricalDtype)
        or pd.api.types.is_object_dtype(train[column].dtype)
    ]
    numeric = [column for column in columns if column not in categorical]
    train_numeric = np.empty((len(train), len(numeric)), dtype=np.float32)
    validation_numeric = np.empty((len(validation), len(numeric)), dtype=np.float32)
    for index, column in enumerate(numeric):
        train_values = pd.to_numeric(train[column], errors="coerce").to_numpy(
            dtype=np.float64, copy=True
        )
        validation_values = pd.to_numeric(
            validation[column], errors="coerce"
        ).to_numpy(dtype=np.float64, copy=True)
        train_values[~np.isfinite(train_values)] = np.nan
        validation_values[~np.isfinite(validation_values)] = np.nan
        finite = train_values[np.isfinite(train_values)]
        median = float(np.median(finite)) if finite.size else 0.0
        train_values[np.isnan(train_values)] = median
        validation_values[np.isnan(validation_values)] = median
        scale = float(np.std(train_values))
        if not math.isfinite(scale) or scale == 0:
            scale = 1.0
        train_numeric[:, index] = (train_values / scale).astype(np.float32)
        validation_numeric[:, index] = (validation_values / scale).astype(np.float32)
    train_parts: list[sparse.spmatrix] = [sparse.csr_matrix(train_numeric)]
    validation_parts: list[sparse.spmatrix] = [
        sparse.csr_matrix(validation_numeric)
    ]
    if categorical:
        encoder = OneHotEncoder(
            handle_unknown="ignore", sparse_output=True, dtype=np.float32
        )
        train_cat = train[categorical].astype("string").fillna("__MISSING__")
        validation_cat = (
            validation[categorical].astype("string").fillna("__MISSING__")
        )
        train_parts.append(encoder.fit_transform(train_cat))
        validation_parts.append(encoder.transform(validation_cat))
    return PreparedMatrix(
        train=sparse.hstack(train_parts, format="csr").astype(np.float32),
        validation=sparse.hstack(validation_parts, format="csr").astype(np.float32),
        numeric_columns=numeric,
        categorical_columns=categorical,
    )


def fit_linear_quantile(
    x: sparse.csr_matrix,
    y: np.ndarray,
    q: float,
    settings: dict[str, object],
    seed: int,
    log: Callable[[str], None],
) -> tuple[np.ndarray, float]:
    epochs = int(settings["epochs"])
    batch_size = int(settings["batch_size"])
    base_rate = float(settings["learning_rate"])
    l2 = float(settings["l2"])
    rng = np.random.default_rng(seed)
    weights = np.zeros(x.shape[1], dtype=np.float64)
    intercept = float(np.quantile(y, q))
    for epoch in range(1, epochs + 1):
        order = rng.permutation(len(y))
        rate = base_rate / math.sqrt(epoch)
        for start in range(0, len(y), batch_size):
            indices = order[start : start + batch_size]
            xb = x[indices]
            residual = y[indices] - (xb @ weights + intercept)
            derivative = np.where(residual >= 0, -q, 1.0 - q)
            gradient = np.asarray(xb.T @ derivative).ravel() / len(indices)
            gradient += l2 * weights
            gradient_norm = float(np.linalg.norm(gradient))
            if gradient_norm > 10.0:
                gradient *= 10.0 / gradient_norm
            weights -= rate * gradient
            intercept -= rate * float(derivative.mean())
        log(f"linear q={q:.1f} epoch={epoch}/{epochs}")
    return weights, intercept


def predict_regularized_linear(
    matrix: PreparedMatrix,
    train_y: np.ndarray,
    settings: dict[str, object],
    seed: int,
    logger: logging.Logger,
) -> np.ndarray:
    predictions: list[np.ndarray] = []
    for offset, quantile in enumerate(QUANTILES):
        logger.info("    regularized_linear quantile %.1f 시작", quantile)
        weights, intercept = fit_linear_quantile(
            matrix.train,
            train_y,
            quantile,
            settings,
            seed + offset,
            logger.info,
        )
        predictions.append(
            np.asarray(matrix.validation @ weights + intercept, dtype=np.float64)
        )
    return np.column_stack(predictions)


def predict_lightgbm(
    matrix: PreparedMatrix,
    train_y: np.ndarray,
    validation_y: np.ndarray,
    settings: dict[str, object],
    seed: int,
    threads: int,
    logger: logging.Logger,
) -> np.ndarray:
    import lightgbm as lgb

    predictions: list[np.ndarray] = []
    for offset, quantile in enumerate(QUANTILES):
        logger.info("    lightgbm quantile %.1f 시작", quantile)
        model = lgb.LGBMRegressor(
            objective="quantile",
            alpha=quantile,
            random_state=seed + offset,
            n_jobs=threads,
            verbosity=-1,
            **settings,
        )
        model.fit(
            matrix.train,
            train_y,
            eval_set=[(matrix.validation, validation_y)],
            eval_metric="quantile",
            callbacks=[lgb.log_evaluation(period=50)],
        )
        predictions.append(model.predict(matrix.validation))
    return np.column_stack(predictions)


def predict_xgboost(
    matrix: PreparedMatrix,
    train_y: np.ndarray,
    validation_y: np.ndarray,
    settings: dict[str, object],
    seed: int,
    threads: int,
    logger: logging.Logger,
) -> np.ndarray:
    from xgboost import XGBRegressor

    predictions: list[np.ndarray] = []
    for offset, quantile in enumerate(QUANTILES):
        logger.info("    xgboost quantile %.1f 시작", quantile)
        model = XGBRegressor(
            objective="reg:quantileerror",
            quantile_alpha=quantile,
            random_state=seed + offset,
            n_jobs=threads,
            tree_method="hist",
            **settings,
        )
        model.fit(
            matrix.train,
            train_y,
            eval_set=[(matrix.validation, validation_y)],
            verbose=50,
        )
        predictions.append(model.predict(matrix.validation))
    return np.column_stack(predictions)


def predict_catboost(
    matrix: PreparedMatrix,
    train_y: np.ndarray,
    validation_y: np.ndarray,
    settings: dict[str, object],
    seed: int,
    threads: int,
    logger: logging.Logger,
) -> np.ndarray:
    from catboost import CatBoostRegressor

    logger.info("    catboost MultiQuantile 0.1,0.5,0.9 시작")
    model = CatBoostRegressor(
        loss_function="MultiQuantile:alpha=0.1,0.5,0.9",
        random_seed=seed,
        thread_count=threads,
        allow_writing_files=False,
        **settings,
    )
    model.fit(
        matrix.train,
        train_y,
        eval_set=(matrix.validation, validation_y),
        verbose=50,
    )
    prediction = np.asarray(model.predict(matrix.validation), dtype=np.float64)
    if prediction.ndim == 1:
        raise RuntimeError("CatBoost MultiQuantile did not return three columns.")
    return prediction


def predict_seasonal(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    train_y: np.ndarray,
) -> np.ndarray:
    feature = "전년동기_매출_증감률"
    train_base = pd.to_numeric(train[feature], errors="coerce").to_numpy(
        dtype=np.float64, copy=True
    )
    validation_base = pd.to_numeric(
        validation[feature], errors="coerce"
    ).to_numpy(dtype=np.float64, copy=True)
    median = float(np.nanmedian(train_base)) if np.isfinite(train_base).any() else 0.0
    train_base[~np.isfinite(train_base)] = median
    validation_base[~np.isfinite(validation_base)] = median
    residual = train_y - train_base
    return np.column_stack(
        [validation_base + np.quantile(residual, q) for q in QUANTILES]
    )


def predict_industry_median(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    train_y: np.ndarray,
) -> np.ndarray:
    work = pd.DataFrame({INDUSTRY: train[INDUSTRY].astype("string"), "y": train_y})
    result = np.empty((len(validation), 3), dtype=np.float64)
    validation_industry = validation[INDUSTRY].astype("string")
    for column_index, quantile in enumerate(QUANTILES):
        mapping = work.groupby(INDUSTRY, observed=True)["y"].quantile(quantile)
        fallback = float(np.quantile(train_y, quantile))
        result[:, column_index] = (
            validation_industry.map(mapping).fillna(fallback).to_numpy(float)
        )
    return result


def pinball(y: np.ndarray, prediction: np.ndarray, q: float) -> float:
    error = y - prediction
    return float(np.mean(np.maximum(q * error, (q - 1.0) * error)))


def compute_metrics(
    y: np.ndarray, raw_prediction: np.ndarray
) -> tuple[dict[str, float], np.ndarray]:
    if raw_prediction.shape != (len(y), 3):
        raise ValueError("Prediction must have shape (rows, 3).")
    if not np.isfinite(raw_prediction).all():
        raise ValueError("Prediction contains NaN or infinity.")
    crossing = (raw_prediction[:, 0] > raw_prediction[:, 1]) | (
        raw_prediction[:, 1] > raw_prediction[:, 2]
    )
    corrected = np.sort(raw_prediction, axis=1)
    p10, p50, p90 = corrected.T
    error = p50 - y
    correlation = spearmanr(y, p50).statistic
    if not np.isfinite(correlation):
        correlation = 0.0
    alpha = 0.2
    interval_score = (
        p90
        - p10
        + (2 / alpha) * np.maximum(p10 - y, 0)
        + (2 / alpha) * np.maximum(y - p90, 0)
    )
    metrics = {
        "mae": float(np.mean(np.abs(error))),
        "median_absolute_error": float(np.median(np.abs(error))),
        "rmse": float(np.sqrt(np.mean(np.square(error)))),
        "mean_error": float(np.mean(error)),
        "pinball_p10": pinball(y, p10, 0.1),
        "pinball_p50": pinball(y, p50, 0.5),
        "pinball_p90": pinball(y, p90, 0.9),
        "attainment_p10": float(np.mean(y <= p10)),
        "attainment_p50": float(np.mean(y <= p50)),
        "attainment_p90": float(np.mean(y <= p90)),
        "coverage_p10_p90": float(np.mean((y >= p10) & (y <= p90))),
        "mean_interval_width": float(np.mean(p90 - p10)),
        "interval_score_80": float(np.mean(interval_score)),
        "spearman": float(correlation),
        "direction_accuracy": float(np.mean(np.sign(y) == np.sign(p50))),
        "crossing_ratio_raw": float(np.mean(crossing)),
        "crossing_ratio_corrected": 0.0,
    }
    return metrics, corrected


def task_paths(target: str, fold: int, model: str) -> tuple[Path, Path]:
    stem = f"{target}__fold{fold}__{model}"
    return CHECKPOINT_DIR / f"{stem}.json", CHECKPOINT_DIR / f"{stem}.parquet"


def contract_hash(config: dict[str, object], manifest: dict[str, object]) -> str:
    payload = {
        "config": config,
        "prepared_manifest_sha256": sha256_file(MANIFEST_PATH),
        "development_sha256": manifest["outputs"]["development"]["sha256"],
        "fold_sha256": manifest["outputs"]["fold_membership"]["sha256"],
        "feature_set_sha256": sha256_file(FEATURE_SET_PATH),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def planned_tasks(config: dict[str, object]) -> list[tuple[str, int, str]]:
    return [
        (target, fold, model)
        for target in TARGETS
        for fold in range(1, len(config["time_split"]["validation_periods"]) + 1)
        for model in config["models"]["candidates"]
    ]


def dry_run() -> None:
    config, manifest, columns = load_contract()
    tasks = planned_tasks(config)
    development_path = ROOT / config["data"]["development"]
    development_columns = set(pq.read_schema(development_path).names)
    missing_features = sorted(set(columns).difference(development_columns))
    if missing_features:
        raise RuntimeError(
            "RE5 preparation is stale or incomplete. Run "
            ".\\scripts\\prepare_re_stage5.ps1 again. "
            f"Missing approved features: {missing_features}"
        )
    packages: dict[str, str] = {}
    for module in ["lightgbm", "catboost", "xgboost"]:
        try:
            imported = __import__(module)
            packages[module] = getattr(imported, "__version__", "unknown")
        except Exception as error:  # pragma: no cover - environment dependent
            packages[module] = f"unavailable: {type(error).__name__}: {error}"
    payload = {
        "status": "ready_user_execution_required",
        "training_executed": False,
        "tasks": len(tasks),
        "targets": TARGETS,
        "folds": config["time_split"]["validation_periods"],
        "models": config["models"]["candidates"],
        "features": len(columns),
        "approved_features_present": True,
        "development_rows": manifest["rows"]["development"],
        "holdout_target_opened": False,
        "packages": packages,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def status() -> None:
    if not PROGRESS_PATH.exists():
        print(
            json.dumps(
                {"status": "not_started", "holdout_target_opened": False},
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    print(PROGRESS_PATH.read_text(encoding="utf-8"))


def collect_results(expected_hash: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    metric_rows: list[dict[str, object]] = []
    industry_frames: list[pd.DataFrame] = []
    for path in sorted(CHECKPOINT_DIR.glob("*.json")):
        item = json.loads(path.read_text(encoding="utf-8"))
        if item.get("status") != "completed" or item.get("contract_sha256") != expected_hash:
            continue
        metric_rows.append(
            {
                "target": item["target"],
                "fold": item["fold"],
                "validation_period": item["validation_period"],
                "model": item["model"],
                "validation_rows": item["validation_rows"],
                "fit_seconds": item["fit_seconds"],
                **item["metrics"],
            }
        )
        prediction_path = ROOT / item["prediction_path"]
        predictions = pd.read_parquet(prediction_path)
        for industry, group in predictions.groupby(INDUSTRY, observed=True):
            metrics, _ = compute_metrics(
                group["actual"].to_numpy(float),
                group[["p10", "p50", "p90"]].to_numpy(float),
            )
            industry_frames.append(
                pd.DataFrame(
                    [
                        {
                            "target": item["target"],
                            "fold": item["fold"],
                            "model": item["model"],
                            INDUSTRY: industry,
                            "rows": len(group),
                            **metrics,
                        }
                    ]
                )
            )
    return pd.DataFrame(metric_rows), pd.concat(industry_frames, ignore_index=True)


def write_summary(metrics: pd.DataFrame, industry: pd.DataFrame) -> None:
    metrics.to_csv(FOLD_METRICS_PATH, index=False, encoding="utf-8-sig")
    industry.to_csv(INDUSTRY_METRICS_PATH, index=False, encoding="utf-8-sig")
    metric_columns = [
        "mae",
        "median_absolute_error",
        "rmse",
        "mean_error",
        "pinball_p10",
        "pinball_p50",
        "pinball_p90",
        "attainment_p10",
        "attainment_p50",
        "attainment_p90",
        "coverage_p10_p90",
        "mean_interval_width",
        "interval_score_80",
        "spearman",
        "direction_accuracy",
        "crossing_ratio_raw",
        "crossing_ratio_corrected",
        "fit_seconds",
    ]
    summary = metrics.groupby(["target", "model"], observed=True)[metric_columns].agg(
        ["mean", "std", "max"]
    )
    summary.columns = [f"{metric}_{stat}" for metric, stat in summary.columns]
    summary = summary.reset_index()
    summary.to_csv(SUMMARY_PATH, index=False, encoding="utf-8-sig")

    lines = [
        "# RE5 Quantile 후보 모델 시간순 CV 비교",
        "",
        "- 이 결과는 2024Q1~Q4 expanding-window 개발검증이다.",
        "- 2025Q2 내부 홀드아웃 Target은 아직 열지 않았다.",
        "- 새 독립 감사기간이 없으므로 어떤 후보도 운영 기본모델로 자동 승격하지 않는다.",
        "- 최종 후보 선택은 평균뿐 아니라 최악 Fold·업종별 붕괴·Coverage·구간 폭을 함께 검토해야 한다.",
        "",
        "## Target별 평균 핵심 지표",
        "",
        "| Target | 모델 | MAE | P50 Pinball | P10~P90 Coverage | 구간 폭 | 최악 Fold MAE |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in summary.sort_values(["target", "mae_mean"]).iterrows():
        lines.append(
            f"| `{row['target']}` | `{row['model']}` | {row['mae_mean']:.4f} "
            f"| {row['pinball_p50_mean']:.4f} | {row['coverage_p10_p90_mean']:.4f} "
            f"| {row['mean_interval_width_mean']:.4f} | {row['mae_max']:.4f} |"
        )
    lines += [
        "",
        "## 아직 하지 않은 결정",
        "",
        "- 모델 최종 선택·Stage 6 교체 여부는 자동 결정하지 않았다.",
        "- 2025Q2 내부 홀드아웃은 사용자 모델 승인 뒤 별도 실행한다.",
        "- 2026Q1·Q2 결과를 쓰는 새 독립 감사는 자료 미확보 상태다.",
        "- 개인 현금흐름 적용률·분기 변화율의 월별 배분은 RE7 승인 전 적용하지 않는다.",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def run_cv(max_new_tasks: int | None = None) -> None:
    logger = configure_logging()
    config, manifest, feature_columns = load_contract()
    expected_hash = contract_hash(config, manifest)
    tasks = planned_tasks(config)
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    development_path = ROOT / config["data"]["development"]
    fold_path = ROOT / config["data"]["fold_membership"]
    logger.info("개발자료 읽기 | %s", development_path)
    development = pd.read_parquet(development_path)
    folds = pd.read_parquet(fold_path)
    missing_features = sorted(set(feature_columns).difference(development.columns))
    if missing_features:
        raise RuntimeError(f"Missing approved features: {missing_features}")
    completed = 0
    completed_this_run = 0
    completed_durations: list[float] = []
    cached_matrix_key: tuple[str, int] | None = None
    cached_matrix: PreparedMatrix | None = None
    cached_data_key: tuple[str, int] | None = None
    cached_train: pd.DataFrame | None = None
    cached_validation: pd.DataFrame | None = None
    for target, fold, model in tasks:
        checkpoint_path, prediction_path = task_paths(target, fold, model)
        if checkpoint_path.exists():
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            if (
                checkpoint.get("status") == "completed"
                and checkpoint.get("contract_sha256") == expected_hash
                and prediction_path.exists()
            ):
                completed += 1
                completed_durations.append(float(checkpoint["fit_seconds"]))
                logger.info(
                    "[%d/%d] SKIP 완료 checkpoint | target=%s fold=%d model=%s",
                    completed,
                    len(tasks),
                    target,
                    fold,
                    model,
                )
                continue
            raise RuntimeError(
                f"Checkpoint contract mismatch or incomplete file: {checkpoint_path}"
            )

        data_key = (target, fold)
        if cached_data_key != data_key:
            membership = folds.loc[
                folds["fold"] == fold, [ROW_ID, "role", "validation_period"]
            ]
            frame = development.merge(
                membership, on=ROW_ID, how="inner", validate="one_to_one"
            )
            cached_train = frame.loc[
                (frame["role"] == "train") & frame[target].notna()
            ].copy()
            cached_validation = frame.loc[
                (frame["role"] == "validation") & frame[target].notna()
            ].copy()
            cached_data_key = data_key
        train = cached_train
        validation = cached_validation
        if train is None or validation is None:  # pragma: no cover - defensive
            raise RuntimeError("Target/Fold frame cache failed.")
        if train.empty or validation.empty:
            raise RuntimeError(f"Empty train/validation: {target}, fold={fold}")
        train_y = train[target].to_numpy(dtype=np.float64)
        validation_y = validation[target].to_numpy(dtype=np.float64)
        task_number = completed + 1
        logger.info(
            "[%d/%d] START | target=%s fold=%d validation=%d model=%s train=%d validation_rows=%d",
            task_number,
            len(tasks),
            target,
            fold,
            int(validation["validation_period"].iloc[0]),
            model,
            len(train),
            len(validation),
        )
        atomic_json(
            PROGRESS_PATH,
            {
                "status": "running",
                "updated_at_kst": now_kst(),
                "contract_sha256": expected_hash,
                "completed_tasks": completed,
                "total_tasks": len(tasks),
                "percent_complete": round(100 * completed / len(tasks), 2),
                "current": {"target": target, "fold": fold, "model": model},
                "holdout_target_opened": False,
            },
        )
        started = time.perf_counter()
        matrix: PreparedMatrix | None = None
        if model not in {"seasonal_naive", "industry_median"}:
            matrix_key = (target, fold)
            if cached_matrix_key != matrix_key or cached_matrix is None:
                logger.info(
                    "    Train-only 전처리 시작 | approved features=%d",
                    len(feature_columns),
                )
                cached_matrix = prepare_matrix(train, validation, feature_columns)
                cached_matrix_key = matrix_key
                logger.info(
                    "    Train-only 전처리 완료 | matrix=%s",
                    cached_matrix.train.shape,
                )
            else:
                logger.info("    동일 Target·Fold 전처리 matrix 재사용")
            matrix = cached_matrix
        seed = int(config["models"]["random_seed"]) + fold * 100
        threads = max(
            1,
            min(
                int(config["models"]["max_threads"]),
                max(1, (os.cpu_count() or 2) - 1),
            ),
        )
        if model == "seasonal_naive":
            raw_prediction = predict_seasonal(train, validation, train_y)
        elif model == "industry_median":
            raw_prediction = predict_industry_median(train, validation, train_y)
        elif model == "regularized_linear":
            raw_prediction = predict_regularized_linear(
                matrix,
                train_y,
                config["models"]["regularized_linear"],
                seed,
                logger,
            )
        elif model == "lightgbm":
            raw_prediction = predict_lightgbm(
                matrix,
                train_y,
                validation_y,
                config["models"]["lightgbm"],
                seed,
                threads,
                logger,
            )
        elif model == "catboost":
            raw_prediction = predict_catboost(
                matrix,
                train_y,
                validation_y,
                config["models"]["catboost"],
                seed,
                threads,
                logger,
            )
        elif model == "xgboost":
            raw_prediction = predict_xgboost(
                matrix,
                train_y,
                validation_y,
                config["models"]["xgboost"],
                seed,
                threads,
                logger,
            )
        else:  # pragma: no cover - protected by config contract
            raise ValueError(f"Unsupported model: {model}")
        metrics, corrected = compute_metrics(validation_y, raw_prediction)
        elapsed = time.perf_counter() - started
        predictions = pd.DataFrame(
            {
                ROW_ID: validation[ROW_ID].to_numpy(dtype=np.int64),
                PERIOD: validation[PERIOD].to_numpy(dtype=np.int32),
                INDUSTRY: validation[INDUSTRY].astype("string").to_numpy(),
                "actual": validation_y,
                "raw_p10": raw_prediction[:, 0],
                "raw_p50": raw_prediction[:, 1],
                "raw_p90": raw_prediction[:, 2],
                "p10": corrected[:, 0],
                "p50": corrected[:, 1],
                "p90": corrected[:, 2],
            }
        )
        temporary_prediction = prediction_path.with_suffix(".parquet.tmp")
        predictions.to_parquet(temporary_prediction, index=False, compression="zstd")
        temporary_prediction.replace(prediction_path)
        checkpoint = {
            "status": "completed",
            "completed_at_kst": now_kst(),
            "contract_sha256": expected_hash,
            "target": target,
            "fold": fold,
            "validation_period": int(validation["validation_period"].iloc[0]),
            "model": model,
            "train_rows": len(train),
            "validation_rows": len(validation),
            "fit_seconds": elapsed,
            "metrics": metrics,
            "prediction_path": str(prediction_path.relative_to(ROOT)),
            "prediction_sha256": sha256_file(prediction_path),
            "holdout_target_opened": False,
        }
        atomic_json(checkpoint_path, checkpoint)
        completed += 1
        completed_this_run += 1
        completed_durations.append(elapsed)
        remaining = len(tasks) - completed
        eta_seconds = float(np.mean(completed_durations) * remaining)
        logger.info(
            "[%d/%d %.1f%%] DONE | MAE=%.6f coverage=%.4f crossing_raw=%.4f elapsed=%.1fs ETA≈%.1fmin",
            completed,
            len(tasks),
            100 * completed / len(tasks),
            metrics["mae"],
            metrics["coverage_p10_p90"],
            metrics["crossing_ratio_raw"],
            elapsed,
            eta_seconds / 60,
        )
        if max_new_tasks is not None and completed_this_run >= max_new_tasks:
            atomic_json(
                PROGRESS_PATH,
                {
                    "status": "paused_after_requested_tasks",
                    "updated_at_kst": now_kst(),
                    "contract_sha256": expected_hash,
                    "completed_tasks": completed,
                    "completed_this_run": completed_this_run,
                    "total_tasks": len(tasks),
                    "percent_complete": round(100 * completed / len(tasks), 2),
                    "last_completed": {
                        "target": target,
                        "fold": fold,
                        "model": model,
                    },
                    "holdout_target_opened": False,
                    "resume_command": ".\\scripts\\run_re_stage5_cv.ps1",
                },
            )
            logger.info(
                "요청된 신규 task %d개 완료 후 안전 중단 | 다음 실행에서 checkpoint 이후 재개",
                max_new_tasks,
            )
            return

    logger.info("모든 CV task 완료 | 결과 집계 시작")
    metrics, industry = collect_results(expected_hash)
    if len(metrics) != len(tasks):
        raise RuntimeError(
            f"Expected {len(tasks)} completed tasks, found {len(metrics)}."
        )
    write_summary(metrics, industry)
    atomic_json(
        PROGRESS_PATH,
        {
            "status": "cv_completed_waiting_for_user_model_approval",
            "completed_at_kst": now_kst(),
            "updated_at_kst": now_kst(),
            "contract_sha256": expected_hash,
            "completed_tasks": len(tasks),
            "total_tasks": len(tasks),
            "percent_complete": 100.0,
            "fold_metrics": str(FOLD_METRICS_PATH.relative_to(ROOT)),
            "model_summary": str(SUMMARY_PATH.relative_to(ROOT)),
            "comparison_report": str(REPORT_PATH.relative_to(ROOT)),
            "holdout_target_opened": False,
            "next_required_decision": "user_approval_of_selected_model_and_stage6_status",
        },
    )
    logger.info(
        "CV 완료 | holdout target=미개방 | 다음 단계=후보 결과 검토 및 사용자 모델 승인"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--phase", choices=["cv"], default="cv")
    parser.add_argument("--max-new-tasks", type=int)
    args = parser.parse_args()
    if args.max_new_tasks is not None and args.max_new_tasks < 1:
        parser.error("--max-new-tasks must be at least 1")
    if args.dry_run:
        dry_run()
    elif args.status:
        status()
    else:
        try:
            run_cv(max_new_tasks=args.max_new_tasks)
        except Exception as error:
            prior: dict[str, object] = {}
            if PROGRESS_PATH.exists():
                try:
                    prior = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    prior = {}
            prior.update(
                {
                    "status": "failed_resumable",
                    "failed_at_kst": now_kst(),
                    "updated_at_kst": now_kst(),
                    "error_type": type(error).__name__,
                    "error": str(error)[:2000],
                    "holdout_target_opened": False,
                    "resume_command": ".\\scripts\\run_re_stage5_cv.ps1",
                }
            )
            atomic_json(PROGRESS_PATH, prior)
            raise


if __name__ == "__main__":
    main()
