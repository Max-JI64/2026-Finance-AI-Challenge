"""Policy-independent 13-week and 6-month cash-flow calculations."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Iterable

from .loans import add_months, build_loan_schedule, first_monthly_date, round_won
from .schemas import CashEvent, DetailedCashflowInput, EventType, SimpleCashflowInput


INFLOW_CATEGORIES = {"operating_inflow", "accounts_receivable"}
OUTFLOW_CATEGORIES = {
    "fixed_cost",
    "variable_cost",
    "tax_utility",
    "accounts_payable",
    "one_time_expense",
    "debt_principal",
    "debt_interest",
    "debt_service_combined",
}
ALL_CATEGORIES = tuple(sorted(INFLOW_CATEGORIES | OUTFLOW_CATEGORIES))


@dataclass(frozen=True)
class LedgerEvent:
    event_id: str
    event_date: date
    category: str
    amount: int
    description: str
    source: str


@dataclass(frozen=True)
class TimelinePeriod:
    period: int
    start_date: date
    end_date: date
    opening_cash: int
    operating_inflow: int
    accounts_receivable: int
    fixed_cost: int
    variable_cost: int
    tax_utility: int
    accounts_payable: int
    one_time_expense: int
    debt_principal: int
    debt_interest: int
    debt_service_combined: int
    closing_cash: int
    minimum_cash: int

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["start_date"] = self.start_date.isoformat()
        payload["end_date"] = self.end_date.isoformat()
        return payload


@dataclass(frozen=True)
class HorizonSummary:
    start_date: date
    end_date: date
    opening_cash: int
    ending_cash: int
    minimum_cash: int
    first_cash_depletion_date: date | None
    first_safe_cash_breach_date: date | None

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["start_date"] = self.start_date.isoformat()
        payload["end_date"] = self.end_date.isoformat()
        payload["first_cash_depletion_date"] = (
            self.first_cash_depletion_date.isoformat()
            if self.first_cash_depletion_date
            else None
        )
        payload["first_safe_cash_breach_date"] = (
            self.first_safe_cash_breach_date.isoformat()
            if self.first_safe_cash_breach_date
            else None
        )
        return payload


@dataclass(frozen=True)
class CashflowResult:
    engine_version: str
    input_mode: str
    safe_cash_threshold: int
    weekly_13: tuple[TimelinePeriod, ...]
    monthly_6: tuple[TimelinePeriod, ...]
    weekly_summary: HorizonSummary
    monthly_summary: HorizonSummary
    loan_schedules: tuple[dict[str, object], ...]
    debt_summary: dict[str, object]
    assumptions: tuple[str, ...]
    warnings: tuple[dict[str, str], ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "engine_version": self.engine_version,
            "input_mode": self.input_mode,
            "safe_cash_threshold": self.safe_cash_threshold,
            "weekly_13": [period.to_dict() for period in self.weekly_13],
            "monthly_6": [period.to_dict() for period in self.monthly_6],
            "weekly_summary": self.weekly_summary.to_dict(),
            "monthly_summary": self.monthly_summary.to_dict(),
            "loan_schedules": list(self.loan_schedules),
            "debt_summary": self.debt_summary,
            "assumptions": list(self.assumptions),
            "warnings": list(self.warnings),
        }


def recurring_dates(reference_date: date, day: int, horizon_end: date) -> list[date]:
    current = first_monthly_date(reference_date, day)
    result: list[date] = []
    while current <= horizon_end:
        result.append(current)
        current = add_months(current, 1)
    return result


def _simple_events(data: SimpleCashflowInput, horizon_end: date) -> list[LedgerEvent]:
    revenue = data.resolved_monthly_revenue()
    variable = (
        data.monthly_variable_cost
        if data.monthly_variable_cost is not None
        else round_won(
            Decimal(revenue)
            * Decimal(str(data.variable_cost_rate_percent))
            / Decimal(100)
        )
    )
    specifications = [
        ("revenue", data.revenue_receipt_day, "operating_inflow", revenue, "월 매출입금"),
        ("rent", data.rent_payment_day, "fixed_cost", data.monthly_rent, "월 임대료"),
        ("labor", data.labor_payment_day, "fixed_cost", data.monthly_labor_cost, "월 인건비"),
        (
            "variable",
            data.variable_cost_payment_day,
            "variable_cost",
            variable,
            "월 변동비",
        ),
        (
            "debt",
            data.debt_payment_day,
            "debt_service_combined",
            data.monthly_debt_payment,
            "월 대출 원금·이자 합계",
        ),
    ]
    events: list[LedgerEvent] = []
    for prefix, day, category, amount, description in specifications:
        for number, event_date in enumerate(
            recurring_dates(data.reference_date, day, horizon_end), start=1
        ):
            events.append(
                LedgerEvent(
                    event_id=f"simple-{prefix}-{number}",
                    event_date=event_date,
                    category=category,
                    amount=amount,
                    description=description,
                    source="user_simple_input",
                )
            )
    for fixed in data.other_fixed_costs:
        category = "tax_utility" if fixed.expense_type.value in {
            "tax",
            "utility",
            "social_insurance",
            "vehicle_fuel",
        } else "fixed_cost"
        for number, event_date in enumerate(
            recurring_dates(data.reference_date, fixed.payment_day, horizon_end), start=1
        ):
            events.append(
                LedgerEvent(
                    event_id=f"simple-other-{fixed.name}-{number}",
                    event_date=event_date,
                    category=category,
                    amount=fixed.amount,
                    description=fixed.name,
                    source="user_simple_input",
                )
            )
    return events


def _detailed_events(
    data: DetailedCashflowInput, horizon_end: date
) -> tuple[list[LedgerEvent], list[dict[str, object]], dict[str, object]]:
    category_map = {
        EventType.OPERATING_INFLOW: "operating_inflow",
        EventType.ACCOUNTS_RECEIVABLE: "accounts_receivable",
        EventType.FIXED_COST: "fixed_cost",
        EventType.VARIABLE_COST: "variable_cost",
        EventType.TAX_UTILITY: "tax_utility",
        EventType.ACCOUNTS_PAYABLE: "accounts_payable",
        EventType.ONE_TIME_EXPENSE: "one_time_expense",
    }
    events = [
        LedgerEvent(
            event_id=event.event_id,
            event_date=event.event_date,
            category=category_map[event.event_type],
            amount=event.amount,
            description=event.description,
            source=event.source,
        )
        for event in data.events
        if event.event_type is not EventType.HISTORICAL_REVENUE
        and data.reference_date <= event.event_date <= horizon_end
    ]
    schedules: list[dict[str, object]] = []
    initial_principal = sum(loan.principal for loan in data.loans)
    remaining_at_horizon = 0
    total_interest_all = 0
    for loan in data.loans:
        schedule = build_loan_schedule(loan, data.reference_date)
        schedules.extend(payment.to_dict() for payment in schedule)
        total_interest_all += sum(payment.interest for payment in schedule)
        last_before_horizon = [
            payment for payment in schedule if payment.payment_date <= horizon_end
        ]
        remaining_at_horizon += (
            last_before_horizon[-1].closing_principal
            if last_before_horizon
            else loan.principal
        )
        for payment in schedule:
            if payment.payment_date > horizon_end:
                continue
            events.extend(
                [
                    LedgerEvent(
                        event_id=f"{loan.loan_id}-{payment.payment_number}-principal",
                        event_date=payment.payment_date,
                        category="debt_principal",
                        amount=payment.principal,
                        description=f"{loan.loan_id} 원금",
                        source="calculated_loan_schedule",
                    ),
                    LedgerEvent(
                        event_id=f"{loan.loan_id}-{payment.payment_number}-interest",
                        event_date=payment.payment_date,
                        category="debt_interest",
                        amount=payment.interest,
                        description=f"{loan.loan_id} 이자",
                        source="calculated_loan_schedule",
                    ),
                ]
            )
    debt_summary = {
        "initial_principal": initial_principal,
        "remaining_principal_at_6_months": remaining_at_horizon,
        "total_interest_through_maturity": total_interest_all,
        "principal_interest_split_available": True,
    }
    return events, schedules, debt_summary


def _period_totals(
    events_by_date: dict[date, dict[str, int]], start: date, end: date
) -> dict[str, int]:
    totals = {category: 0 for category in ALL_CATEGORIES}
    current = start
    while current <= end:
        for category, amount in events_by_date.get(current, {}).items():
            totals[category] += amount
        current += timedelta(days=1)
    return totals


def _cash_path(
    opening_cash: int,
    events_by_date: dict[date, dict[str, int]],
    start: date,
    end: date,
) -> dict[date, int]:
    cash = opening_cash
    path: dict[date, int] = {}
    current = start
    while current <= end:
        daily = events_by_date.get(current, {})
        cash += sum(daily.get(category, 0) for category in INFLOW_CATEGORIES)
        cash -= sum(daily.get(category, 0) for category in OUTFLOW_CATEGORIES)
        path[current] = cash
        current += timedelta(days=1)
    return path


def _timeline(
    periods: Iterable[tuple[date, date]],
    opening_cash: int,
    events_by_date: dict[date, dict[str, int]],
    cash_path: dict[date, int],
) -> tuple[TimelinePeriod, ...]:
    result: list[TimelinePeriod] = []
    period_opening = opening_cash
    for number, (start, end) in enumerate(periods, start=1):
        totals = _period_totals(events_by_date, start, end)
        closing = cash_path[end]
        minimum = min(period_opening, *(cash_path[start + timedelta(days=offset)] for offset in range((end - start).days + 1)))
        result.append(
            TimelinePeriod(
                period=number,
                start_date=start,
                end_date=end,
                opening_cash=period_opening,
                closing_cash=closing,
                minimum_cash=minimum,
                **totals,
            )
        )
        period_opening = closing
    return tuple(result)


def _summary(
    start: date,
    end: date,
    opening_cash: int,
    safe_cash_threshold: int,
    cash_path: dict[date, int],
) -> HorizonSummary:
    relevant = {when: cash for when, cash in cash_path.items() if start <= when <= end}
    depletion = next((when for when, cash in relevant.items() if cash < 0), None)
    safe_breach = next(
        (when for when, cash in relevant.items() if cash < safe_cash_threshold), None
    )
    return HorizonSummary(
        start_date=start,
        end_date=end,
        opening_cash=opening_cash,
        ending_cash=relevant[end],
        minimum_cash=min(opening_cash, *relevant.values()),
        first_cash_depletion_date=depletion,
        first_safe_cash_breach_date=safe_breach,
    )


def _warnings_for_amounts(amounts: Iterable[tuple[str, int]]) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []
    for field, amount in amounts:
        if 0 < amount < 10_000:
            warnings.append(
                {
                    "code": "POSSIBLE_TEN_THOUSAND_WON_UNIT",
                    "field": field,
                    "message": "모든 금액은 원 단위입니다. 만원 단위 입력인지 확인하세요.",
                }
            )
    return warnings


def _run(
    *,
    input_mode: str,
    reference_date: date,
    opening_cash: int,
    safe_cash_threshold: int,
    events: list[LedgerEvent],
    loan_schedules: list[dict[str, object]],
    debt_summary: dict[str, object],
    warnings: list[dict[str, str]],
) -> CashflowResult:
    monthly_end = add_months(reference_date, 6) - timedelta(days=1)
    weekly_end = reference_date + timedelta(days=90)
    events_by_date: dict[date, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for event in events:
        if reference_date <= event.event_date <= monthly_end:
            events_by_date[event.event_date][event.category] += event.amount

    cash_path = _cash_path(opening_cash, events_by_date, reference_date, monthly_end)
    weekly_periods = [
        (
            reference_date + timedelta(days=7 * index),
            reference_date + timedelta(days=7 * index + 6),
        )
        for index in range(13)
    ]
    monthly_periods = [
        (
            add_months(reference_date, index),
            add_months(reference_date, index + 1) - timedelta(days=1),
        )
        for index in range(6)
    ]
    weekly = _timeline(weekly_periods, opening_cash, events_by_date, cash_path)
    monthly = _timeline(monthly_periods, opening_cash, events_by_date, cash_path)
    assumptions = (
        "기준일과 종료일을 모두 포함한다.",
        "13주는 기준일부터 7일씩 13개 구간이며 총 91일이다.",
        "6개월은 기준일과 같은 일자를 경계로 한 연속 6개 월 구간이다.",
        "같은 날짜의 모든 현금 이벤트를 합산한 일말잔액으로 고갈 여부를 판단한다.",
        "계산된 음수 현금은 0원으로 보정하지 않는다.",
        "각 금융 이벤트는 원 단위 ROUND_HALF_UP으로 반올림한다.",
        "정책, ML, RAG 결과는 기준 현금흐름에 포함하지 않는다.",
    )
    return CashflowResult(
        engine_version="re3-v1",
        input_mode=input_mode,
        safe_cash_threshold=safe_cash_threshold,
        weekly_13=weekly,
        monthly_6=monthly,
        weekly_summary=_summary(
            reference_date,
            weekly_end,
            opening_cash,
            safe_cash_threshold,
            cash_path,
        ),
        monthly_summary=_summary(
            reference_date,
            monthly_end,
            opening_cash,
            safe_cash_threshold,
            cash_path,
        ),
        loan_schedules=tuple(loan_schedules),
        debt_summary=debt_summary,
        assumptions=assumptions,
        warnings=tuple(warnings),
    )


def run_simple_cashflow(data: SimpleCashflowInput) -> CashflowResult:
    monthly_end = add_months(data.reference_date, 6) - timedelta(days=1)
    events = _simple_events(data, monthly_end)
    revenue = data.resolved_monthly_revenue()
    amounts = [
        ("opening_cash", data.opening_cash),
        ("safe_cash_threshold", data.safe_cash_threshold),
        ("monthly_revenue", revenue),
        ("monthly_rent", data.monthly_rent),
        ("monthly_labor_cost", data.monthly_labor_cost),
        ("total_loan_balance", data.total_loan_balance),
        ("monthly_debt_payment", data.monthly_debt_payment),
    ]
    warnings = _warnings_for_amounts(amounts)
    if data.variable_cost_rate_percent is not None and data.variable_cost_rate_percent > 80:
        warnings.append(
            {
                "code": "UNUSUALLY_HIGH_VARIABLE_COST_RATE",
                "field": "variable_cost_rate_percent",
                "message": "변동비율이 80%를 초과합니다. 입력값을 확인하세요.",
            }
        )
    return _run(
        input_mode="simple",
        reference_date=data.reference_date,
        opening_cash=data.opening_cash,
        safe_cash_threshold=data.safe_cash_threshold,
        events=events,
        loan_schedules=[],
        debt_summary={
            "initial_principal": data.total_loan_balance,
            "remaining_principal_at_6_months": None,
            "total_interest_through_maturity": None,
            "principal_interest_split_available": False,
            "note": "간편 입력의 월 대출상환액은 원금·이자 합계 현금유출이며 분해하지 않습니다.",
        },
        warnings=warnings,
    )


def run_detailed_cashflow(data: DetailedCashflowInput) -> CashflowResult:
    monthly_end = add_months(data.reference_date, 6) - timedelta(days=1)
    events, schedules, debt_summary = _detailed_events(data, monthly_end)
    warnings = _warnings_for_amounts(
        [("opening_cash", data.opening_cash), ("safe_cash_threshold", data.safe_cash_threshold)]
        + [(f"events.{event.event_id}.amount", event.amount) for event in data.events]
    )
    for loan in data.loans:
        if loan.annual_interest_rate_percent > 50:
            warnings.append(
                {
                    "code": "UNUSUALLY_HIGH_INTEREST_RATE",
                    "field": f"loans.{loan.loan_id}.annual_interest_rate_percent",
                    "message": "연이율이 50%를 초과합니다. 백분율 단위를 확인하세요.",
                }
            )
    return _run(
        input_mode="detailed",
        reference_date=data.reference_date,
        opening_cash=data.opening_cash,
        safe_cash_threshold=data.safe_cash_threshold,
        events=events,
        loan_schedules=schedules,
        debt_summary=debt_summary,
        warnings=warnings,
    )
