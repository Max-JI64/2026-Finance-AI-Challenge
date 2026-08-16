"""Read-only integrity verification for the completed RE5 holdout run."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.run_re_stage5_quantile import compute_metrics
from src.models.re_stage5_artifact import load_re_stage5_artifact


HOLDOUT_DIR = ROOT / "reports" / "re_stage5" / "holdout"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    manifest_path = HOLDOUT_DIR / "holdout_manifest.json"
    access_path = HOLDOUT_DIR / "access.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    access = json.loads(access_path.read_text(encoding="utf-8"))

    failures: list[str] = []
    output_checks: list[dict[str, object]] = []
    for relative, expected in manifest["outputs"].items():
        path = ROOT / relative
        current_hash = sha256(path)
        current_bytes = path.stat().st_size
        hash_ok = current_hash == expected["sha256"]
        bytes_ok = current_bytes == expected["bytes"]
        output_checks.append(
            {
                "path": relative,
                "hash_ok": hash_ok,
                "bytes_ok": bytes_ok,
            }
        )
        if not hash_ok or not bytes_ok:
            failures.append(f"manifest mismatch: {relative}")

    manifest_hash_ok = sha256(manifest_path) == access["manifest_sha256"]
    if not manifest_hash_ok:
        failures.append("access-to-manifest hash mismatch")

    predictions = pd.read_parquet(HOLDOUT_DIR / "holdout_predictions.parquet")
    metrics = pd.read_csv(HOLDOUT_DIR / "holdout_metrics.csv").set_index("target")
    duplicate_target_row_ids = int(
        predictions.duplicated(["target", "re5_row_id"]).sum()
    )
    nonfinite_predictions = int(
        (~np.isfinite(predictions[["p10", "p50", "p90"]].to_numpy(float))).sum()
    )
    corrected_crossings = int(
        (
            (predictions["p10"] > predictions["p50"])
            | (predictions["p50"] > predictions["p90"])
        ).sum()
    )
    invalid_with_actual = int(
        ((~predictions["target_valid"]) & predictions["actual"].notna()).sum()
    )
    if any(
        value
        for value in (
            duplicate_target_row_ids,
            nonfinite_predictions,
            corrected_crossings,
            invalid_with_actual,
        )
    ):
        failures.append("prediction structural validation failed")

    target_checks: list[dict[str, object]] = []
    for target, group in predictions.groupby("target", sort=True):
        valid = group.loc[group["target_valid"]]
        calculated, _ = compute_metrics(
            valid["actual"].to_numpy(dtype=np.float64),
            valid[["raw_p10", "raw_p50", "raw_p90"]].to_numpy(dtype=np.float64),
        )
        metric_max_abs_diff = max(
            abs(float(value) - float(metrics.loc[target, metric]))
            for metric, value in calculated.items()
        )
        actual_missing_valid = int(valid["actual"].isna().sum())
        if len(group) != int(metrics.loc[target, "holdout_rows"]):
            failures.append(f"holdout row mismatch: {target}")
        if len(valid) != int(metrics.loc[target, "valid_rows"]):
            failures.append(f"valid row mismatch: {target}")
        if actual_missing_valid or metric_max_abs_diff > 1e-12:
            failures.append(f"metric recomputation mismatch: {target}")
        target_checks.append(
            {
                "target": target,
                "rows": len(group),
                "valid_rows": len(valid),
                "metric_max_abs_diff": metric_max_abs_diff,
            }
        )

    checkpoint_checks: list[dict[str, object]] = []
    for checkpoint_path in sorted((HOLDOUT_DIR / "checkpoints").glob("*.json")):
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        prediction_hash_ok = (
            sha256(ROOT / checkpoint["prediction_path"])
            == checkpoint["prediction_sha256"]
        )
        artifact_file = ROOT / checkpoint["artifact_path"]
        artifact_hash_ok = sha256(artifact_file) == checkpoint["artifact_sha256"]
        artifact = load_re_stage5_artifact(artifact_file)
        artifact_contract_ok = (
            artifact["contract_sha256"] == manifest["contract_sha256"]
            and artifact["selected_model"] == "lightgbm"
            and artifact["target"] == checkpoint["target"]
            and tuple(artifact["quantiles"]) == (0.1, 0.5, 0.9)
            and set(artifact["models"]) == {"p10", "p50", "p90"}
        )
        if not prediction_hash_ok or not artifact_hash_ok or not artifact_contract_ok:
            failures.append(f"checkpoint/artifact mismatch: {checkpoint_path.name}")
        checkpoint_checks.append(
            {
                "checkpoint": checkpoint_path.name,
                "status": checkpoint["status"],
                "prediction_hash_ok": prediction_hash_ok,
                "artifact_hash_ok": artifact_hash_ok,
                "artifact_contract_ok": artifact_contract_ok,
            }
        )

    log_text = (HOLDOUT_DIR / "evaluation.log").read_text(encoding="utf-8")
    log_error_markers = [
        marker for marker in ("Traceback", "ERROR", "FAILED") if marker in log_text
    ]
    log_completion_ok = (
        log_text.count("] DONE | target=") == 3 and "HOLDOUT 완료" in log_text
    )
    if log_error_markers or not log_completion_ok:
        failures.append("evaluation log validation failed")

    result = {
        "status": "passed" if not failures else "failed",
        "failures": failures,
        "access_status": access["status"],
        "target_opened": access["target_opened"],
        "model_reselection_prohibited": access["model_reselection_prohibited"],
        "manifest_hash_ok": manifest_hash_ok,
        "output_checks": output_checks,
        "prediction_rows": len(predictions),
        "periods": sorted(predictions["기준_년분기_코드"].unique().tolist()),
        "duplicate_target_row_ids": duplicate_target_row_ids,
        "nonfinite_predictions": nonfinite_predictions,
        "corrected_crossings": corrected_crossings,
        "invalid_with_actual": invalid_with_actual,
        "target_checks": target_checks,
        "checkpoint_checks": checkpoint_checks,
        "log_error_markers": log_error_markers,
        "log_completion_ok": log_completion_ok,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
