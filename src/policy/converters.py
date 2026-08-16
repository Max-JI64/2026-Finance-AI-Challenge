"""Deterministic converters from explicit policy scenarios to financial events."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Iterable

from src.cashflow.errors import CashflowInputError
from src.cashflow.loans import add_months, build_loan_schedule, first_monthly_date, round_won
from src.cashflow.schemas import LoanInput, RepaymentMethod

from .catalog import CalculationStatus, PolicyCatalog, PolicyEventProfile, SupportKind
from .schemas import (
    AssumptionEntry,
    CashDirection,
    EffectKind,
    GrantScenario,
    GuaranteeScenario,
    LoanScenario,
    PolicyFinancialEvent,
    PolicyPlan,
    RefinanceScenario,
    ScenarioStatus,
    ValueSource,
    VoucherScenario,
)


CONDITIONAL_NOTICE = (
    "해당 정책이 승인되고 명시된 금액이 입력·공식 조건에 따른 날짜에 실행된 경우의 "
    "기계적 현금흐름 시나리오이며 승인 가능성이나 인과효과를 뜻하지 않습니다."
)


OFFICIAL_TERM_OPTIONS: dict[str, set[tuple[int, int, RepaymentMethod]]] = {
    "SEOUL_GROWTH": {
        (60, 12, RepaymentMethod.EQUAL_PRINCIPAL),
        (60, 24, RepaymentMethod.EQUAL_PRINCIPAL),
        (24, 0, RepaymentMethod.BULLET),
    },
    "SEOUL_EMERGENCY": {(60, 12, RepaymentMethod.EQUAL_PRINCIPAL)},
    "SEOUL_INNOVATION": {
        (60, 12, RepaymentMethod.EQUAL_PRINCIPAL),
        (24, 0, RepaymentMethod.BULLET),
    },
    "SEOUL_DISASTER": {
        (60, 12, RepaymentMethod.EQUAL_PRINCIPAL),
        (24, 0, RepaymentMethod.BULLET),
    },
    "SEOUL_ECONOMY": {
        (36, 12, RepaymentMethod.EQUAL_PRINCIPAL),
        (48, 12, RepaymentMethod.EQUAL_PRINCIPAL),
        (60, 12, RepaymentMethod.EQUAL_PRINCIPAL),
        (24, 0, RepaymentMethod.BULLET),
        (60, 24, RepaymentMethod.EQUAL_PRINCIPAL),
    },
    "SEOUL_INCLUSIVE": {
        (60, 12, RepaymentMethod.EQUAL_PRINCIPAL),
        (60, 24, RepaymentMethod.EQUAL_PRINCIPAL),
    },
    "SEOUL_FAST_DREAM": {(60, 12, RepaymentMethod.EQUAL_PRINCIPAL)},
    "SEOUL_VULNERABLE": {
        (60, 12, RepaymentMethod.EQUAL_PRINCIPAL),
        (60, 24, RepaymentMethod.EQUAL_PRINCIPAL),
    },
    "SEOUL_DELIVERY": {(60, 12, RepaymentMethod.EQUAL_PRINCIPAL)},
    "SEOUL_HOPE": {
        (60, 12, RepaymentMethod.EQUAL_PRINCIPAL),
        (84, 24, RepaymentMethod.EQUAL_PRINCIPAL),
    },
    "SEOUL_JOBS": {
        (60, 12, RepaymentMethod.EQUAL_PRINCIPAL),
        (60, 24, RepaymentMethod.EQUAL_PRINCIPAL),
    },
    "SEOUL_ESG": {
        (60, 12, RepaymentMethod.EQUAL_PRINCIPAL),
        (60, 24, RepaymentMethod.EQUAL_PRINCIPAL),
    },
    "SEOUL_RESTART_FUND": {
        (60, 12, RepaymentMethod.EQUAL_PRINCIPAL),
        (60, 24, RepaymentMethod.EQUAL_PRINCIPAL),
    },
    "SEOUL_MIDEAST": {(60, 12, RepaymentMethod.EQUAL_PRINCIPAL)},
    "SEMAS_RECHALLENGE_GENERAL": {(60, 24, RepaymentMethod.EQUAL_PRINCIPAL)},
    "SEMAS_RECHALLENGE_HOPE": {(60, 24, RepaymentMethod.EQUAL_PRINCIPAL)},
    "SEMAS_RECHALLENGE_LEAP": {(60, 24, RepaymentMethod.EQUAL_PRINCIPAL)},
    "SEMAS_REFINANCE": {
        (120, 0, RepaymentMethod.EQUAL_PRINCIPAL),
        (120, 24, RepaymentMethod.EQUAL_PRINCIPAL),
    },
}


def _profile(catalog: PolicyCatalog, policy_id: str, event_id: str) -> PolicyEventProfile:
    return catalog.get(policy_id, event_id)


def _unconfirmed(profile: PolicyEventProfile) -> list[str]:
    result = [f"미확인 필드: {name}" for name in profile.missing_or_unquantifiable]
    condition = profile.raw.get("unquantifiable_conditions", "")
    if condition not in {"", "해당 없음", "미확인"}:
        result.append(condition)
    return list(dict.fromkeys(result))


def _base_plan(
    profile: PolicyEventProfile,
    scenario_status: ScenarioStatus,
    *,
    events: list[PolicyFinancialEvent] | None = None,
    assumptions: list[AssumptionEntry] | None = None,
    summary: dict[str, object] | None = None,
    extra_unconfirmed: Iterable[str] = (),
) -> PolicyPlan:
    return PolicyPlan(
        policy_id=profile.policy_id,
        policy_version=profile.policy_version,
        event_id=profile.event_id,
        event_name=profile.event_name,
        support_kind=profile.support_kind.value,
        scenario_status=scenario_status,
        calculation_status=(
            "not_approved_zero_effect"
            if scenario_status is ScenarioStatus.NOT_APPROVED
            else "calculated"
        ),
        deduplication_key=profile.deduplication_key,
        linked_event_id=profile.linked_event_id,
        conditional_notice=CONDITIONAL_NOTICE,
        events=events or [],
        assumptions=assumptions or [],
        unconfirmed_conditions=list(dict.fromkeys([*_unconfirmed(profile), *extra_unconfirmed])),
        summary=summary or {"monetary_effect": 0},
    )


def _not_approved(profile: PolicyEventProfile) -> PolicyPlan:
    return _base_plan(
        profile,
        ScenarioStatus.NOT_APPROVED,
        assumptions=[
            AssumptionEntry(
                field="scenario_status",
                value=ScenarioStatus.NOT_APPROVED,
                source=ValueSource.EXPLICIT_SCENARIO_ASSUMPTION,
                reason="승인되지 않음 시나리오는 정책 금융 이벤트를 생성하지 않습니다.",
            )
        ],
    )


def _assert_ready(profile: PolicyEventProfile) -> None:
    if profile.calculation_status is CalculationStatus.BLOCKED_MISSING_OFFICIAL_TERMS:
        raise CashflowInputError(
            "POLICY_TERMS_UNCONFIRMED",
            f"{profile.policy_id}.{profile.event_id}",
            "핵심 공식 조건이 미확인이라 금액 효과를 계산할 수 없습니다.",
        )
    if profile.calculation_status is CalculationStatus.REQUIRES_SUBPRODUCT_SELECTION:
        raise CashflowInputError(
            "POLICY_SUBPRODUCT_REQUIRED",
            f"{profile.policy_id}.{profile.event_id}",
            "세부사업을 먼저 선택해야 하며 대표 한도·조건을 만들 수 없습니다.",
        )


def _assert_cap(profile: PolicyEventProfile, amount: int) -> None:
    if profile.maximum_amount is not None and amount > profile.maximum_amount:
        raise CashflowInputError(
            "POLICY_AMOUNT_EXCEEDS_OFFICIAL_CAP",
            "approved_amount",
            f"입력액 {amount}원이 공식 한도 {profile.maximum_amount}원을 초과합니다.",
        )


def _assert_activity_period(profile: PolicyEventProfile, activity_date: date) -> None:
    if profile.effective_from and activity_date < profile.effective_from:
        raise CashflowInputError(
            "POLICY_EVENT_OUTSIDE_EFFECTIVE_PERIOD",
            "activity_date",
            "정책 적용 시작일 이전 이벤트입니다.",
        )
    if profile.effective_to and activity_date > profile.effective_to:
        raise CashflowInputError(
            "POLICY_EVENT_OUTSIDE_EFFECTIVE_PERIOD",
            "activity_date",
            "정책 적용 종료일 이후 이벤트입니다.",
        )


def _event(
    profile: PolicyEventProfile,
    sequence: int,
    kind: EffectKind,
    direction: CashDirection,
    event_date: date | None,
    amount: int | None,
    source: ValueSource,
    description: str,
) -> PolicyFinancialEvent:
    return PolicyFinancialEvent(
        policy_id=profile.policy_id,
        policy_version=profile.policy_version,
        event_id=profile.event_id,
        linked_event_id=profile.linked_event_id,
        deduplication_key=profile.deduplication_key,
        sequence=sequence,
        effect_kind=kind,
        cash_direction=direction,
        event_date=event_date,
        amount=amount,
        amount_source=source,
        description=description,
    )


def convert_grant(
    scenario: GrantScenario, catalog: PolicyCatalog | None = None
) -> PolicyPlan:
    catalog = catalog or PolicyCatalog()
    profile = _profile(catalog, scenario.policy_id, scenario.event_id)
    if profile.support_kind not in {SupportKind.GRANT, SupportKind.REIMBURSEMENT_GRANT}:
        raise CashflowInputError("WRONG_CONVERTER", "event_id", "보조금 이벤트가 아닙니다.")
    if scenario.scenario_status is ScenarioStatus.NOT_APPROVED:
        return _not_approved(profile)
    _assert_ready(profile)
    assert scenario.approved_support_amount is not None and scenario.payment_date is not None
    _assert_cap(profile, scenario.approved_support_amount)
    assumptions = [
        AssumptionEntry(
            field="scenario_status",
            value=scenario.scenario_status,
            source=ValueSource.EXPLICIT_SCENARIO_ASSUMPTION,
            reason="승인을 예측하지 않고 승인된 경우만 가정합니다.",
        ),
        AssumptionEntry(
            field="approved_support_amount",
            value=scenario.approved_support_amount,
            source=scenario.approved_support_amount_source,
            reason="실제 승인금액 또는 사용자가 검토하려는 조건부 금액입니다.",
        ),
        AssumptionEntry(
            field="payment_date",
            value=scenario.payment_date,
            source=scenario.payment_date_source,
            reason="공식 개별 지급일이 없으면 사용자가 날짜를 명시해야 합니다.",
        ),
    ]
    events: list[PolicyFinancialEvent] = []
    user_contribution = 0
    if profile.support_kind is SupportKind.REIMBURSEMENT_GRANT:
        if (
            scenario.total_project_cost is None
            or scenario.eligible_expense_amount is None
            or scenario.expense_date is None
        ):
            raise CashflowInputError(
                "REIMBURSEMENT_INPUT_REQUIRED",
                "grant_scenario",
                "사후정산은 총사업비·적격비용·선지출일이 필요합니다.",
            )
        _assert_activity_period(profile, scenario.expense_date)
        if scenario.eligible_expense_amount > scenario.total_project_cost:
            raise CashflowInputError(
                "INVALID_ELIGIBLE_EXPENSE",
                "eligible_expense_amount",
                "적격비용은 총사업비를 초과할 수 없습니다.",
            )
        if scenario.eligible_expense_amount + scenario.vat_amount > scenario.total_project_cost:
            raise CashflowInputError(
                "INVALID_VAT_AND_ELIGIBLE_EXPENSE",
                "vat_amount",
                "적격비용과 부가세 합계는 총사업비를 초과할 수 없습니다.",
            )
        if scenario.approved_support_amount > scenario.eligible_expense_amount:
            raise CashflowInputError(
                "SUPPORT_EXCEEDS_ELIGIBLE_EXPENSE",
                "approved_support_amount",
                "지원액은 적격비용을 초과할 수 없습니다.",
            )
        user_contribution = scenario.total_project_cost - scenario.approved_support_amount
        assumptions.extend(
            [
                AssumptionEntry(
                    field="total_project_cost",
                    value=scenario.total_project_cost,
                    source=ValueSource.USER_INPUT,
                    reason="사후정산 전 선행현금과 최종 자부담 계산에 사용합니다.",
                ),
                AssumptionEntry(
                    field="expense_already_in_baseline",
                    value=scenario.expense_already_in_baseline,
                    source=ValueSource.USER_INPUT,
                    reason="기준 현금흐름 비용의 중복 반영을 막습니다.",
                ),
            ]
        )
        if not scenario.expense_already_in_baseline:
            events.append(
                _event(
                    profile,
                    1,
                    EffectKind.PROJECT_EXPENSE,
                    CashDirection.OUTFLOW,
                    scenario.expense_date,
                    scenario.total_project_cost,
                    ValueSource.USER_INPUT,
                    "지원사업 수행을 위한 선지출 총액",
                )
            )
    elif scenario.total_project_cost is not None:
        if scenario.approved_support_amount > scenario.total_project_cost:
            raise CashflowInputError(
                "SUPPORT_EXCEEDS_PROJECT_COST",
                "approved_support_amount",
                "지원액은 입력한 총사업비를 초과할 수 없습니다.",
            )
        user_contribution = scenario.total_project_cost - scenario.approved_support_amount

    events.append(
        _event(
            profile,
            len(events) + 1,
            EffectKind.SUPPORT_CASH_INFLOW,
            CashDirection.INFLOW,
            scenario.payment_date,
            scenario.approved_support_amount,
            scenario.approved_support_amount_source,
            "조건부 지원금 지급",
        )
    )
    return _base_plan(
        profile,
        scenario.scenario_status,
        events=events,
        assumptions=assumptions,
        summary={
            "official_cap": profile.maximum_amount,
            "support_amount": scenario.approved_support_amount,
            "user_contribution": user_contribution,
            "vat_amount": scenario.vat_amount,
            "reimbursement": profile.support_kind is SupportKind.REIMBURSEMENT_GRANT,
            "pre_financing_required": (
                scenario.total_project_cost
                if profile.support_kind is SupportKind.REIMBURSEMENT_GRANT
                else 0
            ),
        },
    )


VOUCHER_ELIGIBLE_TYPES = {
    "utility",
    "social_insurance",
    "vehicle_fuel",
    "fire_mutual_aid",
}


def convert_voucher(
    scenario: VoucherScenario, catalog: PolicyCatalog | None = None
) -> PolicyPlan:
    catalog = catalog or PolicyCatalog()
    profile = _profile(catalog, scenario.policy_id, scenario.event_id)
    if profile.support_kind is not SupportKind.VOUCHER:
        raise CashflowInputError("WRONG_CONVERTER", "event_id", "바우처 이벤트가 아닙니다.")
    if scenario.scenario_status is ScenarioStatus.NOT_APPROVED:
        return _not_approved(profile)
    _assert_ready(profile)
    assert scenario.awarded_amount is not None
    assert scenario.activation_date is not None and scenario.expiry_date is not None
    _assert_cap(profile, scenario.awarded_amount)
    if scenario.expiry_date < scenario.activation_date:
        raise CashflowInputError(
            "INVALID_VOUCHER_PERIOD", "expiry_date", "소진기한은 활성일보다 빠를 수 없습니다."
        )
    official_expiry = date(2026, 12, 31) if profile.event_id == "STABILITY_VOUCHER" else profile.effective_to
    if official_expiry and scenario.expiry_date > official_expiry:
        raise CashflowInputError(
            "VOUCHER_EXPIRY_EXCEEDS_OFFICIAL_DATE",
            "expiry_date",
            f"공식 소진기한 {official_expiry.isoformat()}을 초과합니다.",
        )
    remaining = scenario.awarded_amount
    events: list[PolicyFinancialEvent] = []
    ignored_expenses: list[str] = []
    for expense in sorted(scenario.expenses, key=lambda item: (item.expense_date, item.expense_id)):
        expense_type = str(expense.expense_type)
        if not scenario.activation_date <= expense.expense_date <= scenario.expiry_date:
            ignored_expenses.append(f"{expense.expense_id}: 사용기간 밖")
            continue
        if expense_type not in VOUCHER_ELIGIBLE_TYPES:
            ignored_expenses.append(f"{expense.expense_id}: 비적격 비용유형 {expense_type}")
            continue
        reduction = min(expense.amount, remaining)
        if reduction <= 0:
            ignored_expenses.append(f"{expense.expense_id}: 바우처 잔액 소진")
            continue
        events.append(
            _event(
                profile,
                len(events) + 1,
                EffectKind.COST_REDUCTION,
                CashDirection.INFLOW,
                expense.expense_date,
                reduction,
                ValueSource.CALCULATED,
                f"{expense.expense_id} 적격 결제비용 선차감",
            )
        )
        remaining -= reduction
    return _base_plan(
        profile,
        scenario.scenario_status,
        events=events,
        assumptions=[
            AssumptionEntry(
                field="awarded_amount",
                value=scenario.awarded_amount,
                source=scenario.awarded_amount_source,
                reason="실제 선정액 또는 조건부 시나리오 금액입니다.",
            ),
            AssumptionEntry(
                field="expense_presence_in_baseline",
                value=True,
                source=ValueSource.EXPLICIT_SCENARIO_ASSUMPTION,
                reason="비용감면 이벤트는 동일 비용이 기준 현금흐름에 있을 때만 적용합니다.",
            ),
            AssumptionEntry(
                field="active_period",
                value=(scenario.activation_date, scenario.expiry_date),
                source=scenario.active_period_source,
                reason="공식 카드 등록일·소진기한 또는 사용자가 명시한 조건부 기간입니다.",
            ),
        ],
        summary={
            "official_cap": profile.maximum_amount,
            "voucher_award": scenario.awarded_amount,
            "cost_reduction": scenario.awarded_amount - remaining,
            "eligible_expense_total": sum(
                expense.amount
                for expense in scenario.expenses
                if scenario.activation_date
                <= expense.expense_date
                <= scenario.expiry_date
                and str(expense.expense_type) in VOUCHER_ELIGIBLE_TYPES
            ),
            "user_paid_eligible_expense": max(
                0,
                sum(
                    expense.amount
                    for expense in scenario.expenses
                    if scenario.activation_date
                    <= expense.expense_date
                    <= scenario.expiry_date
                    and str(expense.expense_type) in VOUCHER_ELIGIBLE_TYPES
                )
                - (scenario.awarded_amount - remaining),
            ),
            "expired_or_unused_balance": remaining,
            "cash_inflow": 0,
            "ignored_expenses": ignored_expenses,
        },
    )


def _maturity(execution_date: date, payment_day: int, term_months: int) -> date:
    first = first_monthly_date(execution_date, payment_day)
    return add_months(first, term_months - 1)


def _assert_official_terms(profile: PolicyEventProfile, scenario: LoanScenario) -> None:
    options = OFFICIAL_TERM_OPTIONS.get(profile.event_id)
    if options is None:
        if profile.event_id == "SEOUL_STARTUP":
            raise CashflowInputError(
                "POLICY_OPTION_CONFIRMATION_REQUIRED",
                "loan_terms",
                "창업기업자금은 선택한 세부 상환옵션의 공식 확인이 필요합니다.",
            )
        return
    assert scenario.term_months is not None and scenario.repayment_method is not None
    selected = (scenario.term_months, scenario.grace_months, scenario.repayment_method)
    if selected not in options:
        raise CashflowInputError(
            "LOAN_TERMS_NOT_IN_OFFICIAL_OPTIONS",
            "loan_terms",
            f"선택한 기간·거치·상환방식이 공식 옵션에 없습니다: {selected}",
        )


def _loan_rate(profile: PolicyEventProfile, scenario: LoanScenario) -> float:
    if profile.support_kind is SupportKind.INTEREST_SUBSIDIZED_LOAN:
        if scenario.bank_interest_rate_percent is None:
            raise CashflowInputError(
                "BANK_RATE_REQUIRED",
                "bank_interest_rate_percent",
                "은행 심사금리는 사용자 입력이 필요합니다.",
            )
        return scenario.bank_interest_rate_percent
    if profile.official_interest_rate_percent is not None:
        return profile.official_interest_rate_percent
    if profile.reference_rate_spread_percent is not None:
        if scenario.reference_interest_rate_percent is None:
            raise CashflowInputError(
                "REFERENCE_RATE_REQUIRED",
                "reference_interest_rate_percent",
                "해당 분기의 정책자금 기준금리 입력이 필요합니다.",
            )
        return scenario.reference_interest_rate_percent + profile.reference_rate_spread_percent
    raise CashflowInputError(
        "POLICY_INTEREST_RATE_UNCONFIRMED",
        "interest_rate",
        "공식 금리 또는 계산 가능한 기준금리 규칙이 없습니다.",
    )


def _phase_rate(phases: tuple, payment_index: int) -> float:
    consumed = 0
    for phase in phases:
        consumed += phase.months
        if payment_index <= consumed:
            return phase.percentage_points
    return 0.0


def convert_loan(
    scenario: LoanScenario, catalog: PolicyCatalog | None = None
) -> PolicyPlan:
    catalog = catalog or PolicyCatalog()
    profile = _profile(catalog, scenario.policy_id, scenario.event_id)
    if profile.support_kind not in {
        SupportKind.DIRECT_LOAN,
        SupportKind.INTEREST_SUBSIDIZED_LOAN,
    }:
        raise CashflowInputError("WRONG_CONVERTER", "event_id", "융자 이벤트가 아닙니다.")
    if scenario.scenario_status is ScenarioStatus.NOT_APPROVED:
        return _not_approved(profile)
    _assert_ready(profile)
    assert scenario.approved_principal is not None
    assert scenario.execution_date is not None and scenario.payment_day is not None
    assert scenario.term_months is not None and scenario.repayment_method is not None
    _assert_cap(profile, scenario.approved_principal)
    _assert_activity_period(profile, scenario.execution_date)
    _assert_official_terms(profile, scenario)
    gross_rate = _loan_rate(profile, scenario)
    loan = LoanInput(
        loan_id=f"policy-{profile.event_id}",
        principal=scenario.approved_principal,
        annual_interest_rate_percent=gross_rate,
        repayment_method=scenario.repayment_method,
        payment_day=scenario.payment_day,
        maturity_date=_maturity(
            scenario.execution_date, scenario.payment_day, scenario.term_months
        ),
        grace_months=scenario.grace_months,
    )
    schedule = build_loan_schedule(loan, scenario.execution_date)
    events = [
        _event(
            profile,
            1,
            EffectKind.NEW_DEBT_PRINCIPAL,
            CashDirection.INFLOW,
            scenario.execution_date,
            scenario.approved_principal,
            scenario.approved_principal_source,
            "정책대출 실행금 유입",
        )
    ]
    if scenario.upfront_fee:
        events.append(
            _event(
                profile,
                len(events) + 1,
                EffectKind.OTHER_FEE,
                CashDirection.OUTFLOW,
                scenario.execution_date,
                scenario.upfront_fee,
                ValueSource.USER_INPUT,
                "대출 부대비용",
            )
        )
    if scenario.guarantee_fee:
        events.append(
            _event(
                profile,
                len(events) + 1,
                EffectKind.GUARANTEE_FEE,
                CashDirection.OUTFLOW,
                scenario.execution_date,
                scenario.guarantee_fee,
                ValueSource.USER_INPUT,
                "보증료",
            )
        )
    total_gross_interest = 0
    total_net_interest = 0
    total_interest_reduction = 0
    net_payments: list[int] = []
    for index, payment in enumerate(schedule, start=1):
        subsidy_pp = _phase_rate(profile.subsidy_phases, index)
        reduction = min(
            payment.interest,
            round_won(
                Decimal(payment.opening_principal)
                * Decimal(str(subsidy_pp))
                / Decimal(1200)
            ),
        )
        net_interest = payment.interest - reduction
        total_gross_interest += payment.interest
        total_net_interest += net_interest
        total_interest_reduction += reduction
        net_payments.append(payment.principal + net_interest)
        events.append(
            _event(
                profile,
                len(events) + 1,
                EffectKind.DEBT_PRINCIPAL_REPAYMENT,
                CashDirection.OUTFLOW,
                payment.payment_date,
                payment.principal,
                ValueSource.CALCULATED,
                f"정책대출 {index}회차 원금",
            )
        )
        events.append(
            _event(
                profile,
                len(events) + 1,
                EffectKind.DEBT_INTEREST,
                CashDirection.OUTFLOW,
                payment.payment_date,
                net_interest,
                ValueSource.CALCULATED,
                f"정책대출 {index}회차 순이자",
            )
        )
        if reduction:
            events.append(
                _event(
                    profile,
                    len(events) + 1,
                    EffectKind.INTEREST_REDUCTION,
                    CashDirection.NONE,
                    payment.payment_date,
                    reduction,
                    ValueSource.CALCULATED,
                    f"정책대출 {index}회차 이차보전 절감액",
                )
            )
    assumptions = [
        AssumptionEntry(
            field="scenario_status",
            value=scenario.scenario_status,
            source=ValueSource.EXPLICIT_SCENARIO_ASSUMPTION,
            reason="승인확률 없이 승인·실행된 경우만 가정합니다.",
        ),
        AssumptionEntry(
            field="approved_principal",
            value=scenario.approved_principal,
            source=scenario.approved_principal_source,
            reason="실제 승인액 또는 사용자가 검토하는 조건부 금액입니다.",
        ),
        AssumptionEntry(
            field="execution_date",
            value=scenario.execution_date,
            source=scenario.execution_date_source,
            reason="개별 실행일은 사용자 입력이며 임의 생성하지 않습니다.",
        ),
        AssumptionEntry(
            field="gross_interest_rate_percent",
            value=gross_rate,
            source=(
                ValueSource.OFFICIAL
                if profile.official_interest_rate_percent is not None
                else ValueSource.CALCULATED
            ),
            reason="공식 고정금리 또는 사용자 입력 기준금리·은행금리와 공식 규칙의 결합입니다.",
        ),
        AssumptionEntry(
            field="loan_terms",
            value=(
                scenario.term_months,
                scenario.grace_months,
                scenario.repayment_method,
            ),
            source=ValueSource.OFFICIAL,
            reason="사용자 선택값을 공식 기간·거치·상환방식 옵션과 대조했습니다.",
        ),
    ]
    return _base_plan(
        profile,
        scenario.scenario_status,
        events=events,
        assumptions=assumptions,
        summary={
            "official_cap": profile.maximum_amount,
            "new_debt_principal": scenario.approved_principal,
            "gross_interest_rate_percent": gross_rate,
            "total_gross_interest": total_gross_interest,
            "total_interest_reduction": total_interest_reduction,
            "total_net_interest": total_net_interest,
            "total_principal_repayment": sum(item.principal for item in schedule),
            "remaining_principal_at_maturity": schedule[-1].closing_principal,
            "first_payment": net_payments[0],
            "last_payment": net_payments[-1],
            "payment_count": len(schedule),
            "upfront_fee": scenario.upfront_fee,
            "guarantee_fee": scenario.guarantee_fee,
        },
    )


def convert_refinance(
    scenario: RefinanceScenario, catalog: PolicyCatalog | None = None
) -> PolicyPlan:
    catalog = catalog or PolicyCatalog()
    profile = _profile(catalog, scenario.policy_id, scenario.event_id)
    if profile.support_kind is not SupportKind.REFINANCE:
        raise CashflowInputError("WRONG_CONVERTER", "event_id", "대환 이벤트가 아닙니다.")
    if scenario.scenario_status is ScenarioStatus.NOT_APPROVED:
        return _not_approved(profile)
    _assert_ready(profile)
    assert scenario.execution_date is not None
    assert scenario.existing_refinanced_loan is not None
    assert scenario.replacement_loan is not None
    _assert_cap(profile, scenario.replacement_loan.principal)
    _assert_activity_period(profile, scenario.execution_date)
    if profile.official_interest_rate_percent is not None and (
        scenario.replacement_loan.annual_interest_rate_percent
        != profile.official_interest_rate_percent
    ):
        raise CashflowInputError(
            "REFINANCE_RATE_MISMATCH",
            "replacement_loan.annual_interest_rate_percent",
            f"공식 대환금리 {profile.official_interest_rate_percent}%와 일치해야 합니다.",
        )
    existing_schedule = build_loan_schedule(
        scenario.existing_refinanced_loan, scenario.execution_date
    )
    replacement_schedule = build_loan_schedule(
        scenario.replacement_loan, scenario.execution_date
    )
    replacement_term = len(replacement_schedule)
    option = (
        replacement_term,
        scenario.replacement_loan.grace_months,
        scenario.replacement_loan.repayment_method,
    )
    if option not in OFFICIAL_TERM_OPTIONS[profile.event_id]:
        raise CashflowInputError(
            "LOAN_TERMS_NOT_IN_OFFICIAL_OPTIONS",
            "replacement_loan",
            f"대환 후 계약이 공식 옵션에 없습니다: {option}",
        )
    events = [
        _event(
            profile,
            1,
            EffectKind.NEW_DEBT_PRINCIPAL,
            CashDirection.INFLOW,
            scenario.execution_date,
            scenario.replacement_loan.principal,
            ValueSource.USER_INPUT,
            "대환대출 실행금 유입",
        ),
        _event(
            profile,
            2,
            EffectKind.EXISTING_DEBT_PAYOFF,
            CashDirection.OUTFLOW,
            scenario.execution_date,
            scenario.existing_refinanced_loan.principal,
            ValueSource.USER_INPUT,
            "기존 대출 원금 상환",
        ),
    ]
    for payment in existing_schedule:
        for amount, label, kind in (
            (
                payment.principal,
                "원금",
                EffectKind.EXISTING_PRINCIPAL_PAYMENT_REVERSAL,
            ),
            (
                payment.interest,
                "이자",
                EffectKind.EXISTING_INTEREST_PAYMENT_REVERSAL,
            ),
        ):
            events.append(
                _event(
                    profile,
                    len(events) + 1,
                    kind,
                    CashDirection.INFLOW,
                    payment.payment_date,
                    amount,
                    ValueSource.CALCULATED,
                    f"대환으로 제거되는 기존 {payment.payment_number}회차 {label}",
                )
            )
    for payment in replacement_schedule:
        events.append(
            _event(
                profile,
                len(events) + 1,
                EffectKind.DEBT_PRINCIPAL_REPAYMENT,
                CashDirection.OUTFLOW,
                payment.payment_date,
                payment.principal,
                ValueSource.CALCULATED,
                f"대환 후 {payment.payment_number}회차 원금",
            )
        )
        events.append(
            _event(
                profile,
                len(events) + 1,
                EffectKind.DEBT_INTEREST,
                CashDirection.OUTFLOW,
                payment.payment_date,
                payment.interest,
                ValueSource.CALCULATED,
                f"대환 후 {payment.payment_number}회차 이자",
            )
        )
    if scenario.upfront_fee:
        events.append(
            _event(
                profile,
                len(events) + 1,
                EffectKind.OTHER_FEE,
                CashDirection.OUTFLOW,
                scenario.execution_date,
                scenario.upfront_fee,
                ValueSource.USER_INPUT,
                "대환 부대비용",
            )
        )
    old_interest = sum(item.interest for item in existing_schedule)
    new_interest = sum(item.interest for item in replacement_schedule)
    return _base_plan(
        profile,
        scenario.scenario_status,
        events=events,
        assumptions=[
            AssumptionEntry(
                field="existing_refinanced_loan",
                value=scenario.existing_refinanced_loan.loan_id,
                source=ValueSource.USER_INPUT,
                reason="부분대환이면 대환되는 원금 구간만 별도 대출로 입력합니다.",
            ),
            AssumptionEntry(
                field="scenario_status",
                value=scenario.scenario_status,
                source=ValueSource.EXPLICIT_SCENARIO_ASSUMPTION,
                reason="승인·실행된 경우를 조건부로 비교합니다.",
            ),
            AssumptionEntry(
                field="execution_date",
                value=scenario.execution_date,
                source=scenario.execution_date_source,
                reason="대환 실행일의 출처를 공식·사용자·가정으로 구분합니다.",
            ),
        ],
        summary={
            "official_cap": profile.maximum_amount,
            "refinanced_principal": scenario.replacement_loan.principal,
            "new_debt_principal": scenario.replacement_loan.principal,
            "existing_debt_payoff": scenario.existing_refinanced_loan.principal,
            "existing_loan_id": scenario.existing_refinanced_loan.loan_id,
            "replacement_loan_id": scenario.replacement_loan.loan_id,
            "old_first_payment": existing_schedule[0].total_payment,
            "new_first_payment": replacement_schedule[0].total_payment,
            "first_payment_change": (
                replacement_schedule[0].total_payment
                - existing_schedule[0].total_payment
            ),
            "old_total_interest": old_interest,
            "new_total_interest": new_interest,
            "total_interest_change": new_interest - old_interest,
            "old_payment_count": len(existing_schedule),
            "new_payment_count": len(replacement_schedule),
            "upfront_fee": scenario.upfront_fee,
        },
    )


def convert_guarantee(
    scenario: GuaranteeScenario, catalog: PolicyCatalog | None = None
) -> PolicyPlan:
    catalog = catalog or PolicyCatalog()
    profile = _profile(catalog, scenario.policy_id, scenario.event_id)
    if profile.support_kind is not SupportKind.GUARANTEE:
        raise CashflowInputError("WRONG_CONVERTER", "event_id", "보증 이벤트가 아닙니다.")
    if scenario.scenario_status is ScenarioStatus.NOT_APPROVED:
        return _not_approved(profile)
    _assert_ready(profile)
    if scenario.linked_loan_scenario is None:
        return _base_plan(
            profile,
            scenario.scenario_status,
            events=[
                _event(
                    profile,
                    1,
                    EffectKind.INFORMATION_ONLY,
                    CashDirection.NONE,
                    None,
                    None,
                    ValueSource.UNCONFIRMED,
                    "보증 자체는 현금유입이 아니며 실제 대출조건 없이는 금액효과를 계산하지 않습니다.",
                )
            ],
            assumptions=[
                AssumptionEntry(
                    field="linked_loan_scenario",
                    value=None,
                    source=ValueSource.UNCONFIRMED,
                    reason="실제 대출조건이 입력되지 않았습니다.",
                )
            ],
            summary={"cash_inflow": 0, "financial_access_support_only": True},
        )
    linked = convert_loan(scenario.linked_loan_scenario, catalog)
    if linked.deduplication_key != profile.deduplication_key:
        raise CashflowInputError(
            "INVALID_LINKED_POLICY_EVENT",
            "linked_loan_scenario",
            "공식적으로 연결된 동일 대출 이벤트가 아닙니다.",
        )
    events = list(linked.events)
    if scenario.guarantee_fee_amount:
        assert scenario.guarantee_fee_date is not None
        events.append(
            _event(
                profile,
                len(events) + 1,
                EffectKind.GUARANTEE_FEE,
                CashDirection.OUTFLOW,
                scenario.guarantee_fee_date,
                scenario.guarantee_fee_amount,
                ValueSource.USER_INPUT,
                "실제 보증료",
            )
        )
    if scenario.guarantee_fee_support_amount:
        assert scenario.guarantee_fee_date is not None
        if scenario.guarantee_fee_support_amount > 400_000:
            raise CashflowInputError(
                "GUARANTEE_FEE_SUPPORT_EXCEEDS_CAP",
                "guarantee_fee_support_amount",
                "공식 보증료 지원한도 40만원을 초과합니다.",
            )
        if scenario.guarantee_fee_support_amount > scenario.guarantee_fee_amount:
            raise CashflowInputError(
                "GUARANTEE_FEE_SUPPORT_EXCEEDS_FEE",
                "guarantee_fee_support_amount",
                "보증료 지원액은 실제 보증료를 초과할 수 없습니다.",
            )
        events.append(
            _event(
                profile,
                len(events) + 1,
                EffectKind.GUARANTEE_FEE_SUPPORT,
                CashDirection.INFLOW,
                scenario.guarantee_fee_date,
                scenario.guarantee_fee_support_amount,
                ValueSource.USER_INPUT,
                "보증료 지원에 따른 비용감면",
            )
        )
    return _base_plan(
        profile,
        scenario.scenario_status,
        events=events,
        assumptions=[*linked.assumptions],
        summary={
            **linked.summary,
            "financial_access_support_only": False,
            "guarantee_fee": scenario.guarantee_fee_amount,
            "guarantee_fee_support": scenario.guarantee_fee_support_amount,
        },
    )
