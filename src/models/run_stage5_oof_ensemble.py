"""Build leakage-safe OOF predictions for selected tuned models and ensembles.

The script is intended to be run by the user in a terminal.  It prints every
model/Fold step to the console, writes the same messages to a UTF-8 log, keeps
a machine-readable progress file, and resumes from per-task checkpoints.
Only Stage 4 development data is read; the locked 2025 test is never opened.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml
from catboost import CatBoostClassifier
from sklearn.linear_model import LogisticRegression

from src.models.run_stage5_base_comparison import (
    RANDOM_SEED,
    TARGET,
    build_industry_metrics,
    compute_metrics,
    transform_fold_union,
)
from src.models.run_stage5_optuna import (
    build_sparse_estimator,
    prepare_feature_data,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config" / "stage5.yaml"
REPORT_DIR = PROJECT_ROOT / "reports" / "stage5"
TRIALS_PATH = REPORT_DIR / "optuna_trials.csv"
CHECKPOINT_DIR = REPORT_DIR / "ensemble_checkpoints"
LOG_PATH = REPORT_DIR / "ensemble_run.log"
PROGRESS_PATH = REPORT_DIR / "ensemble_progress.json"
PREDICTIONS_PATH = REPORT_DIR / "selected_oof_predictions.parquet"
FOLD_METRICS_PATH = REPORT_DIR / "selected_oof_fold_metrics.csv"
SUMMARY_PATH = REPORT_DIR / "selected_oof_summary.csv"
INDUSTRY_PATH = REPORT_DIR / "selected_oof_industry_metrics.csv"
REPORT_PATH = REPORT_DIR / "selected_oof_report.md"
MANIFEST_PATH = REPORT_DIR / "selected_oof_manifest.json"

PROBABILITY_COLUMNS = ["lightgbm", "xgboost", "catboost"]


@dataclass(frozen=True)
class Candidate:
    model: str
    feature_set_id: str
    trial_number: int
    params: dict[str, Any]

    @property
    def run_id(self) -> str:
        return f"{self.model}__trial{self.trial_number}"

    @property
    def params_sha256(self) -> str:
        payload = json.dumps(self.params, sort_keys=True).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class SplitSpec:
    kind: str
    outer_fold: int
    train_ids: np.ndarray
    validation_ids: np.ndarray
    validation_period: int | None = None

    @property
    def label(self) -> str:
        if self.kind == "outer":
            return f"Outer Fold {self.outer_fold}"
        return f"Outer Fold {self.outer_fold} / Inner {self.validation_period}"


def now_kst() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")


def configure_logger() -> logging.Logger:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("stage5_oof_ensemble")
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


def shift_quarter(period: int, quarters: int) -> int:
    year, quarter = divmod(int(period), 10)
    if quarter not in {1, 2, 3, 4}:
        raise ValueError(f"Invalid YYYYQ period code: {period}")
    ordinal = year * 4 + quarter - 1 + quarters
    shifted_year, shifted_zero_quarter = divmod(ordinal, 4)
    return shifted_year * 10 + shifted_zero_quarter + 1


def load_execution_contract() -> tuple[dict[str, Any], list[Candidate]]:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    status = config["status"]
    if status.get("representative_trials") != "approved":
        raise RuntimeError("Representative Trials are not user-approved.")
    if status.get("ensemble_execution") not in {
        "approved_for_user_terminal_run",
        "completed",
    }:
        raise RuntimeError("OOF ensemble execution is not authorized.")
    ensemble = config["oof_ensemble"]
    if ensemble["locked_test_access"] != "forbidden":
        raise RuntimeError("Locked-test guard is not active.")
    configured = ensemble["selected_trials"]
    expected = [
        {"model": "lightgbm", "feature_set": "common_baseline", "trial_number": 10},
        {
            "model": "xgboost",
            "feature_set": "tree_plus_transaction_count_raw_components",
            "trial_number": 16,
        },
        {
            "model": "catboost",
            "feature_set": "tree_plus_worker_population_raw_components",
            "trial_number": 18,
        },
    ]
    if configured != expected:
        raise RuntimeError("Configured representative Trials differ from user approval.")
    trials = pd.read_csv(TRIALS_PATH, encoding="utf-8-sig")
    candidates: list[Candidate] = []
    for item in configured:
        match = trials[
            (trials["model"] == item["model"])
            & (trials["feature_set"] == item["feature_set"])
            & (trials["trial_number"] == item["trial_number"])
            & (trials["state"] == "COMPLETE")
        ]
        if len(match) != 1:
            raise RuntimeError(f"Approved Trial is missing or duplicated: {item}")
        candidates.append(
            Candidate(
                model=item["model"],
                feature_set_id=item["feature_set"],
                trial_number=int(item["trial_number"]),
                params=json.loads(match.iloc[0]["params_json"]),
            )
        )
    return config, candidates


def outer_splits(membership: pd.DataFrame) -> list[SplitSpec]:
    splits: list[SplitSpec] = []
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
        if not len(train_ids) or not len(validation_ids):
            raise RuntimeError(f"Outer Fold {fold} is empty.")
        if np.intersect1d(train_ids, validation_ids).size:
            raise RuntimeError(f"Outer Fold {fold} Train and Validation overlap.")
        splits.append(SplitSpec("outer", fold, train_ids, validation_ids))
    return splits


def inner_splits(outer: SplitSpec, periods: pd.Series, count: int = 3) -> list[SplitSpec]:
    outer_periods = periods.loc[outer.train_ids]
    validation_periods = sorted(int(value) for value in outer_periods.unique())[-count:]
    if len(validation_periods) != count:
        raise RuntimeError(f"{outer.label} lacks {count} inner periods.")
    splits: list[SplitSpec] = []
    for validation_period in validation_periods:
        maximum_train_period = shift_quarter(validation_period, -2)
        train_ids = outer_periods.index[
            outer_periods.to_numpy(dtype="int32") <= maximum_train_period
        ].to_numpy(dtype="int64")
        validation_ids = outer_periods.index[
            outer_periods.to_numpy(dtype="int32") == validation_period
        ].to_numpy(dtype="int64")
        if not len(train_ids) or not len(validation_ids):
            raise RuntimeError(
                f"Invalid inner split: outer={outer.outer_fold}, period={validation_period}"
            )
        if int(periods.loc[train_ids].max()) > maximum_train_period:
            raise RuntimeError("Inner purge rule failed.")
        if np.intersect1d(train_ids, validation_ids).size:
            raise RuntimeError("Inner Train and Validation overlap.")
        splits.append(
            SplitSpec(
                "inner",
                outer.outer_fold,
                train_ids,
                validation_ids,
                validation_period,
            )
        )
    return splits


def checkpoint_stem(split: SplitSpec, run_id: str) -> str:
    if split.kind == "outer":
        return f"outer__fold{split.outer_fold}__{run_id}"
    return (
        f"inner__outer{split.outer_fold}__period{split.validation_period}__{run_id}"
    )


def checkpoint_paths(stem: str) -> tuple[Path, Path]:
    return CHECKPOINT_DIR / f"{stem}.json", CHECKPOINT_DIR / f"{stem}.parquet"


def checkpoint_valid(
    stem: str,
    run_id: str,
    feature_set_sha256: str | None,
    params_sha256: str | None,
) -> bool:
    metric_path, prediction_path = checkpoint_paths(stem)
    if not metric_path.exists() or not prediction_path.exists():
        return False
    try:
        metric = json.loads(metric_path.read_text(encoding="utf-8"))
        columns = pq.ParquetFile(prediction_path).schema_arrow.names
    except Exception:
        return False
    expected_columns = ["stage4_row_id", "target", "probability"]
    return (
        metric.get("status") == "completed"
        and metric.get("run_id") == run_id
        and metric.get("feature_set_sha256") == feature_set_sha256
        and metric.get("params_sha256") == params_sha256
        and columns == expected_columns
    )


def write_checkpoint(
    stem: str,
    metric: dict[str, Any],
    row_ids: np.ndarray,
    target: np.ndarray,
    probability: np.ndarray,
) -> None:
    metric_path, prediction_path = checkpoint_paths(stem)
    temporary_metric = metric_path.with_suffix(".json.tmp")
    temporary_prediction = prediction_path.with_suffix(".parquet.tmp")
    pd.DataFrame(
        {
            "stage4_row_id": row_ids.astype("int64"),
            "target": target.astype("int8"),
            "probability": np.asarray(probability, dtype="float32"),
        }
    ).to_parquet(temporary_prediction, index=False, compression="zstd")
    temporary_metric.write_text(
        json.dumps(metric, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary_prediction.replace(prediction_path)
    temporary_metric.replace(metric_path)


class Progress:
    def __init__(self, planned_steps: int, logger: logging.Logger):
        self.planned_steps = planned_steps
        self.completed_steps = 0
        self.completed_fits = 0
        self.logger = logger
        self.started_at = now_kst()
        self.write("running", "초기화")

    def write(self, status: str, current: str, error: str | None = None) -> None:
        payload = {
            "status": status,
            "started_at_kst": self.started_at,
            "updated_at_kst": now_kst(),
            "planned_steps": self.planned_steps,
            "completed_steps": self.completed_steps,
            "progress_percent": round(100 * self.completed_steps / self.planned_steps, 1),
            "new_model_fits_this_run": self.completed_fits,
            "planned_model_fit_steps": 48,
            "current": current,
            "error": error,
            "locked_test_opened": False,
            "log_file": str(LOG_PATH.relative_to(PROJECT_ROOT)),
        }
        temporary = PROGRESS_PATH.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(PROGRESS_PATH)

    def start(self, label: str) -> None:
        self.write("running", label)
        self.logger.info(
            "START step=%d/%d (%.1f%%) | %s",
            self.completed_steps + 1,
            self.planned_steps,
            100 * self.completed_steps / self.planned_steps,
            label,
        )

    def done(self, label: str, was_fit: bool = False, skipped: bool = False) -> None:
        self.completed_steps += 1
        if was_fit:
            self.completed_fits += 1
        self.write("running", label)
        self.logger.info(
            "%s step=%d/%d (%.1f%%) | %s",
            "SKIP" if skipped else "DONE",
            self.completed_steps,
            self.planned_steps,
            100 * self.completed_steps / self.planned_steps,
            label,
        )


def fit_candidate(
    candidate: Candidate,
    split: SplitSpec,
    features: pd.DataFrame,
    target: pd.Series,
    feature_spec: Any,
    categorical_columns: list[str],
    jobs: int,
    logger: logging.Logger,
) -> dict[str, Any]:
    stem = checkpoint_stem(split, candidate.run_id)
    if checkpoint_valid(
        stem, candidate.run_id, feature_spec.sha256, candidate.params_sha256
    ):
        return json.loads(checkpoint_paths(stem)[0].read_text(encoding="utf-8"))
    train_target = target.loc[split.train_ids].to_numpy(dtype="int8")
    validation_target = target.loc[split.validation_ids].to_numpy(dtype="int8")
    columns = list(feature_spec.columns)
    transform_seconds = 0.0
    if candidate.model in {"lightgbm", "xgboost"}:
        categories = [column for column in columns if column in categorical_columns]
        numeric = [column for column in columns if column not in categories]
        transform_started = time.perf_counter()
        train_matrix, validation_matrix, _ = transform_fold_union(
            features.loc[split.train_ids, columns],
            features.loc[split.validation_ids, columns],
            numeric,
            categories,
        )
        transform_seconds = time.perf_counter() - transform_started
        estimator = build_sparse_estimator(candidate.model, candidate.params, jobs)
        fit_started = time.perf_counter()
        estimator.fit(train_matrix, train_target)
        fit_seconds = time.perf_counter() - fit_started
        predict_started = time.perf_counter()
        probability = estimator.predict_proba(validation_matrix)[:, 1]
        predict_seconds = time.perf_counter() - predict_started
        del train_matrix, validation_matrix
    else:
        categories = [column for column in columns if column in categorical_columns]
        train_frame = features.loc[split.train_ids, columns].copy()
        validation_frame = features.loc[split.validation_ids, columns].copy()
        for column in categories:
            train_frame[column] = (
                train_frame[column].astype("string").fillna("__MISSING__").astype(str)
            )
            validation_frame[column] = (
                validation_frame[column]
                .astype("string")
                .fillna("__MISSING__")
                .astype(str)
            )
        estimator = CatBoostClassifier(
            **candidate.params,
            loss_function="Logloss",
            random_seed=RANDOM_SEED,
            thread_count=jobs,
            verbose=False,
            allow_writing_files=False,
        )
        fit_started = time.perf_counter()
        estimator.fit(train_frame, train_target, cat_features=categories)
        fit_seconds = time.perf_counter() - fit_started
        predict_started = time.perf_counter()
        probability = estimator.predict_proba(validation_frame)[:, 1]
        predict_seconds = time.perf_counter() - predict_started
        del train_frame, validation_frame
    metrics = compute_metrics(validation_target, probability)
    metric = {
        "status": "completed",
        "created_at_kst": now_kst(),
        "run_id": candidate.run_id,
        "model": candidate.model,
        "feature_set_id": candidate.feature_set_id,
        "feature_set_sha256": feature_spec.sha256,
        "trial_number": candidate.trial_number,
        "params": candidate.params,
        "params_sha256": candidate.params_sha256,
        "split_kind": split.kind,
        "outer_fold": split.outer_fold,
        "validation_period": split.validation_period,
        "train_rows": len(split.train_ids),
        "validation_rows": len(split.validation_ids),
        "transform_seconds": transform_seconds,
        "fit_seconds": fit_seconds,
        "predict_seconds": predict_seconds,
        "metrics": metrics,
        "locked_test_opened": False,
    }
    write_checkpoint(
        stem,
        metric,
        split.validation_ids,
        validation_target,
        probability,
    )
    logger.info(
        "METRIC | %s | %s | AP=%.5f AUC=%.5f Brier=%.5f fit=%.1fs",
        split.label,
        candidate.run_id,
        metrics["average_precision"],
        metrics["roc_auc"],
        metrics["brier_score"],
        fit_seconds,
    )
    del estimator, probability, train_target, validation_target
    gc.collect()
    return metric


def load_prediction(stem: str, probability_name: str) -> pd.DataFrame:
    frame = pd.read_parquet(checkpoint_paths(stem)[1])
    return frame.rename(columns={"probability": probability_name})


def merge_predictions(
    split: SplitSpec, candidates: list[Candidate]
) -> pd.DataFrame:
    merged: pd.DataFrame | None = None
    for candidate in candidates:
        stem = checkpoint_stem(split, candidate.run_id)
        frame = load_prediction(stem, candidate.model)
        if merged is None:
            merged = frame
        else:
            merged = merged.merge(
                frame,
                on=["stage4_row_id", "target"],
                how="inner",
                validate="one_to_one",
            )
    if merged is None or len(merged) != len(split.validation_ids):
        raise RuntimeError(f"Prediction merge failed for {split.label}.")
    return merged


def ensemble_checkpoint(
    split: SplitSpec,
    run_id: str,
    model: str,
    probability: np.ndarray,
    target: np.ndarray,
    row_ids: np.ndarray,
    fit_seconds: float,
    predict_seconds: float,
    detail: dict[str, Any],
) -> None:
    stem = checkpoint_stem(split, run_id)
    metric = {
        "status": "completed",
        "created_at_kst": now_kst(),
        "run_id": run_id,
        "model": model,
        "feature_set_id": "three_selected_trial_probabilities",
        "feature_set_sha256": None,
        "params_sha256": None,
        "split_kind": "outer",
        "outer_fold": split.outer_fold,
        "validation_period": None,
        "train_rows": len(split.train_ids),
        "validation_rows": len(split.validation_ids),
        "fit_seconds": fit_seconds,
        "predict_seconds": predict_seconds,
        "metrics": compute_metrics(target, probability),
        "detail": detail,
        "locked_test_opened": False,
    }
    write_checkpoint(stem, metric, row_ids, target, probability)


def make_ensembles(
    outer: SplitSpec,
    inners: list[SplitSpec],
    candidates: list[Candidate],
    logger: logging.Logger,
) -> None:
    outer_predictions = merge_predictions(outer, candidates)
    target = outer_predictions["target"].to_numpy(dtype="int8")
    row_ids = outer_predictions["stage4_row_id"].to_numpy(dtype="int64")

    voting_id = "soft_voting_equal"
    voting_stem = checkpoint_stem(outer, voting_id)
    if not checkpoint_valid(voting_stem, voting_id, None, None):
        predict_started = time.perf_counter()
        voting_probability = outer_predictions[PROBABILITY_COLUMNS].mean(axis=1).to_numpy()
        predict_seconds = time.perf_counter() - predict_started
        ensemble_checkpoint(
            outer,
            voting_id,
            "soft_voting",
            voting_probability,
            target,
            row_ids,
            0.0,
            predict_seconds,
            {"weights": [1 / 3, 1 / 3, 1 / 3]},
        )
        metric = compute_metrics(target, voting_probability)
        logger.info(
            "METRIC | %s | %s | AP=%.5f AUC=%.5f Brier=%.5f",
            outer.label,
            voting_id,
            metric["average_precision"],
            metric["roc_auc"],
            metric["brier_score"],
        )

    stacking_id = "stacking_nested_logistic"
    stacking_stem = checkpoint_stem(outer, stacking_id)
    if not checkpoint_valid(stacking_stem, stacking_id, None, None):
        inner_predictions = pd.concat(
            [merge_predictions(inner, candidates) for inner in inners],
            ignore_index=True,
        )
        if inner_predictions["stage4_row_id"].duplicated().any():
            raise RuntimeError(f"Duplicate nested OOF rows in {outer.label}.")
        meta_model = LogisticRegression(
            penalty="l2",
            C=1.0,
            solver="lbfgs",
            max_iter=1000,
            random_state=RANDOM_SEED,
            class_weight=None,
        )
        fit_started = time.perf_counter()
        meta_model.fit(
            inner_predictions[PROBABILITY_COLUMNS],
            inner_predictions["target"].to_numpy(dtype="int8"),
        )
        fit_seconds = time.perf_counter() - fit_started
        predict_started = time.perf_counter()
        stacking_probability = meta_model.predict_proba(
            outer_predictions[PROBABILITY_COLUMNS]
        )[:, 1]
        predict_seconds = time.perf_counter() - predict_started
        ensemble_checkpoint(
            outer,
            stacking_id,
            "stacking",
            stacking_probability,
            target,
            row_ids,
            fit_seconds,
            predict_seconds,
            {
                "meta_model": "logistic_regression_l2",
                "inner_validation_periods": [inner.validation_period for inner in inners],
                "inner_oof_rows": len(inner_predictions),
                "coefficients": meta_model.coef_[0].tolist(),
                "intercept": float(meta_model.intercept_[0]),
            },
        )
        metric = compute_metrics(target, stacking_probability)
        logger.info(
            "METRIC | %s | %s | AP=%.5f AUC=%.5f Brier=%.5f meta_fit=%.2fs",
            outer.label,
            stacking_id,
            metric["average_precision"],
            metric["roc_auc"],
            metric["brier_score"],
            fit_seconds,
        )


def output_run_specs(candidates: list[Candidate]) -> list[dict[str, str]]:
    specs = [
        {
            "run_id": candidate.run_id,
            "model": candidate.model,
            "feature_set_id": candidate.feature_set_id,
        }
        for candidate in candidates
    ]
    specs.extend(
        [
            {
                "run_id": "soft_voting_equal",
                "model": "soft_voting",
                "feature_set_id": "three_selected_trial_probabilities",
            },
            {
                "run_id": "stacking_nested_logistic",
                "model": "stacking",
                "feature_set_id": "three_selected_trial_probabilities",
            },
        ]
    )
    return specs


def collect_outputs(
    outer: list[SplitSpec], candidates: list[Candidate], industry: pd.Series
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    specs = output_run_specs(candidates)
    prediction_frames: list[pd.DataFrame] = []
    metric_rows: list[dict[str, Any]] = []
    for split in outer:
        for spec in specs:
            stem = checkpoint_stem(split, spec["run_id"])
            metric = json.loads(checkpoint_paths(stem)[0].read_text(encoding="utf-8"))
            prediction = pd.read_parquet(checkpoint_paths(stem)[1])
            prediction.insert(1, "fold", split.outer_fold)
            prediction.insert(2, "run_id", spec["run_id"])
            prediction.insert(3, "model", spec["model"])
            prediction.insert(4, "feature_set_id", spec["feature_set_id"])
            prediction_frames.append(prediction)
            row = {
                "fold": split.outer_fold,
                "run_id": spec["run_id"],
                "model": spec["model"],
                "feature_set_id": spec["feature_set_id"],
                "fit_seconds": metric["fit_seconds"],
                "predict_seconds": metric["predict_seconds"],
                **metric["metrics"],
            }
            metric_rows.append(row)
    predictions = pd.concat(prediction_frames, ignore_index=True)
    if predictions.duplicated(["run_id", "stage4_row_id"]).any():
        raise RuntimeError("OOF prediction rows are duplicated.")
    folds = pd.DataFrame(metric_rows)
    summary_rows: list[dict[str, Any]] = []
    for spec in specs:
        group_predictions = predictions[predictions["run_id"] == spec["run_id"]]
        group_folds = folds[folds["run_id"] == spec["run_id"]]
        overall = compute_metrics(
            group_predictions["target"].to_numpy(dtype="int8"),
            group_predictions["probability"].to_numpy(dtype="float64"),
        )
        summary_rows.append(
            {
                **spec,
                "completed_folds": len(group_folds),
                "oof_rows": len(group_predictions),
                "overall_average_precision": overall["average_precision"],
                "overall_roc_auc": overall["roc_auc"],
                "overall_brier_score": overall["brier_score"],
                "overall_log_loss": overall["log_loss"],
                "overall_f2_at_0_5": overall["f2"],
                "mean_fold_average_precision": group_folds["average_precision"].mean(),
                "std_fold_average_precision": group_folds["average_precision"].std(ddof=0),
                "worst_fold_average_precision": group_folds["average_precision"].min(),
                "mean_fold_roc_auc": group_folds["roc_auc"].mean(),
                "std_fold_roc_auc": group_folds["roc_auc"].std(ddof=0),
                "worst_fold_roc_auc": group_folds["roc_auc"].min(),
                "total_incremental_fit_seconds": group_folds["fit_seconds"].sum(),
                "total_predict_seconds": group_folds["predict_seconds"].sum(),
                "inference_base_model_count": 1 if spec["model"] in PROBABILITY_COLUMNS else 3,
            }
        )
    summary = pd.DataFrame(summary_rows)
    industry_metrics = build_industry_metrics(predictions, industry)
    return predictions, folds, summary, industry_metrics


def write_report(summary: pd.DataFrame) -> None:
    table = []
    for row in summary.itertuples(index=False):
        table.append(
            f"| {row.run_id} | {row.mean_fold_average_precision:.4f} | "
            f"{row.mean_fold_roc_auc:.4f} | {row.overall_average_precision:.4f} | "
            f"{row.overall_roc_auc:.4f} | {row.worst_fold_average_precision:.4f} | "
            f"{row.std_fold_average_precision:.4f} | {row.overall_brier_score:.4f} | "
            f"{row.overall_log_loss:.4f} | {int(row.inference_base_model_count)} |"
        )
    indexed = summary.set_index("run_id")
    lightgbm = indexed.loc["lightgbm__trial10"]
    voting = indexed.loc["soft_voting_equal"]
    stacking = indexed.loc["stacking_nested_logistic"]
    lines = [
        "# Stage 5 선택 Trial OOF·Ensemble 비교",
        "",
        f"- 생성 시각: {now_kst()}",
        "- 대표 설정: LightGBM Trial 10, XGBoost Trial 16, CatBoost Trial 18",
        "- Outer 평가: Stage 4 고정 4개 시간순 Fold",
        "- Soft Voting: 세 모델 확률의 사전 고정 동일 가중 평균",
        "- Stacking: 각 Outer Train 안에서 마지막 3개 기간의 nested OOF를 생성해 L2 Logistic meta-model을 Fit",
        "- 누수 방지: Inner Train의 Target 종료분기는 Inner Validation보다 최소 2분기 앞서며 Outer Validation은 meta-model Fit에 사용하지 않음",
        "- 임계값 0.5 지표는 참고용이며 최종 F2 임계값은 아직 선택하지 않음",
        "- 자동 최종 순위·최종 모델 선택 없음",
        "- 2025 잠긴 테스트: 미접근",
        "",
        "| 실행 | 평균 Fold AUPRC | 평균 Fold AUROC | 전체 OOF AUPRC | 전체 OOF AUROC | 최악 Fold AUPRC | AP 표준편차 | Brier | Log Loss | 추론 Base 모델 수 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        *table,
        "",
        "## 종합 검토",
        "",
        f"- 동일 가중 Soft Voting은 LightGBM 단일 모델보다 평균 Fold AUPRC `{voting['mean_fold_average_precision']-lightgbm['mean_fold_average_precision']:+.4f}`, 평균 Fold AUROC `{voting['mean_fold_roc_auc']-lightgbm['mean_fold_roc_auc']:+.4f}`, 최악 Fold AUPRC `{voting['worst_fold_average_precision']-lightgbm['worst_fold_average_precision']:+.4f}` 개선됐다.",
        f"- Soft Voting은 전체 OOF AUPRC `{voting['overall_average_precision']:.4f}`, 전체 OOF AUROC `{voting['overall_roc_auc']:.4f}`, Brier `{voting['overall_brier_score']:.4f}`, Log Loss `{voting['overall_log_loss']:.4f}`로 다섯 실행 중 가장 균형이 좋다.",
        f"- Stacking은 평균 Fold AUROC `{stacking['mean_fold_roc_auc']:.4f}`가 가장 높지만 Soft Voting보다 전체 OOF AUPRC·AUROC와 확률 품질이 낮아 추가 복잡도를 정당화하지 못했다.",
        "- 성능 우선 권장안은 동일 가중 Soft Voting이고, 단일 모델 운영 단순성을 우선하면 성능 차이가 작은 LightGBM Trial 10이 대안이다.",
        "",
        "전체 Fold·업종별 지표와 확률은 CSV·Parquet 산출물에 보존했다. 이 표를 사용자와 종합 검토한 뒤에만 최종 모델과 F2 운영 임계값을 확정한다.",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def show_status() -> None:
    if not PROGRESS_PATH.exists():
        print(
            json.dumps(
                {
                    "status": "not_started",
                    "message": "진행 파일이 없습니다. 기본 실행 명령으로 시작하세요.",
                    "run_command": (
                        r"& 'C:\Program Files\Python313\python.exe' -u -m "
                        "src.models.run_stage5_oof_ensemble"
                    ),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    print(PROGRESS_PATH.read_text(encoding="utf-8"))


def main(validate_only: bool = False) -> None:
    config, candidates = load_execution_contract()
    logger = configure_logger()
    features, target, membership, feature_specs, categorical_columns = (
        prepare_feature_data()
    )
    support_path = PROJECT_ROOT / config["data"]["development"]
    support = pd.read_parquet(
        support_path,
        columns=["stage4_row_id", "target_end_period", "서비스_업종_코드"],
    ).set_index("stage4_row_id")
    periods = support["target_end_period"].astype("int32")
    industry = support["서비스_업종_코드"].astype("string")
    outer = outer_splits(membership)
    inner_by_outer = {
        split.outer_fold: inner_splits(split, periods, count=3) for split in outer
    }
    for candidate in candidates:
        if candidate.feature_set_id not in feature_specs:
            raise RuntimeError(f"Unknown feature set: {candidate.feature_set_id}")
    planned_model_fits = sum(
        len(candidates) * (1 + len(inner_by_outer[split.outer_fold]))
        for split in outer
    )
    planned_ensemble_steps = len(outer)
    if planned_model_fits != 48 or planned_ensemble_steps != 4:
        raise RuntimeError("Expected exactly 48 base Fits and 4 ensemble steps.")
    if validate_only:
        payload = {
            "status": "validation_passed",
            "rows": len(features),
            "selected_trials": [
                {
                    "model": candidate.model,
                    "feature_set": candidate.feature_set_id,
                    "trial_number": candidate.trial_number,
                    "feature_count": len(feature_specs[candidate.feature_set_id].columns),
                }
                for candidate in candidates
            ],
            "outer_folds": 4,
            "inner_periods": {
                str(fold): [split.validation_period for split in splits]
                for fold, splits in inner_by_outer.items()
            },
            "planned_model_fits": planned_model_fits,
            "planned_ensemble_steps": planned_ensemble_steps,
            "planned_total_steps": planned_model_fits + planned_ensemble_steps,
            "locked_test_opened": False,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2), flush=True)
        return

    jobs = max(
        1,
        min(
            int(config["screen_budget"]["max_parallel_cpu_threads"]),
            max(1, (os.cpu_count() or 2) - 1),
        ),
    )
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    progress = Progress(planned_model_fits + planned_ensemble_steps, logger)
    logger.info("=" * 72)
    logger.info(
        "RUN START | 3 selected Trials | 4 Outer Folds | 48 model Fits | 4 ensemble steps"
    )
    logger.info("Progress file: %s", PROGRESS_PATH)
    logger.info("Log file: %s", LOG_PATH)
    logger.info("Locked 2025 test: FORBIDDEN / NOT OPENED")
    try:
        for outer_split in outer:
            inners = inner_by_outer[outer_split.outer_fold]
            all_splits = [outer_split, *inners]
            for split in all_splits:
                for candidate in candidates:
                    label = f"{split.label} | {candidate.run_id}"
                    stem = checkpoint_stem(split, candidate.run_id)
                    valid = checkpoint_valid(
                        stem,
                        candidate.run_id,
                        feature_specs[candidate.feature_set_id].sha256,
                        candidate.params_sha256,
                    )
                    progress.start(label)
                    fit_candidate(
                        candidate,
                        split,
                        features,
                        target,
                        feature_specs[candidate.feature_set_id],
                        categorical_columns,
                        jobs,
                        logger,
                    )
                    progress.done(label, was_fit=not valid, skipped=valid)
            label = f"{outer_split.label} | Soft Voting + nested Stacking"
            voting_valid = checkpoint_valid(
                checkpoint_stem(outer_split, "soft_voting_equal"),
                "soft_voting_equal",
                None,
                None,
            )
            stacking_valid = checkpoint_valid(
                checkpoint_stem(outer_split, "stacking_nested_logistic"),
                "stacking_nested_logistic",
                None,
                None,
            )
            progress.start(label)
            make_ensembles(outer_split, inners, candidates, logger)
            progress.done(label, skipped=voting_valid and stacking_valid)
        predictions, folds, summary, industry_metrics = collect_outputs(
            outer, candidates, industry
        )
        predictions.to_parquet(PREDICTIONS_PATH, index=False, compression="zstd")
        folds.to_csv(FOLD_METRICS_PATH, index=False, encoding="utf-8-sig")
        summary.to_csv(SUMMARY_PATH, index=False, encoding="utf-8-sig")
        industry_metrics.to_csv(INDUSTRY_PATH, index=False, encoding="utf-8-sig")
        write_report(summary)
        manifest = {
            "created_at_kst": now_kst(),
            "status": "completed",
            "selected_trials": [
                {
                    "model": candidate.model,
                    "feature_set": candidate.feature_set_id,
                    "trial_number": candidate.trial_number,
                    "params_sha256": candidate.params_sha256,
                }
                for candidate in candidates
            ],
            "outer_folds": 4,
            "nested_inner_periods_per_outer_fold": 3,
            "completed_model_fits_or_valid_checkpoints": 48,
            "completed_ensemble_steps": 4,
            "automatic_final_model_selection": False,
            "final_threshold_selected": False,
            "locked_test_opened": False,
            "outputs": {
                "predictions": str(PREDICTIONS_PATH.relative_to(PROJECT_ROOT)),
                "fold_metrics": str(FOLD_METRICS_PATH.relative_to(PROJECT_ROOT)),
                "summary": str(SUMMARY_PATH.relative_to(PROJECT_ROOT)),
                "industry_metrics": str(INDUSTRY_PATH.relative_to(PROJECT_ROOT)),
                "report": str(REPORT_PATH.relative_to(PROJECT_ROOT)),
                "log": str(LOG_PATH.relative_to(PROJECT_ROOT)),
                "progress": str(PROGRESS_PATH.relative_to(PROJECT_ROOT)),
            },
        }
        MANIFEST_PATH.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        progress.write("completed", "모든 OOF·Ensemble 결과 저장 완료")
        logger.info("RUN COMPLETE | results=%s", REPORT_PATH)
    except KeyboardInterrupt:
        progress.write("interrupted", "사용자 중단 — 같은 명령으로 재개 가능")
        logger.warning("RUN INTERRUPTED | completed checkpoints are preserved")
        raise
    except Exception as error:
        progress.write("failed", "실행 실패", f"{type(error).__name__}: {error}")
        logger.exception("RUN FAILED")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()
    if args.status:
        show_status()
    else:
        main(validate_only=args.validate_only)
