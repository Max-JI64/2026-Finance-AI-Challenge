from __future__ import annotations

import pytest

from src.guards.re_stage2_guard import (
    Stage2GuardViolation,
    assert_stage2_action_allowed,
    load_stage2_config,
)


def test_approved_ac_portfolio_has_ten_unique_policies() -> None:
    portfolio = load_stage2_config()["portfolio"]
    assert portfolio["selected_variant"] == "A+C"
    assert portfolio["selection_status"] == "final_user_approved"
    assert len(portfolio["policy_ids"]) == 10
    assert len(set(portfolio["policy_ids"])) == 10


def test_all_declared_stage2_actions_pass() -> None:
    config = load_stage2_config()
    for action in config["guard"]["allowed_actions"]:
        assert_stage2_action_allowed(action)


def test_all_later_actions_are_blocked() -> None:
    config = load_stage2_config()
    for action in config["guard"]["blocked_until_later_approval"]:
        with pytest.raises(Stage2GuardViolation):
            assert_stage2_action_allowed(action)


def test_unknown_action_is_blocked() -> None:
    with pytest.raises(Stage2GuardViolation):
        assert_stage2_action_allowed("unregistered_action")

