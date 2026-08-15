"""Run the approved Stage 5 full untuned chronological comparison.

Every common baseline and every independent tree raw-group ablation is run
before a selection is made. The script reports fixed metrics and baseline
deltas but intentionally performs no automatic ranking or retention. Only
Stage 4 development labels are read; the locked 2025 test is never opened.
"""

from __future__ import annotations

import argparse
import gc
import json
import math
import os
import time
import warnings
from dataclasses import dataclass
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

from src.features.build_stage45_features import build_stage45_features
from src.features.build_stage5_feature_sets import (
    TREE_RAW_GROUPS,
    FeatureSetSpec,
    build_feature_set_specs,
    read_contract_rows,
    write_feature_set_manifest,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config" / "stage5.yaml"
FEATURE_CONTRACT_PATH = PROJECT_ROOT / "reports" / "stage45" / "feature_contract.md"
REPORT_DIR = PROJECT_ROOT / "reports" / "stage5"
CHECKPOINT_DIR = REPORT_DIR / "checkpoints_v2"
FEATURE_SET_MANIFEST_PATH = REPORT_DIR / "feature_sets.json"
FOLD_METRICS_PATH = REPORT_DIR / "full_fold_metrics.csv"
SUMMARY_PATH = REPORT_DIR / "full_model_feature_summary.csv"
INDUSTRY_METRICS_PATH = REPORT_DIR / "full_oof_industry_metrics.csv"
OOF_PATH = REPORT_DIR / "full_oof_predictions.parquet"
REPORT_PATH = REPORT_DIR / "full_comparison.md"
MANIFEST_PATH = REPORT_DIR / "full_manifest.json"

RANDOM_SEED = 20260815
TARGET = "target_persistent_decline"
MODEL_ORDER = [
    "dummy_prior", "logistic_l2", "logistic_l1", "logistic_elasticnet",
    "random_forest", "extra_trees", "lightgbm", "xgboost", "catboost",
]
LINEAR_MODELS = ["logistic_l2", "logistic_l1", "logistic_elasticnet"]
TREE_MODELS = ["random_forest", "extra_trees", "lightgbm", "xgboost", "catboost"]
SUMMARY_METRICS = [
    "average_precision", "roc_auc", "log_loss", "brier_score", "precision",
    "recall", "f1", "f2", "mcc", "balanced_accuracy", "accuracy",
    "predicted_positive_rate", "fit_seconds", "predict_seconds",
]


@dataclass(frozen=True)
class RunSpec:
    run_id: str
    model: str
    feature_set_id: str
    raw_group: str | None


def load_contract() -> tuple[dict[str, object], Path, Path, list[str]]:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    status = config["status"]
    if status["candidate_models"] != "approved":
        raise RuntimeError("Candidate model list is not approved.")
    if status["metric_policy"] != "approved":
        raise RuntimeError("Metric policy is not approved.")
    if status["feature_contract"] != "approved":
        raise RuntimeError("Stage 4.5 Feature contract is not approved.")
    if status["base_comparison"] != "approved_to_run":
        raise RuntimeError("Stage 5 full comparison is not authorized.")
    if config["candidate_models"] != MODEL_ORDER:
        raise RuntimeError("Configured candidate list differs from implementation.")
    ranking = config["metrics"]["candidate_ranking"]["rule"]
    if ranking != "no_automatic_ranking_before_user_review":
        raise RuntimeError("Stage 5 policy must prohibit automatic ranking.")
    data = config["data"]
    development_path = PROJECT_ROOT / data["development"]
    fold_path = PROJECT_ROOT / data["fold_membership"]
    manifest = json.loads(
        (PROJECT_ROOT / data["feature_manifest"]).read_text(encoding="utf-8")
    )
    if not manifest["verification"]["gate4_passed"]:
        raise RuntimeError("Stage 4 Gate is not complete.")
    if manifest["verification"]["locked_test_target_materialized"]:
        raise RuntimeError("Locked-test Target must remain unmaterialized.")
    return config, development_path, fold_path, manifest["feature_columns"]


def build_run_specs(feature_sets: dict[str, FeatureSetSpec]) -> list[RunSpec]:
    specs = [RunSpec("dummy_prior__prior", "dummy_prior", "prior", None)]
    specs.extend(
        RunSpec(f"{model}__linear_common_plus_log1p", model,
                "linear_common_plus_log1p", None)
        for model in LINEAR_MODELS
    )
    tree_sets = ["common_baseline", *(f"tree_plus_{g}" for g in TREE_RAW_GROUPS)]
    for feature_set_id in tree_sets:
        feature_set = feature_sets[feature_set_id]
        specs.extend(
            RunSpec(f"{model}__{feature_set_id}", model, feature_set_id,
                    feature_set.raw_group)
            for model in TREE_MODELS
        )
    if len(specs) != 34:
        raise RuntimeError(f"Expected 34 variants, got {len(specs)}")
    return specs


def checkpoint_paths(run_id: str, fold: int) -> tuple[Path, Path]:
    stem = f"{run_id}__fold{fold}"
    return CHECKPOINT_DIR / f"{stem}.json", CHECKPOINT_DIR / f"{stem}.parquet"


def completed_checkpoint(run_spec: RunSpec, fold: int) -> bool:
    metric_path, prediction_path = checkpoint_paths(run_spec.run_id, fold)
    if not metric_path.exists() or not prediction_path.exists():
        return False
    try:
        metric = json.loads(metric_path.read_text(encoding="utf-8"))
        columns = pq.ParquetFile(prediction_path).schema_arrow.names
    except Exception:
        return False
    expected = ["stage4_row_id", "fold", "run_id", "model", "feature_set_id",
                "target", "probability"]
    return (metric.get("status") == "completed"
            and metric.get("run_id") == run_spec.run_id
            and columns == expected)


def write_checkpoint(run_spec: RunSpec, fold: int, metric: dict[str, object],
                     row_ids: np.ndarray, target: np.ndarray,
                     probability: np.ndarray) -> None:
    metric_path, prediction_path = checkpoint_paths(run_spec.run_id, fold)
    temporary_metric = metric_path.with_suffix(".json.tmp")
    temporary_prediction = prediction_path.with_suffix(".parquet.tmp")
    prediction = pd.DataFrame({
        "stage4_row_id": row_ids.astype("int64"),
        "fold": np.full(len(row_ids), fold, dtype="int8"),
        "run_id": run_spec.run_id,
        "model": run_spec.model,
        "feature_set_id": run_spec.feature_set_id,
        "target": target.astype("int8"),
        "probability": probability.astype("float32"),
    })
    prediction.to_parquet(temporary_prediction, index=False, compression="zstd")
    temporary_metric.write_text(
        json.dumps(metric, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary_prediction.replace(prediction_path)
    temporary_metric.replace(metric_path)


def failed_checkpoint(run_spec: RunSpec, fold: int, error: Exception,
                      fit_seconds: float) -> None:
    metric_path, _ = checkpoint_paths(run_spec.run_id, fold)
    metric_path.write_text(json.dumps({
        "status": "failed", "run_id": run_spec.run_id,
        "model": run_spec.model, "feature_set_id": run_spec.feature_set_id,
        "raw_group": run_spec.raw_group, "fold": fold,
        "fit_seconds": fit_seconds, "error_type": type(error).__name__,
        "error": str(error)[:1000],
    }, ensure_ascii=False, indent=2), encoding="utf-8")


def compute_metrics(target: np.ndarray, probability: np.ndarray,
                    threshold: float = 0.5) -> dict[str, float | int]:
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
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
    }


def transform_fold_union(train_frame: pd.DataFrame,
                         validation_frame: pd.DataFrame,
                         numeric_columns: list[str],
                         categorical_columns: list[str]) -> tuple[
                             sparse.csr_matrix, sparse.csr_matrix,
                             dict[str, np.ndarray]]:
    """Fit union preprocessing on Train only and map source features to columns."""
    train_numeric = np.empty((len(train_frame), len(numeric_columns)), dtype=np.float32)
    validation_numeric = np.empty(
        (len(validation_frame), len(numeric_columns)), dtype=np.float32
    )
    feature_indices: dict[str, np.ndarray] = {}
    for index, column in enumerate(numeric_columns):
        train_values = train_frame[column].to_numpy(dtype=np.float32, copy=True)
        valid_values = validation_frame[column].to_numpy(dtype=np.float32, copy=True)
        train_values[~np.isfinite(train_values)] = np.nan
        valid_values[~np.isfinite(valid_values)] = np.nan
        median = float(np.nanmedian(train_values))
        if not math.isfinite(median):
            median = 0.0
        train_values[np.isnan(train_values)] = median
        valid_values[np.isnan(valid_values)] = median
        scale = float(train_values.std(dtype=np.float64))
        if not math.isfinite(scale) or scale == 0:
            scale = 1.0
        train_numeric[:, index] = train_values / scale
        validation_numeric[:, index] = valid_values / scale
        feature_indices[column] = np.array([index], dtype="int32")
    train_parts = [sparse.csr_matrix(train_numeric)]
    validation_parts = [sparse.csr_matrix(validation_numeric)]
    del train_numeric, validation_numeric
    offset = len(numeric_columns)
    if categorical_columns:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=True,
                                dtype=np.float32)
        train_categories = train_frame[categorical_columns].astype("string").fillna("__MISSING__")
        valid_categories = validation_frame[categorical_columns].astype("string").fillna("__MISSING__")
        train_parts.append(encoder.fit_transform(train_categories))
        validation_parts.append(encoder.transform(valid_categories))
        for column, categories in zip(categorical_columns, encoder.categories_):
            stop = offset + len(categories)
            feature_indices[column] = np.arange(offset, stop, dtype="int32")
            offset = stop
        del train_categories, valid_categories, encoder
    train_sparse = sparse.hstack(train_parts, format="csr").astype(np.float32)
    valid_sparse = sparse.hstack(validation_parts, format="csr").astype(np.float32)
    del train_parts, validation_parts
    gc.collect()
    return train_sparse, valid_sparse, feature_indices


def indices_for_feature_set(spec: FeatureSetSpec,
                            feature_indices: dict[str, np.ndarray]) -> np.ndarray:
    missing = [column for column in spec.columns if column not in feature_indices]
    if missing:
        raise KeyError(f"Preprocessed indices missing for {missing[:10]}")
    return np.concatenate([feature_indices[column] for column in spec.columns])


def sparse_model(model_name: str, jobs: int, config: dict[str, object]):
    budget = config["screen_budget"]
    if model_name.startswith("logistic_"):
        common = {"solver": "saga", "C": 1.0,
                  "max_iter": int(budget["logistic_max_iter"]), "tol": 1e-3,
                  "random_state": RANDOM_SEED, "class_weight": None}
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
            random_state=RANDOM_SEED, n_jobs=jobs, class_weight=None)
    if model_name == "extra_trees":
        return ExtraTreesClassifier(
            n_estimators=int(budget["bagging_trees"]),
            max_depth=int(budget["bagging_max_depth"]),
            min_samples_leaf=int(budget["bagging_min_samples_leaf"]),
            random_state=RANDOM_SEED, n_jobs=jobs, class_weight=None)
    iterations = int(budget["boosting_iterations"])
    if model_name == "lightgbm":
        return LGBMClassifier(n_estimators=iterations, learning_rate=0.05,
                              num_leaves=31, objective="binary",
                              random_state=RANDOM_SEED, n_jobs=jobs, verbosity=-1)
    if model_name == "xgboost":
        return XGBClassifier(n_estimators=iterations, learning_rate=0.05,
                             max_depth=6, objective="binary:logistic",
                             eval_metric="logloss", tree_method="hist",
                             random_state=RANDOM_SEED, n_jobs=jobs)
    raise KeyError(model_name)


def run_catboost(train_frame: pd.DataFrame, train_target: np.ndarray,
                 validation_frame: pd.DataFrame, columns: tuple[str, ...],
                 categorical_columns: list[str], jobs: int,
                 iterations: int) -> np.ndarray:
    categories = [column for column in columns if column in categorical_columns]
    train = train_frame.loc[:, list(columns)].copy()
    validation = validation_frame.loc[:, list(columns)].copy()
    for column in categories:
        train[column] = train[column].astype("string").fillna("__MISSING__").astype(str)
        validation[column] = validation[column].astype("string").fillna("__MISSING__").astype(str)
    model = CatBoostClassifier(
        iterations=iterations, depth=6, learning_rate=0.05,
        loss_function="Logloss", random_seed=RANDOM_SEED,
        thread_count=jobs, verbose=False, allow_writing_files=False)
    model.fit(train, train_target, cat_features=categories)
    probability = model.predict_proba(validation)[:, 1]
    del train, validation, model
    return probability


def process_run(run_spec: RunSpec, fold: int,
                feature_spec: FeatureSetSpec | None,
                train_target: np.ndarray, validation_target: np.ndarray,
                validation_row_ids: np.ndarray,
                train_sparse: sparse.csr_matrix | None,
                validation_sparse: sparse.csr_matrix | None,
                train_frame: pd.DataFrame, validation_frame: pd.DataFrame,
                categorical_columns: list[str], jobs: int,
                config: dict[str, object]) -> None:
    if completed_checkpoint(run_spec, fold):
        print(f"SKIP fold={fold} run={run_spec.run_id} checkpoint=completed", flush=True)
        return
    started = time.perf_counter()
    try:
        convergence_warnings = 0
        if run_spec.model == "dummy_prior":
            probability = np.full(len(validation_target), train_target.mean(), dtype="float64")
            fit_seconds = time.perf_counter() - started
            predict_seconds = 0.0
            feature_count = 0
        elif run_spec.model == "catboost":
            if feature_spec is None:
                raise RuntimeError("CatBoost requires a feature set.")
            fit_started = time.perf_counter()
            probability = run_catboost(
                train_frame, train_target, validation_frame, feature_spec.columns,
                categorical_columns, jobs,
                int(config["screen_budget"]["boosting_iterations"]))
            fit_seconds = time.perf_counter() - fit_started
            predict_seconds = 0.0
            feature_count = len(feature_spec.columns)
        else:
            if train_sparse is None or validation_sparse is None or feature_spec is None:
                raise RuntimeError("Sparse model inputs are missing.")
            model = sparse_model(run_spec.model, jobs, config)
            fit_started = time.perf_counter()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", ConvergenceWarning)
                model.fit(train_sparse, train_target)
            fit_seconds = time.perf_counter() - fit_started
            predict_started = time.perf_counter()
            probability = model.predict_proba(validation_sparse)[:, 1]
            predict_seconds = time.perf_counter() - predict_started
            convergence_warnings = sum(
                issubclass(item.category, ConvergenceWarning) for item in caught)
            feature_count = len(feature_spec.columns)
            del model
        metrics = compute_metrics(validation_target, probability)
        metrics.update({
            "status": "completed", "run_id": run_spec.run_id,
            "model": run_spec.model, "feature_set_id": run_spec.feature_set_id,
            "raw_group": run_spec.raw_group, "feature_count": feature_count,
            "fold": fold, "train_rows": int(len(train_target)),
            "validation_rows": int(len(validation_target)),
            "train_positive_rate": float(train_target.mean()),
            "validation_positive_rate": float(validation_target.mean()),
            "fit_seconds": float(fit_seconds),
            "predict_seconds": float(predict_seconds),
            "convergence_warnings": int(convergence_warnings),
        })
        write_checkpoint(run_spec, fold, metrics, validation_row_ids,
                         validation_target, probability)
        print(f"DONE fold={fold} run={run_spec.run_id} "
              f"AP={metrics['average_precision']:.5f} "
              f"AUC={metrics['roc_auc']:.5f} fit={fit_seconds:.1f}s", flush=True)
    except Exception as error:
        elapsed = time.perf_counter() - started
        failed_checkpoint(run_spec, fold, error, elapsed)
        print(f"FAILED fold={fold} run={run_spec.run_id} "
              f"error={type(error).__name__}: {str(error)[:300]}", flush=True)


def load_development_compressed(development_path: Path,
                                feature_columns: list[str],
                                categorical_columns: list[str]) -> pd.DataFrame:
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


def collect_results(run_specs: list[RunSpec]) -> tuple[pd.DataFrame, pd.DataFrame,
                                                          pd.DataFrame]:
    metric_rows: list[dict[str, object]] = []
    prediction_frames: list[pd.DataFrame] = []
    for run_spec in run_specs:
        for fold in range(1, 5):
            metric_path, prediction_path = checkpoint_paths(run_spec.run_id, fold)
            if metric_path.exists():
                metric_rows.append(json.loads(metric_path.read_text(encoding="utf-8")))
            if completed_checkpoint(run_spec, fold):
                prediction_frames.append(pd.read_parquet(prediction_path))
    metrics = pd.DataFrame(metric_rows)
    completed = metrics[metrics["status"] == "completed"].copy()
    if completed.empty:
        raise RuntimeError("No comparison run completed successfully.")
    rows: list[dict[str, object]] = []
    for (run_id, model, feature_set_id), group in completed.groupby(
            ["run_id", "model", "feature_set_id"], sort=False):
        row: dict[str, object] = {
            "run_id": run_id, "model": model,
            "feature_set_id": feature_set_id,
            "raw_group": (group["raw_group"].dropna().iloc[0]
                          if group["raw_group"].notna().any() else None),
            "feature_count": int(group["feature_count"].max()),
            "completed_folds": int(group["fold"].nunique()),
        }
        for metric in SUMMARY_METRICS:
            values = pd.to_numeric(group[metric], errors="coerce")
            row[f"mean_{metric}"] = float(values.mean())
            row[f"std_{metric}"] = float(values.std(ddof=0))
            row[f"min_{metric}"] = float(values.min())
        row["total_fit_seconds"] = float(group["fit_seconds"].sum())
        row["total_predict_seconds"] = float(group["predict_seconds"].sum())
        rows.append(row)
    summary = pd.DataFrame(rows)
    delta_metrics = [
        "mean_average_precision", "mean_roc_auc", "min_average_precision",
        "std_average_precision", "std_roc_auc", "mean_brier_score",
        "mean_log_loss", "total_fit_seconds", "total_predict_seconds",
    ]
    for metric in delta_metrics:
        summary[f"delta_vs_same_model_common__{metric}"] = np.nan
    for model in TREE_MODELS:
        baseline = summary[(summary["model"] == model)
                           & (summary["feature_set_id"] == "common_baseline")]
        if len(baseline) != 1:
            continue
        baseline_row = baseline.iloc[0]
        model_rows = summary["model"] == model
        for metric in delta_metrics:
            column = f"delta_vs_same_model_common__{metric}"
            summary.loc[model_rows, column] = (
                summary.loc[model_rows, metric] - float(baseline_row[metric]))
    order = {spec.run_id: index for index, spec in enumerate(run_specs)}
    summary["display_order"] = summary["run_id"].map(order)
    summary = summary.sort_values("display_order").drop(columns="display_order")
    predictions = pd.concat(prediction_frames, ignore_index=True)
    return metrics, summary, predictions


def build_industry_metrics(predictions: pd.DataFrame,
                           industry_by_row: pd.Series) -> pd.DataFrame:
    work = predictions.merge(
        industry_by_row.rename("서비스_업종_코드"), left_on="stage4_row_id",
        right_index=True, how="left", validate="many_to_one")
    rows = []
    keys = ["run_id", "model", "feature_set_id", "서비스_업종_코드"]
    for values, group in work.groupby(keys, observed=True, sort=False):
        target = group["target"].to_numpy(dtype="int8")
        probability = group["probability"].to_numpy(dtype="float64")
        prediction = (probability >= 0.5).astype("int8")
        both_classes = np.unique(target).size == 2
        rows.append({
            "run_id": values[0], "model": values[1],
            "feature_set_id": values[2], "서비스_업종_코드": values[3],
            "rows": len(group), "positive_rate": float(target.mean()),
            "average_precision": (float(average_precision_score(target, probability))
                                  if both_classes else np.nan),
            "roc_auc": (float(roc_auc_score(target, probability))
                        if both_classes else np.nan),
            "precision_at_0_5": float(precision_score(target, prediction,
                                                       zero_division=0)),
            "recall_at_0_5": float(recall_score(target, prediction,
                                                 zero_division=0)),
            "f1_at_0_5": float(f1_score(target, prediction, zero_division=0)),
            "predicted_positive_rate_at_0_5": float(prediction.mean()),
        })
    return pd.DataFrame(rows)


def write_report(summary: pd.DataFrame, failures: pd.DataFrame,
                 planned_variants: int) -> None:
    table = []
    for row in summary.itertuples(index=False):
        delta_ap = getattr(row, "delta_vs_same_model_common__mean_average_precision")
        delta_auc = getattr(row, "delta_vs_same_model_common__mean_roc_auc")
        table.append(
            f"| {row.model} | {row.feature_set_id} | {int(row.completed_folds)}/4 | "
            f"{int(row.feature_count)} | {row.mean_average_precision:.4f} | "
            f"{row.mean_roc_auc:.4f} | {row.min_average_precision:.4f} | "
            f"{row.std_average_precision:.4f} | {row.mean_brier_score:.4f} | "
            f"{row.mean_log_loss:.4f} | "
            f"{'-' if pd.isna(delta_ap) else f'{delta_ap:+.4f}'} | "
            f"{'-' if pd.isna(delta_auc) else f'{delta_auc:+.4f}'} | "
            f"{row.total_fit_seconds:.1f} |")
    lines = [
        "# Stage 5 전체 무튜닝 비교", "",
        f"- 계획 변형: {planned_variants}개, 완료 변형: {int((summary['completed_folds'] == 4).sum())}개",
        "- 분할: Stage 4에서 고정한 4개 시간순 expanding-window Fold",
        "- 전처리: 각 Fold Train에만 Fit",
        "- 비교 정책: 사전 숫자 컷과 자동 순위 없이 모든 계획 결과를 공개한 뒤 종합 판단",
        "- 공동 핵심 지표: AUPRC/AP와 AUROC",
        "- 보조 관찰: 최악 Fold AUPRC, Fold 표준편차, Brier Score, Log Loss, 학습·추론 시간",
        "- F2와 임계값 0.5 지표: 참고값이며 후보 선택 자동 규칙에 사용하지 않음",
        "- 2025 잠긴 테스트: 미접근", "",
        "## Feature-set 해석", "",
        "- Feature-set은 서로 다른 표본 데이터셋이 아니라 동일한 개발 행에 적용하는 열 조합이다. Target과 4개 Fold는 모든 실행에서 동일하다.",
        "- 공통 197개에도 인구 총계·구성비·인구 간 비율·점포당·면적당 지표가 포함된다. 트리 Ablation은 성별·연령별 원시 절대값 한 묶음만 독립적으로 추가한다.",
        "- 실제 7개 Feature-set의 정확한 열 목록과 SHA-256은 `reports/stage5/feature_sets.json`에 기록했다.", "",
        "| 모델 | Feature set | 완료 Fold | Feature 수 | 평균 AUPRC | 평균 AUROC | 최악 Fold AUPRC | AUPRC 표준편차 | 평균 Brier | 평균 Log Loss | 기준선 대비 AUPRC | 기준선 대비 AUROC | 총 학습초 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        *table, "", "## 의사결정 상태", "",
        "자동 유지·탈락 또는 상위 3개 선택을 수행하지 않았다. 전체 결과와 모델별 기준선 대비 차이를 사용자와 종합 검토한 뒤 Optuna 후보를 확정한다.", "",
    ]
    if not failures.empty:
        lines.extend(["## 실패 기록", "", *[
            f"- {row.run_id} Fold {int(row.fold)}: {row.error_type} — {row.error}"
            for row in failures.itertuples(index=False)], ""])
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main(validate_only: bool = False) -> None:
    config, development_path, fold_path, original_columns = load_contract()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    jobs = max(1, min(int(config["screen_budget"]["max_parallel_cpu_threads"]),
                      max(1, (os.cpu_count() or 2) - 1)))
    schema = pq.ParquetFile(development_path).schema_arrow
    type_by_column = {field.name: field.type for field in schema}
    original_categorical = [column for column in original_columns
                            if pa.types.is_string(type_by_column[column])]
    frame = load_development_compressed(development_path, original_columns,
                                        original_categorical)
    if len(frame) != 222_973:
        raise RuntimeError("Unexpected Stage 4 development row count.")
    if not frame["stage4_row_id"].is_unique or frame["stage4_row_id"].isna().any():
        raise RuntimeError("Stage 4 row IDs must be unique and non-null.")
    frame = frame.set_index("stage4_row_id", drop=False)
    target = frame[TARGET].astype("int8")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", pd.errors.PerformanceWarning)
        enriched, _ = build_stage45_features(frame[original_columns])
    contract_rows = read_contract_rows(FEATURE_CONTRACT_PATH)
    feature_sets = build_feature_set_specs(contract_rows, enriched.columns)
    write_feature_set_manifest(FEATURE_SET_MANIFEST_PATH, feature_sets,
                               FEATURE_CONTRACT_PATH.relative_to(PROJECT_ROOT))
    run_specs = build_run_specs(feature_sets)
    union_columns = list(dict.fromkeys(
        column for spec in feature_sets.values() for column in spec.columns))
    features = enriched.loc[:, union_columns].copy()
    industry_by_row = frame["서비스_업종_코드"].astype("string")
    del enriched, frame
    gc.collect()
    categorical_columns = [
        column for column in union_columns
        if isinstance(features[column].dtype, pd.CategoricalDtype)
        or pd.api.types.is_string_dtype(features[column].dtype)
        or pd.api.types.is_object_dtype(features[column].dtype)]
    numeric_columns = [column for column in union_columns
                       if column not in categorical_columns]
    for column in categorical_columns:
        if not isinstance(features[column].dtype, pd.CategoricalDtype):
            features[column] = features[column].astype("category")
    if validate_only:
        print(json.dumps({
            "status": "validation_passed",
            "rows": len(features),
            "union_feature_count": len(union_columns),
            "categorical_feature_count": len(categorical_columns),
            "planned_variants": len(run_specs),
            "feature_set_counts": {
                feature_set_id: len(spec.columns)
                for feature_set_id, spec in feature_sets.items()
            },
            "locked_test_opened": False,
        }, ensure_ascii=False), flush=True)
        return
    membership = pd.read_parquet(fold_path)
    print(f"START rows={len(features)} union_features={len(union_columns)} "
          f"categorical={len(categorical_columns)} variants={len(run_specs)} "
          f"jobs={jobs}", flush=True)
    for fold in range(1, 5):
        if all(completed_checkpoint(run_spec, fold) for run_spec in run_specs):
            print(f"SKIP fold={fold} all_variants_completed", flush=True)
            continue
        train_ids = membership.loc[
            (membership["fold"] == fold) & (membership["partition"] == "train"),
            "stage4_row_id"].to_numpy(dtype="int64")
        validation_ids = membership.loc[
            (membership["fold"] == fold)
            & (membership["partition"] == "validation"),
            "stage4_row_id"].to_numpy(dtype="int64")
        train_frame = features.loc[train_ids]
        validation_frame = features.loc[validation_ids]
        train_target = target.loc[train_ids].to_numpy(dtype="int8")
        validation_target = target.loc[validation_ids].to_numpy(dtype="int8")
        transform_started = time.perf_counter()
        union_train, union_validation, feature_indices = transform_fold_union(
            train_frame, validation_frame, numeric_columns, categorical_columns)
        print(f"TRANSFORM fold={fold} train={union_train.shape} "
              f"validation={union_validation.shape} "
              f"seconds={time.perf_counter()-transform_started:.1f}", flush=True)
        active_feature_set_id = None
        selected_train = selected_validation = None
        for run_spec in run_specs:
            feature_spec = feature_sets.get(run_spec.feature_set_id)
            needs_sparse = run_spec.model not in {"dummy_prior", "catboost"}
            if needs_sparse and run_spec.feature_set_id != active_feature_set_id:
                if selected_train is not None:
                    del selected_train, selected_validation
                    gc.collect()
                indices = indices_for_feature_set(feature_spec, feature_indices)
                selected_train = union_train[:, indices]
                selected_validation = union_validation[:, indices]
                active_feature_set_id = run_spec.feature_set_id
            process_run(
                run_spec, fold, feature_spec, train_target, validation_target,
                validation_ids, selected_train if needs_sparse else None,
                selected_validation if needs_sparse else None, train_frame,
                validation_frame, categorical_columns, jobs, config)
            gc.collect()
        del (train_frame, validation_frame, train_target, validation_target,
             union_train, union_validation, feature_indices, selected_train,
             selected_validation)
        gc.collect()
    metrics, summary, predictions = collect_results(run_specs)
    metrics.to_csv(FOLD_METRICS_PATH, index=False, encoding="utf-8-sig")
    summary.to_csv(SUMMARY_PATH, index=False, encoding="utf-8-sig")
    predictions.to_parquet(OOF_PATH, index=False, compression="zstd")
    industry_metrics = build_industry_metrics(predictions, industry_by_row)
    industry_metrics.to_csv(INDUSTRY_METRICS_PATH, index=False, encoding="utf-8-sig")
    failures = metrics[metrics["status"] == "failed"].copy()
    write_report(summary, failures, len(run_specs))
    complete_variants = summary.loc[
        summary["completed_folds"] == 4, "run_id"].tolist()
    mandatory_passed = len(complete_variants) == len(run_specs) and failures.empty
    manifest = {
        "created_at_kst": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="minutes"),
        "status": "full_comparison_completed" if mandatory_passed else "partial",
        "selection_policy": "full_result_review_without_precommitted_numeric_cutoff",
        "planned_variants": len(run_specs), "planned_fold_runs": len(run_specs) * 4,
        "completed_variants_all_four_folds": complete_variants,
        "failed_fold_runs": int(len(failures)),
        "automatic_ranking_performed": False,
        "automatic_feature_retention_performed": False,
        "decision_status": "awaiting_user_holistic_review",
        "optuna_executed": False, "locked_test_opened": False,
        "mandatory_full_comparison_passed": bool(mandatory_passed),
        "outputs": {
            "feature_sets": str(FEATURE_SET_MANIFEST_PATH.relative_to(PROJECT_ROOT)),
            "fold_metrics": str(FOLD_METRICS_PATH.relative_to(PROJECT_ROOT)),
            "model_feature_summary": str(SUMMARY_PATH.relative_to(PROJECT_ROOT)),
            "industry_metrics": str(INDUSTRY_METRICS_PATH.relative_to(PROJECT_ROOT)),
            "oof_predictions": str(OOF_PATH.relative_to(PROJECT_ROOT)),
            "report": str(REPORT_PATH.relative_to(PROJECT_ROOT)),
        },
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    print(json.dumps({
        "status": manifest["status"], "completed_variants": len(complete_variants),
        "planned_variants": len(run_specs), "failures": len(failures),
        "decision_status": manifest["decision_status"],
    }, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    main(validate_only=args.validate_only)
