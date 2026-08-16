"""Command-line verification for the RE Stage 1 fail-closed guard."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.guards.re_stage_guard import (
    StageGuardViolation,
    assert_action_allowed,
    load_guard_config,
    validate_final_portfolio_pending,
    validate_legacy_scope_disabled,
)


def main() -> None:
    config = load_guard_config()
    for action in config["guard"]["allowed_actions"]:
        assert_action_allowed(action)

    for action in config["guard"]["blocked_until_later_approval"]:
        try:
            assert_action_allowed(action)
        except StageGuardViolation:
            continue
        raise AssertionError(f"Blocked action was allowed: {action}")

    try:
        assert_action_allowed("unregistered_action")
    except StageGuardViolation:
        pass
    else:
        raise AssertionError("Unknown action was allowed")

    validate_legacy_scope_disabled()
    validate_final_portfolio_pending()
    print("RE_STAGE1_GUARD=PASS")


if __name__ == "__main__":
    main()
