from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.data.build_re_stage5_baseline import (
    AREA,
    INDUSTRY,
    PERIOD,
    ROW_ID,
    SALES,
    build_targets,
    make_fold_membership,
)
from src.models.run_re_stage5_quantile import (
    compute_metrics,
    predict_seasonal,
    prepare_matrix,
)
from src.models.run_re_stage5_holdout import (
    access_resume_state,
    fit_sparse_preprocessor,
    target_reason_column,
    target_valid_column,
)


def make_rows(area: str, sales: list[float | None]) -> list[dict[str, object]]:
    periods = [20211, 20212, 20213, 20214, 20221, 20222]
    return [
        {
            PERIOD: period,
            AREA: area,
            INDUSTRY: "CS100001",
            SALES: value,
        }
        for period, value in zip(periods, sales, strict=True)
    ]


def test_target_contract_zero_future_and_positive_denominator() -> None:
    panel = pd.DataFrame(make_rows("A", [100, 100, 100, 100, 0, 120]))
    targets = build_targets(panel)
    row = targets.iloc[3]
    assert row["target_a_next_quarter_yoy"] == -1.0
    assert row["target_b_next_two_quarters_yoy"] == -0.4
    assert row["target_aux_min_next_two_quarters_yoy"] == -1.0
    assert row["target_challenger_next_quarter_qoq"] == -1.0
    assert row["target_a_reason"] == "valid"


def test_target_contract_missing_and_zero_denominator_stay_null() -> None:
    rows = make_rows("A", [0, 100, 100, 100, 50, 120])
    rows += make_rows("B", [100, 100, 100, 100, None, 120])
    panel = pd.DataFrame(rows)
    targets = build_targets(panel)
    zero_denominator = targets.iloc[3]
    missing_future = targets.iloc[9]
    assert np.isnan(zero_denominator["target_a_next_quarter_yoy"])
    assert zero_denominator["target_a_reason"] == "invalid_denominator"
    assert np.isnan(missing_future["target_a_next_quarter_yoy"])
    assert missing_future["target_a_reason"] == "missing_future"


def test_four_expanding_folds_and_one_quarter_purge() -> None:
    periods = [
        20214,
        20221,
        20222,
        20223,
        20224,
        20231,
        20232,
        20233,
        20234,
        20241,
        20242,
        20243,
        20244,
    ]
    development = pd.DataFrame({ROW_ID: range(1, 14), PERIOD: periods})
    folds = make_fold_membership(development, [20241, 20242, 20243, 20244])
    purge = (
        folds.loc[folds["role"] == "purge", ["fold", "purge_period"]]
        .drop_duplicates()
        .set_index("fold")["purge_period"]
        .to_dict()
    )
    assert purge == {1: 20234, 2: 20241, 3: 20242, 4: 20243}
    train_counts = folds.loc[folds["role"] == "train"].groupby("fold").size()
    assert train_counts.is_monotonic_increasing


def test_quantile_metrics_report_and_correct_crossing() -> None:
    actual = np.array([-1.0, 0.0, 1.0])
    raw = np.array(
        [
            [0.0, -0.5, 0.5],
            [-0.2, 0.0, 0.2],
            [0.5, 1.0, 1.5],
        ]
    )
    metrics, corrected = compute_metrics(actual, raw)
    assert metrics["crossing_ratio_raw"] == 1 / 3
    assert metrics["crossing_ratio_corrected"] == 0.0
    assert np.all(corrected[:, 0] <= corrected[:, 1])
    assert np.all(corrected[:, 1] <= corrected[:, 2])
    assert 0 <= metrics["coverage_p10_p90"] <= 1


def test_seasonal_baseline_copies_readonly_pandas_arrays() -> None:
    train = pd.DataFrame(
        {"전년동기_매출_증감률": [0.1, np.nan, -0.2, 0.3]}
    )
    validation = pd.DataFrame(
        {"전년동기_매출_증감률": [np.nan, 0.2]}
    )
    train_y = np.array([0.0, 0.1, -0.1, 0.4])
    prediction = predict_seasonal(train, validation, train_y)
    assert prediction.shape == (2, 3)
    assert np.isfinite(prediction).all()


def test_train_only_preprocessor_copies_readonly_numeric_arrays() -> None:
    train = pd.DataFrame(
        {"numeric": [1.0, np.inf, np.nan], "category": ["A", "B", None]}
    )
    validation = pd.DataFrame(
        {"numeric": [np.nan, 2.0], "category": ["C", "A"]}
    )
    matrix = prepare_matrix(train, validation, ["numeric", "category"])
    assert matrix.train.shape[0] == 3
    assert matrix.validation.shape[0] == 2
    assert np.isfinite(matrix.train.data).all()
    assert np.isfinite(matrix.validation.data).all()


def test_holdout_preprocessor_matches_cv_preprocessing_contract() -> None:
    train = pd.DataFrame(
        {
            "numeric": [1.0, np.inf, np.nan, 4.0],
            "category": ["A", "B", None, "A"],
        }
    )
    validation = pd.DataFrame(
        {"numeric": [np.nan, 2.0], "category": ["C", "A"]}
    )
    reference = prepare_matrix(train, validation, ["numeric", "category"])
    preprocessor, train_matrix = fit_sparse_preprocessor(
        train, ["numeric", "category"]
    )
    validation_matrix = preprocessor.transform(validation)
    assert np.allclose(train_matrix.toarray(), reference.train.toarray())
    assert np.allclose(
        validation_matrix.toarray(), reference.validation.toarray()
    )


def test_holdout_access_allows_only_same_contract_resume() -> None:
    assert access_resume_state(None, "contract-a") == "new"
    access = {
        "status": "failed_same_model_resume_only",
        "target_opened": True,
        "selected_model": "lightgbm",
        "contract_sha256": "contract-a",
    }
    assert (
        access_resume_state(access, "contract-a")
        == "resume_same_model_only"
    )
    with pytest.raises(RuntimeError, match="different frozen contract"):
        access_resume_state(access, "contract-b")
    completed = {**access, "status": "completed"}
    with pytest.raises(RuntimeError, match="already completed"):
        access_resume_state(completed, "contract-a")


def test_holdout_target_metadata_mapping_is_explicit() -> None:
    assert target_valid_column("target_a_next_quarter_yoy") == "target_a_valid"
    assert target_valid_column("target_b_next_two_quarters_yoy") == "target_b_valid"
    assert (
        target_reason_column("target_aux_min_next_two_quarters_yoy")
        == "target_aux_reason"
    )
