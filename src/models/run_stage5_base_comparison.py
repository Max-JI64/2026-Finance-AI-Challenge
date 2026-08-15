"""Run the approved Stage 5 untuned nine-model chronological comparison.

Only Stage 4 development labels are read. Preprocessing is fit independently
inside each training fold, and the locked 2025 test data is never opened.
"""

from __future__ import annotations

import gc
import json
import math
import os
import time
import warnings
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import yaml
from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier
from scipy import sparse
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    fbeta_score,
    log_loss,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config" / "stage5.yaml"
REPORT_DIR = PROJECT_ROOT / "reports" / "stage5"
CHECKPOINT_DIR = REPORT_DIR / "checkpoints"
FOLD_METRICS_PATH = REPORT_DIR / "base_fold_metrics.csv"
SUMMARY_PATH = REPORT_DIR / "base_model_summary.csv"
OOF_PATH = REPORT_DIR / "base_oof_predictions.parquet"
REPORT_PATH = REPORT_DIR / "base_comparison.md"
MANIFEST_PATH = REPORT_DIR / "base_manifest.json"

RANDOM_SEED = 20260815
TARGET = "target_persistent_decline"
METADATA = {
    "stage4_row_id",
    "target_start_period",
    "target_end_period",
    "final_partition",
    TARGET,
}
MODEL_ORDER = [
    "dummy_prior",
    "logistic_l2",
    "logistic_l1",
    "logistic_elasticnet",
    "random_forest",
    "extra_trees",
    "lightgbm",
    "xgboost",
    "catboost",
]


def load_contract() -> tuple[dict[str, object], Path, Path, list[str]]:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    if config["status"]["candidate_models"] != "approved":
        raise RuntimeError("Candidate model list is not approved.")
    if config["status"]["metric_policy"] != "approved":
        raise RuntimeError("Metric policy is not approved.")
    if config["status"]["feature_contract"] != "approved":
        raise RuntimeError("Pre-model EDA and the Stage 5 Feature contract are not approved.")
    if config["status"]["base_comparison"] != "approved_to_run":
        raise RuntimeError("Stage 5 execution is not authorized; planning only.")
    if config["candidate_models"] != MODEL_ORDER:
        raise RuntimeError("Configured candidate list differs from the implemented list.")
    data = config["data"]
    development_path = PROJECT_ROOT / data["development"]
    fold_path = PROJECT_ROOT / data["fold_membership"]
    stage4_manifest = json.loads(
        (PROJECT_ROOT / data["feature_manifest"]).read_text(encoding="utf-8")
    )
    if not stage4_manifest["verification"]["gate4_passed"]:
        raise RuntimeError("Stage 4 Gate is not complete.")
    if stage4_manifest["verification"]["locked_test_target_materialized"]:
        raise RuntimeError("Locked-test Target must remain unmaterialized.")
    return config, development_path, fold_path, stage4_manifest["feature_columns"]


def checkpoint_paths(model_name: str, fold: int) -> tuple[Path, Path]:
    stem = f"{model_name}__fold{fold}"
    return CHECKPOINT_DIR / f"{stem}.json", CHECKPOINT_DIR / f"{stem}.parquet"


def completed_checkpoint(model_name: str, fold: int) -> bool:
    metric_path, prediction_path = checkpoint_paths(model_name, fold)
    if not metric_path.exists() or not prediction_path.exists():
        return False
    try:
        metric = json.loads(metric_path.read_text(encoding="utf-8"))
        columns = pq.ParquetFile(prediction_path).schema_arrow.names
    except Exception:
        return False
    return metric.get("status") == "completed" and columns == [
        "stage4_row_id",
        "fold",
        "model",
        "target",
        "probability",
    ]


def write_checkpoint(
    model_name: str,
    fold: int,
    metric: dict[str, object],
    row_ids: np.ndarray,
    target: np.ndarray,
    probability: np.ndarray,
) -> None:
    metric_path, prediction_path = checkpoint_paths(model_name, fold)
    temporary_metric = metric_path.with_suffix(".json.tmp")
    temporary_prediction = prediction_path.with_suffix(".parquet.tmp")
    prediction = pd.DataFrame(
        {
            "stage4_row_id": row_ids.astype("int64"),
            "fold": np.full(len(row_ids), fold, dtype="int8"),
            "model": model_name,
            "target": target.astype("int8"),
            "probability": probability.astype("float32"),
        }
    )
    prediction.to_parquet(temporary_prediction, index=False, compression="zstd")
    temporary_metric.write_text(
        json.dumps(metric, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary_prediction.replace(prediction_path)
    temporary_metric.replace(metric_path)


def failed_checkpoint(
    model_name: str, fold: int, error: Exception, fit_seconds: float
) -> None:
    metric_path, _ = checkpoint_paths(model_name, fold)
    metric_path.write_text(
        json.dumps(
            {
                "status": "failed",
                "model": model_name,
                "fold": fold,
                "fit_seconds": fit_seconds,
                "error_type": type(error).__name__,
                "error": str(error)[:1000],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def compute_metrics(
    target: np.ndarray,
    probability: np.ndarray,
    threshold: float = 0.5,
) -> dict[str, float | int]:
    probability = np.clip(np.asarray(probability, dtype="float64"), 1e-7, 1 - 1e-7)
    prediction = (probability >= threshold).astype("int8")
    tn, fp, fn, tp = confusion_matrix(target, prediction, labels=[0, 1]).ravel()
    return {
        "average_precision": float(average_precision_score(target, probability)),
        "roc_auc": float(roc_auc_score(target, probability)),
        "log_loss": float(log_loss(target, probability, labels=[0, 1])),
        "brier_score": float(brier_score_loss(target, probability)),
        "threshold": threshold,
        "precision": float(precision_score(target, prediction, zero_division=0)),
        "recall": float(recall_score(target, prediction, zero_division=0)),
        "f1": float(f1_score(target, prediction, zero_division=0)),
        "f2": float(fbeta_score(target, prediction, beta=2, zero_division=0)),
        "mcc": float(matthews_corrcoef(target, prediction)),
        "balanced_accuracy": float(balanced_accuracy_score(target, prediction)),
        "accuracy": float(accuracy_score(target, prediction)),
        "predicted_positive_rate": float(prediction.mean()),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def transform_fold(
    train_frame: pd.DataFrame,
    validation_frame: pd.DataFrame,
    numeric_columns: list[str],
    categorical_columns: list[str],
):
    """Fit median/scale/one-hot rules on training only with bounded temporaries."""
    train_numeric = np.empty(
        (len(train_frame), len(numeric_columns)), dtype=np.float32
    )
    validation_numeric = np.empty(
        (len(validation_frame), len(numeric_columns)), dtype=np.float32
    )
    for index, column in enumerate(numeric_columns):
        train_values = train_frame[column].to_numpy(dtype=np.float32, copy=True)
        validation_values = validation_frame[column].to_numpy(
            dtype=np.float32, copy=True
        )
        median = float(np.nanmedian(train_values))
        if not math.isfinite(median):
            median = 0.0
        train_values[np.isnan(train_values)] = median
        validation_values[np.isnan(validation_values)] = median
        scale = float(train_values.std(dtype=np.float64))
        if not math.isfinite(scale) or scale == 0:
            scale = 1.0
        train_values /= scale
        validation_values /= scale
        train_numeric[:, index] = train_values
        validation_numeric[:, index] = validation_values

    train_numeric_sparse = sparse.csr_matrix(train_numeric)
    validation_numeric_sparse = sparse.csr_matrix(validation_numeric)
    del train_numeric, validation_numeric

    encoder = OneHotEncoder(
        handle_unknown="ignore",
        sparse_output=True,
        dtype=np.float32,
    )
    train_categories = (
        train_frame[categorical_columns]
        .astype("string")
        .fillna("__MISSING__")
    )
    validation_categories = (
        validation_frame[categorical_columns]
        .astype("string")
        .fillna("__MISSING__")
    )
    train_categorical_sparse = encoder.fit_transform(train_categories)
    validation_categorical_sparse = encoder.transform(validation_categories)
    train_sparse = sparse.hstack(
        [train_numeric_sparse, train_categorical_sparse], format="csr"
    ).astype(np.float32)
    validation_sparse = sparse.hstack(
        [validation_numeric_sparse, validation_categorical_sparse], format="csr"
    ).astype(np.float32)
    del (
        train_numeric_sparse,
        validation_numeric_sparse,
        train_categorical_sparse,
        validation_categorical_sparse,
        train_categories,
        validation_categories,
        encoder,
    )
    gc.collect()
    return train_sparse, validation_sparse


def sparse_model(model_name: str, jobs: int, config: dict[str, object]):
    budget = config["screen_budget"]
    if model_name.startswith("logistic_"):
        common = {
            "solver": "saga",
            "C": 1.0,
            "max_iter": int(budget["logistic_max_iter"]),
            "tol": 1e-3,
            "random_state": RANDOM_SEED,
            "class_weight": None,
        }
        if model_name == "logistic_l2":
            return LogisticRegression(penalty="l2", **common)
        if model_name == "logistic_l1":
            return LogisticRegression(penalty="l1", **common)
        return LogisticRegression(penalty="elasticnet", l1_ratio=0.5, **common)
    if model_name == "random_forest":
        return RandomForestClassifier(
            n_estimators=int(budget["bagging_trees"]),
            max_depth=int(budget["bagging_max_depth"]),
            min_samples_leaf=int(budget["bagging_min_samples_leaf"]),
            random_state=RANDOM_SEED,
            n_jobs=jobs,
            class_weight=None,
        )
    if model_name == "extra_trees":
        return ExtraTreesClassifier(
            n_estimators=int(budget["bagging_trees"]),
            max_depth=int(budget["bagging_max_depth"]),
            min_samples_leaf=int(budget["bagging_min_samples_leaf"]),
            random_state=RANDOM_SEED,
            n_jobs=jobs,
            class_weight=None,
        )
    iterations = int(budget["boosting_iterations"])
    if model_name == "lightgbm":
        return LGBMClassifier(
            n_estimators=iterations,
            learning_rate=0.05,
            num_leaves=31,
            objective="binary",
            random_state=RANDOM_SEED,
            n_jobs=jobs,
            verbosity=-1,
        )
    if model_name == "xgboost":
        return XGBClassifier(
            n_estimators=iterations,
            learning_rate=0.05,
            max_depth=6,
            objective="binary:logistic",
            eval_metric="logloss",
            tree_method="hist",
            random_state=RANDOM_SEED,
            n_jobs=jobs,
        )
    raise KeyError(model_name)


def run_dummy(
    train_target: np.ndarray,
    validation_target: np.ndarray,
) -> np.ndarray:
    return np.full(len(validation_target), train_target.mean(), dtype="float64")


def prepare_catboost_frame(
    frame: pd.DataFrame,
    categorical_columns: list[str],
    numeric_columns: list[str],
) -> pd.DataFrame:
    result = frame.copy(deep=False)
    for column in categorical_columns:
        result[column] = result[column].astype("string").fillna("__MISSING__").astype(str)
    for column in numeric_columns:
        result[column] = pd.to_numeric(result[column], errors="coerce").astype("float32")
    return result


def load_development_compressed(
    development_path: Path,
    feature_columns: list[str],
    categorical_columns: list[str],
) -> pd.DataFrame:
    """Load the processed panel once without pandas float64 duplication."""
    columns = ["stage4_row_id", *feature_columns, TARGET]
    table = pq.read_table(development_path, columns=columns)
    arrays: list[pa.Array | pa.ChunkedArray] = []
    fields: list[pa.Field] = []
    categorical = set(categorical_columns)
    for column in columns:
        values = table[column]
        if column == "stage4_row_id":
            values = values.cast(pa.int64(), safe=False)
        elif column == TARGET:
            values = values.cast(pa.int8(), safe=False)
        elif column in categorical:
            values = values.combine_chunks().dictionary_encode()
        else:
            values = values.cast(pa.float32(), safe=False)
        arrays.append(values)
        fields.append(pa.field(column, values.type))
    compressed = pa.Table.from_arrays(arrays, schema=pa.schema(fields))
    del table, arrays
    return compressed.to_pandas(split_blocks=True, self_destruct=True)


def run_catboost(
    train_frame: pd.DataFrame,
    train_target: np.ndarray,
    validation_frame: pd.DataFrame,
    categorical_columns: list[str],
    numeric_columns: list[str],
    jobs: int,
    iterations: int,
) -> np.ndarray:
    train = prepare_catboost_frame(train_frame, categorical_columns, numeric_columns)
    validation = prepare_catboost_frame(
        validation_frame, categorical_columns, numeric_columns
    )
    model = CatBoostClassifier(
        iterations=iterations,
        depth=6,
        learning_rate=0.05,
        loss_function="Logloss",
        random_seed=RANDOM_SEED,
        thread_count=jobs,
        verbose=False,
        allow_writing_files=False,
    )
    model.fit(train, train_target, cat_features=categorical_columns)
    probability = model.predict_proba(validation)[:, 1]
    del train, validation, model
    return probability


def process_model(
    model_name: str,
    fold: int,
    train_target: np.ndarray,
    validation_target: np.ndarray,
    validation_row_ids: np.ndarray,
    train_sparse,
    validation_sparse,
    train_frame: pd.DataFrame,
    validation_frame: pd.DataFrame,
    categorical_columns: list[str],
    numeric_columns: list[str],
    jobs: int,
    config: dict[str, object],
) -> None:
    if completed_checkpoint(model_name, fold):
        print(f"SKIP fold={fold} model={model_name} checkpoint=completed", flush=True)
        return
    started = time.perf_counter()
    try:
        if model_name == "dummy_prior":
            probability = run_dummy(train_target, validation_target)
            fit_seconds = time.perf_counter() - started
            predict_seconds = 0.0
        elif model_name == "catboost":
            fit_started = time.perf_counter()
            probability = run_catboost(
                train_frame,
                train_target,
                validation_frame,
                categorical_columns,
                numeric_columns,
                jobs,
                int(config["screen_budget"]["boosting_iterations"]),
            )
            fit_seconds = time.perf_counter() - fit_started
            predict_seconds = 0.0
        else:
            model = sparse_model(model_name, jobs, config)
            fit_started = time.perf_counter()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", ConvergenceWarning)
                model.fit(train_sparse, train_target)
            fit_seconds = time.perf_counter() - fit_started
            predict_started = time.perf_counter()
            probability = model.predict_proba(validation_sparse)[:, 1]
            predict_seconds = time.perf_counter() - predict_started
            convergence_warnings = sum(
                issubclass(item.category, ConvergenceWarning) for item in caught
            )
            del model
        metrics = compute_metrics(validation_target, probability)
        metrics.update(
            {
                "status": "completed",
                "model": model_name,
                "fold": fold,
                "train_rows": int(len(train_target)),
                "validation_rows": int(len(validation_target)),
                "train_positive_rate": float(train_target.mean()),
                "validation_positive_rate": float(validation_target.mean()),
                "fit_seconds": float(fit_seconds),
                "predict_seconds": float(predict_seconds),
                "convergence_warnings": int(
                    locals().get("convergence_warnings", 0)
                ),
            }
        )
        write_checkpoint(
            model_name,
            fold,
            metrics,
            validation_row_ids,
            validation_target,
            probability,
        )
        print(
            f"DONE fold={fold} model={model_name} "
            f"AP={metrics['average_precision']:.5f} "
            f"AUC={metrics['roc_auc']:.5f} fit={fit_seconds:.1f}s",
            flush=True,
        )
    except Exception as error:
        elapsed = time.perf_counter() - started
        failed_checkpoint(model_name, fold, error, elapsed)
        print(
            f"FAILED fold={fold} model={model_name} "
            f"error={type(error).__name__}: {str(error)[:300]}",
            flush=True,
        )


def collect_results() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metric_rows: list[dict[str, object]] = []
    prediction_frames: list[pd.DataFrame] = []
    for model_name in MODEL_ORDER:
        for fold in range(1, 5):
            metric_path, prediction_path = checkpoint_paths(model_name, fold)
            if metric_path.exists():
                metric_rows.append(json.loads(metric_path.read_text(encoding="utf-8")))
            if completed_checkpoint(model_name, fold):
                prediction_frames.append(pd.read_parquet(prediction_path))
    metrics = pd.DataFrame(metric_rows)
    completed = metrics[metrics["status"] == "completed"].copy()
    if completed.empty:
        raise RuntimeError("No model completed successfully.")
    numeric_metrics = [
        "average_precision",
        "roc_auc",
        "log_loss",
        "brier_score",
        "precision",
        "recall",
        "f1",
        "f2",
        "mcc",
        "balanced_accuracy",
        "accuracy",
        "predicted_positive_rate",
        "fit_seconds",
        "predict_seconds",
    ]
    rows = []
    for model_name, group in completed.groupby("model", sort=False):
        row: dict[str, object] = {
            "model": model_name,
            "completed_folds": int(group["fold"].nunique()),
        }
        for metric in numeric_metrics:
            values = pd.to_numeric(group[metric], errors="coerce")
            row[f"mean_{metric}"] = float(values.mean())
            row[f"std_{metric}"] = float(values.std(ddof=0))
            row[f"min_{metric}"] = float(values.min())
        row["total_fit_seconds"] = float(group["fit_seconds"].sum())
        row["total_predict_seconds"] = float(group["predict_seconds"].sum())
        rows.append(row)
    summary = pd.DataFrame(rows)
    summary["eligible_for_top3"] = (
        (summary["model"] != "dummy_prior") & (summary["completed_folds"] == 4)
    )
    eligible = summary[summary["eligible_for_top3"]].copy()
    eligible["auprc_rank"] = eligible["mean_average_precision"].rank(
        ascending=False, method="min"
    )
    eligible["auroc_rank"] = eligible["mean_roc_auc"].rank(
        ascending=False, method="min"
    )
    eligible["joint_rank_score"] = (
        eligible["auprc_rank"] + eligible["auroc_rank"]
    ) / 2
    eligible = eligible.sort_values(
        ["joint_rank_score", "min_average_precision", "mean_brier_score", "total_fit_seconds"],
        ascending=[True, False, True, True],
    )
    eligible["recommended_rank"] = np.arange(1, len(eligible) + 1)
    summary = summary.merge(
        eligible[
            [
                "model",
                "auprc_rank",
                "auroc_rank",
                "joint_rank_score",
                "recommended_rank",
            ]
        ],
        on="model",
        how="left",
    ).sort_values(["recommended_rank", "model"], na_position="last")
    predictions = pd.concat(prediction_frames, ignore_index=True)
    return metrics, summary, predictions


def write_report(
    summary: pd.DataFrame,
    failures: pd.DataFrame,
    config: dict[str, object],
    feature_count: int,
    categorical_count: int,
) -> list[str]:
    recommended = summary[
        (summary["eligible_for_top3"]) & (summary["recommended_rank"] <= 3)
    ].sort_values("recommended_rank")
    top3 = recommended["model"].tolist()
    table = []
    for row in summary.itertuples(index=False):
        rank = "-" if pd.isna(row.recommended_rank) else str(int(row.recommended_rank))
        table.append(
            f"| {row.model} | {int(row.completed_folds)}/4 | "
            f"{row.mean_average_precision:.4f} | {row.mean_roc_auc:.4f} | "
            f"{row.min_average_precision:.4f} | {row.mean_brier_score:.4f} | "
            f"{row.mean_f2:.4f} | {row.total_fit_seconds:.1f} | {rank} |"
        )
    lines = [
        "# Stage 5 기본 모델 비교",
        "",
        "- 상태: 1차 무튜닝 비교 완료 / 상위 3개 Optuna 후보 사용자 승인 대기",
        "- 분할: Stage 4에서 고정한 4개 시간순 expanding-window Fold",
        "- 전처리: 각 Fold의 학습 파티션에만 Fit",
        f"- 입력 Feature: {feature_count}개(문자형 {categorical_count}개)",
        "- 공동 핵심 지표: AUPRC/AP와 AUROC",
        "- F2: 임계값 0.5 참고값이며 후보 순위에는 사용하지 않음",
        "- 순위: 평균 AUPRC 순위와 평균 AUROC 순위의 평균; 동률 시 최저 Fold AUPRC, Brier Score, 학습시간 순",
        "- 2025 잠긴 테스트: 미접근",
        "",
        "| 모델 | 완료 Fold | 평균 AUPRC | 평균 AUROC | 최저 Fold AUPRC | 평균 Brier | F2@0.5 | 총 학습초 | 권장 순위 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        *table,
        "",
        "## Optuna 후보 권장안",
        "",
        f"자동 규칙상 상위 3개: {', '.join(top3)}",
        "",
        "이 목록은 아직 확정하지 않는다. 사용자 승인 후에만 세 모델의 Optuna를 실행한다.",
        "",
    ]
    if not failures.empty:
        lines.extend(
            [
                "## 실패 기록",
                "",
                *[
                    f"- {row.model} Fold {int(row.fold)}: {row.error_type} — {row.error}"
                    for row in failures.itertuples(index=False)
                ],
                "",
            ]
        )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    return top3


def main() -> None:
    config, development_path, fold_path, feature_columns = load_contract()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    jobs = max(
        1,
        min(
            int(config["screen_budget"]["max_parallel_cpu_threads"]),
            max(1, (os.cpu_count() or 2) - 1),
        ),
    )

    parquet_schema = pq.ParquetFile(development_path).schema_arrow
    type_by_column = {field.name: field.type for field in parquet_schema}
    categorical_columns = [
        column
        for column in feature_columns
        if pa.types.is_string(type_by_column[column])
    ]
    numeric_columns = [
        column for column in feature_columns if column not in categorical_columns
    ]
    frame = load_development_compressed(
        development_path, feature_columns, categorical_columns
    )
    if len(frame) != 222_973:
        raise RuntimeError("Unexpected Stage 4 development row count.")
    if not frame["stage4_row_id"].is_unique or frame["stage4_row_id"].isna().any():
        raise RuntimeError("Stage 4 row IDs must be unique and non-null.")
    frame = frame.set_index("stage4_row_id", drop=False)
    target = frame[TARGET].astype("int8")
    features = frame[feature_columns].copy(deep=False)
    del frame
    for column in categorical_columns:
        if not isinstance(features[column].dtype, pd.CategoricalDtype):
            features[column] = features[column].astype("category")

    membership = pd.read_parquet(fold_path)
    print(
        f"START rows={len(features)} features={len(feature_columns)} "
        f"categorical={len(categorical_columns)} jobs={jobs}",
        flush=True,
    )
    for fold in range(1, 5):
        train_ids = membership.loc[
            (membership["fold"] == fold) & (membership["partition"] == "train"),
            "stage4_row_id",
        ].to_numpy(dtype="int64")
        validation_ids = membership.loc[
            (membership["fold"] == fold)
            & (membership["partition"] == "validation"),
            "stage4_row_id",
        ].to_numpy(dtype="int64")
        train_frame = features.loc[train_ids]
        validation_frame = features.loc[validation_ids]
        train_target = target.loc[train_ids].to_numpy(dtype="int8")
        validation_target = target.loc[validation_ids].to_numpy(dtype="int8")

        needed_sparse = any(
            not completed_checkpoint(model_name, fold)
            for model_name in MODEL_ORDER
            if model_name not in {"dummy_prior", "catboost"}
        )
        train_sparse = validation_sparse = None
        if needed_sparse:
            transform_started = time.perf_counter()
            train_sparse, validation_sparse = transform_fold(
                train_frame,
                validation_frame,
                numeric_columns,
                categorical_columns,
            )
            print(
                f"TRANSFORM fold={fold} train={train_sparse.shape} "
                f"validation={validation_sparse.shape} "
                f"seconds={time.perf_counter()-transform_started:.1f}",
                flush=True,
            )

        for model_name in MODEL_ORDER:
            if model_name == "catboost" and train_sparse is not None:
                del train_sparse, validation_sparse
                train_sparse = validation_sparse = None
                gc.collect()
            process_model(
                model_name,
                fold,
                train_target,
                validation_target,
                validation_ids,
                train_sparse,
                validation_sparse,
                train_frame,
                validation_frame,
                categorical_columns,
                numeric_columns,
                jobs,
                config,
            )
            gc.collect()
        del (
            train_frame,
            validation_frame,
            train_target,
            validation_target,
            train_sparse,
            validation_sparse,
        )
        gc.collect()

    metrics, summary, predictions = collect_results()
    metrics.to_csv(FOLD_METRICS_PATH, index=False, encoding="utf-8-sig")
    summary.to_csv(SUMMARY_PATH, index=False, encoding="utf-8-sig")
    predictions.to_parquet(OOF_PATH, index=False, compression="zstd")
    failures = metrics[metrics["status"] == "failed"].copy()
    top3 = write_report(
        summary,
        failures,
        config,
        len(feature_columns),
        len(categorical_columns),
    )
    complete_models = summary.loc[
        summary["completed_folds"] == 4, "model"
    ].tolist()
    mandatory_passed = (
        "dummy_prior" in complete_models
        and any(model.startswith("logistic_") for model in complete_models)
        and any(
            model in {"random_forest", "extra_trees"} for model in complete_models
        )
        and any(
            model in {"lightgbm", "xgboost", "catboost"}
            for model in complete_models
        )
        and len(top3) == 3
    )
    manifest = {
        "created_at_kst": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(
            timespec="minutes"
        ),
        "status": "base_comparison_completed" if mandatory_passed else "partial",
        "candidate_models": MODEL_ORDER,
        "completed_models_all_four_folds": complete_models,
        "failed_fold_runs": int(len(failures)),
        "feature_count": len(feature_columns),
        "categorical_feature_count": len(categorical_columns),
        "preprocessing_fit_scope": "each_fold_training_partition_only",
        "ranking_rule": config["metrics"]["candidate_ranking"],
        "recommended_top3_unapproved": top3,
        "optuna_executed": False,
        "locked_test_opened": False,
        "mandatory_base_comparison_passed": bool(mandatory_passed),
        "outputs": {
            "fold_metrics": str(FOLD_METRICS_PATH.relative_to(PROJECT_ROOT)),
            "model_summary": str(SUMMARY_PATH.relative_to(PROJECT_ROOT)),
            "oof_predictions": str(OOF_PATH.relative_to(PROJECT_ROOT)),
            "report": str(REPORT_PATH.relative_to(PROJECT_ROOT)),
        },
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "completed_models": complete_models,
                "failures": len(failures),
                "recommended_top3_unapproved": top3,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
