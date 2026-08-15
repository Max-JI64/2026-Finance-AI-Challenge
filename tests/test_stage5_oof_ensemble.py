from __future__ import annotations

import numpy as np
import pandas as pd

from src.models.run_stage5_oof_ensemble import (
    SplitSpec,
    inner_splits,
    load_execution_contract,
    output_run_specs,
    shift_quarter,
)


def test_shift_quarter_crosses_year_boundaries() -> None:
    assert shift_quarter(20241, -1) == 20234
    assert shift_quarter(20241, -2) == 20233
    assert shift_quarter(20234, 1) == 20241


def test_inner_splits_use_last_three_periods_and_one_quarter_purge() -> None:
    row_ids = np.arange(1, 10, dtype="int64")
    periods = pd.Series(
        [20222, 20223, 20224, 20231, 20232, 20233, 20234, 20241, 20242],
        index=row_ids,
        dtype="int32",
    )
    outer = SplitSpec("outer", 4, row_ids, np.array([100], dtype="int64"))
    splits = inner_splits(outer, periods, count=3)

    assert [split.validation_period for split in splits] == [20234, 20241, 20242]
    assert [int(periods.loc[split.train_ids].max()) for split in splits] == [
        20232,
        20233,
        20234,
    ]
    assert all(
        not np.intersect1d(split.train_ids, split.validation_ids).size
        for split in splits
    )


def test_execution_contract_uses_exact_approved_trials() -> None:
    _, candidates = load_execution_contract()
    assert [(item.model, item.trial_number) for item in candidates] == [
        ("lightgbm", 10),
        ("xgboost", 16),
        ("catboost", 18),
    ]
    assert all(item.params for item in candidates)


def test_output_specs_include_three_individuals_and_two_ensembles() -> None:
    _, candidates = load_execution_contract()
    specs = output_run_specs(candidates)
    assert [item["run_id"] for item in specs] == [
        "lightgbm__trial10",
        "xgboost__trial16",
        "catboost__trial18",
        "soft_voting_equal",
        "stacking_nested_logistic",
    ]
