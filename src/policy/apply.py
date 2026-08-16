"""Apply RE4 event plans to the RE3 detailed baseline without changing RE3 rules."""

from __future__ import annotations

from dataclasses import replace

from pydantic import BaseModel, ConfigDict

from src.cashflow.engine import CashflowResult, run_detailed_cashflow
from src.cashflow.errors import CashflowInputError
from src.cashflow.schemas import CashEvent, DetailedCashflowInput

from .schemas import CashDirection, EffectKind, PolicyPlan


class PolicyImpactResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    engine_version: str = "re4-v1"
    baseline: CashflowResult
    with_policy: CashflowResult
    plans: list[PolicyPlan]
    delta: dict[str, int | None]
    conditional_notice: str


def combine_policy_plans(plans: list[PolicyPlan]) -> list[PolicyPlan]:
    """Reject duplicated or officially linked events before any cash calculation."""

    dedup: dict[str, PolicyPlan] = {}
    event_keys: set[tuple[str, str, int, str]] = set()
    for plan in plans:
        if plan.deduplication_key in dedup:
            prior = dedup[plan.deduplication_key]
            raise CashflowInputError(
                "DUPLICATE_LINKED_POLICY_EVENT",
                "plans",
                f"{prior.event_id}와 {plan.event_id}는 같은 금융효과라 함께 적용할 수 없습니다.",
            )
        dedup[plan.deduplication_key] = plan
        for event in plan.events:
            key = (
                event.policy_id,
                event.event_id,
                event.sequence,
                event.effect_kind.value,
            )
            if key in event_keys:
                raise CashflowInputError(
                    "DUPLICATE_POLICY_EVENT", "plans", f"중복 이벤트: {key}"
                )
            event_keys.add(key)
    return plans


def _cash_event(plan: PolicyPlan, index: int) -> CashEvent | None:
    event = plan.events[index]
    if event.cash_direction is CashDirection.NONE or not event.amount:
        return None
    assert event.event_date is not None
    if event.cash_direction is CashDirection.INFLOW:
        event_type = "accounts_receivable"
        expense_type = None
    else:
        event_type = "one_time_expense"
        expense_type = "other"
    return CashEvent(
        event_id=(
            f"policy:{event.policy_id}:{event.event_id}:"
            f"{event.sequence}:{event.effect_kind.value}"
        ),
        event_date=event.event_date,
        event_type=event_type,
        amount=event.amount,
        expense_type=expense_type,
        description=f"[{event.effect_kind.value}] {event.description}",
        source=f"policy_plan:{plan.policy_version}",
    )


def _verify_refinance_baseline(
    baseline: DetailedCashflowInput, plans: list[PolicyPlan]
) -> None:
    loan_by_id = {loan.loan_id: loan for loan in baseline.loans}
    for plan in plans:
        existing_id = plan.summary.get("existing_loan_id")
        if not existing_id:
            continue
        if existing_id not in loan_by_id:
            raise CashflowInputError(
                "REFINANCED_LOAN_NOT_IN_BASELINE",
                "baseline.loans",
                f"대환 대상 {existing_id}가 기준 현금흐름에 없습니다.",
            )
        execution_events = [
            event
            for event in plan.events
            if event.effect_kind is EffectKind.EXISTING_DEBT_PAYOFF
        ]
        if not execution_events or execution_events[0].event_date != baseline.reference_date:
            raise CashflowInputError(
                "REFINANCE_BASELINE_ALIGNMENT_REQUIRED",
                "execution_date",
                "자동 전후비교는 기준일에 실행되는 대환만 지원합니다. 이후 실행은 실행일 기준 대출잔액으로 새 기준선을 만드세요.",
            )


def apply_policy_plan(
    baseline_input: DetailedCashflowInput, plans: list[PolicyPlan]
) -> PolicyImpactResult:
    plans = combine_policy_plans(plans)
    _verify_refinance_baseline(baseline_input, plans)
    adjustments: list[CashEvent] = []
    for plan in plans:
        for index in range(len(plan.events)):
            converted = _cash_event(plan, index)
            if converted is not None:
                adjustments.append(converted)
    payload = baseline_input.model_dump(mode="python")
    payload["events"] = [
        *[event.model_dump(mode="python") for event in baseline_input.events],
        *[event.model_dump(mode="python") for event in adjustments],
    ]
    adjusted_input = DetailedCashflowInput.model_validate(payload)
    baseline = run_detailed_cashflow(baseline_input)
    with_policy = run_detailed_cashflow(adjusted_input)
    new_debt = sum(int(plan.summary.get("new_debt_principal", 0)) for plan in plans)
    support = sum(
        int(plan.summary.get("support_amount", 0))
        + int(plan.summary.get("cost_reduction", 0))
        + int(plan.summary.get("guarantee_fee_support", 0))
        for plan in plans
    )
    horizon_end = baseline.monthly_summary.end_date
    new_principal = sum(
        int(event.amount or 0)
        for plan in plans
        for event in plan.events
        if event.effect_kind is EffectKind.NEW_DEBT_PRINCIPAL
    )
    payoff = sum(
        int(event.amount or 0)
        for plan in plans
        for event in plan.events
        if event.effect_kind is EffectKind.EXISTING_DEBT_PAYOFF
    )
    principal_paid = sum(
        int(event.amount or 0)
        for plan in plans
        for event in plan.events
        if event.effect_kind is EffectKind.DEBT_PRINCIPAL_REPAYMENT
        and event.event_date is not None
        and event.event_date <= horizon_end
    )
    reversed_principal = sum(
        int(event.amount or 0)
        for plan in plans
        for event in plan.events
        if event.effect_kind is EffectKind.EXISTING_PRINCIPAL_PAYMENT_REVERSAL
        and event.event_date is not None
        and event.event_date <= horizon_end
    )
    baseline_remaining = int(
        baseline.debt_summary.get("remaining_principal_at_6_months") or 0
    )
    adjusted_remaining = (
        baseline_remaining
        + new_principal
        - payoff
        - principal_paid
        + reversed_principal
    )
    baseline_total_interest = baseline.debt_summary.get("total_interest_through_maturity")
    interest_delta = sum(
        int(plan.summary.get("total_net_interest", 0))
        + int(plan.summary.get("total_interest_change", 0))
        for plan in plans
    )
    adjusted_total_interest = (
        int(baseline_total_interest) + interest_delta
        if baseline_total_interest is not None
        else None
    )
    with_policy = replace(
        with_policy,
        debt_summary={
            "initial_principal": (
                int(baseline.debt_summary.get("initial_principal") or 0)
                + new_principal
                - payoff
            ),
            "remaining_principal_at_6_months": adjusted_remaining,
            "total_interest_through_maturity": adjusted_total_interest,
            "principal_interest_split_available": True,
            "policy_adjusted": True,
            "new_policy_debt_principal": new_principal,
            "existing_debt_payoff": payoff,
        },
    )
    return PolicyImpactResult(
        baseline=baseline,
        with_policy=with_policy,
        plans=plans,
        delta={
            "week13_ending_cash": (
                with_policy.weekly_summary.ending_cash
                - baseline.weekly_summary.ending_cash
            ),
            "month6_ending_cash": (
                with_policy.monthly_summary.ending_cash
                - baseline.monthly_summary.ending_cash
            ),
            "week13_minimum_cash": (
                with_policy.weekly_summary.minimum_cash
                - baseline.weekly_summary.minimum_cash
            ),
            "month6_minimum_cash": (
                with_policy.monthly_summary.minimum_cash
                - baseline.monthly_summary.minimum_cash
            ),
            "new_debt_principal": new_debt,
            "month6_remaining_principal": (
                adjusted_remaining - baseline_remaining
            ),
            "support_or_cost_reduction": support,
        },
        conditional_notice=(
            "모든 결과는 정책 승인·실행을 가정한 기계적 비교이며 승인확률이나 "
            "정책의 인과효과를 나타내지 않습니다."
        ),
    )
