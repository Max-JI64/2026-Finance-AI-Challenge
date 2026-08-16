"""Verify prepared RE5 artifacts without fitting or evaluating a model."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "re_stage5"
MANIFEST_PATH = REPORT_DIR / "manifest.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    checks = dict(manifest["leakage_checks"])
    for name, output in manifest["outputs"].items():
        path = ROOT / output["path"]
        checks[f"output_exists__{name}"] = path.exists()
        checks[f"output_hash__{name}"] = (
            path.exists() and sha256_file(path) == output["sha256"]
        )
    holdout = pd.read_parquet(
        ROOT / manifest["outputs"]["holdout_features"]["path"]
    )
    checks["holdout_contains_no_target_column"] = not any(
        column.startswith("target_") for column in holdout.columns
    )
    feature_sets = json.loads(
        (ROOT / "reports" / "stage5" / "feature_sets.json").read_text(
            encoding="utf-8"
        )
    )
    approved = set(feature_sets["feature_sets"]["common_baseline"]["columns"])
    development_schema = set(
        pq.read_schema(ROOT / manifest["outputs"]["development"]["path"]).names
    )
    holdout_schema = set(
        pq.read_schema(ROOT / manifest["outputs"]["holdout_features"]["path"]).names
    )
    checks["development_contains_approved_197_features"] = approved.issubset(
        development_schema
    )
    checks["holdout_contains_approved_197_features"] = approved.issubset(
        holdout_schema
    )
    checks["model_training_progress_absent_or_not_completed"] = not (
        (REPORT_DIR / "cv" / "progress.json").exists()
        and json.loads(
            (REPORT_DIR / "cv" / "progress.json").read_text(encoding="utf-8")
        ).get("status")
        == "cv_completed_waiting_for_user_model_approval"
    )
    payload = {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "model_fits_executed_by_verifier": 0,
        "holdout_target_opened": False,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
