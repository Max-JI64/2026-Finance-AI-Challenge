from __future__ import annotations

import json
from datetime import date

import pytest

from src.cashflow.errors import CashflowInputError
from src.cashflow.schemas import CashEvent, DetailedCashflowInput, LoanInput
from src.policy.apply import apply_policy_plan, combine_policy_plans
from src.policy.catalog import CalculationStatus, PolicyCatalog, SupportKind
from src.policy.converters import (
    convert_grant,
    convert_guarantee,
    convert_loan,
    convert_refinance,
    convert_voucher,
)
from src.policy.schemas import (
    CashDirection,
    EffectKind,
    GrantScenario,
    GuaranteeScenario,
    LoanScenario,
    RefinanceScenario,
    VoucherExpense,
    VoucherScenario,
)


@pytest.fixture(scope="module")
def catalog() -> PolicyCatalog:
    return PolicyCatalog()


def empty_baseline(*, opening_cash: int = 2_000_000) -> DetailedCashflowInput:
    return DetailedCashflowInput(
        reference_date=date(2026, 9, 1),
        opening_cash=opening_cash,
        safe_cash_threshold=1_000_000,
        events=[],
        loans=[],
    )


def test_catalog_preserves_all_30_reviewed_events_and_10_policies(
    catalog: PolicyCatalog,
) -> None:
    assert len(catalog.profiles) == 30
    assert len({profile.policy_id for profile in catalog.profiles}) == 10
    assert sum(
        profile.calculation_status is CalculationStatus.READY_WITH_USER_SCENARIO
        for profile in catalog.profiles
    ) == 27
    assert catalog.get("POL_SEMAS_STABILITY_VOUCHER_2026", "STABILITY_VOUCHER").support_kind is SupportKind.VOUCHER
    assert catalog.get("POL_SEOUL_ZERO_MARKET_2026_2", "ZERO_MARKET_GRANT").support_kind is SupportKind.REIMBURSEMENT_GRANT
    assert catalog.get("POL_SEMAS_REFINANCE_2026", "SEMAS_REFINANCE").official_interest_rate_percent == 4.5


def test_missing_facility_and_safe_account_terms_are_not_invented(
    catalog: PolicyCatalog,
) -> None:
    with pytest.raises(CashflowInputError) as facility:
        convert_loan(
            LoanScenario(
                policy_id="POL_SEOUL_FUND_2026",
                event_id="SEOUL_FACILITY",
                scenario_status="assumed_approved",
                approved_principal=10_000_000,
                execution_date=date(2026, 9, 1),
                payment_day=1,
                term_months=60,
                grace_months=12,
                repayment_method="equal_principal",
            ),
            catalog,
        )
    assert facility.value.code == "POLICY_SUBPRODUCT_REQUIRED"
    safe = catalog.get("POL_SEOUL_FUND_2026", "SEOUL_SAFE_ACCOUNT")
    assert safe.calculation_status is CalculationStatus.BLOCKED_MISSING_OFFICIAL_TERMS
    assert safe.maximum_amount is None


def test_not_approved_scenario_has_zero_events_and_no_probability(
    catalog: PolicyCatalog,
) -> None:
    plan = convert_grant(
        GrantScenario(
            policy_id="POL_SEOUL_RESTART_2026",
            event_id="RESTART_SEED",
            scenario_status="not_approved",
        ),
        catalog,
    )
    assert plan.events == []
    assert plan.summary["monetary_effect"] == 0
    text = json.dumps(plan.model_dump(mode="json"), ensure_ascii=False)
    assert "approval_probability" not in text
    assert "인과효과" in plan.conditional_notice


def test_reimbursement_grant_exposes_pre_financing_shortage(
    catalog: PolicyCatalog,
) -> None:
    plan = convert_grant(
        GrantScenario(
            policy_id="POL_SEOUL_CRISIS_TRACK2_2026H2",
            event_id="CRISIS_SOLUTION",
            scenario_status="assumed_approved",
            approved_support_amount=3_000_000,
            payment_date=date(2026, 10, 1),
            total_project_cost=4_000_000,
            eligible_expense_amount=3_000_000,
            vat_amount=300_000,
            expense_date=date(2026, 9, 1),
            expense_already_in_baseline=False,
        ),
        catalog,
    )
    result = apply_policy_plan(empty_baseline(), [plan])

    assert plan.summary["pre_financing_required"] == 4_000_000
    assert plan.summary["user_contribution"] == 1_000_000
    assert result.with_policy.weekly_summary.minimum_cash == -2_000_000
    assert result.with_policy.monthly_summary.ending_cash == 1_000_000
    assert result.delta["month6_ending_cash"] == -1_000_000


def test_grant_cap_and_policy_activity_period_are_enforced(
    catalog: PolicyCatalog,
) -> None:
    with pytest.raises(CashflowInputError) as cap:
        convert_grant(
            GrantScenario(
                policy_id="POL_SEOUL_RESTART_2026",
                event_id="RESTART_SEED",
                scenario_status="assumed_approved",
                approved_support_amount=2_000_001,
                payment_date=date(2026, 9, 10),
            ),
            catalog,
        )
    assert cap.value.code == "POLICY_AMOUNT_EXCEEDS_OFFICIAL_CAP"
    with pytest.raises(CashflowInputError) as period:
        convert_grant(
            GrantScenario(
                policy_id="POL_SEOUL_CRISIS_TRACK2_2026H2",
                event_id="CRISIS_SOLUTION",
                scenario_status="assumed_approved",
                approved_support_amount=1_000_000,
                payment_date=date(2026, 7, 15),
                total_project_cost=1_500_000,
                eligible_expense_amount=1_000_000,
                expense_date=date(2026, 6, 1),
            ),
            catalog,
        )
    assert period.value.code == "POLICY_EVENT_OUTSIDE_EFFECTIVE_PERIOD"


def test_voucher_reduces_only_eligible_costs_and_never_becomes_cash_grant(
    catalog: PolicyCatalog,
) -> None:
    plan = convert_voucher(
        VoucherScenario(
            policy_id="POL_SEMAS_STABILITY_VOUCHER_2026",
            event_id="STABILITY_VOUCHER",
            scenario_status="assumed_approved",
            awarded_amount=250_000,
            activation_date=date(2026, 9, 1),
            expiry_date=date(2026, 12, 31),
            expenses=[
                VoucherExpense(
                    expense_id="utility",
                    expense_date=date(2026, 9, 10),
                    expense_type="utility",
                    amount=100_000,
                ),
                VoucherExpense(
                    expense_id="insurance",
                    expense_date=date(2026, 10, 10),
                    expense_type="social_insurance",
                    amount=200_000,
                ),
                VoucherExpense(
                    expense_id="late-fuel",
                    expense_date=date(2027, 1, 10),
                    expense_type="vehicle_fuel",
                    amount=50_000,
                ),
            ],
        ),
        catalog,
    )
    baseline = DetailedCashflowInput(
        reference_date=date(2026, 9, 1),
        opening_cash=1_000_000,
        safe_cash_threshold=100_000,
        events=[
            CashEvent(
                event_id="utility-base",
                event_date=date(2026, 9, 10),
                event_type="tax_utility",
                amount=100_000,
                expense_type="utility",
            ),
            CashEvent(
                event_id="insurance-base",
                event_date=date(2026, 10, 10),
                event_type="tax_utility",
                amount=200_000,
                expense_type="social_insurance",
            ),
        ],
    )
    impact = apply_policy_plan(baseline, [plan])

    assert plan.summary["cash_inflow"] == 0
    assert plan.summary["cost_reduction"] == 250_000
    assert plan.summary["user_paid_eligible_expense"] == 50_000
    assert plan.summary["expired_or_unused_balance"] == 0
    assert all(event.effect_kind is EffectKind.COST_REDUCTION for event in plan.events)
    assert impact.delta["month6_ending_cash"] == 250_000


def test_direct_policy_loan_hand_calculation_and_grace_boundary(
    catalog: PolicyCatalog,
) -> None:
    plan = convert_loan(
        LoanScenario(
            policy_id="POL_SEOUL_FUND_2026",
            event_id="SEOUL_EMERGENCY",
            scenario_status="assumed_approved",
            approved_principal=10_000_000,
            execution_date=date(2026, 9, 1),
            payment_day=1,
            term_months=60,
            grace_months=12,
            repayment_method="equal_principal",
        ),
        catalog,
    )
    principal_events = [
        event for event in plan.events if event.effect_kind is EffectKind.DEBT_PRINCIPAL_REPAYMENT
    ]
    interest_events = [
        event for event in plan.events if event.effect_kind is EffectKind.DEBT_INTEREST
    ]

    assert plan.summary["new_debt_principal"] == 10_000_000
    assert plan.summary["gross_interest_rate_percent"] == 2.5
    assert len(principal_events) == 60
    assert all(event.amount == 0 for event in principal_events[:12])
    assert principal_events[12].amount == 208_333
    assert interest_events[0].amount == 20_833
    assert plan.summary["remaining_principal_at_maturity"] == 0
    impact = apply_policy_plan(empty_baseline(), [plan])
    assert impact.with_policy.debt_summary["remaining_principal_at_6_months"] == 10_000_000


def test_interest_subsidy_uses_user_bank_rate_and_official_support_phase(
    catalog: PolicyCatalog,
) -> None:
    plan = convert_loan(
        LoanScenario(
            policy_id="POL_SEOUL_FUND_2026",
            event_id="SEOUL_ECONOMY",
            scenario_status="assumed_approved",
            approved_principal=12_000_000,
            execution_date=date(2026, 9, 1),
            payment_day=1,
            term_months=60,
            grace_months=12,
            repayment_method="equal_principal",
            bank_interest_rate_percent=5.0,
        ),
        catalog,
    )
    net_interest = [
        event for event in plan.events if event.effect_kind is EffectKind.DEBT_INTEREST
    ]
    reductions = [
        event for event in plan.events if event.effect_kind is EffectKind.INTEREST_REDUCTION
    ]

    assert net_interest[0].amount == 32_000
    assert reductions[0].amount == 18_000
    assert len(reductions) == 48
    assert net_interest[48].amount > net_interest[47].amount
    assert plan.summary["total_interest_reduction"] > 0
    assert plan.summary["total_net_interest"] < plan.summary["total_gross_interest"]


def test_reference_rate_policy_and_invalid_term_option(
    catalog: PolicyCatalog,
) -> None:
    plan = convert_loan(
        LoanScenario(
            policy_id="POL_SEMAS_RECHALLENGE_2026",
            event_id="SEMAS_RECHALLENGE_GENERAL",
            scenario_status="assumed_approved",
            approved_principal=20_000_000,
            execution_date=date(2026, 9, 1),
            payment_day=1,
            term_months=60,
            grace_months=24,
            repayment_method="equal_principal",
            reference_interest_rate_percent=3.0,
        ),
        catalog,
    )
    assert plan.summary["gross_interest_rate_percent"] == pytest.approx(4.6)

    with pytest.raises(CashflowInputError) as caught:
        convert_loan(
            LoanScenario(
                policy_id="POL_SEOUL_FUND_2026",
                event_id="SEOUL_EMERGENCY",
                scenario_status="assumed_approved",
                approved_principal=10_000_000,
                execution_date=date(2026, 9, 1),
                payment_day=1,
                term_months=48,
                grace_months=12,
                repayment_method="equal_principal",
            ),
            catalog,
        )
    assert caught.value.code == "LOAN_TERMS_NOT_IN_OFFICIAL_OPTIONS"


def test_refinance_cancels_old_schedule_and_adds_new_schedule(
    catalog: PolicyCatalog,
) -> None:
    existing = LoanInput(
        loan_id="old-high-rate",
        principal=12_000_000,
        annual_interest_rate_percent=12,
        repayment_method="equal_principal",
        payment_day=1,
        maturity_date=date(2027, 8, 1),
        grace_months=0,
    )
    replacement = LoanInput(
        loan_id="new-refinance",
        principal=12_000_000,
        annual_interest_rate_percent=4.5,
        repayment_method="equal_principal",
        payment_day=1,
        maturity_date=date(2036, 8, 1),
        grace_months=0,
    )
    plan = convert_refinance(
        RefinanceScenario(
            policy_id="POL_SEMAS_REFINANCE_2026",
            event_id="SEMAS_REFINANCE",
            scenario_status="assumed_approved",
            execution_date=date(2026, 9, 1),
            existing_refinanced_loan=existing,
            replacement_loan=replacement,
        ),
        catalog,
    )
    baseline = DetailedCashflowInput(
        reference_date=date(2026, 9, 1),
        opening_cash=5_000_000,
        safe_cash_threshold=1_000_000,
        events=[],
        loans=[existing],
    )
    impact = apply_policy_plan(baseline, [plan])

    assert plan.summary["first_payment_change"] < 0
    assert plan.summary["new_payment_count"] == 120
    assert plan.summary["old_payment_count"] == 12
    assert plan.summary["total_interest_change"] > 0
    assert impact.with_policy.monthly_summary.ending_cash > impact.baseline.monthly_summary.ending_cash
    assert impact.with_policy.debt_summary["remaining_principal_at_6_months"] == 11_400_000
    assert impact.with_policy.debt_summary["total_interest_through_maturity"] == plan.summary["new_total_interest"]


def test_guarantee_without_loan_has_no_cash_and_linked_effect_cannot_duplicate(
    catalog: PolicyCatalog,
) -> None:
    info_only = convert_guarantee(
        GuaranteeScenario(
            policy_id="POL_SEOUL_RESTART_2026",
            event_id="RESTART_GUARANTEE",
            scenario_status="assumed_approved",
        ),
        catalog,
    )
    assert info_only.summary["cash_inflow"] == 0
    assert info_only.events[0].cash_direction is CashDirection.NONE

    linked_loan = LoanScenario(
        policy_id="POL_SEOUL_FUND_2026",
        event_id="SEOUL_RESTART_FUND",
        scenario_status="assumed_approved",
        approved_principal=10_000_000,
        execution_date=date(2026, 9, 1),
        payment_day=1,
        term_months=60,
        grace_months=12,
        repayment_method="equal_principal",
        bank_interest_rate_percent=5.0,
    )
    guarantee = convert_guarantee(
        GuaranteeScenario(
            policy_id="POL_SEOUL_RESTART_2026",
            event_id="RESTART_GUARANTEE",
            scenario_status="assumed_approved",
            linked_loan_scenario=linked_loan,
            guarantee_fee_amount=500_000,
            guarantee_fee_date=date(2026, 9, 1),
            guarantee_fee_support_amount=400_000,
        ),
        catalog,
    )
    direct_linked = convert_loan(linked_loan, catalog)
    assert guarantee.summary["guarantee_fee_support"] == 400_000
    with pytest.raises(CashflowInputError) as duplicate:
        combine_policy_plans([guarantee, direct_linked])
    assert duplicate.value.code == "DUPLICATE_LINKED_POLICY_EVENT"


def test_policy_application_is_deterministic(catalog: PolicyCatalog) -> None:
    plan = convert_grant(
        GrantScenario(
            policy_id="POL_SEOUL_RESTART_2026",
            event_id="RESTART_SEED",
            scenario_status="assumed_approved",
            approved_support_amount=2_000_000,
            payment_date=date(2026, 9, 15),
        ),
        catalog,
    )
    first = apply_policy_plan(empty_baseline(), [plan]).model_dump(mode="json")
    second = apply_policy_plan(empty_baseline(), [plan]).model_dump(mode="json")
    assert first == second
    assert first["delta"]["week13_ending_cash"] == 2_000_000
