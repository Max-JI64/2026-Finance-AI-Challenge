"""Fail-closed execution guard for RE Stage 2."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config" / "re_stage2.yaml"


class Stage2GuardViolation(RuntimeError):
    """Raised when an action exceeds the approved RE Stage 2 boundary."""


def load_stage2_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    if not isinstance(config, dict):
        raise ValueError("RE Stage 2 config must be a mapping")
    for section in ("project", "portfolio", "source_contract", "guard", "paths"):
        if section not in config:
            raise ValueError(f"Missing RE Stage 2 config section: {section}")
    portfolio = config["portfolio"]
    if portfolio.get("selected_variant") != "A+C":
        raise ValueError("The approved portfolio must be A+C")
    if portfolio.get("selection_status") != "final_user_approved":
        raise ValueError("The final portfolio is not user-approved")
    ids = portfolio.get("policy_ids")
    if not isinstance(ids, list) or len(ids) != 10 or len(ids) != len(set(ids)):
        raise ValueError("The approved portfolio must contain 10 unique policy IDs")
    allowed = config["guard"].get("allowed_actions", [])
    blocked = config["guard"].get("blocked_until_later_approval", [])
    if set(allowed).intersection(blocked):
        raise ValueError("Guard allowed and blocked actions overlap")
    return config


def assert_stage2_action_allowed(
    action: str,
    path: Path = DEFAULT_CONFIG,
) -> None:
    config = load_stage2_config(path)
    allowed = set(config["guard"]["allowed_actions"])
    blocked = set(config["guard"]["blocked_until_later_approval"])
    if action in allowed:
        return
    if action in blocked:
        raise Stage2GuardViolation(f"Action '{action}' is blocked in RE Stage 2")
    raise Stage2GuardViolation(f"Unknown action '{action}' is denied fail-closed")

