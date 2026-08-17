from __future__ import annotations

from datetime import date
import hashlib
import json

import pytest

from src.cashflow.schemas import CashEvent, DetailedCashflowInput, LoanInput
from src.policy import GrantScenario, LoanScenario, convert_grant, convert_loan
from src.policy.eligibility import (
    AvailabilityStatus,
    EligibilityDecision,
    EligibilityStatus,
)
from src.recommendation import (
    AlternativeKind,
    AlternativeSpec,
    CandidateContext,
    CandidateState,
    CombinationRegistry,
    CombinationRule,
    CombinationStatus,
    MarketScenario,
    compare_alternatives,
    route_candidate,
    suggest_safe_cash,
)
from src.settings import PROJECT_ROOT


AS_OF = date(2026, 8, 16)


def baseline() -> DetailedCashflowInput:
    events: list[CashEvent] = []
    months = [(2026, 9), (2026, 10), (2026, 11), (2026, 12), (2027, 1), (2027, 2)]
    for index, (year, month) in enumerate(months, start=1):
        events.extend(
            [
                CashEvent(
                    event_id=f"revenue-{index}",
                    event_date=date(year, month, 20),
                    event_type="operating_inflow",
                    amount=3_500_000,
                    description="월 매출입금",
                ),
                CashEvent(
                    event_id=f"rent-{index}",
                    event_date=date(year, month, 1),
                    event_type="fixed_cost",
                    amount=1_500_000,
                    expense_type="rent",
                    description="월 임대료",
                ),
                CashEvent(
                    event_id=f"labor-{index}",
                    event_date=date(year, month, 10),
                    event_type="fixed_cost",
                    amount=2_200_000,
                    expense_type="labor",
                    description="월 인건비",
                ),
                CashEvent(
                    event_id=f"variable-{index}",
                    event_date=date(year, month, 15),
                    event_type="variable_cost",
                    amount=900_000,
                    expense_type="purchase",
                    description="월 필수매입",
                ),
                CashEvent(
                    event_id=f"fuel-{index}",
                    event_date=date(year, month, 8),
                    event_type="fixed_cost",
                    amount=250_000,
                    expense_type="vehicle_fuel",
                    description="차량연료비",
                ),
            ]
        )
    return DetailedCashflowInput(
        reference_date=date(2026, 9, 1),
        opening_cash=1_000_000,
        safe_cash_threshold=2_000_000,
        events=events,
        loans=[
            LoanInput(
                loan_id="existing-high-rate",
                principal=30_000_000,
                annual_interest_rate_percent=12,
                repayment_method="equal_principal",
                payment_day=5,
                maturity_date=date(2031, 8, 5),
            )
        ],
    )


def context(policy_id: str, *, state: CandidateState = CandidateState.ACTIONABLE) -> CandidateContext:
    if state is CandidateState.ACTIONABLE:
        eligibility = "입력 기준 적격 후보"
        availability = "기준일상 접수 가능"
        items: list[str] = []
    elif state is CandidateState.CONDITIONAL:
        eligibility = "추가 확인 필요"
        availability = "접수 가능 여부 확인 필요"
        items = ["현재 접수상태", "세부 자격조건"]
    else:
        eligibility = "부적격"
        availability = "기준일상 접수 가능"
        items = ["지원대상 아님"]
    return CandidateContext(
        policy_id=policy_id,
        policy_version="test-v1",
        eligibility_status=eligibility,
        availability_status=availability,
        candidate_state=state,
        reason_summary="테스트 상태",
        items_to_confirm=items,
        as_of=AS_OF,
    )


def grant_plan(*, approved: bool = True):
    return convert_grant(
        GrantScenario(
            policy_id="POL_SEOUL_CRISIS_TRACK2_2026H2",
            event_id="CRISIS_SOLUTION",
            scenario_status="assumed_approved" if approved else "not_approved",
            approved_support_amount=3_000_000 if approved else None,
            payment_date=date(2026, 11, 15) if approved else None,
            total_project_cost=3_750_000 if approved else None,
            eligible_expense_amount=3_000_000 if approved else None,
            expense_date=date(2026, 9, 15) if approved else None,
        )
    )


def loan_plan(amount: int = 10_000_000):
    return convert_loan(
        LoanScenario(
            policy_id="POL_SEOUL_FUND_2026",
            event_id="SEOUL_EMERGENCY",
            scenario_status="assumed_approved",
            approved_principal=amount,
            execution_date=date(2026, 9, 1),
            payment_day=5,
            term_months=60,
            grace_months=12,
            repayment_method="equal_principal",
        )
    )


def market() -> MarketScenario:
    return MarketScenario(target_a_percent=-10, target_b_percent=-15)


def test_re6_candidate_routing_preserves_separate_statuses() -> None:
    decision = EligibilityDecision(
        policy_id="P",
        policy_version="v1",
        eligibility_status=EligibilityStatus.ELIGIBLE_CANDIDATE,
        availability_status=AvailabilityStatus.NEEDS_CURRENT_CHECK,
        overall_status="추가 확인 필요",
        as_of=AS_OF,
        rule_results=[],
        passed_rule_ids=[],
        failed_rule_ids=[],
        unknown_rule_ids=[],
        official_notice_url="https://example.test/notice",
        application_url="https://example.test/apply",
    )
    routed = route_candidate(decision)
    assert routed.candidate_state is CandidateState.CONDITIONAL
    assert routed.eligibility_status == "입력 기준 적격 후보"
    assert routed.availability_status == "접수 가능 여부 확인 필요"
    assert routed.items_to_confirm == ["기준일 현재 접수 가능 여부"]
    assert "rule_id" not in routed.model_dump(mode="json")


def test_safe_cash_is_next_28_day_required_outflows_and_user_editable() -> None:
    calculated = suggest_safe_cash(baseline())
    # Sep rent, labor, mandatory purchases, fuel + the Sep 5 existing-loan payment.
    assert calculated.suggested_amount == 5_650_000
    assert calculated.source.value == "calculated"
    overridden = suggest_safe_cash(baseline(), user_override=6_000_000)
    assert overridden.suggested_amount == 6_000_000
    assert overridden.source.value == "user_input"


def test_unknown_combination_requires_confirmation_and_duplicate_expense_is_blocked() -> None:
    registry = CombinationRegistry()
    status, reasons = registry.evaluate(
        ["A", "B"], deduplication_keys=["A:1", "B:1"]
    )
    assert status is CombinationStatus.NEEDS_CONFIRMATION
    assert reasons
    prohibited, _ = registry.evaluate(
        ["A", "B"],
        deduplication_keys=["A:1", "B:1"],
        same_expense_support_keys={"A": ["rent:2026-09"], "B": ["rent:2026-09"]},
    )
    assert prohibited is CombinationStatus.PROHIBITED


def test_evidence_backed_pair_can_be_combined() -> None:
    registry = CombinationRegistry(
        [
            CombinationRule(
                policy_ids=("A", "B"),
                status=CombinationStatus.COMPATIBLE,
                reason="공식 동시수혜 근거 확인",
                evidence="official:test",
            )
        ]
    )
    status, _ = registry.evaluate(["B", "A"], deduplication_keys=["B:1", "A:1"])
    assert status is CombinationStatus.COMPATIBLE


def test_same_market_basis_compares_no_action_cost_grant_and_loan() -> None:
    result = compare_alternatives(
        baseline(),
        market(),
        [
            AlternativeSpec(
                alternative_id="cost_5",
                label="비용 5% 절감",
                kind=AlternativeKind.COST_REDUCTION,
                cost_reduction_rate_percent=5,
            ),
            AlternativeSpec(
                alternative_id="grant",
                label="Track2 사후정산",
                kind=AlternativeKind.NON_DEBT_SUPPORT,
                plans=[grant_plan()],
                candidate_contexts=[context("POL_SEOUL_CRISIS_TRACK2_2026H2")],
                estimated_days_to_effect=75,
            ),
            AlternativeSpec(
                alternative_id="loan",
                label="긴급자영업자금",
                kind=AlternativeKind.POLICY_LOAN,
                plans=[loan_plan()],
                candidate_contexts=[context("POL_SEOUL_FUND_2026")],
                estimated_days_to_effect=14,
            ),
        ],
        as_of=AS_OF,
    )
    by_id = {item.alternative_id: item for item in result.alternatives}
    assert set(by_id) == {"no_action", "cost_5", "grant", "loan"}
    assert all(item.simulated for item in by_id.values())
    assert by_id["loan"].metrics is not None
    assert by_id["loan"].metrics.net_new_borrowing == 10_000_000
    assert by_id["loan"].metrics.first_policy_monthly_payment > 0
    assert by_id["loan"].metrics.total_interest_through_maturity is not None
    assert by_id["grant"].metrics.net_new_borrowing == 0
    assert by_id["cost_5"].metrics.support_or_cost_reduction > 0
    assert result.comparison_basis.startswith("13주는 Target A")


def test_conditional_policy_requires_explicit_assumption_and_never_ranks() -> None:
    spec = AlternativeSpec(
        alternative_id="conditional_grant",
        label="조건부 지원",
        kind=AlternativeKind.NON_DEBT_SUPPORT,
        plans=[grant_plan()],
        candidate_contexts=[context("POL_SEOUL_CRISIS_TRACK2_2026H2", state=CandidateState.CONDITIONAL)],
    )
    blocked = compare_alternatives(baseline(), market(), [spec], as_of=AS_OF)
    blocked_item = blocked.alternatives[1]
    assert blocked_item.simulated is False
    assumed = compare_alternatives(
        baseline(),
        market(),
        [spec.model_copy(update={"explicit_condition_assumption": True})],
        as_of=AS_OF,
    )
    conditional = assumed.alternatives[1]
    assert conditional.simulated is True
    assert conditional.ranking_eligible is False
    assert all("conditional_grant" not in rank.ordered_alternative_ids for rank in assumed.rankings)


def test_unknown_policy_pair_requires_both_explicit_assumptions_and_never_ranks() -> None:
    spec = AlternativeSpec(
        alternative_id="combo",
        label="지원 + 최소대출 복합안",
        kind=AlternativeKind.COMBINED,
        plans=[grant_plan(), loan_plan()],
        candidate_contexts=[
            context("POL_SEOUL_CRISIS_TRACK2_2026H2"),
            context("POL_SEOUL_FUND_2026"),
        ],
        explicit_condition_assumption=True,
        explicit_combination_assumption=True,
        cost_reduction_rate_percent=5,
    )
    result = compare_alternatives(baseline(), market(), [spec], as_of=AS_OF)
    combo = result.alternatives[1]
    assert combo.simulated is True
    assert combo.candidate_state is CandidateState.CONDITIONAL
    assert combo.combination_status is CombinationStatus.NEEDS_CONFIRMATION
    assert combo.ranking_eligible is False


def test_excluded_policy_is_not_simulated_or_ranked() -> None:
    result = compare_alternatives(
        baseline(),
        market(),
        [
            AlternativeSpec(
                alternative_id="excluded",
                label="부적격 지원",
                kind=AlternativeKind.NON_DEBT_SUPPORT,
                plans=[grant_plan()],
                candidate_contexts=[context("POL_SEOUL_CRISIS_TRACK2_2026H2", state=CandidateState.EXCLUDED)],
            )
        ],
        as_of=AS_OF,
    )
    excluded = result.alternatives[1]
    assert excluded.simulated is False
    assert excluded.metrics is None
    assert excluded.ranking_eligible is False


def test_not_approved_scenario_has_no_policy_cash_effect() -> None:
    result = compare_alternatives(
        baseline(),
        market(),
        [
            AlternativeSpec(
                alternative_id="grant_failed",
                label="지원 미승인",
                kind=AlternativeKind.NON_DEBT_SUPPORT,
                plans=[grant_plan(approved=False)],
                candidate_contexts=[context("POL_SEOUL_CRISIS_TRACK2_2026H2")],
            )
        ],
        as_of=AS_OF,
    )
    no_action = result.alternatives[0].metrics
    failed = result.alternatives[1].metrics
    assert no_action is not None and failed is not None
    assert failed.week13_ending_cash == no_action.week13_ending_cash
    assert failed.month6_ending_cash == no_action.month6_ending_cash
    assert failed.support_or_cost_reduction == 0


def test_payment_delay_changes_cash_timing_but_not_approval_probability() -> None:
    base_spec = AlternativeSpec(
        alternative_id="grant",
        label="지원",
        kind=AlternativeKind.NON_DEBT_SUPPORT,
        plans=[grant_plan()],
        candidate_contexts=[context("POL_SEOUL_CRISIS_TRACK2_2026H2")],
    )
    regular = compare_alternatives(baseline(), market(), [base_spec], as_of=AS_OF)
    delayed = compare_alternatives(
        baseline(),
        market(),
        [base_spec.model_copy(update={"alternative_id": "delayed", "payment_delay_days": 30})],
        as_of=AS_OF,
    )
    regular_metrics = regular.alternatives[1].metrics
    delayed_metrics = delayed.alternatives[1].metrics
    assert regular_metrics is not None and delayed_metrics is not None
    assert delayed_metrics.payment_delay_days == 30
    assert delayed_metrics.week13_ending_cash <= regular_metrics.week13_ending_cash
    assert "approval_probability" not in delayed.model_dump(mode="json")


def test_all_four_goal_rankings_are_reproducible_and_unweighted() -> None:
    specs = [
        AlternativeSpec(
            alternative_id="cost_5",
            label="비용절감",
            kind=AlternativeKind.COST_REDUCTION,
            cost_reduction_rate_percent=5,
        ),
        AlternativeSpec(
            alternative_id="loan",
            label="정책자금",
            kind=AlternativeKind.POLICY_LOAN,
            plans=[loan_plan()],
            candidate_contexts=[context("POL_SEOUL_FUND_2026")],
            estimated_days_to_effect=14,
        ),
    ]
    first = compare_alternatives(baseline(), market(), specs, as_of=AS_OF)
    second = compare_alternatives(baseline(), market(), specs, as_of=AS_OF)
    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    assert {rank.goal.value for rank in first.rankings} == {"최소부채", "최장생존", "최소상환", "빠른실행"}
    assert all(rank.top_alternative_id is not None for rank in first.rankings)
    assert all(rank.top_alternative_id == "loan" for rank in first.rankings)
    dumped = first.model_dump_json()
    assert "score" not in dumped.casefold()
    assert "fit_percentage" not in dumped
    assert "임의 적합도 백분율" in first.prohibited_claims


def test_pareto_engine_marks_dominated_actionable_alternative() -> None:
    result = compare_alternatives(
        baseline(),
        MarketScenario(target_a_percent=0, target_b_percent=0),
        [
            AlternativeSpec(
                alternative_id="cost_5",
                label="비용 5% 절감",
                kind=AlternativeKind.COST_REDUCTION,
                cost_reduction_rate_percent=5,
            )
        ],
        as_of=AS_OF,
    )
    no_action, cost = result.alternatives
    assert "cost_5" in no_action.dominated_by
    assert "cost_5" in result.pareto_frontier_ids
    assert cost.dominated_by == []


def test_direct_market_shock_overrides_model_targets() -> None:
    modeled = compare_alternatives(baseline(), market(), [], as_of=AS_OF)
    direct = compare_alternatives(
        baseline(),
        MarketScenario(
            target_a_percent=-10,
            target_b_percent=-15,
            direct_shock_13_week_percent=0,
            direct_shock_6_month_percent=0,
        ),
        [],
        as_of=AS_OF,
    )
    assert direct.alternatives[0].metrics.week13_ending_cash > modeled.alternatives[0].metrics.week13_ending_cash
    assert direct.alternatives[0].assumption_ledger[0]["source"] == "user_input"


def test_generated_re7_artifacts_are_complete_and_hash_verified() -> None:
    manifest_path = PROJECT_ROOT / "reports/re_stage7/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["sample_count"] == 3
    assert manifest["alternative_count_including_no_action"] == 6
    assert manifest["goal_ranking_count"] == 4
    assert len(manifest["hero_visible_curve_ids"]) == 4
    assert manifest["hero_toggle_ids"] == ["cost_reduction_5", "refinance"]
    for entry in [*manifest["samples"], *manifest["outputs"]]:
        path = PROJECT_ROOT / entry["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]

    result = json.loads(
        (PROJECT_ROOT / "data/processed_re/re_stage7/hero_decision_result.json").read_text(
            encoding="utf-8"
        )
    )
    by_id = {item["alternative_id"]: item for item in result["alternatives"]}
    assert by_id["no_action"]["ranking_eligible"] is True
    assert by_id["combined_safe_cash"]["candidate_state"] == "확인 후 비교"
    assert by_id["combined_safe_cash"]["combination_status"] == "확인 필요"
    assert by_id["combined_safe_cash"]["ranking_eligible"] is False
    assert by_id["emergency_loan"]["metrics"]["net_new_borrowing"] > 0
    assert by_id["emergency_loan"]["metrics"]["maximum_monthly_debt_service"] > 0
    assert by_id["emergency_loan"]["metrics"]["total_interest_through_maturity"] > 0
    assert by_id["refinance"]["metrics"]["net_new_borrowing"] == 0
    assert by_id["refinance"]["metrics"]["refinanced_principal"] == 30_000_000
    serialized = json.dumps(result, ensure_ascii=False)
    assert "fit_percentage" not in serialized
    assert "approval_probability" not in serialized
    sources = {
        entry["source"]
        for alternative in result["alternatives"]
        for entry in alternative["assumption_ledger"]
    }
    assert {"official", "user_input", "explicit_scenario_assumption", "calculated"} <= sources
