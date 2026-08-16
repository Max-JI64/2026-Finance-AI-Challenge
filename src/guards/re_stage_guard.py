"""Fail-closed action guard for RE Stage 1.

Only explicitly allowed, non-destructive preparation actions may run while the
final policy portfolio and later-stage data/model decisions remain pending.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "re_stage1.yaml"


class StageGuardViolation(RuntimeError):
    """Raised when an action is not explicitly allowed in the active stage."""


def load_guard_config(path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Load and structurally validate the RE Stage 1 guard configuration."""

    with path.open("r", encoding="utf-8") as stream:
        config = yaml.safe_load(stream)

    if not isinstance(config, dict):
        raise ValueError(f"RE Stage 1 config must be a mapping: {path}")

    for key in ("project", "portfolio_decision", "legacy_scope", "guard"):
        if key not in config:
            raise ValueError(f"Missing RE Stage 1 config section: {key}")

    guard = config["guard"]
    allowed = guard.get("allowed_actions")
    blocked = guard.get("blocked_until_later_approval")
    if not isinstance(allowed, list) or not isinstance(blocked, list):
        raise ValueError("Guard action lists must be present")
    if set(allowed).intersection(blocked):
        raise ValueError("An action cannot be both allowed and blocked")

    return config


def assert_action_allowed(
    action: str,
    path: Path = DEFAULT_CONFIG_PATH,
) -> None:
    """Allow only actions explicitly listed for RE Stage 1; reject unknowns."""

    config = load_guard_config(path)
    guard = config["guard"]
    allowed = set(guard["allowed_actions"])
    blocked = set(guard["blocked_until_later_approval"])

    if action in allowed:
        return
    if action in blocked:
        raise StageGuardViolation(
            f"Action '{action}' is blocked until the required later-stage approval"
        )
    raise StageGuardViolation(
        f"Unknown action '{action}' is denied because the guard is fail-closed"
    )


def validate_legacy_scope_disabled(
    path: Path = DEFAULT_CONFIG_PATH,
) -> None:
    """Verify that every retired Stage 7 behavior is explicitly disabled."""

    config = load_guard_config(path)
    enabled = [
        name for name, value in config["legacy_scope"].items() if value is not False
    ]
    if enabled:
        raise StageGuardViolation(
            "Retired legacy behaviors must remain disabled: " + ", ".join(enabled)
        )


def validate_final_portfolio_pending(
    path: Path = DEFAULT_CONFIG_PATH,
) -> None:
    """Verify that comparison output cannot be mistaken for a final selection."""

    decision = load_guard_config(path)["portfolio_decision"]
    if decision.get("status") != "comparison_required_final_selection_pending":
        raise StageGuardViolation("Final policy portfolio status is not pending")
    if decision.get("final_selection_requires_user_approval") is not True:
        raise StageGuardViolation("Final portfolio must require user approval")

