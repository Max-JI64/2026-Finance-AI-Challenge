"""Create or verify the Stage 0-6 frozen-artifact hash inventory."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.guards.re_stage_guard import assert_action_allowed


REPORT_DIR = ROOT / "reports" / "re_stage1"
CSV_PATH = REPORT_DIR / "artifact_disposition.csv"
MANIFEST_PATH = REPORT_DIR / "artifact_freeze_manifest.json"

FROZEN_ROOTS = [
    "reports/stage0", "reports/stage1", "reports/stage2", "reports/stage3",
    "reports/stage4", "reports/stage45", "reports/stage5", "reports/stage6",
    "data/processed",
]

FROZEN_FILES = [
    "config/stage4.yaml", "config/stage5.yaml", "config/stage6.yaml",
    "src/data/audit_raw_archives.py", "src/data/run_stage2_quality.py",
    "src/data/build_stage3_panel.py", "src/data/build_stage4_dataset.py",
    "src/features/build_stage45_features.py", "src/analysis/run_stage45_eda.py",
    "src/features/build_stage5_feature_sets.py", "src/models/run_stage5_base_comparison.py",
    "src/models/run_stage5_optuna.py", "src/models/run_stage5_oof_ensemble.py",
    "src/models/run_stage5_final_2025.py", "src/models/build_stage6_reference.py",
    "src/models/stage6_risk_service.py",
]

LEGACY_REBUILD_FILES = [
    "app/main.py", "config/settings.yaml", "src/settings.py",
    "tests/test_app.py", "tests/test_settings.py",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_rows() -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    seen: set[str] = set()

    def add(path: Path, disposition: str, reason: str) -> None:
        relative = path.relative_to(ROOT).as_posix()
        if relative in seen or not path.is_file():
            return
        seen.add(relative)
        rows.append(
            {
                "path": relative,
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
                "disposition": disposition,
                "reason": reason,
                "overwrite_allowed": "no",
            }
        )

    for root_text in FROZEN_ROOTS:
        root = ROOT / root_text
        if root.exists():
            for path in sorted(root.rglob("*")):
                add(path, "frozen_baseline", "Stage 0-6 verified artifact")

    for relative in FROZEN_FILES:
        add(ROOT / relative, "frozen_reference", "Stage 0-6 reproducibility reference")

    for relative in LEGACY_REBUILD_FILES:
        add(
            ROOT / relative,
            "preserve_legacy_rebuild_later",
            "Preserve original; do not use as the new service contract",
        )

    return sorted(rows, key=lambda row: str(row["path"]))


def create() -> None:
    assert_action_allowed("hash_frozen_artifacts")
    if CSV_PATH.exists() or MANIFEST_PATH.exists():
        raise FileExistsError("Freeze inventory already exists; use --verify")
    rows = collect_rows()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "stage": "RE Stage 1",
        "status": "frozen",
        "file_count": len(rows),
        "total_size_bytes": sum(int(row["size_bytes"]) for row in rows),
        "inventory_sha256": sha256(CSV_PATH),
        "overwrite_allowed": False,
    }
    MANIFEST_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"FROZEN_FILES={len(rows)}")
    print(f"FROZEN_BYTES={summary['total_size_bytes']}")


def verify() -> None:
    if not CSV_PATH.exists() or not MANIFEST_PATH.exists():
        raise FileNotFoundError("Freeze inventory is missing")
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as stream:
        recorded = list(csv.DictReader(stream))
    current = {str(row["path"]): row for row in collect_rows()}
    errors: list[str] = []
    for row in recorded:
        path = row["path"]
        now = current.get(path)
        if now is None:
            errors.append(f"missing:{path}")
        elif now["sha256"] != row["sha256"]:
            errors.append(f"changed:{path}")
    unexpected = sorted(set(current).difference(row["path"] for row in recorded))
    errors.extend(f"new_in_frozen_scope:{path}" for path in unexpected)
    if errors:
        raise RuntimeError("Frozen artifact verification failed: " + "; ".join(errors[:20]))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest["inventory_sha256"] != sha256(CSV_PATH):
        raise RuntimeError("artifact_disposition.csv hash does not match manifest")
    print(f"FROZEN_FILES_VERIFIED={len(recorded)}")
    print("ARTIFACT_FREEZE=PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("create", "verify"))
    args = parser.parse_args()
    if args.mode == "create":
        create()
    else:
        verify()


if __name__ == "__main__":
    main()
