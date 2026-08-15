from pathlib import Path

from src.features.build_stage5_feature_sets import (
    TREE_RAW_GROUPS,
    build_feature_set_specs,
    read_contract_rows,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROJECT_ROOT / "reports" / "stage45" / "feature_contract.md"


def _actual_specs():
    rows = read_contract_rows(CONTRACT_PATH)
    available = [row.feature for row in rows if row.recommendation != "remove"]
    return rows, build_feature_set_specs(rows, available)


def test_actual_contract_builds_all_planned_feature_sets() -> None:
    _, specs = _actual_specs()
    assert set(specs) == {
        "common_baseline",
        "linear_common_plus_log1p",
        *(f"tree_plus_{group}" for group in TREE_RAW_GROUPS),
    }


def test_linear_extension_adds_exactly_ten_features() -> None:
    _, specs = _actual_specs()
    common = set(specs["common_baseline"].columns)
    linear = set(specs["linear_common_plus_log1p"].columns)
    added = linear - common
    assert len(added) == 10
    assert all(feature.startswith("log1p__") for feature in added)


def test_tree_ablations_are_independent_and_never_restore_remove_features() -> None:
    rows, specs = _actual_specs()
    common = set(specs["common_baseline"].columns)
    remove = {row.feature for row in rows if row.recommendation == "remove"}
    added_groups = []
    for group in TREE_RAW_GROUPS:
        columns = set(specs[f"tree_plus_{group}"].columns)
        assert common < columns
        assert not columns.intersection(remove)
        added_groups.append(columns - common)
    for index, left in enumerate(added_groups):
        for right in added_groups[index + 1 :]:
            assert left.isdisjoint(right)
