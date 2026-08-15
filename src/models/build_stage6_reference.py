"""Build the versioned Stage 6 reference distribution and audit artifacts."""

from __future__ import annotations

import argparse
import json
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import joblib
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from src.features.build_stage45_features import build_stage45_features
from src.models.stage6_risk_service import (
    INTERNAL_SCORE,
    PROJECT_ROOT,
    friendly_feature_name,
    load_stage6_config,
    rank_reference_scores,
    sha256_file,
    transform_with_saved_preprocessor,
    transformed_source_columns,
)


def now_kst() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)


def _aggregate_importance(artifact: dict[str, Any]) -> pd.DataFrame:
    sources = transformed_source_columns(artifact["preprocessor"])
    gains = artifact["model"].booster_.feature_importance(importance_type="gain")
    if len(sources) != len(gains):
        raise RuntimeError("Model importance length differs from transformed features.")
    aggregate: dict[str, float] = {}
    for source, gain in zip(sources, gains):
        aggregate[source] = aggregate.get(source, 0.0) + float(gain)
    total = sum(aggregate.values())
    result = pd.DataFrame(
        {
            "source_feature": list(aggregate),
            "friendly_name": [friendly_feature_name(name) for name in aggregate],
            "gain": list(aggregate.values()),
        }
    )
    result["normalized_gain"] = result["gain"] / total if total else 0.0
    result = result.sort_values(
        ["gain", "source_feature"], ascending=[False, True], kind="stable"
    ).reset_index(drop=True)
    result.insert(0, "importance_rank", np.arange(1, len(result) + 1))
    return result


def build_reference(config_path: Path) -> dict[str, Any]:
    config = load_stage6_config(config_path)
    paths = config["artifacts"]
    model_path = PROJECT_ROOT / paths["model"]
    panel_path = PROJECT_ROOT / paths["source_panel"]
    stage4_manifest_path = PROJECT_ROOT / paths["stage4_manifest"]
    reference_path = PROJECT_ROOT / paths["reference_features"]
    report_dir = PROJECT_ROOT / "reports" / "stage6"
    area_catalog_path = PROJECT_ROOT / paths["area_catalog"]
    industry_catalog_path = PROJECT_ROOT / paths["industry_catalog"]
    importance_path = PROJECT_ROOT / paths["feature_importance"]
    manifest_path = PROJECT_ROOT / paths["manifest"]

    artifact = joblib.load(model_path)
    if artifact.get("operating_threshold") is not None:
        raise RuntimeError("Stage 6 v1 must not have a binary operating threshold.")
    if artifact.get("artifact_version") != "stage5_lightgbm_trial10_v1":
        raise RuntimeError("Unexpected final model artifact version.")
    stage4_manifest = json.loads(stage4_manifest_path.read_text(encoding="utf-8"))
    source_columns = list(stage4_manifest["feature_columns"])
    table = pq.read_table(panel_path, columns=source_columns)
    panel = table.to_pandas(split_blocks=True, self_destruct=True)
    if panel.duplicated(
        ["기준_년분기_코드", "상권_코드", "서비스_업종_코드"]
    ).any():
        raise RuntimeError("Stage 3 panel contains duplicate reference keys.")

    configured_quarter = str(config["service_ranking_policy"]["reference_quarter"])
    actual_latest = panel["기준_년분기_코드"].astype(str).max()
    if actual_latest != configured_quarter:
        raise RuntimeError(
            f"Configured reference quarter {configured_quarter} is not latest {actual_latest}."
        )

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", pd.errors.PerformanceWarning)
        enriched, _ = build_stage45_features(panel)
    feature_columns = list(artifact["source_feature_columns"])
    missing = sorted(set(feature_columns) - set(enriched.columns))
    if missing:
        raise RuntimeError(f"Reference feature columns are missing: {missing[:5]}")
    latest = enriched[enriched["기준_년분기_코드"].astype(str).eq(actual_latest)].copy()
    if latest.empty:
        raise RuntimeError("Latest reference quarter has no rows.")
    if latest.duplicated(["상권_코드", "서비스_업종_코드"]).any():
        raise RuntimeError("Latest reference quarter contains duplicate keys.")

    matrix = transform_with_saved_preprocessor(
        latest[feature_columns], artifact["preprocessor"]
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        scores = artifact["model"].predict_proba(matrix)[:, 1]
    if not np.isfinite(scores).all() or ((scores < 0) | (scores > 1)).any():
        raise RuntimeError("Model emitted invalid internal ranking scores.")
    latest[INTERNAL_SCORE] = scores.astype("float64")
    latest = rank_reference_scores(latest)

    keep = list(
        dict.fromkeys(
            [
                "기준_년분기_코드",
                "상권_코드",
                "상권_코드_명",
                "서비스_업종_코드",
                "서비스_업종_코드_명",
                *feature_columns,
                INTERNAL_SCORE,
                "primary_priority_rank",
                "primary_population_size",
                "primary_relative_risk_percentile",
                "primary_top_share_percent",
                "overall_priority_rank",
                "overall_population_size",
                "overall_relative_risk_percentile",
                "overall_top_share_percent",
            ]
        )
    )
    output = latest[keep].copy()
    for column in output.columns:
        if isinstance(output[column].dtype, pd.CategoricalDtype):
            output[column] = output[column].astype("string")

    reference_path.parent.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    temporary = reference_path.with_suffix(reference_path.suffix + ".tmp")
    output.to_parquet(temporary, index=False, compression="zstd")
    temporary.replace(reference_path)

    area_catalog = (
        panel[["상권_코드", "상권_코드_명"]]
        .drop_duplicates("상권_코드")
        .sort_values("상권_코드")
    )
    industry_catalog = (
        panel[["서비스_업종_코드", "서비스_업종_코드_명"]]
        .drop_duplicates("서비스_업종_코드")
        .sort_values("서비스_업종_코드")
    )
    area_catalog.to_csv(area_catalog_path, index=False, encoding="utf-8-sig")
    industry_catalog.to_csv(industry_catalog_path, index=False, encoding="utf-8-sig")
    importance = _aggregate_importance(artifact)
    importance.to_csv(importance_path, index=False, encoding="utf-8-sig")

    group_sizes = output.groupby("서비스_업종_코드", observed=True).size()
    manifest = {
        "created_at_kst": now_kst(),
        "status": "completed",
        "service_ranking_policy_version": config["service_ranking_policy"]["version"],
        "model_artifact_version": artifact["artifact_version"],
        "model_role": "relative_area_industry_risk_ranking",
        "raw_score_exposure": "internal_only",
        "binary_operating_threshold": None,
        "reference_quarter": actual_latest,
        "reference_quarter_display": f"{actual_latest[:4]}년 {actual_latest[-1]}분기",
        "reference_rows": int(len(output)),
        "reference_area_count": int(output["상권_코드"].nunique()),
        "reference_industry_count": int(output["서비스_업종_코드"].nunique()),
        "primary_group_size_min": int(group_sizes.min()),
        "primary_group_size_max": int(group_sizes.max()),
        "duplicate_reference_keys": int(
            output.duplicated(["상권_코드", "서비스_업종_코드"]).sum()
        ),
        "finite_internal_scores": bool(np.isfinite(scores).all()),
        "feature_count": len(feature_columns),
        "transformed_feature_count": int(matrix.shape[1]),
        "global_importance_rows": int(len(importance)),
        "tie_method": config["ranking"]["tie_method"],
        "percentile_formula": config["ranking"]["percentile_formula"],
        "outputs": {
            "reference_features": str(reference_path.relative_to(PROJECT_ROOT)),
            "area_catalog": str(area_catalog_path.relative_to(PROJECT_ROOT)),
            "industry_catalog": str(industry_catalog_path.relative_to(PROJECT_ROOT)),
            "feature_importance": str(importance_path.relative_to(PROJECT_ROOT)),
        },
        "sha256": {
            "model": sha256_file(model_path),
            "reference_features": sha256_file(reference_path),
            "area_catalog": sha256_file(area_catalog_path),
            "industry_catalog": sha256_file(industry_catalog_path),
            "feature_importance": sha256_file(importance_path),
        },
    }
    atomic_json(manifest_path, manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=PROJECT_ROOT / "config" / "stage6.yaml")
    args = parser.parse_args()
    manifest = build_reference(args.config)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
