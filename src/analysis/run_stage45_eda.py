"""Run plot-free, discovery-period-only Stage 4.5 modeling EDA.

This program deliberately never opens the locked-test parquet.  Target-guided
work is limited by a Parquet predicate to Fold 1 training target-end periods.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml
from scipy.stats import chi2_contingency, mannwhitneyu
from sklearn.metrics import average_precision_score, mutual_info_score, normalized_mutual_info_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.features.build_stage45_features import build_stage45_features, definitions_frame


DEVELOPMENT = ROOT / "data" / "processed" / "stage4_development.parquet"
FOLDS = ROOT / "data" / "processed" / "stage4_fold_membership.parquet"
STAGE4_CONFIG = ROOT / "config" / "stage4.yaml"
STAGE4_MANIFEST = ROOT / "reports" / "stage4" / "stage4_manifest.json"
OUTPUT = ROOT / "reports" / "stage45"
TARGET = "target_persistent_decline"
PERIOD = "기준_년분기_코드"
RANDOM_SEED = 20260815
CORRELATION_SAMPLE = 20_000
VIF_SAMPLE = 10_000
RARE_CATEGORY_COUNT = 100


def bh_adjust(pvalues: pd.Series) -> pd.Series:
    values = pd.to_numeric(pvalues, errors="coerce").to_numpy(dtype="float64")
    output = np.full(len(values), np.nan)
    valid = np.isfinite(values)
    if not valid.any():
        return pd.Series(output, index=pvalues.index)
    selected = values[valid]
    order = np.argsort(selected)
    ranked = selected[order]
    adjusted = np.minimum.accumulate((ranked * len(ranked) / np.arange(1, len(ranked) + 1))[::-1])[::-1]
    adjusted = np.minimum(adjusted, 1.0)
    restored = np.empty_like(adjusted)
    restored[order] = adjusted
    output[np.flatnonzero(valid)] = restored
    return pd.Series(output, index=pvalues.index)


def cramers_v(table: pd.DataFrame) -> tuple[float, float]:
    if table.shape[0] < 2 or table.shape[1] < 2 or table.to_numpy().sum() == 0:
        return math.nan, math.nan
    chi2, pvalue, _, _ = chi2_contingency(table, correction=False)
    n = table.to_numpy().sum()
    phi2 = chi2 / n
    rows, columns = table.shape
    corrected_phi2 = max(0.0, phi2 - ((columns - 1) * (rows - 1)) / max(n - 1, 1))
    corrected_rows = rows - ((rows - 1) ** 2) / max(n - 1, 1)
    corrected_columns = columns - ((columns - 1) ** 2) / max(n - 1, 1)
    denominator = min(corrected_rows - 1, corrected_columns - 1)
    return (math.sqrt(corrected_phi2 / denominator) if denominator > 0 else math.nan), float(pvalue)


def pooled_categories(series: pd.Series, limit: int = 100) -> pd.Series:
    values = series.astype("string").fillna("__MISSING__")
    keep = set(values.value_counts().head(limit).index)
    return values.where(values.isin(keep), "__OTHER__")


def psi_numeric(reference: pd.Series, current: pd.Series) -> float:
    reference = pd.to_numeric(reference, errors="coerce")
    current = pd.to_numeric(current, errors="coerce")
    available = reference.dropna()
    if available.nunique() < 2:
        return 0.0 if current.dropna().nunique() <= 1 else math.nan
    edges = np.unique(np.quantile(available, np.linspace(0, 1, 11)))
    if len(edges) < 3:
        return math.nan
    edges[0], edges[-1] = -np.inf, np.inf
    reference_bins = pd.cut(reference, bins=edges, include_lowest=True).astype("string").fillna("__MISSING__")
    current_bins = pd.cut(current, bins=edges, include_lowest=True).astype("string").fillna("__MISSING__")
    categories = sorted(set(reference_bins) | set(current_bins))
    ref = reference_bins.value_counts(normalize=True).reindex(categories, fill_value=0).clip(lower=1e-6)
    cur = current_bins.value_counts(normalize=True).reindex(categories, fill_value=0).clip(lower=1e-6)
    return float(((cur - ref) * np.log(cur / ref)).sum())


def psi_categorical(reference: pd.Series, current: pd.Series) -> float:
    ref = pooled_categories(reference, 30)
    keep = set(ref.unique()) - {"__OTHER__"}
    cur = current.astype("string").fillna("__MISSING__").where(lambda x: x.isin(keep), "__OTHER__")
    categories = sorted(set(ref) | set(cur))
    ref_freq = ref.value_counts(normalize=True).reindex(categories, fill_value=0).clip(lower=1e-6)
    cur_freq = cur.value_counts(normalize=True).reindex(categories, fill_value=0).clip(lower=1e-6)
    return float(((cur_freq - ref_freq) * np.log(cur_freq / ref_freq)).sum())


def load_discovery() -> tuple[pd.DataFrame, list[str], dict[str, object]]:
    config = yaml.safe_load(STAGE4_CONFIG.read_text(encoding="utf-8"))
    manifest = json.loads(STAGE4_MANIFEST.read_text(encoding="utf-8"))
    fold1 = config["cross_validation"]["folds"][0]
    start, end = [str(value) for value in fold1["train_target_end_period"]]
    feature_columns = manifest["feature_columns"]
    columns = ["stage4_row_id", *feature_columns, "target_end_period", TARGET]
    table = pq.read_table(
        DEVELOPMENT,
        columns=columns,
        filters=[("target_end_period", ">=", start), ("target_end_period", "<=", end)],
    )
    frame = table.to_pandas()
    membership = pq.read_table(FOLDS, filters=[("fold", "=", 1), ("partition", "=", "train")]).to_pandas()
    expected_ids = set(membership["stage4_row_id"].astype("int64"))
    actual_ids = set(frame["stage4_row_id"].astype("int64"))
    if actual_ids != expected_ids:
        raise RuntimeError("Fold 1 membership and filtered development rows differ.")
    if not frame["target_end_period"].between(start, end).all():
        raise RuntimeError("A non-discovery Target period entered Stage 4.5.")
    if frame[TARGET].isna().any() or not set(frame[TARGET].unique()).issubset({0, 1}):
        raise RuntimeError("Discovery Target is invalid.")
    metadata = {
        "fold": 1,
        "partition": "train",
        "target_end_start": start,
        "target_end_end": end,
        "row_count": int(len(frame)),
        "positive_rows": int(frame[TARGET].sum()),
        "positive_rate": float(frame[TARGET].mean()),
        "original_feature_count": len(feature_columns),
    }
    return frame, feature_columns, metadata


def profile_features(frame: pd.DataFrame, features: list[str], original: set[str]) -> pd.DataFrame:
    target = frame[TARGET]
    rows: list[dict[str, object]] = []
    for column in features:
        series = frame[column]
        numeric = pd.api.types.is_numeric_dtype(series)
        counts = series.value_counts(dropna=False)
        nonmissing = series.dropna()
        missing_mask = series.isna()
        missing_rate_target = target[missing_mask].mean() if missing_mask.any() else math.nan
        observed_rate_target = target[~missing_mask].mean() if (~missing_mask).any() else math.nan
        overall_rate = target.mean()
        row: dict[str, object] = {
            "feature": column,
            "origin": "original" if column in original else "derived",
            "dtype": str(series.dtype),
            "kind": "numeric" if numeric else "categorical",
            "rows": len(series),
            "nonmissing_count": int(series.notna().sum()),
            "missing_count": int(missing_mask.sum()),
            "missing_rate": float(missing_mask.mean()),
            "unique_count": int(series.nunique(dropna=True)),
            "zero_count": int(series.eq(0).sum()) if numeric else math.nan,
            "zero_rate": float(series.eq(0).mean()) if numeric else math.nan,
            "top_frequency": int(counts.iloc[0]) if len(counts) else 0,
            "top_rate": float(counts.iloc[0] / len(series)) if len(counts) else math.nan,
            "constant": bool(series.nunique(dropna=False) <= 1),
            "near_constant_99_5pct": bool(len(counts) and counts.iloc[0] / len(series) >= 0.995),
            "rare_category_count_lt_100": int((series.value_counts(dropna=True) < RARE_CATEGORY_COUNT).sum()) if not numeric else math.nan,
            "target_rate_when_missing": missing_rate_target,
            "target_rate_when_observed": observed_rate_target,
            "missing_target_lift": (missing_rate_target / overall_rate) if missing_mask.any() and overall_rate else math.nan,
        }
        if numeric and len(nonmissing):
            quantiles = pd.to_numeric(nonmissing, errors="coerce").quantile([0, 0.01, 0.25, 0.5, 0.75, 0.99, 1])
            row.update(
                {
                    "min": quantiles.loc[0.0],
                    "p01": quantiles.loc[0.01],
                    "p25": quantiles.loc[0.25],
                    "median": quantiles.loc[0.5],
                    "mean": pd.to_numeric(nonmissing, errors="coerce").mean(),
                    "p75": quantiles.loc[0.75],
                    "p99": quantiles.loc[0.99],
                    "max": quantiles.loc[1.0],
                }
            )
        rows.append(row)
    return pd.DataFrame(rows)


def arithmetic_relationships(frame: pd.DataFrame) -> list[dict[str, object]]:
    days = "월요일 화요일 수요일 목요일 금요일 토요일 일요일".split()
    specs = [
        ("당월_매출_금액", ["주중_매출_금액", "주말_매출_금액"], "weekday_weekend_amount_sum"),
        ("당월_매출_금액", [f"{day}_매출_금액" for day in days], "weekday_amount_sum"),
        ("당월_매출_금액", [f"시간대_{x}_매출_금액" for x in ["00~06", "06~11", "11~14", "14~17", "17~21", "21~24"]], "time_amount_sum"),
        ("당월_매출_금액", ["남성_매출_금액", "여성_매출_금액"], "gender_amount_sum"),
        ("당월_매출_금액", [f"연령대_{x}_매출_금액" for x in ["10", "20", "30", "40", "50", "60_이상"]], "age_amount_sum"),
        ("당월_매출_건수", ["주중_매출_건수", "주말_매출_건수"], "weekday_weekend_count_sum"),
        ("당월_매출_건수", [f"{day}_매출_건수" for day in days], "weekday_count_sum"),
        ("당월_매출_건수", [f"시간대_건수~{x}_매출_건수" for x in ["06", "11", "14", "17", "21", "24"]], "time_count_sum"),
        ("당월_매출_건수", ["남성_매출_건수", "여성_매출_건수"], "gender_count_sum"),
        ("당월_매출_건수", [f"연령대_{x}_매출_건수" for x in ["10", "20", "30", "40", "50", "60_이상"]], "age_count_sum"),
        ("유동__총_유동인구_수", ["유동__남성_유동인구_수", "유동__여성_유동인구_수"], "floating_gender_sum"),
        ("상주__총_상주인구_수", ["상주__남성_상주인구_수", "상주__여성_상주인구_수"], "resident_gender_sum"),
        ("직장__총_직장_인구_수", ["직장__남성_직장_인구_수", "직장__여성_직장_인구_수"], "worker_gender_sum"),
    ]
    rows: list[dict[str, object]] = []
    for total, parts, name in specs:
        complete = frame[[total, *parts]].notna().all(axis=1)
        total_values = frame.loc[complete, total].astype("float64")
        sum_values = frame.loc[complete, parts].sum(axis=1).astype("float64")
        scale = total_values.abs().clip(lower=1.0)
        relative = (total_values - sum_values).abs() / scale
        rows.append(
            {
                "relation_type": "arithmetic_sum",
                "feature_a": total,
                "feature_b": " + ".join(parts),
                "metric": name,
                "value": float((relative <= 1e-6).mean()) if len(relative) else math.nan,
                "secondary_value": float(relative.max()) if len(relative) else math.nan,
                "sample_count": int(len(relative)),
                "note": "value=exact match rate; secondary=max relative difference",
            }
        )
    return rows


def feature_relationships(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    rows = arithmetic_relationships(frame)
    numeric = [column for column in features if pd.api.types.is_numeric_dtype(frame[column]) and frame[column].nunique(dropna=True) > 1]
    sampled = frame[numeric].sample(min(CORRELATION_SAMPLE, len(frame)), random_state=RANDOM_SEED)
    pearson = sampled.corr(method="pearson")
    spearman = sampled.corr(method="spearman")
    for i, first in enumerate(numeric):
        for second in numeric[i + 1 :]:
            p = pearson.at[first, second]
            s = spearman.at[first, second]
            if (np.isfinite(p) and abs(p) >= 0.90) or (np.isfinite(s) and abs(s) >= 0.90):
                rows.append(
                    {
                        "relation_type": "numeric_correlation",
                        "feature_a": first,
                        "feature_b": second,
                        "metric": "pearson_and_spearman",
                        "value": p,
                        "secondary_value": s,
                        "sample_count": len(sampled),
                        "note": "deterministic discovery sample; threshold abs>=0.90",
                    }
                )

    categorical = [column for column in features if not pd.api.types.is_numeric_dtype(frame[column])]
    for i, first in enumerate(categorical):
        for second in categorical[i + 1 :]:
            paired = frame[[first, second]].dropna()
            if paired.empty:
                continue
            a = pooled_categories(paired[first])
            b = pooled_categories(paired[second])
            table = pd.crosstab(a, b)
            cv, _ = cramers_v(table)
            mi = mutual_info_score(paired[first].astype("string"), paired[second].astype("string"))
            nmi = normalized_mutual_info_score(paired[first].astype("string"), paired[second].astype("string"))
            one_to_one = paired.groupby(first, observed=True)[second].nunique().max() == 1 and paired.groupby(second, observed=True)[first].nunique().max() == 1
            positive_cells = table.to_numpy()[table.to_numpy() > 0]
            rows.append(
                {
                    "relation_type": "categorical_association",
                    "feature_a": first,
                    "feature_b": second,
                    "metric": "cramers_v",
                    "value": cv,
                    "secondary_value": nmi,
                    "sample_count": len(paired),
                    "note": f"MI={mi:.6g}; one_to_one={one_to_one}; min_positive_cell={int(positive_cells.min()) if len(positive_cells) else 0}; top100 pooled for V",
                }
            )

    # VIF is meaningful only after deterministic structural redundancy removal.
    # This screening mirrors contract option A without using Target information.
    raw_components = component_columns(
        [column for column in numeric if not column.startswith(("구성비__", "log1p__"))]
    )
    reference_shares = {
        "구성비__주말_매출_금액",
        "구성비__일요일_매출_금액",
        "구성비__시간대_21~24_매출_금액",
        "구성비__여성_매출_금액",
        "구성비__연령대_60_이상_매출_금액",
        "구성비__주말_매출_건수",
        "구성비__일요일_매출_건수",
        "구성비__시간대_건수~24_매출_건수",
        "구성비__여성_매출_건수",
        "구성비__연령대_60_이상_매출_건수",
        "구성비__유동__여성_유동인구_수",
        "구성비__유동__연령대_60_이상_유동인구_수",
        "구성비__유동__시간대_21_24_유동인구_수",
        "구성비__유동__일요일_유동인구_수",
        "구성비__상주__여성_상주인구_수",
        "구성비__상주__연령대_60_이상_상주인구_수",
        "구성비__직장__여성_직장_인구_수",
        "구성비__직장__연령대_60_이상_직장_인구_수",
    }
    structural_drop = raw_components | reference_shares
    vif_candidates = [
        column
        for column in numeric
        if not column.endswith("__분모0") and column not in structural_drop
    ]
    # Remove pairwise-perfect survivors before evaluating the remaining design.
    selected: list[str] = []
    for column in vif_candidates:
        duplicate_of = next(
            (
                prior
                for prior in selected
                if np.isfinite(pearson.at[column, prior])
                and abs(pearson.at[column, prior]) >= 0.999999
            ),
            None,
        )
        if duplicate_of is None:
            selected.append(column)
        else:
            rows.append(
                {
                    "relation_type": "vif_structural_drop",
                    "feature_a": column,
                    "feature_b": duplicate_of,
                    "metric": "pairwise_perfect_correlation",
                    "value": pearson.at[column, duplicate_of],
                    "secondary_value": spearman.at[column, duplicate_of],
                    "sample_count": len(sampled),
                    "note": "removed before VIF; Target-independent structural screen",
                }
            )
    vif_candidates = selected
    vif_sample = frame[vif_candidates].sample(min(VIF_SAMPLE, len(frame)), random_state=RANDOM_SEED)
    vif_sample = vif_sample.replace([np.inf, -np.inf], np.nan)
    vif_sample = vif_sample.fillna(vif_sample.median(numeric_only=True))
    std = vif_sample.std(ddof=0)
    vif_candidates = [column for column in vif_candidates if np.isfinite(std[column]) and std[column] > 0]
    standardized = (vif_sample[vif_candidates] - vif_sample[vif_candidates].mean()) / vif_sample[vif_candidates].std(ddof=0)
    correlation = np.nan_to_num(np.corrcoef(standardized.to_numpy(dtype="float64"), rowvar=False), nan=0.0)
    condition_number = float(np.linalg.cond(correlation))
    inverse = np.linalg.pinv(correlation, rcond=1e-8)
    rows.append(
        {
            "relation_type": "linear_design",
            "feature_a": "ALL_NUMERIC_CANDIDATES",
            "feature_b": "",
            "metric": "correlation_matrix_condition_number",
            "value": condition_number,
            "secondary_value": math.nan,
            "sample_count": len(vif_sample),
            "note": "after option-A raw-component, reference-share, and perfect-pair removal; pseudoinverse VIF follows",
        }
    )
    for column, value in zip(vif_candidates, np.diag(inverse), strict=True):
        if value >= 10:
            rows.append(
                {
                    "relation_type": "vif",
                    "feature_a": column,
                    "feature_b": "",
                    "metric": "pseudoinverse_vif",
                    "value": float(value),
                    "secondary_value": math.nan,
                    "sample_count": len(vif_sample),
                    "note": "screening only; recompute after approved structural removal inside train",
                }
            )
    return pd.DataFrame(rows)


def univariate_metrics(values: pd.Series, target: pd.Series) -> dict[str, object]:
    numeric = pd.to_numeric(values, errors="coerce").replace([np.inf, -np.inf], np.nan)
    complete = numeric.notna() & target.notna()
    x = numeric[complete].astype("float64")
    y = target[complete].astype("int8")
    x0, x1 = x[y.eq(0)], x[y.eq(1)]
    output: dict[str, object] = {
        "complete_count": len(x),
        "target0_count": len(x0),
        "target1_count": len(x1),
        "target0_mean": x0.mean(),
        "target1_mean": x1.mean(),
        "target0_median": x0.median(),
        "target1_median": x1.median(),
        "target0_p25": x0.quantile(0.25),
        "target1_p25": x1.quantile(0.25),
        "target0_p75": x0.quantile(0.75),
        "target1_p75": x1.quantile(0.75),
    }
    if len(x0) < 2 or len(x1) < 2 or x.nunique() < 2:
        return output
    pooled = math.sqrt(((len(x0) - 1) * x0.var(ddof=1) + (len(x1) - 1) * x1.var(ddof=1)) / max(len(x0) + len(x1) - 2, 1))
    point_biserial = np.corrcoef(x, y)[0, 1]
    try:
        auc = roc_auc_score(y, x)
        ap_high = average_precision_score(y, x)
        ap_low = average_precision_score(y, -x)
    except ValueError:
        auc = ap_high = ap_low = math.nan
    try:
        pvalue = mannwhitneyu(x0, x1, alternative="two-sided").pvalue
    except ValueError:
        pvalue = math.nan
    try:
        bins = pd.qcut(x, q=10, duplicates="drop")
        rates = pd.DataFrame({"bin": bins, "target": y}).groupby("bin", observed=True)["target"].agg(["count", "mean"])
        bin_rates = ";".join(f"{index + 1}:{row['count']}:{row['mean']:.6f}" for index, (_, row) in enumerate(rates.iterrows()))
        monotonicity = pd.Series(np.arange(len(rates))).corr(rates["mean"].reset_index(drop=True), method="spearman") if len(rates) > 1 else math.nan
    except ValueError:
        bin_rates, monotonicity = "", math.nan
    output.update(
        {
            "point_biserial": point_biserial,
            "standardized_effect_cohens_d": (x1.mean() - x0.mean()) / pooled if pooled > 0 else math.nan,
            "mann_whitney_pvalue": pvalue,
            "univariate_roc_auc_raw_direction": auc,
            "univariate_roc_auc_direction_free": max(auc, 1 - auc) if np.isfinite(auc) else math.nan,
            "univariate_auprc_high_direction": ap_high,
            "univariate_auprc_low_direction": ap_low,
            "univariate_auprc_best_direction": max(ap_high, ap_low) if np.isfinite(ap_high) else math.nan,
            "best_direction": "higher" if ap_high >= ap_low else "lower",
            "quantile_bin_count_target_rate": bin_rates,
            "quantile_target_rate_spearman": monotonicity,
        }
    )
    return output


def numeric_target_relationships(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    target = frame[TARGET]
    periods = sorted(frame["target_end_period"].astype(str).unique())
    split = len(periods) // 2
    early_periods, late_periods = set(periods[:split]), set(periods[split:])
    rows: list[dict[str, object]] = []
    for column in features:
        if not pd.api.types.is_numeric_dtype(frame[column]):
            continue
        row = {"feature": column, **univariate_metrics(frame[column], target)}
        missing = frame[column].isna()
        base = target.mean()
        row["missing_count"] = int(missing.sum())
        row["missing_target_rate"] = target[missing].mean() if missing.any() else math.nan
        row["missing_target_lift"] = row["missing_target_rate"] / base if missing.any() and base else math.nan
        early = frame["target_end_period"].astype(str).isin(early_periods)
        late = frame["target_end_period"].astype(str).isin(late_periods)
        early_metrics = univariate_metrics(frame.loc[early, column], target.loc[early])
        late_metrics = univariate_metrics(frame.loc[late, column], target.loc[late])
        row["early_effect_d"] = early_metrics.get("standardized_effect_cohens_d", math.nan)
        row["late_effect_d"] = late_metrics.get("standardized_effect_cohens_d", math.nan)
        row["early_auc_direction_free"] = early_metrics.get("univariate_roc_auc_direction_free", math.nan)
        row["late_auc_direction_free"] = late_metrics.get("univariate_roc_auc_direction_free", math.nan)
        early_d, late_d = row["early_effect_d"], row["late_effect_d"]
        row["effect_direction_stable"] = bool(np.isfinite(early_d) and np.isfinite(late_d) and np.sign(early_d) == np.sign(late_d))
        rows.append(row)
    result = pd.DataFrame(rows)
    result["mann_whitney_fdr_bh"] = bh_adjust(result["mann_whitney_pvalue"])
    return result


def categorical_target_relationships(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    target = frame[TARGET].astype("int8")
    base_rate = target.mean()
    rows: list[dict[str, object]] = []
    feature_tests: list[dict[str, object]] = []
    categorical = [column for column in features if not pd.api.types.is_numeric_dtype(frame[column])]
    for column in categorical:
        values = frame[column].astype("string").fillna("__MISSING__")
        pooled = pooled_categories(values)
        table = pd.crosstab(pooled, target)
        cv, pvalue = cramers_v(table)
        mi = mutual_info_score(values, target)
        feature_tests.append({"feature": column, "chi_square_pvalue": pvalue, "cramers_v": cv, "mutual_information": mi})
        grouped = pd.DataFrame({"category": values, "target": target}).groupby("category", observed=True)["target"].agg(["count", "sum", "mean"])
        for category, item in grouped.iterrows():
            rows.append(
                {
                    "feature": column,
                    "category": category,
                    "count": int(item["count"]),
                    "positive_count": int(item["sum"]),
                    "target_rate": float(item["mean"]),
                    "target_lift": float(item["mean"] / base_rate) if base_rate else math.nan,
                    "rare_lt_100": bool(item["count"] < RARE_CATEGORY_COUNT),
                }
            )
    tests = pd.DataFrame(feature_tests)
    if len(tests):
        tests["chi_square_fdr_bh"] = bh_adjust(tests["chi_square_pvalue"])
    return pd.DataFrame(rows).merge(tests, on="feature", how="left")


def drift_summary(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    periods = sorted(frame[PERIOD].astype("string").dropna().unique())
    baseline_period = periods[0]
    baseline_mask = frame[PERIOD].astype("string").eq(baseline_period)
    rows: list[dict[str, object]] = []
    for column in features:
        numeric = pd.api.types.is_numeric_dtype(frame[column])
        reference = frame.loc[baseline_mask, column]
        for period in periods:
            current = frame.loc[frame[PERIOD].astype("string").eq(period), column]
            row: dict[str, object] = {
                "feature": column,
                "kind": "numeric" if numeric else "categorical",
                "feature_period": period,
                "baseline_period": baseline_period,
                "count": len(current),
                "missing_rate": float(current.isna().mean()),
                "unique_count": int(current.nunique(dropna=True)),
                "psi": psi_numeric(reference, current) if numeric else psi_categorical(reference, current),
            }
            if numeric:
                numeric_current = pd.to_numeric(current, errors="coerce")
                row.update(
                    {
                        "mean": numeric_current.mean(),
                        "median": numeric_current.median(),
                        "p25": numeric_current.quantile(0.25),
                        "p75": numeric_current.quantile(0.75),
                    }
                )
            rows.append(row)
    return pd.DataFrame(rows)


def component_columns(features: list[str]) -> set[str]:
    columns: set[str] = set()
    for column in features:
        if column.endswith("_매출_금액") and column not in {"당월_매출_금액"} and not column.startswith(("최근_", "현재값_")):
            columns.add(column)
        if column.endswith("_매출_건수") and column != "당월_매출_건수":
            columns.add(column)
        if column.startswith(("유동__", "상주__", "직장__")) and "총_" not in column and not column.endswith(("결합_여부", "평균")):
            if "연령대_" in column or "남성_" in column or "여성_" in column or "시간대_" in column or any(day in column for day in "월요일 화요일 수요일 목요일 금요일 토요일 일요일".split()):
                columns.add(column)
    return columns


def write_derived_definitions(definitions: pd.DataFrame) -> None:
    lines = [
        "# Stage 4.5 파생 Feature 정의",
        "",
        "## 누수 방지와 계산 시점",
        "",
        "- 모든 값은 기준 분기 말에 존재하는 원천 열과 현재·과거 분기만 사용한다.",
        "- Rolling은 `상권_코드 × 서비스_업종_코드` 내부에서 계산하고 필요한 분기가 연속일 때만 값을 만든다.",
        "- 분모가 0인 비율은 무한대가 아니라 결측이며, 같은 분모의 `__분모0` Indicator를 함께 만든다.",
        "- Stage 4.5 실행에서는 Fold 1 Train만 변환했다. 승인 후 Stage 5에서는 각 Fold의 Feature 행에 동일한 결정적 계산을 적용하고 Target 기반 객체는 Fold Train 안에서만 Fit한다.",
        "",
        "## 계산식",
        "",
        "| Feature | 그룹 | 계산식 | 사용 가능 시점 |",
        "| --- | --- | --- | --- |",
    ]
    for row in definitions.itertuples(index=False):
        lines.append(f"| {row.feature} | {row.group} | {str(row.formula).replace('|', '/')} | {row.available_at} |")
    (OUTPUT / "derived_feature_definitions.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_contract(
    original_features: list[str],
    definitions: pd.DataFrame,
    profile: pd.DataFrame,
    relationships: pd.DataFrame,
) -> dict[str, object]:
    name_duplicates = {
        "상권_구분_코드_명",
        "상권_코드_명",
        "서비스_업종_코드_명",
        "변화__상권_변화_지표_명",
        "공간__상권_구분_코드",
        "공간__상권_구분_코드_명",
        "공간__상권_코드_명",
    }
    time_duplicate = {"기준_년분기_코드"}
    components = component_columns(original_features)
    all_constants = set(profile.loc[profile["constant"], "feature"])
    constants = all_constants & set(original_features)
    preserve_indicators = {column for column in original_features if column.endswith(("결합_여부", "연속_여부"))}
    removal = (name_duplicates | time_duplicate | components | constants) - preserve_indicators
    removal &= set(original_features)
    derived = definitions["feature"].tolist()
    derived_add = [feature for feature in derived if feature not in all_constants]
    actions: list[dict[str, str]] = []
    for feature in original_features:
        if feature in name_duplicates:
            action, scope, reason = "remove", "all", "코드와 중복되는 이름/공간 조인 중복"
        elif feature in time_duplicate:
            action, scope, reason = "remove", "all", "기준 연도와 분기로 완전히 복원 가능"
        elif feature in constants:
            action, scope, reason = "remove", "all", "발견 구간 상수"
        elif feature in components:
            action, scope, reason = "replace", "all", "원시 구성요소를 총계+구성비로 치환해 산술 중복 축소"
        else:
            action = "keep"
            scope = "auxiliary_ablation" if feature.startswith(("유동__", "상주__", "직장__", "시설__", "아파트__", "공간__")) else "common"
            reason = "원천 수준/추세/가용성 정보 유지"
        actions.append({"feature": feature, "origin": "original", "proposed_action": action, "model_scope": scope, "reason": reason})
    definition_by_feature = definitions.set_index("feature")
    for feature in derived:
        group = definition_by_feature.at[feature, "group"]
        if feature in all_constants:
            action, scope, reason = "remove", "all", "발견 구간 상수"
        else:
            action = "add"
            scope = "linear_only" if group == "log_transform" else "common"
            reason = "양수 왜도 완화" if group == "log_transform" else f"Stage 4.5 {group} 후보"
        actions.append(
            {
                "feature": feature,
                "origin": "derived",
                "proposed_action": action,
                "model_scope": scope,
                "reason": reason,
            }
        )
    action_frame = pd.DataFrame(actions)
    high_corr = relationships.loc[
        (relationships["relation_type"] == "numeric_correlation")
        & (relationships["value"].abs() >= 0.98)
    ]
    linear_condition = relationships.loc[
        relationships["relation_type"] == "linear_design", "value"
    ]
    condition_number = float(linear_condition.iloc[0]) if len(linear_condition) else math.nan
    lines = [
        "# Stage 4.5 Feature contract — D안 승인 완료",
        "",
        "> 사용자가 2026-08-15 12:17 KST에 D안(공통 기준선 + 트리 원시 변수군 Ablation)을 승인했다. 계약과 다음 단계 계획만 갱신했으며 Stage 5 학습·Ablation은 시작하지 않았다.",
        "",
        "## 승인된 D안 — 공통 기준선 + 트리 Ablation",
        "",
        "### 1. 모든 모델의 공통 기준선",
        "",
        "- 코드와 코드명은 코드만 유지하고, 시간은 `기준_연도`와 `기준_분기`만 유지한다.",
        "- 총매출·총거래·총인구는 유지하되 요일·시간대·성별·연령별 원시 구성요소는 구성비로 치환한다.",
        "- 평균 객단가, 점포당 지표, 개·폐업 강도, 인구 상호비율·밀도, 과거 Rolling, 변화 지속성 Indicator를 공통 Feature로 추가한다.",
        "- 유동·상주·직장인구, 시설, 아파트, 공간 변수는 보조 Feature군으로 유지해 Stage 5에서 데이터군별 Ablation을 가능하게 한다.",
        "- PCA는 적용하지 않는다.",
        "",
        "### 2. 선형 모델 확장",
        "",
        "- L2·L1·Elastic-Net Logistic에만 `log1p` 후보 10개를 추가한다.",
        "- 구조 제거 후 조건수가 높으므로 비정규화 Logistic은 사용하지 않는다.",
        "- 이 규제는 선형 모델군에만 해당하며 트리 모델을 제외하지 않는다.",
        "",
        "### 3. 트리 모델 원시 변수군 Ablation",
        "",
        "- Random Forest, Extra Trees, LightGBM, XGBoost, CatBoost를 모두 유지한다.",
        "- 각 트리는 공통 기준선으로 먼저 평가한다.",
        "- 매출금액, 거래건수, 유동인구, 상주인구, 직장인구의 원시 세부변수군을 공통 기준선에 한 번에 하나씩 독립적으로 추가한다.",
        "- `replace`로 분류된 원시 구성요소만 재추가할 수 있다. 코드명·상수·완전 중복처럼 `remove`인 변수는 되살리지 않는다.",
        "- 여러 원시 변수군을 자동 누적하지 않으며 Feature-set ID와 정확한 열 목록을 남긴다.",
        "",
        "### 4. 비교와 중지 조건",
        "",
        "- 공통 기준선 전체 모델 비교 후 트리 원시 변수군 Ablation을 수행하고, 적격 변형을 포함해 상위 3개 튜닝 후보를 정한다.",
        "- 유지 판단은 평균 AUPRC, 평균 AUROC, 최악 Fold AUPRC, Fold 표준편차를 함께 본다.",
        "- '개선'의 정확한 허용오차는 Stage 5 실행 전에 사용자 승인을 받아야 하며 아직 정하지 않았다.",
        "- 사용자 재개 요청 전에는 데이터 변환, 모델 Fit, Ablation, 기존 Dummy 체크포인트 재사용을 하지 않는다.",
        "",
        "## 검토했던 다른 안",
        "",
        "- A 구조 중복 축소형: D안의 공통 기준선으로 채택했다.",
        "- B 보수형: 원값과 파생값을 모두 유지하는 안으로, 메모리·공선성 부담 때문에 단독 채택하지 않았다.",
        "- C 모델군 분리형: 모델마다 처음부터 다른 Feature를 쓰는 안으로, 공통 기준 비교가 약해 단독 채택하지 않았다.",
        "",
        "## D안 공통 기준선 규모",
        "",
        f"- 원본 Feature: {len(original_features)}개",
        f"- 유지 제안: {len(original_features) - len(removal)}개",
        f"- 제거·치환 제안: {len(removal)}개",
        f"- 파생 생성 후보: {len(derived)}개, 상수 제외 후 추가 제안: {len(derived_add)}개(그중 선형 전용 log1p {int((definitions['group'] == 'log_transform').sum())}개)",
        f"- 발견 구간 절대 Pearson 0.98 이상 쌍: {len(high_corr)}개 — 자동 제거하지 않고 관계표에 보존",
        f"- 구조 제거 후 상관행렬 조건수: {condition_number:.4e} — 선형 모델군에서는 비정규화 Logistic을 제외하고 L1/L2/Elastic-Net Logistic을 비교하며, 트리 모델군은 모두 유지",
        "- 아래 표의 `replace`는 공통 기준선에서 구성비로 치환한다는 뜻이며, D안의 트리 원시 변수군 Ablation 후보가 될 수 있다.",
        "",
        "## Feature별 제안",
        "",
        "| Feature | 출처 | 제안 | 모델 범위 | 근거 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in action_frame.itertuples(index=False):
        lines.append(f"| {row.feature} | {row.origin} | {row.proposed_action} | {row.model_scope} | {row.reason} |")
    lines.extend(
        [
            "",
            "## 승인 후 다음 단계 반영 상태",
            "",
            "- `config/stage5.yaml`에 D안, 비교 순서, 트리 원시 변수군 5개와 실행 보류 상태를 기록했다.",
            "- `MVP 단계별 구현 체크리스트.md`의 Stage 5에 공통 기준선과 트리 Ablation 절차를 추가했다.",
            "- Stage 5 로더의 실제 Feature-set 생성·저장 구현은 다음 단계 작업으로 남겼다.",
            "- L1·Elastic-Net 선택과 트리 Importance는 실행 시 각 Fold Train 안에서만 Fit한다.",
            "- 사용자 요청에 따라 Stage 5는 아직 시작하지 않는다.",
        ]
    )
    (OUTPUT / "feature_contract.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "approved_option": "D_common_baseline_plus_tree_ablation",
        "original_feature_count": len(original_features),
        "proposed_original_keep_count": len(original_features) - len(removal),
        "proposed_original_remove_or_replace_count": len(removal),
        "proposed_derived_add_count": len(derived_add),
        "proposed_derived_remove_count": len(derived) - len(derived_add),
        "linear_only_log_count": int((definitions["group"] == "log_transform").sum()),
        "approval_status": "approved_2026-08-15T12:17+09:00",
    }


def write_summary(
    metadata: dict[str, object],
    profile: pd.DataFrame,
    relationships: pd.DataFrame,
    numeric_target: pd.DataFrame,
    categorical_target: pd.DataFrame,
    drift: pd.DataFrame,
    contract: dict[str, object],
) -> None:
    constants = profile.loc[profile["constant"], "feature"].tolist()
    near_constants = profile.loc[profile["near_constant_99_5pct"], "feature"].tolist()
    high_corr = relationships.loc[relationships["relation_type"].eq("numeric_correlation")].copy()
    high_corr["strength"] = high_corr[["value", "secondary_value"]].abs().max(axis=1)
    high_corr = high_corr.nlargest(10, "strength")
    top_numeric = numeric_target.nlargest(15, "univariate_roc_auc_direction_free")
    stable_numeric = numeric_target.loc[numeric_target["effect_direction_stable"]].nlargest(15, "univariate_roc_auc_direction_free")
    drift_max = drift.groupby("feature", observed=True)["psi"].max().sort_values(ascending=False).head(15)
    categorical_feature = (
        categorical_target[["feature", "cramers_v", "mutual_information", "chi_square_fdr_bh"]]
        .drop_duplicates("feature")
        .sort_values("cramers_v", ascending=False)
    )
    linear_condition = relationships.loc[
        relationships["relation_type"] == "linear_design", "value"
    ]
    condition_number = float(linear_condition.iloc[0]) if len(linear_condition) else math.nan
    lines = [
        "# Stage 4.5 모델링 EDA 요약",
        "",
        "## 실행 경계",
        "",
        f"- 발견 데이터: Fold {metadata['fold']} Train, Target 종료 {metadata['target_end_start']}~{metadata['target_end_end']}",
        f"- 행 수: {metadata['row_count']:,}, 양성: {metadata['positive_rows']:,} ({metadata['positive_rate']:.2%})",
        "- `stage4_development.parquet`는 위 기간 Predicate로만 읽었고, 2024 Validation Target은 읽지 않았다.",
        "- `stage4_locked_test_features.parquet`는 경로를 열거나 통계를 계산하지 않았다.",
        "- PNG/JPG/SVG/HTML/Notebook 등 플롯 산출물은 만들지 않았다.",
        "- 상관계수는 계산량을 제한하기 위해 고정 Seed의 발견 데이터 20,000행 표본을 사용했고, 분포·Target·Drift 통계는 발견 데이터 전체를 사용했다.",
        "",
        "## 구조 요약",
        "",
        f"- 원본 {metadata['original_feature_count']}개와 파생 {int((profile['origin'] == 'derived').sum())}개를 분석했다.",
        f"- 상수 {len(constants)}개: {', '.join(constants[:20]) if constants else '없음'}",
        f"- 99.5% 준상수 {len(near_constants)}개. 자동 제거하지 않고 `feature_profile.csv`에 표시했다.",
        f"- 절대 Pearson 또는 Spearman 0.90 이상 관계 {int((relationships['relation_type'] == 'numeric_correlation').sum())}쌍을 기록했다.",
        "- 합계·구성요소의 산술 일치율, 코드-코드명의 일대일 대응, VIF/조건수를 `feature_relationships.csv`에 함께 기록했다.",
        f"- 권장안 A의 구조 제거 후에도 조건수는 {condition_number:.4e}로 매우 높다. 선형 모델군에서는 비정규화 Logistic을 제외하고 L1/L2/Elastic-Net 정규화와 Fold 내부 선택을 유지한다. 이는 트리 모델 제외를 뜻하지 않으며 승인된 5개 트리 모델은 모두 비교한다.",
        "",
        "## Target 단변량 신호 상위",
        "",
        "| Feature | 방향무관 AUROC | 최선 방향 AUPRC | Cohen d | FDR q | 기간 방향 안정 |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in top_numeric.itertuples(index=False):
        lines.append(f"| {row.feature} | {row.univariate_roc_auc_direction_free:.4f} | {row.univariate_auprc_best_direction:.4f} | {row.standardized_effect_cohens_d:.4f} | {row.mann_whitney_fdr_bh:.3g} | {row.effect_direction_stable} |")
    lines.extend(["", "### 기간 방향이 안정적인 상위 신호", ""])
    lines.append(", ".join(stable_numeric["feature"].tolist()) if len(stable_numeric) else "없음")
    lines.extend(["", "## 범주형 관계", "", "| Feature | Cramér's V | Mutual Information | FDR q |", "| --- | ---: | ---: | ---: |"])
    for row in categorical_feature.head(10).itertuples(index=False):
        lines.append(f"| {row.feature} | {row.cramers_v:.4f} | {row.mutual_information:.4f} | {row.chi_square_fdr_bh:.3g} |")
    lines.extend(["", "## 높은 상관 관계 상위", "", "| Feature A | Feature B | Pearson | Spearman |", "| --- | --- | ---: | ---: |"])
    for row in high_corr.itertuples(index=False):
        lines.append(f"| {row.feature_a} | {row.feature_b} | {row.value:.4f} | {row.secondary_value:.4f} |")
    lines.extend(["", "## 발견 구간 Drift 상위", "", "| Feature | 최대 PSI |", "| --- | ---: |"])
    for feature, value in drift_max.items():
        lines.append(f"| {feature} | {value:.4f} |")
    lines.extend(
        [
            "",
            "## 해석 원칙과 결론",
            "",
            "- p-value와 FDR은 표본 수의 영향을 크게 받으므로 단독 선택 기준으로 쓰지 않았다. 효과크기, 단변량 판별력, 결측 Lift, 기간 방향 안정성, 서비스 시점 가용성을 함께 남겼다.",
            "- 극단값은 삭제하지 않았다. `feature_profile.csv`의 p01/p99와 min/max를 통해 선형 모델의 log1p·Fold Train 기반 Scaling 후보로만 처리했다.",
            "- 높은 상관만으로 자동 제거하지 않았다. 산술 합계, 코드-이름, 시간 중복처럼 의미가 명확한 구조 중복만 계약의 제거·치환 후보로 올렸다.",
            "- 범주형은 희소 범주와 고 Cardinality를 기록했으며 Stage 5 OneHotEncoder는 `handle_unknown=ignore`를 유지해야 한다.",
            f"- Feature contract는 `{contract['approved_option']}`으로 사용자 승인됐다.",
            "",
            "## Gate와 다음 단계",
            "",
            "- D안 승인으로 Gate 4.5는 통과했다.",
            "- 사용자 요청에 따라 Stage 5는 시작하지 않았으며, 실행 전 원시 변수군 유지 허용오차를 별도 승인받는다.",
        ]
    )
    (OUTPUT / "eda_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--relationships-only",
        action="store_true",
        help="Refresh structural relationships/VIF and dependent reports only.",
    )
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    source, original_features, metadata = load_discovery()
    expanded, definitions = build_stage45_features(source)
    definition_table = definitions_frame(definitions)
    derived_features = definition_table["feature"].tolist()
    features = [*original_features, *[column for column in derived_features if column not in original_features]]
    if args.relationships_only:
        profile = pd.read_csv(OUTPUT / "feature_profile.csv", encoding="utf-8-sig")
    else:
        profile = profile_features(expanded, features, set(original_features))
        profile.to_csv(OUTPUT / "feature_profile.csv", index=False, encoding="utf-8-sig")
    relationships = feature_relationships(expanded, features)
    relationships.to_csv(OUTPUT / "feature_relationships.csv", index=False, encoding="utf-8-sig")
    if args.relationships_only:
        numeric_target = pd.read_csv(OUTPUT / "numeric_target_relationships.csv", encoding="utf-8-sig")
        categorical_target = pd.read_csv(OUTPUT / "categorical_target_relationships.csv", encoding="utf-8-sig")
        drift = pd.read_csv(OUTPUT / "drift_summary.csv", encoding="utf-8-sig")
    else:
        numeric_target = numeric_target_relationships(expanded, features)
        numeric_target.to_csv(OUTPUT / "numeric_target_relationships.csv", index=False, encoding="utf-8-sig")
        categorical_target = categorical_target_relationships(expanded, features)
        categorical_target.to_csv(OUTPUT / "categorical_target_relationships.csv", index=False, encoding="utf-8-sig")
        drift = drift_summary(expanded, features)
        drift.to_csv(OUTPUT / "drift_summary.csv", index=False, encoding="utf-8-sig")
    write_derived_definitions(definition_table)
    contract = write_contract(original_features, definition_table, profile, relationships)
    write_summary(metadata, profile, relationships, numeric_target, categorical_target, drift, contract)
    manifest = {
        "created_at_kst": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="minutes"),
        "status": "gate45_completed_feature_contract_d_approved",
        "feature_contract_approved_at_kst": "2026-08-15T12:17+09:00",
        "stage5_execution_started": False,
        "discovery": metadata,
        "outputs": [
            "eda_summary.md",
            "feature_profile.csv",
            "feature_relationships.csv",
            "numeric_target_relationships.csv",
            "categorical_target_relationships.csv",
            "drift_summary.csv",
            "derived_feature_definitions.md",
            "feature_contract.md",
        ],
        "analysis": {
            "profiled_feature_count": len(features),
            "derived_feature_count": len(derived_features),
            "numeric_target_rows": len(numeric_target),
            "categorical_target_rows": len(categorical_target),
            "relationship_rows": len(relationships),
            "drift_rows": len(drift),
            "correlation_sample_rows": min(CORRELATION_SAMPLE, len(expanded)),
        },
        "contract": contract,
        "guards": {
            "validation_target_accessed": False,
            "locked_test_path_accessed": False,
            "plot_files_created": 0,
            "target_guided_period": [metadata["target_end_start"], metadata["target_end_end"]],
        },
    }
    (OUTPUT / "stage45_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
