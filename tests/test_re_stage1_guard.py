from __future__ import annotations

import pytest

from src.guards.re_stage_guard import (
    StageGuardViolation,
    assert_action_allowed,
    load_guard_config,
    validate_final_portfolio_pending,
    validate_legacy_scope_disabled,
)


def test_every_declared_allowed_action_passes() -> None:
    config = load_guard_config()

    for action in config["guard"]["allowed_actions"]:
        assert_action_allowed(action)


def test_every_later_stage_action_is_blocked() -> None:
    config = load_guard_config()

    for action in config["guard"]["blocked_until_later_approval"]:
        with pytest.raises(StageGuardViolation):
            assert_action_allowed(action)


def test_unknown_action_is_denied() -> None:
    with pytest.raises(StageGuardViolation):
        assert_action_allowed("unregistered_action")


def test_retired_scope_and_final_selection_state_are_guarded() -> None:
    validate_legacy_scope_disabled()
    validate_final_portfolio_pending()

