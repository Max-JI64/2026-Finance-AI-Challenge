"""Freeze the user-approved A+C portfolio as the RE Stage 2 input."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.guards.re_stage2_guard import assert_stage2_action_allowed, load_stage2_config


SOURCE = ROOT / "data" / "processed_re" / "policy" / "re_stage1" / "portfolio_candidates.csv"
OUTPUT_DIR = ROOT / "data" / "processed_re" / "policy" / "re_stage2"
OUTPUT = OUTPUT_DIR / "selected_policies.csv"
MANIFEST = OUTPUT_DIR / "selection_manifest.json"

POLICY_IDS = {
    "GRP_986459037b76bc05": "POL_SEOUL_FUND_2026",
    "GRP_059661575f800512": "POL_SEOUL_CRISIS_TRACK2_2026H2",
    "GRP_8addc5b8a4605054": "POL_SEOUL_CLOSURE_2026",
    "GRP_3e9edccb0ee86990": "POL_SEOUL_DIGITAL_MIDLIFE_2026H2",
    "GRP_9952c69b120ce343": "POL_SEOUL_ZERO_MARKET_2026_2",
    "GRP_0437d4b877340e15": "POL_SEOUL_SAFETY_TEST_2026H2",
    "GRP_eebf82e34fa3bb67": "POL_SEOUL_RESTART_2026",
    "GRP_b2fae65b4e109c08": "POL_SEMAS_REFINANCE_2026",
    "GRP_8a8a930f24156e8c": "POL_SEMAS_RECHALLENGE_2026",
    "GRP_5c8130070c7bb48f": "POL_SEMAS_STABILITY_VOUCHER_2026",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    assert_stage2_action_allowed("finalize_approved_portfolio")
    config = load_stage2_config()
    with SOURCE.open("r", encoding="utf-8-sig", newline="") as stream:
        source_rows = [
            row for row in csv.DictReader(stream) if row["portfolio_code"] == "A+C"
        ]
    if len(source_rows) != 10:
        raise ValueError(f"Expected 10 A+C rows, found {len(source_rows)}")
    if set(row["group_id"] for row in source_rows) != set(POLICY_IDS):
        raise ValueError("A+C group IDs differ from the approved mapping")

    rows = []
    for row in source_rows:
        rows.append(
            {
                "policy_id": POLICY_IDS[row["group_id"]],
                "group_id": row["group_id"],
                "portfolio": "A+C",
                "display_order": row["rank"],
                "policy_name": row["title"],
                "role": row["role"],
                "cashflow_potential": row["cashflow_potential"],
                "seoul_focus": row["seoul_focus"],
                "source_codes": row["source_codes"],
                "selection_status": "최종선정_사용자승인",
                "official_validation_status": "원문검증진행중",
            }
        )

    expected_ids = set(config["portfolio"]["policy_ids"])
    if set(row["policy_id"] for row in rows) != expected_ids:
        raise ValueError("Selected policy IDs differ from config/re_stage2.yaml")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    manifest = {
        "stage": "RE Stage 2",
        "selected_variant": "A+C",
        "selection_status": "final_user_approved",
        "policy_count": len(rows),
        "source": SOURCE.relative_to(ROOT).as_posix(),
        "source_sha256": sha256(SOURCE),
        "output": OUTPUT.relative_to(ROOT).as_posix(),
        "output_sha256": sha256(OUTPUT),
        "policy_ids": [row["policy_id"] for row in rows],
    }
    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("SELECTED_VARIANT=A+C")
    print(f"SELECTED_POLICIES={len(rows)}")


if __name__ == "__main__":
    main()

