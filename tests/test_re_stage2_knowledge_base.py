from __future__ import annotations

import csv
import json
from pathlib import Path

from src.guards.re_stage2_guard import load_stage2_config


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed_re" / "policy" / "re_stage2"


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_metadata_matches_the_user_approved_portfolio() -> None:
    approved = set(load_stage2_config()["portfolio"]["policy_ids"])
    rows = read_csv("policy_metadata.csv")
    assert len(rows) == 10
    assert {row["policy_id"] for row in rows} == approved
    assert all(row["official_small_business_applicability"] == "확인" for row in rows)


def test_every_policy_has_rules_events_sources_and_chunks() -> None:
    approved = set(load_stage2_config()["portfolio"]["policy_ids"])
    for name in ("eligibility_rules.csv", "financial_metadata.csv", "source_manifest.csv"):
        assert {row["policy_id"] for row in read_csv(name)} == approved
    chunk_ids = {
        json.loads(line)["policy_id"]
        for line in (DATA / "policy_chunks.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    assert chunk_ids == approved
    assert {row["policy_id"] for row in read_csv("eligibility_examples.csv")} == approved


def test_source_manifest_is_reproducible() -> None:
    rows = read_csv("source_manifest.csv")
    assert rows
    assert all((ROOT / row["source_path"]).is_file() for row in rows)
    assert all(len(row["sha256"]) == 64 for row in rows)
    assert all(row["signature_status"] == "valid" for row in rows)


def test_unknown_values_are_explicit_not_blank() -> None:
    for name in ("policy_metadata.csv", "eligibility_rules.csv", "financial_metadata.csv"):
        rows = read_csv(name)
        assert rows
        assert all(value != "" for row in rows for key, value in row.items() if key != "notes")


def test_structured_qa_passed() -> None:
    qa = json.loads((ROOT / "reports" / "re_stage2" / "structured_qa.json").read_text(encoding="utf-8"))
    assert qa["result"] == "pass"
    assert all(qa["checks"].values())
