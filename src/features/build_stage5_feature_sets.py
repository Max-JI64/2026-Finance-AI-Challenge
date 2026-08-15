"""Build the approved Stage 5 feature sets from the Stage 4.5 contract.

The module turns the human-readable contract table into deterministic column
lists.  It never reads Target values and it never makes a performance-based
retain/drop decision.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path


TREE_RAW_GROUPS = {
    "sales_amount_raw_components": lambda name: name.endswith("_매출_금액"),
    "transaction_count_raw_components": lambda name: name.endswith("_매출_건수"),
    "floating_population_raw_components": lambda name: name.startswith("유동__"),
    "resident_population_raw_components": lambda name: name.startswith("상주__"),
    "worker_population_raw_components": lambda name: name.startswith("직장__"),
}


@dataclass(frozen=True)
class ContractRow:
    feature: str
    origin: str
    recommendation: str
    model_scope: str
    reason: str


@dataclass(frozen=True)
class FeatureSetSpec:
    feature_set_id: str
    scope: str
    columns: tuple[str, ...]
    raw_group: str | None = None

    @property
    def sha256(self) -> str:
        payload = "\n".join(self.columns).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


def read_contract_rows(contract_path: Path) -> list[ContractRow]:
    """Parse the five-column feature decision table from the contract."""
    rows: list[ContractRow] = []
    in_table = False
    for line in contract_path.read_text(encoding="utf-8").splitlines():
        if line == "## Feature별 제안":
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if not in_table or not line.startswith("|"):
            continue
        values = [value.strip() for value in line.strip().strip("|").split("|")]
        if len(values) != 5 or values[0] in {"Feature", "---"}:
            continue
        if all(set(value) <= {"-", ":"} for value in values):
            continue
        rows.append(ContractRow(*values))
    if not rows:
        raise ValueError(f"No feature-contract rows found in {contract_path}")
    duplicates = sorted(
        feature for feature in {row.feature for row in rows}
        if sum(item.feature == feature for item in rows) > 1
    )
    if duplicates:
        raise ValueError(f"Duplicate contract features: {duplicates[:10]}")
    return rows


def build_feature_set_specs(
    contract_rows: list[ContractRow],
    available_columns: list[str] | tuple[str, ...] | set[str],
) -> dict[str, FeatureSetSpec]:
    """Return common, linear, and five independent tree-ablation sets."""
    available = set(available_columns)
    common_original = [
        row.feature
        for row in contract_rows
        if row.origin == "original" and row.recommendation == "keep"
    ]
    common_derived = [
        row.feature
        for row in contract_rows
        if row.origin == "derived"
        and row.recommendation == "add"
        and row.model_scope == "common"
    ]
    linear_only = [
        row.feature
        for row in contract_rows
        if row.origin == "derived"
        and row.recommendation == "add"
        and row.model_scope == "linear_only"
    ]
    common = tuple(dict.fromkeys([*common_original, *common_derived]))
    linear = tuple(dict.fromkeys([*common, *linear_only]))
    specs = {
        "common_baseline": FeatureSetSpec(
            feature_set_id="common_baseline",
            scope="common",
            columns=common,
        ),
        "linear_common_plus_log1p": FeatureSetSpec(
            feature_set_id="linear_common_plus_log1p",
            scope="linear",
            columns=linear,
        ),
    }
    replace_rows = [
        row
        for row in contract_rows
        if row.origin == "original" and row.recommendation == "replace"
    ]
    assigned: set[str] = set()
    for group, matcher in TREE_RAW_GROUPS.items():
        raw_columns = [row.feature for row in replace_rows if matcher(row.feature)]
        overlap = assigned.intersection(raw_columns)
        if overlap:
            raise ValueError(f"Raw ablation groups overlap: {sorted(overlap)[:10]}")
        if not raw_columns:
            raise ValueError(f"Raw ablation group is empty: {group}")
        assigned.update(raw_columns)
        feature_set_id = f"tree_plus_{group}"
        specs[feature_set_id] = FeatureSetSpec(
            feature_set_id=feature_set_id,
            scope="tree_ablation",
            columns=tuple(dict.fromkeys([*common, *raw_columns])),
            raw_group=group,
        )

    missing = {
        feature_set_id: sorted(set(spec.columns) - available)
        for feature_set_id, spec in specs.items()
        if set(spec.columns) - available
    }
    if missing:
        raise ValueError(f"Feature-set columns are unavailable: {missing}")
    remove_columns = {
        row.feature for row in contract_rows if row.recommendation == "remove"
    }
    resurrected = {
        feature_set_id: sorted(set(spec.columns).intersection(remove_columns))
        for feature_set_id, spec in specs.items()
        if set(spec.columns).intersection(remove_columns)
    }
    if resurrected:
        raise ValueError(f"Remove-class features were resurrected: {resurrected}")
    if len(linear_only) != 10:
        raise ValueError(f"Expected 10 linear-only log1p features, got {len(linear_only)}")
    return specs


def write_feature_set_manifest(
    output_path: Path,
    specs: dict[str, FeatureSetSpec],
    contract_path: Path,
) -> None:
    payload = {
        "contract": str(contract_path),
        "selection_policy": "full_result_review_without_precommitted_numeric_cutoff",
        "feature_sets": {
            feature_set_id: {
                **asdict(spec),
                "columns": list(spec.columns),
                "column_count": len(spec.columns),
                "sha256": spec.sha256,
            }
            for feature_set_id, spec in specs.items()
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
