from __future__ import annotations

from src.models.run_stage5_final_2025 import (
    APPROVED_FEATURE_SET,
    APPROVED_METRICS,
    APPROVED_MODEL,
    APPROVED_TRIAL,
    LOCKED_PERIODS,
    REFIT_PERIODS,
    load_contract,
    load_trial,
)


def test_final_2025_contract_is_exactly_approved_scope() -> None:
    _, stage5, _ = load_contract()
    policy = stage5["metrics"]["locked_test_without_threshold"]

    assert (APPROVED_MODEL, APPROVED_TRIAL, APPROVED_FEATURE_SET) == (
        "lightgbm",
        10,
        "common_baseline",
    )
    assert APPROVED_METRICS == (
        "average_precision",
        "roc_auc",
        "brier_score",
        "log_loss",
    )
    assert policy["exclude"] == [
        "binary_classification_metrics",
        "threshold_search",
        "threshold_selection",
    ]
    assert REFIT_PERIODS == (20222, 20243)
    assert LOCKED_PERIODS == (20251, 20254)


def test_final_trial_parameters_exist_and_are_stable() -> None:
    params, params_hash = load_trial()

    assert params["n_estimators"] == 550
    assert params["max_depth"] == 8
    assert len(params_hash) == 64
