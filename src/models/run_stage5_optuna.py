"""Tune the three user-approved Stage 5 candidates with chronological CV.

The locked 2025 test is never read.  Each Optuna trial uses the same four
expanding-window folds as the untuned comparison and returns two objectives:
mean average precision (AUPRC) and mean ROC-AUC.  No scalar weighting or final
model selection is performed here.
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
import optuna
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import yaml
from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier
from scipy import sparse
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)
from xgboost import XGBClassifier

from src.features.build_stage45_features import build_stage45_features
from src.features.build_stage5_feature_sets import (
    FeatureSetSpec,
    build_feature_set_specs,
    read_contract_rows,
)
from src.models.run_stage5_base_comparison import (
    FEATURE_CONTRACT_PATH,
    RANDOM_SEED,
    TARGET,
    load_contract,
    load_development_compressed,
    transform_fold_union,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config" / "stage5.yaml"
REPORT_DIR = PROJECT_ROOT / "reports" / "stage5"
CACHE_DIR = PROJECT_ROOT / "data" / "interim" / "stage5_optuna_cache"
STUDY_DB_PATH = REPORT_DIR / "optuna_studies.db"
TRIALS_PATH = REPORT_DIR / "optuna_trials.csv"
PARETO_PATH = REPORT_DIR / "optuna_pareto_trials.csv"
REPORT_PATH = REPORT_DIR / "optuna_report.md"
MANIFEST_PATH = REPORT_DIR / "optuna_manifest.json"
BASE_SUMMARY_PATH = REPORT_DIR / "full_model_feature_summary.csv"


def now_kst() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="minutes")


def storage_url(path: Path) -> str:
    return "sqlite:///" + path.resolve().as_posix()


def load_tuning_contract() -> tuple[dict[str, Any], list[dict[str, str]], int, int]:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    status = config["status"]
    if status["optuna_candidates"] != "approved":
        raise RuntimeError("Optuna candidates are not user-approved.")
    if status["optuna_execution"] not in {"approved_to_run", "completed"}:
        raise RuntimeError("Optuna execution is not authorized.")
    optuna_config = config["optuna"]
    candidates = optuna_config["candidates"]
    expected = [
        {"model": "lightgbm", "feature_set": "common_baseline"},
        {
            "model": "xgboost",
            "feature_set": "tree_plus_transaction_count_raw_components",
        },
        {
            "model": "catboost",
            "feature_set": "tree_plus_worker_population_raw_components",
        },
    ]
    if candidates != expected:
        raise RuntimeError("Configured Optuna candidates differ from the approved top three.")
    objective = optuna_config["objective"]
    if objective["type"] != "multi_objective" or objective["scalar_weighting"]:
        raise RuntimeError("Optuna must use unweighted AUPRC/AUROC multi-objective tuning.")
    if objective["metrics"] != ["mean_average_precision", "mean_roc_auc"]:
        raise RuntimeError("Unexpected Optuna objective metrics.")
    trials = int(optuna_config["trials_per_model"])
    folds = int(optuna_config["folds_per_trial"])
    if trials != 20 or folds != 4:
        raise RuntimeError("Approved tuning budget is exactly 20 trials x 4 folds.")
    if config["data"]["locked_test_access"] != "forbidden_during_model_selection":
        raise RuntimeError("Locked-test access guard is not active.")
    return config, candidates, trials, folds


def prepare_feature_data() -> tuple[
    pd.DataFrame,
    pd.Series,
    pd.DataFrame,
    dict[str, FeatureSetSpec],
    list[str],
]:
    _, development_path, fold_path, original_columns = load_contract()
    schema = pq.ParquetFile(development_path).schema_arrow
    type_by_column = {field.name: field.type for field in schema}
    original_categorical = [
        column
        for column in original_columns
        if pa.types.is_string(type_by_column[column])
    ]
    frame = load_development_compressed(
        development_path, original_columns, original_categorical
    )
    if len(frame) != 222_973:
        raise RuntimeError(f"Unexpected development rows: {len(frame):,}")
    if not frame["stage4_row_id"].is_unique or frame["stage4_row_id"].isna().any():
        raise RuntimeError("Stage 4 row IDs must be unique and non-null.")
    frame = frame.set_index("stage4_row_id", drop=False)
    target = frame[TARGET].astype("int8")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", pd.errors.PerformanceWarning)
        enriched, _ = build_stage45_features(frame[original_columns])
    specs = build_feature_set_specs(
        read_contract_rows(FEATURE_CONTRACT_PATH), enriched.columns
    )
    configured = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))["optuna"]
    selected_ids = [item["feature_set"] for item in configured["candidates"]]
    selected_union = list(
        dict.fromkeys(
            column
            for feature_set_id in selected_ids
            for column in specs[feature_set_id].columns
        )
    )
    features = enriched.loc[:, selected_union].copy()
    categorical_columns = [
        column
        for column in selected_union
        if isinstance(features[column].dtype, pd.CategoricalDtype)
        or pd.api.types.is_string_dtype(features[column].dtype)
        or pd.api.types.is_object_dtype(features[column].dtype)
    ]
    for column in categorical_columns:
        if not isinstance(features[column].dtype, pd.CategoricalDtype):
            features[column] = features[column].astype("category")
    membership = pd.read_parquet(fold_path)
    expected_partitions = {"train", "validation"}
    if set(membership["partition"].unique()) != expected_partitions:
        raise RuntimeError("Unexpected Stage 4 fold partitions.")
    if sorted(membership["fold"].unique().tolist()) != [1, 2, 3, 4]:
        raise RuntimeError("Exactly four chronological folds are required.")
    del enriched, frame
    gc.collect()
    return features, target, membership, specs, categorical_columns


def fold_ids(membership: pd.DataFrame, fold: int) -> tuple[np.ndarray, np.ndarray]:
    train_ids = membership.loc[
        (membership["fold"] == fold) & (membership["partition"] == "train"),
        "stage4_row_id",
    ].to_numpy(dtype="int64")
    valid_ids = membership.loc[
        (membership["fold"] == fold)
        & (membership["partition"] == "validation"),
        "stage4_row_id",
    ].to_numpy(dtype="int64")
    if len(train_ids) == 0 or len(valid_ids) == 0:
        raise RuntimeError(f"Fold {fold} is empty.")
    if np.intersect1d(train_ids, valid_ids).size:
        raise RuntimeError(f"Fold {fold} Train and Validation overlap.")
    return train_ids, valid_ids


def save_csr(prefix: Path, matrix: sparse.csr_matrix) -> None:
    matrix = matrix.tocsr(copy=False)
    np.save(prefix.with_name(prefix.name + "_data.npy"), matrix.data)
    np.save(prefix.with_name(prefix.name + "_indices.npy"), matrix.indices)
    np.save(prefix.with_name(prefix.name + "_indptr.npy"), matrix.indptr)


def load_csr(prefix: Path, shape: tuple[int, int]) -> sparse.csr_matrix:
    data = np.load(prefix.with_name(prefix.name + "_data.npy"), mmap_mode="r")
    indices = np.load(prefix.with_name(prefix.name + "_indices.npy"), mmap_mode="r")
    indptr = np.load(prefix.with_name(prefix.name + "_indptr.npy"), mmap_mode="r")
    return sparse.csr_matrix((data, indices, indptr), shape=shape, copy=False)


def cache_is_valid(cache: Path, spec: FeatureSetSpec, fold: int) -> bool:
    manifest_path = cache / "manifest.json"
    required = [
        cache / f"{part}_{array}.npy"
        for part in ("train", "valid")
        for array in ("data", "indices", "indptr")
    ] + [cache / "train_target.npy", cache / "valid_target.npy"]
    if not manifest_path.exists() or not all(path.exists() for path in required):
        return False
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return (
        manifest.get("feature_set_sha256") == spec.sha256
        and manifest.get("fold") == fold
        and manifest.get("target") == TARGET
        and manifest.get("preprocessing") == "fold_train_only_v1"
    )


def build_sparse_cache(
    model: str,
    spec: FeatureSetSpec,
    features: pd.DataFrame,
    target: pd.Series,
    membership: pd.DataFrame,
    categorical_columns: list[str],
) -> list[dict[str, Any]]:
    cached_folds: list[dict[str, Any]] = []
    spec_categories = [c for c in spec.columns if c in categorical_columns]
    spec_numeric = [c for c in spec.columns if c not in spec_categories]
    for fold in range(1, 5):
        cache = CACHE_DIR / f"{model}__{spec.feature_set_id}" / f"fold{fold}"
        cache.mkdir(parents=True, exist_ok=True)
        if not cache_is_valid(cache, spec, fold):
            train_ids, valid_ids = fold_ids(membership, fold)
            train_frame = features.loc[train_ids, list(spec.columns)]
            valid_frame = features.loc[valid_ids, list(spec.columns)]
            train_matrix, valid_matrix, _ = transform_fold_union(
                train_frame, valid_frame, spec_numeric, spec_categories
            )
            train_target = target.loc[train_ids].to_numpy(dtype="int8")
            valid_target = target.loc[valid_ids].to_numpy(dtype="int8")
            save_csr(cache / "train", train_matrix)
            save_csr(cache / "valid", valid_matrix)
            np.save(cache / "train_target.npy", train_target)
            np.save(cache / "valid_target.npy", valid_target)
            (cache / "manifest.json").write_text(
                json.dumps(
                    {
                        "created_at_kst": now_kst(),
                        "model": model,
                        "feature_set": spec.feature_set_id,
                        "feature_set_sha256": spec.sha256,
                        "feature_count_source": len(spec.columns),
                        "categorical_count": len(spec_categories),
                        "fold": fold,
                        "target": TARGET,
                        "preprocessing": "fold_train_only_v1",
                        "train_shape": list(train_matrix.shape),
                        "valid_shape": list(valid_matrix.shape),
                        "locked_test_opened": False,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            del (
                train_ids,
                valid_ids,
                train_frame,
                valid_frame,
                train_matrix,
                valid_matrix,
                train_target,
                valid_target,
            )
            gc.collect()
        manifest = json.loads((cache / "manifest.json").read_text(encoding="utf-8"))
        train_shape = tuple(manifest["train_shape"])
        valid_shape = tuple(manifest["valid_shape"])
        cached_folds.append(
            {
                "fold": fold,
                "train": load_csr(cache / "train", train_shape),
                "valid": load_csr(cache / "valid", valid_shape),
                "train_target": np.load(cache / "train_target.npy", mmap_mode="r"),
                "valid_target": np.load(cache / "valid_target.npy", mmap_mode="r"),
            }
        )
    return cached_folds


def suggest_parameters(trial: optuna.Trial, model: str) -> dict[str, Any]:
    if model == "lightgbm":
        return {
            "n_estimators": trial.suggest_int("n_estimators", 150, 700, step=50),
            "learning_rate": trial.suggest_float("learning_rate", 0.015, 0.15, log=True),
            "num_leaves": trial.suggest_int("num_leaves", 15, 127),
            "max_depth": trial.suggest_categorical("max_depth", [-1, 4, 5, 6, 7, 8, 10, 12]),
            "min_child_samples": trial.suggest_int("min_child_samples", 10, 100, step=5),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
            "max_bin": trial.suggest_categorical("max_bin", [63, 127, 255]),
        }
    if model == "xgboost":
        return {
            "n_estimators": trial.suggest_int("n_estimators", 150, 700, step=50),
            "learning_rate": trial.suggest_float("learning_rate", 0.015, 0.15, log=True),
            "max_depth": trial.suggest_int("max_depth", 3, 10),
            "min_child_weight": trial.suggest_float("min_child_weight", 1.0, 20.0, log=True),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "gamma": trial.suggest_float("gamma", 0.0, 5.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 20.0, log=True),
            "max_bin": trial.suggest_categorical("max_bin", [128, 256, 512]),
        }
    if model == "catboost":
        return {
            "iterations": trial.suggest_int("iterations", 150, 550, step=50),
            "depth": trial.suggest_int("depth", 4, 9),
            "learning_rate": trial.suggest_float("learning_rate", 0.015, 0.15, log=True),
            "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1.0, 30.0, log=True),
            "random_strength": trial.suggest_float("random_strength", 1e-3, 10.0, log=True),
            "bagging_temperature": trial.suggest_float("bagging_temperature", 0.0, 5.0),
            "border_count": trial.suggest_categorical("border_count", [64, 128, 254]),
            "leaf_estimation_iterations": trial.suggest_int("leaf_estimation_iterations", 1, 10),
        }
    raise KeyError(model)


def build_sparse_estimator(model: str, params: dict[str, Any], jobs: int):
    if model == "lightgbm":
        return LGBMClassifier(
            **params,
            objective="binary",
            random_state=RANDOM_SEED,
            n_jobs=jobs,
            verbosity=-1,
        )
    if model == "xgboost":
        return XGBClassifier(
            **params,
            objective="binary:logistic",
            eval_metric="logloss",
            tree_method="hist",
            random_state=RANDOM_SEED,
            n_jobs=jobs,
            verbosity=0,
        )
    raise KeyError(model)


def probability_metrics(target: np.ndarray, probability: np.ndarray) -> dict[str, float]:
    probability = np.clip(np.asarray(probability, dtype="float64"), 1e-7, 1 - 1e-7)
    return {
        "average_precision": float(average_precision_score(target, probability)),
        "roc_auc": float(roc_auc_score(target, probability)),
        "brier_score": float(brier_score_loss(target, probability)),
        "log_loss": float(log_loss(target, probability, labels=[0, 1])),
    }


def record_trial_metrics(
    trial: optuna.Trial, fold_metrics: list[dict[str, float]]
) -> tuple[float, float]:
    average_precision = np.array(
        [row["average_precision"] for row in fold_metrics], dtype="float64"
    )
    roc_auc = np.array([row["roc_auc"] for row in fold_metrics], dtype="float64")
    brier = np.array([row["brier_score"] for row in fold_metrics], dtype="float64")
    losses = np.array([row["log_loss"] for row in fold_metrics], dtype="float64")
    fit_seconds = np.array([row["fit_seconds"] for row in fold_metrics], dtype="float64")
    attributes = {
        "fold_metrics": fold_metrics,
        "mean_average_precision": float(average_precision.mean()),
        "std_average_precision": float(average_precision.std(ddof=0)),
        "worst_fold_average_precision": float(average_precision.min()),
        "mean_roc_auc": float(roc_auc.mean()),
        "std_roc_auc": float(roc_auc.std(ddof=0)),
        "worst_fold_roc_auc": float(roc_auc.min()),
        "mean_brier_score": float(brier.mean()),
        "mean_log_loss": float(losses.mean()),
        "total_fit_seconds": float(fit_seconds.sum()),
    }
    for key, value in attributes.items():
        trial.set_user_attr(key, value)
    return attributes["mean_average_precision"], attributes["mean_roc_auc"]


def sparse_objective(
    model: str, cached_folds: list[dict[str, Any]], jobs: int
):
    def objective(trial: optuna.Trial) -> tuple[float, float]:
        params = suggest_parameters(trial, model)
        results: list[dict[str, float]] = []
        for cached in cached_folds:
            estimator = build_sparse_estimator(model, params, jobs)
            started = time.perf_counter()
            estimator.fit(cached["train"], cached["train_target"])
            fit_seconds = time.perf_counter() - started
            probability = estimator.predict_proba(cached["valid"])[:, 1]
            metrics = probability_metrics(cached["valid_target"], probability)
            metrics.update({"fold": int(cached["fold"]), "fit_seconds": fit_seconds})
            results.append(metrics)
            del estimator, probability
            gc.collect()
        return record_trial_metrics(trial, results)

    return objective


def catboost_objective(
    spec: FeatureSetSpec,
    features: pd.DataFrame,
    target: pd.Series,
    membership: pd.DataFrame,
    categorical_columns: list[str],
    jobs: int,
):
    categories = [column for column in spec.columns if column in categorical_columns]
    source = features.loc[:, list(spec.columns)].copy()
    for column in categories:
        source[column] = source[column].astype("string").fillna("__MISSING__").astype(str)

    def objective(trial: optuna.Trial) -> tuple[float, float]:
        params = suggest_parameters(trial, "catboost")
        results: list[dict[str, float]] = []
        for fold in range(1, 5):
            train_ids, valid_ids = fold_ids(membership, fold)
            train_frame = source.loc[train_ids]
            valid_frame = source.loc[valid_ids]
            train_target = target.loc[train_ids].to_numpy(dtype="int8")
            valid_target = target.loc[valid_ids].to_numpy(dtype="int8")
            estimator = CatBoostClassifier(
                **params,
                loss_function="Logloss",
                random_seed=RANDOM_SEED,
                thread_count=jobs,
                verbose=False,
                allow_writing_files=False,
            )
            started = time.perf_counter()
            estimator.fit(train_frame, train_target, cat_features=categories)
            fit_seconds = time.perf_counter() - started
            probability = estimator.predict_proba(valid_frame)[:, 1]
            metrics = probability_metrics(valid_target, probability)
            metrics.update({"fold": fold, "fit_seconds": fit_seconds})
            results.append(metrics)
            del (
                train_ids,
                valid_ids,
                train_frame,
                valid_frame,
                train_target,
                valid_target,
                estimator,
                probability,
            )
            gc.collect()
        return record_trial_metrics(trial, results)

    return objective, source


def study_name(model: str, feature_set: str) -> str:
    return f"stage5__{model}__{feature_set}__v1"


def complete_trial_count(study: optuna.study.Study) -> int:
    return sum(trial.state == optuna.trial.TrialState.COMPLETE for trial in study.trials)


def create_study(model: str, feature_set: str, seed_offset: int) -> optuna.study.Study:
    sampler = optuna.samplers.TPESampler(
        seed=RANDOM_SEED + seed_offset, multivariate=True
    )
    study = optuna.create_study(
        study_name=study_name(model, feature_set),
        storage=storage_url(STUDY_DB_PATH),
        sampler=sampler,
        directions=["maximize", "maximize"],
        load_if_exists=True,
    )
    study.set_user_attr("model", model)
    study.set_user_attr("feature_set", feature_set)
    study.set_user_attr("objective_0", "mean_average_precision")
    study.set_user_attr("objective_1", "mean_roc_auc")
    study.set_user_attr("folds", 4)
    study.set_user_attr("locked_test_opened", False)
    return study


def trial_row(study: optuna.study.Study, trial: optuna.trial.FrozenTrial) -> dict[str, Any]:
    values = trial.values or [np.nan, np.nan]
    row: dict[str, Any] = {
        "study_name": study.study_name,
        "model": study.user_attrs["model"],
        "feature_set": study.user_attrs["feature_set"],
        "trial_number": trial.number,
        "state": trial.state.name,
        "mean_average_precision": values[0] if len(values) > 0 else np.nan,
        "mean_roc_auc": values[1] if len(values) > 1 else np.nan,
        "std_average_precision": trial.user_attrs.get("std_average_precision"),
        "worst_fold_average_precision": trial.user_attrs.get("worst_fold_average_precision"),
        "std_roc_auc": trial.user_attrs.get("std_roc_auc"),
        "worst_fold_roc_auc": trial.user_attrs.get("worst_fold_roc_auc"),
        "mean_brier_score": trial.user_attrs.get("mean_brier_score"),
        "mean_log_loss": trial.user_attrs.get("mean_log_loss"),
        "total_fit_seconds": trial.user_attrs.get("total_fit_seconds"),
        "params_json": json.dumps(trial.params, ensure_ascii=False, sort_keys=True),
        "fold_metrics_json": json.dumps(
            trial.user_attrs.get("fold_metrics", []), ensure_ascii=False
        ),
    }
    for key, value in sorted(trial.params.items()):
        row[f"param_{key}"] = value
    return row


def format_metric(value: Any) -> str:
    return "-" if value is None or pd.isna(value) else f"{float(value):.4f}"


def write_outputs(
    studies: list[optuna.study.Study], candidates: list[dict[str, str]], trials_per_model: int
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    pareto_keys: set[tuple[str, int]] = set()
    for study in studies:
        for trial in study.best_trials:
            pareto_keys.add((study.study_name, trial.number))
        rows.extend(trial_row(study, trial) for trial in study.trials)
    trials = pd.DataFrame(rows)
    if not trials.empty:
        trials["is_pareto"] = [
            (study, number) in pareto_keys
            for study, number in zip(trials["study_name"], trials["trial_number"])
        ]
        trials.to_csv(TRIALS_PATH, index=False, encoding="utf-8-sig")
        pareto = trials[trials["is_pareto"]].copy()
        pareto.to_csv(PARETO_PATH, index=False, encoding="utf-8-sig")
    else:
        pareto = pd.DataFrame()

    base = pd.read_csv(BASE_SUMMARY_PATH, encoding="utf-8-sig")
    lines = [
        "# Stage 5 Optuna 다목적 튜닝 결과",
        "",
        f"- 생성 시각: {now_kst()}",
        "- 범위: 사용자 승인 후보 3개, 후보별 20회, Trial마다 고정 4개 시간순 Fold",
        "- 목적함수: 평균 AUPRC와 평균 AUROC 동시 최대화(단일 가중합 없음)",
        "- 안정성·확률 품질: 최악 Fold, Fold 표준편차, Brier Score, Log Loss를 함께 공개",
        "- 2025 잠긴 테스트: 접근하지 않음",
        "- 이 보고서는 Pareto 결과를 공개하며 최종 모델이나 대표 Trial을 자동 확정하지 않음",
        "",
        "## 후보별 완료 상태",
        "",
        "| 모델 | Feature-set | 무튜닝 AP | 무튜닝 AUC | 완료 Trial | Pareto Trial |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    by_name = {study.study_name: study for study in studies}
    for candidate in candidates:
        model = candidate["model"]
        feature_set = candidate["feature_set"]
        study = by_name[study_name(model, feature_set)]
        base_row = base[(base["model"] == model) & (base["feature_set_id"] == feature_set)]
        if len(base_row) != 1:
            raise RuntimeError(f"Missing untuned baseline for {model}/{feature_set}.")
        lines.append(
            f"| {model} | `{feature_set}` | "
            f"{float(base_row.iloc[0]['mean_average_precision']):.4f} | "
            f"{float(base_row.iloc[0]['mean_roc_auc']):.4f} | "
            f"{complete_trial_count(study)} / {trials_per_model} | {len(study.best_trials)} |"
        )
    lines.extend(
        [
            "",
            "## Pareto Trial 전체",
            "",
            "어느 한 지표를 높이려면 다른 지표가 낮아지는 비지배 해만 표시한다. "
            "아래 표의 수치와 전체 CSV를 함께 보고 대표 설정을 결정한다.",
            "",
            "| 모델 | Trial | 평균 AP | 평균 AUC | 최악 Fold AP | AP 표준편차 | Brier | Log Loss | Fit 초 |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    if pareto.empty:
        lines.append("| 완료 결과 없음 | - | - | - | - | - | - | - | - |")
    else:
        ordered = pareto.sort_values(
            ["model", "mean_average_precision", "mean_roc_auc"],
            ascending=[True, False, False],
        )
        for row in ordered.itertuples(index=False):
            lines.append(
                f"| {row.model} | {int(row.trial_number)} | "
                f"{format_metric(row.mean_average_precision)} | {format_metric(row.mean_roc_auc)} | "
                f"{format_metric(row.worst_fold_average_precision)} | "
                f"{format_metric(row.std_average_precision)} | "
                f"{format_metric(row.mean_brier_score)} | {format_metric(row.mean_log_loss)} | "
                f"{float(row.total_fit_seconds):.1f} |"
            )
    lines.extend(
        [
            "",
            "## 하이퍼파라미터 확인 방법",
            "",
            "- 모든 Trial의 파라미터와 Fold별 지표: `optuna_trials.csv`",
            "- Pareto Trial만 모은 표: `optuna_pareto_trials.csv`",
            "- 중단 후 재개 가능한 원본 Study: `optuna_studies.db`",
            "- 다음 단계: 사용자와 모델별 대표 Trial을 종합 선택한 뒤 동일 OOF 예측으로 개별 모델, Soft Voting, Stacking을 비교",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")

    counts = {
        study.study_name: complete_trial_count(study)
        for study in studies
    }
    all_complete = len(studies) == len(candidates) and all(
        counts.get(study_name(item["model"], item["feature_set"]), 0) >= trials_per_model
        for item in candidates
    )
    manifest = {
        "created_at_kst": now_kst(),
        "status": "completed" if all_complete else "partial",
        "candidates": candidates,
        "trials_per_model": trials_per_model,
        "folds_per_trial": 4,
        "maximum_model_fits": len(candidates) * trials_per_model * 4,
        "completed_trial_counts": counts,
        "objective": ["mean_average_precision", "mean_roc_auc"],
        "scalar_weighting_performed": False,
        "automatic_representative_trial_selection": False,
        "automatic_final_model_selection": False,
        "locked_test_opened": False,
        "outputs": {
            "all_trials": str(TRIALS_PATH.relative_to(PROJECT_ROOT)),
            "pareto_trials": str(PARETO_PATH.relative_to(PROJECT_ROOT)),
            "report": str(REPORT_PATH.relative_to(PROJECT_ROOT)),
            "study_storage": str(STUDY_DB_PATH.relative_to(PROJECT_ROOT)),
        },
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def main(validate_only: bool = False) -> None:
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    config, candidates, trials_per_model, folds = load_tuning_contract()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    features, target, membership, specs, categorical_columns = prepare_feature_data()
    for candidate in candidates:
        if candidate["feature_set"] not in specs:
            raise RuntimeError(f"Unknown feature set: {candidate['feature_set']}")
    jobs = max(
        1,
        min(
            int(config["screen_budget"]["max_parallel_cpu_threads"]),
            max(1, (os.cpu_count() or 2) - 1),
        ),
    )
    if validate_only:
        print(
            json.dumps(
                {
                    "status": "validation_passed",
                    "rows": len(features),
                    "candidate_count": len(candidates),
                    "trials_per_model": trials_per_model,
                    "folds_per_trial": folds,
                    "maximum_model_fits": len(candidates) * trials_per_model * folds,
                    "candidate_feature_counts": {
                        f"{item['model']}__{item['feature_set']}": len(
                            specs[item["feature_set"]].columns
                        )
                        for item in candidates
                    },
                    "locked_test_opened": False,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        return

    studies: list[optuna.study.Study] = []
    for index, candidate in enumerate(candidates):
        model = candidate["model"]
        feature_set = candidate["feature_set"]
        spec = specs[feature_set]
        study = create_study(model, feature_set, index * 1000)
        studies.append(study)
        remaining = max(0, trials_per_model - complete_trial_count(study))
        if remaining == 0:
            continue
        if model in {"lightgbm", "xgboost"}:
            cached_folds = build_sparse_cache(
                model,
                spec,
                features,
                target,
                membership,
                categorical_columns,
            )
            objective = sparse_objective(model, cached_folds, jobs)
            study.optimize(objective, n_trials=remaining, n_jobs=1, gc_after_trial=True)
            del objective, cached_folds
        else:
            objective, source = catboost_objective(
                spec,
                features,
                target,
                membership,
                categorical_columns,
                jobs,
            )
            study.optimize(objective, n_trials=remaining, n_jobs=1, gc_after_trial=True)
            del objective, source
        gc.collect()
        write_outputs(studies, candidates[: len(studies)], trials_per_model)

    manifest = write_outputs(studies, candidates, trials_per_model)
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "completed_trial_counts": manifest["completed_trial_counts"],
                "locked_test_opened": False,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    main(validate_only=args.validate_only)
