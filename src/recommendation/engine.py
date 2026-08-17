"""Deterministic RE Stage 7 scenario, comparison, ranking and Pareto engine."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from itertools import combinations
from typing import Iterable

from src.cashflow.engine import CashflowResult, run_detailed_cashflow
from src.cashflow.schemas import CashEvent, DetailedCashflowInput, EventType
from src.policy import apply_policy_plan
from src.policy.schemas import CashDirection, EffectKind, PolicyPlan, ScenarioStatus, ValueSource

from .routing import CombinationRegistry
from .schemas import (
    AlternativeKind,
    AlternativeMetrics,
    AlternativeResult,
    AlternativeSpec,
    CandidateState,
    CombinationStatus,
    DecisionResult,
    ExecutionPlan,
    GoalRanking,
    MarketScenario,
    SafeCashSuggestion,
    UserGoal,
)


EXPENSE_EVENTS = {
    EventType.FIXED_COST,
    EventType.VARIABLE_COST,
    EventType.TAX_UTILITY,
    EventType.ACCOUNTS_PAYABLE,
    EventType.ONE_TIME_EXPENSE,
}


def _won(value: Decimal | float | int) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def suggest_safe_cash(
    baseline: DetailedCashflowInput,
    *,
    user_override: int | None = None,
) -> SafeCashSuggestion:
    """Sum required outflows dated in the next 28 days; never invent a fixed amount."""

    if user_override is not None:
        if user_override < 0:
            raise ValueError("user_override cannot be negative")
        return SafeCashSuggestion(
            status="사용자 직접 입력",
            suggested_amount=user_override,
            source=ValueSource.USER_INPUT,
            explanation="사용자가 4주 필수지출 기준 권장값을 직접 수정했습니다.",
        )
    horizon_end = baseline.reference_date + timedelta(days=27)
    required = [
        event
        for event in baseline.events
        if baseline.reference_date <= event.event_date <= horizon_end
        and event.event_type in EXPENSE_EVENTS
    ]
    loan_payments: list[tuple[str, int]] = []
    calculated = run_detailed_cashflow(baseline)
    for payment in calculated.loan_schedules:
        when = date.fromisoformat(str(payment["payment_date"]))
        if baseline.reference_date <= when <= horizon_end:
            loan_payments.append(
                (
                    f"loan:{payment['loan_id']}:{payment['payment_number']}",
                    int(payment["total_payment"]),
                )
            )
    included_ids = [event.event_id for event in required] + [item[0] for item in loan_payments]
    if not included_ids:
        return SafeCashSuggestion(
            status="직접 입력 필요",
            suggested_amount=None,
            source=ValueSource.UNCONFIRMED,
            missing_inputs=["향후 28일 필수 지출 일정"],
            explanation="필수 지출 일정이 없어 임의 정액을 만들지 않습니다.",
        )
    amount = sum(event.amount for event in required) + sum(item[1] for item in loan_payments)
    return SafeCashSuggestion(
        status="권장값 계산 완료",
        suggested_amount=amount,
        source=ValueSource.CALCULATED,
        included_event_ids=included_ids,
        explanation="향후 28일의 필수 지출 일정과 대출상환 일정 합계입니다.",
    )


def minimum_loan_for_safe_cash(result: CashflowResult, safe_cash_amount: int) -> int:
    """Mechanical principal top-up before new-loan repayment effects."""

    return max(0, safe_cash_amount - result.weekly_summary.minimum_cash)


def _apply_market_shock(
    baseline: DetailedCashflowInput,
    shock_percent: float,
    *,
    horizon_label: str,
) -> DetailedCashflowInput:
    multiplier = Decimal("1") + Decimal(str(shock_percent)) / Decimal("100")
    events = []
    for event in baseline.events:
        payload = event.model_dump(mode="python")
        if event.event_type in {EventType.OPERATING_INFLOW, EventType.ACCOUNTS_RECEIVABLE}:
            payload["amount"] = _won(Decimal(event.amount) * multiplier)
            payload["source"] = f"re7_market_scenario:{horizon_label}"
        events.append(payload)
    payload = baseline.model_dump(mode="python")
    payload["events"] = events
    return DetailedCashflowInput.model_validate(payload)


def _apply_cost_reduction(
    baseline: DetailedCashflowInput,
    rate_percent: float,
) -> tuple[DetailedCashflowInput, int]:
    if not rate_percent:
        return baseline, 0
    multiplier = Decimal("1") - Decimal(str(rate_percent)) / Decimal("100")
    events = []
    reduction = 0
    for event in baseline.events:
        payload = event.model_dump(mode="python")
        if event.event_type in EXPENSE_EVENTS:
            adjusted = _won(Decimal(event.amount) * multiplier)
            reduction += event.amount - adjusted
            payload["amount"] = adjusted
            payload["source"] = "re7_user_cost_reduction_assumption"
        events.append(payload)
    payload = baseline.model_dump(mode="python")
    payload["events"] = events
    return DetailedCashflowInput.model_validate(payload), reduction


def _delay_plans(plans: list[PolicyPlan], delay_days: int) -> list[PolicyPlan]:
    if not delay_days:
        return plans
    shifted: list[PolicyPlan] = []
    for plan in plans:
        events = [
            event.model_copy(
                update={
                    "event_date": (
                        event.event_date + timedelta(days=delay_days)
                        if event.event_date is not None
                        else None
                    )
                }
            )
            for event in plan.events
        ]
        shifted.append(plan.model_copy(update={"events": events}))
    return shifted


def _run_alternative(
    baseline: DetailedCashflowInput,
    plans: list[PolicyPlan],
    cost_reduction_rate_percent: float,
) -> tuple[CashflowResult, int]:
    adjusted, reduction = _apply_cost_reduction(baseline, cost_reduction_rate_percent)
    if plans:
        return apply_policy_plan(adjusted, plans).with_policy, reduction
    return run_detailed_cashflow(adjusted), reduction


def _survival_days(result: CashflowResult, horizon: str) -> int:
    summary = result.weekly_summary if horizon == "13_week" else result.monthly_summary
    if summary.first_cash_depletion_date is None:
        return (summary.end_date - summary.start_date).days + 1
    return max(0, (summary.first_cash_depletion_date - summary.start_date).days)


def _plan_amounts(plans: Iterable[PolicyPlan]) -> dict[str, int]:
    values = {
        "new_debt": 0,
        "payoff": 0,
        "refinanced": 0,
        "support": 0,
        "first_payment": 0,
    }
    for plan in plans:
        values["new_debt"] += int(plan.summary.get("new_debt_principal", 0))
        values["payoff"] += int(plan.summary.get("existing_debt_payoff", 0))
        values["refinanced"] += int(plan.summary.get("refinanced_principal", 0))
        values["support"] += (
            int(plan.summary.get("support_amount", 0))
            + int(plan.summary.get("cost_reduction", 0))
            + int(plan.summary.get("guarantee_fee_support", 0))
        )
        values["first_payment"] += int(
            plan.summary.get("new_first_payment", plan.summary.get("first_payment", 0))
        )
    return values


def _metrics(
    week_result: CashflowResult,
    month_result: CashflowResult,
    plans: list[PolicyPlan],
    *,
    cost_reduction: int,
    spec: AlternativeSpec,
    confirmation_count: int,
) -> AlternativeMetrics:
    amounts = _plan_amounts(plans)
    monthly_services = [
        period.debt_principal + period.debt_interest + period.debt_service_combined
        for period in month_result.monthly_6
    ]
    for plan in plans:
        for event in plan.events:
            if event.event_date is None:
                continue
            for index, period in enumerate(month_result.monthly_6):
                if not period.start_date <= event.event_date <= period.end_date:
                    continue
                if event.effect_kind in {
                    EffectKind.DEBT_PRINCIPAL_REPAYMENT,
                    EffectKind.DEBT_INTEREST,
                }:
                    monthly_services[index] += int(event.amount or 0)
                elif event.effect_kind in {
                    EffectKind.EXISTING_PRINCIPAL_PAYMENT_REVERSAL,
                    EffectKind.EXISTING_INTEREST_PAYMENT_REVERSAL,
                }:
                    monthly_services[index] -= int(event.amount or 0)
                break
    debt = month_result.debt_summary
    principal = int(debt.get("initial_principal") or 0)
    interest = debt.get("total_interest_through_maturity")
    total_obligation = principal + int(interest) if interest is not None else None
    return AlternativeMetrics(
        week13_ending_cash=week_result.weekly_summary.ending_cash,
        month6_ending_cash=month_result.monthly_summary.ending_cash,
        week13_minimum_cash=week_result.weekly_summary.minimum_cash,
        month6_minimum_cash=month_result.monthly_summary.minimum_cash,
        week13_depletion_date=week_result.weekly_summary.first_cash_depletion_date,
        month6_depletion_date=month_result.monthly_summary.first_cash_depletion_date,
        survival_days_13_week=_survival_days(week_result, "13_week"),
        survival_days_6_month=_survival_days(month_result, "6_month"),
        survives_13_weeks=week_result.weekly_summary.first_cash_depletion_date is None,
        survives_6_months=month_result.monthly_summary.first_cash_depletion_date is None,
        net_new_borrowing=amounts["new_debt"] - amounts["payoff"],
        refinanced_principal=amounts["refinanced"],
        maximum_monthly_debt_service=max(monthly_services, default=0),
        first_policy_monthly_payment=amounts["first_payment"],
        total_interest_through_maturity=(int(interest) if interest is not None else None),
        total_repayment_obligation=total_obligation,
        support_or_cost_reduction=amounts["support"] + cost_reduction,
        payment_delay_days=spec.payment_delay_days,
        application_deadline=spec.application_deadline,
        confirmation_item_count=confirmation_count,
        days_to_first_effect=spec.estimated_days_to_effect + spec.payment_delay_days,
        cash_needed_before_payment=_cash_needed_before_first_policy_inflow(
            week_result, plans
        ),
    )


def _candidate_state(spec: AlternativeSpec) -> CandidateState:
    states = {context.candidate_state for context in spec.candidate_contexts}
    if CandidateState.EXCLUDED in states:
        return CandidateState.EXCLUDED
    if CandidateState.CONDITIONAL in states:
        return CandidateState.CONDITIONAL
    return CandidateState.ACTIONABLE


def _dominates(left: AlternativeMetrics, right: AlternativeMetrics) -> bool:
    left_values = (
        left.survival_days_6_month,
        left.month6_ending_cash,
        -left.net_new_borrowing,
        -left.maximum_monthly_debt_service,
        -(left.total_interest_through_maturity or 0),
        -left.days_to_first_effect,
    )
    right_values = (
        right.survival_days_6_month,
        right.month6_ending_cash,
        -right.net_new_borrowing,
        -right.maximum_monthly_debt_service,
        -(right.total_interest_through_maturity or 0),
        -right.days_to_first_effect,
    )
    return all(a >= b for a, b in zip(left_values, right_values)) and any(
        a > b for a, b in zip(left_values, right_values)
    )


GOAL_MEANINGS = {
    UserGoal.MINIMUM_DEBT: "13주 비고갈을 먼저 충족한 뒤 순신규차입과 총상환의무가 작은 순서",
    UserGoal.LONGEST_SURVIVAL: "6개월 내 현금 비고갈 일수와 6개월 말 현금이 큰 순서",
    UserGoal.MINIMUM_REPAYMENT: "13주 비고갈을 먼저 충족한 뒤 월 최대 원리금과 총상환의무가 작은 순서",
    UserGoal.FAST_EXECUTION: "13주 비고갈을 먼저 충족한 뒤 첫 효과까지 걸리는 날이 짧은 순서",
}


def _goal_key(goal: UserGoal, result: AlternativeResult) -> tuple:
    assert result.metrics is not None
    item = result.metrics
    feasible = int(item.survives_13_weeks)
    obligation = (
        item.total_repayment_obligation
        if item.total_repayment_obligation is not None
        else 10**30
    )
    if goal is UserGoal.MINIMUM_DEBT:
        return (-feasible, item.net_new_borrowing, obligation, -item.survival_days_6_month, result.alternative_id)
    if goal is UserGoal.LONGEST_SURVIVAL:
        return (-item.survival_days_6_month, -item.month6_ending_cash, item.net_new_borrowing, result.alternative_id)
    if goal is UserGoal.MINIMUM_REPAYMENT:
        return (-feasible, item.maximum_monthly_debt_service, obligation, -item.survival_days_6_month, result.alternative_id)
    return (-feasible, item.days_to_first_effect, item.net_new_borrowing, -item.survival_days_6_month, result.alternative_id)


def _rank(results: list[AlternativeResult], goal: UserGoal) -> GoalRanking:
    candidates = [item for item in results if item.ranking_eligible and item.metrics is not None]
    fallback = bool(candidates) and not any(item.metrics.survives_13_weeks for item in candidates if item.metrics)
    ordered = sorted(candidates, key=lambda item: _goal_key(goal, item))
    return GoalRanking(
        goal=goal,
        meaning=GOAL_MEANINGS[goal],
        ordered_alternative_ids=[item.alternative_id for item in ordered],
        top_alternative_id=ordered[0].alternative_id if ordered else None,
        fallback_used=fallback,
    )


def _cash_needed_before_first_policy_inflow(
    result: CashflowResult,
    plans: list[PolicyPlan],
) -> int:
    inflow_dates = [
        event.event_date
        for plan in plans
        for event in plan.events
        if event.cash_direction is CashDirection.INFLOW
        and event.amount
        and event.event_date is not None
    ]
    if not inflow_dates:
        return 0
    first_inflow = min(inflow_dates)
    relevant_minima = [
        period.minimum_cash
        for period in result.weekly_13
        if period.start_date <= first_inflow
    ]
    return max(0, -min(relevant_minima, default=result.weekly_summary.opening_cash))


def compare_alternatives(
    baseline: DetailedCashflowInput,
    market: MarketScenario,
    alternatives: list[AlternativeSpec],
    *,
    as_of: date,
    combination_registry: CombinationRegistry | None = None,
    safe_cash_override: int | None = None,
) -> DecisionResult:
    """Compare all approved alternatives on identical deterministic horizons."""

    registry = combination_registry or CombinationRegistry()
    if len({item.alternative_id for item in alternatives}) != len(alternatives):
        raise ValueError("alternative_id must be unique")
    if any(item.kind is AlternativeKind.NO_ACTION for item in alternatives):
        raise ValueError("no-action is injected automatically; do not provide it")
    specs = [
        AlternativeSpec(alternative_id="no_action", label="무대응", kind=AlternativeKind.NO_ACTION),
        *alternatives,
    ]
    shock13, source13, note13 = market.selected_shock("13_week")
    shock6, source6, note6 = market.selected_shock("6_month")
    baseline13 = _apply_market_shock(baseline, shock13, horizon_label="13_week")
    baseline6 = _apply_market_shock(baseline, shock6, horizon_label="6_month")
    results: list[AlternativeResult] = []

    for spec in specs:
        state = _candidate_state(spec)
        policies = [plan.policy_id for plan in spec.plans]
        combination_status, combination_reasons = registry.evaluate(
            policies,
            deduplication_keys=[plan.deduplication_key for plan in spec.plans],
            same_expense_support_keys=spec.same_expense_support_keys,
        )
        items = [item for context in spec.candidate_contexts for item in context.items_to_confirm]
        items.extend(combination_reasons if combination_status is not CombinationStatus.COMPATIBLE else [])
        items = list(dict.fromkeys(items))
        if combination_status is CombinationStatus.PROHIBITED:
            state = CandidateState.EXCLUDED
        elif combination_status is CombinationStatus.NEEDS_CONFIRMATION and len(set(policies)) > 1:
            state = CandidateState.CONDITIONAL

        condition_ok = state is not CandidateState.CONDITIONAL or spec.explicit_condition_assumption
        combination_ok = (
            combination_status is not CombinationStatus.NEEDS_CONFIRMATION
            or len(set(policies)) <= 1
            or spec.explicit_combination_assumption
        )
        simulated = state is not CandidateState.EXCLUDED and condition_ok and combination_ok
        reason = "동일 기준 비교 완료" if simulated else " / ".join(items) or "비교 제외"
        if not simulated:
            results.append(
                AlternativeResult(
                    alternative_id=spec.alternative_id,
                    label=spec.label,
                    kind=spec.kind,
                    candidate_state=state,
                    combination_status=combination_status,
                    simulated=False,
                    ranking_eligible=False,
                    reason_summary=reason,
                    items_to_confirm=items,
                    official_urls=spec.official_urls,
                )
            )
            continue

        plans = _delay_plans(spec.plans, spec.payment_delay_days)
        week_result, reduction13 = _run_alternative(
            baseline13, plans, spec.cost_reduction_rate_percent
        )
        month_result, reduction6 = _run_alternative(
            baseline6, plans, spec.cost_reduction_rate_percent
        )
        metrics = _metrics(
            week_result,
            month_result,
            plans,
            cost_reduction=reduction6,
            spec=spec,
            confirmation_count=len(items),
        )
        assumptions = [
            {"field": "market_shock_13_week_percent", "value": shock13, "source": source13.value, "reason": note13},
            {"field": "market_shock_6_month_percent", "value": shock6, "source": source6.value, "reason": note6},
            {"field": "market_result_label", "value": "상권환경 변화율을 동일 비율로 반영한 참고 스트레스 계산", "source": ValueSource.EXPLICIT_SCENARIO_ASSUMPTION.value, "reason": "개인 점포 실제 매출예측이 아님"},
            {"field": "cost_reduction_rate_percent", "value": spec.cost_reduction_rate_percent, "source": ValueSource.USER_INPUT.value if spec.cost_reduction_rate_percent else ValueSource.CALCULATED.value, "reason": "사용자가 선택한 비용절감 시나리오"},
            {"field": "payment_delay_days", "value": spec.payment_delay_days, "source": ValueSource.EXPLICIT_SCENARIO_ASSUMPTION.value, "reason": "지급지연 민감도"},
            {"field": "cost_reduction_13_week", "value": reduction13, "source": ValueSource.CALCULATED.value, "reason": "13주 시나리오 비용 감소액"},
        ]
        assumptions.extend(
            {
                "field": f"alternative_assumption_{index}",
                "value": note,
                "source": ValueSource.EXPLICIT_SCENARIO_ASSUMPTION.value,
                "reason": "대안 비교를 위해 명시한 가정",
            }
            for index, note in enumerate(spec.assumptions, start=1)
        )
        for plan in plans:
            assumptions.extend(item.model_dump(mode="json") for item in plan.assumptions)
        results.append(
            AlternativeResult(
                alternative_id=spec.alternative_id,
                label=spec.label,
                kind=spec.kind,
                candidate_state=state,
                combination_status=combination_status,
                simulated=True,
                ranking_eligible=state is CandidateState.ACTIONABLE,
                reason_summary=reason,
                items_to_confirm=items,
                metrics=metrics,
                weekly_13=[item.to_dict() for item in week_result.weekly_13],
                monthly_6=[item.to_dict() for item in month_result.monthly_6],
                assumption_ledger=assumptions,
                official_urls=list(dict.fromkeys(spec.official_urls)),
                warnings=[*week_result.warnings, *month_result.warnings],
            )
        )

    actionable = [item for item in results if item.ranking_eligible and item.metrics is not None]
    for left, right in combinations(actionable, 2):
        assert left.metrics is not None and right.metrics is not None
        if _dominates(left.metrics, right.metrics):
            right.dominated_by.append(left.alternative_id)
        if _dominates(right.metrics, left.metrics):
            left.dominated_by.append(right.alternative_id)
    frontier = [item.alternative_id for item in actionable if not item.dominated_by]
    rankings = [_rank(results, goal) for goal in UserGoal]
    top_by_default = next(
        (item.top_alternative_id for item in rankings if item.goal is UserGoal.MINIMUM_DEBT),
        None,
    )
    safe_cash = suggest_safe_cash(baseline, user_override=safe_cash_override)
    execution_plans: list[ExecutionPlan] = []
    no_action = next(item for item in results if item.alternative_id == "no_action")
    for result, spec in zip(results, specs):
        if result.metrics is None:
            continue
        payment_cash_gap = result.metrics.cash_needed_before_payment
        safe_target = safe_cash.suggested_amount or baseline.safe_cash_threshold
        execution_plans.append(
            ExecutionPlan(
                alternative_id=result.alternative_id,
                conditions_to_check_now=result.items_to_confirm,
                application_deadline=spec.application_deadline,
                required_documents=spec.required_documents,
                cash_needed_before_payment=payment_cash_gap,
                fallback_alternative_id=(no_action.alternative_id if result.alternative_id != "no_action" else top_by_default),
                minimum_loan_amount=max(
                    0, safe_target - result.metrics.week13_minimum_cash
                ),
                inquiry=spec.inquiry,
                official_urls=spec.official_urls,
            )
        )
    return DecisionResult(
        as_of=as_of,
        comparison_basis="13주는 Target A, 6개월은 Target B를 각 기간 매출유입에 적용한 동일 기준 비교",
        alternatives=results,
        rankings=rankings,
        pareto_frontier_ids=frontier,
        execution_plans=execution_plans,
        safe_cash=safe_cash,
        prohibited_claims=["개인 매출예측", "승인확률", "정책 인과효과", "AI 최적 정책", "임의 적합도 백분율"],
    )
