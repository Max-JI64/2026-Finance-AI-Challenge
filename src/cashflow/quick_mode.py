"""Approved RE3 quick-mode wrapper implemented for the RE8 interface."""

from __future__ import annotations

import calendar
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator

from src.cashflow.loans import add_months
from src.cashflow.schemas import CashEvent, DetailedCashflowInput, LoanInput


class RevenueTiming(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTH_START = "month_start"
    MONTH_MIDDLE = "month_middle"
    MONTH_END = "month_end"


class CashTiming(StrEnum):
    EARLY = "early"
    MIDDLE = "middle"
    LATE = "late"


class QuickModeInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    reference_date: date
    opening_cash: StrictInt = Field(ge=0)
    safe_cash_threshold: StrictInt = Field(ge=0)
    monthly_revenue: StrictInt | None = Field(default=None, ge=0)
    recent_monthly_revenues: list[StrictInt] | None = None
    revenue_timing: RevenueTiming
    monthly_rent: StrictInt = Field(ge=0)
    monthly_labor_cost: StrictInt = Field(ge=0)
    monthly_variable_cost: StrictInt = Field(ge=0)
    expense_timing: CashTiming
    total_loan_balance: StrictInt = Field(ge=0)
    annual_interest_rate_percent: float = Field(default=0, ge=0, le=100)
    remaining_term_months: StrictInt = Field(default=60, ge=1, le=360)
    debt_timing: CashTiming

    @field_validator("recent_monthly_revenues")
    @classmethod
    def validate_recent_revenues(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return value
        if not 3 <= len(value) <= 12:
            raise ValueError("최근 월 매출은 3개월 이상 12개월 이하여야 합니다.")
        if any(item < 0 for item in value):
            raise ValueError("최근 월 매출에는 음수를 입력할 수 없습니다.")
        return value

    @model_validator(mode="after")
    def validate_loan_terms(self) -> "QuickModeInput":
        revenue_sources = int(self.monthly_revenue is not None) + int(
            self.recent_monthly_revenues is not None
        )
        if revenue_sources != 1:
            raise ValueError("월 평균 매출 또는 최근 월 매출 중 하나만 입력해야 합니다.")
        if self.reference_date.day != 1:
            raise ValueError("간편모드 기준일은 월 1일이어야 합니다.")
        if self.total_loan_balance == 0 and self.annual_interest_rate_percent != 0:
            raise ValueError("대출잔액이 0원이면 기존 대출금리는 0이어야 합니다.")
        return self

    def resolved_monthly_revenue(self) -> int:
        if self.monthly_revenue is not None:
            return self.monthly_revenue
        assert self.recent_monthly_revenues is not None
        average = Decimal(sum(self.recent_monthly_revenues)) / Decimal(
            len(self.recent_monthly_revenues)
        )
        return int(average.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _timing_range(timing: CashTiming, last_day: int) -> tuple[int, int]:
    if timing is CashTiming.EARLY:
        return 1, min(10, last_day)
    if timing is CashTiming.MIDDLE:
        return min(11, last_day), min(20, last_day)
    return min(21, last_day), last_day


def _pick_day(
    timing: CashTiming,
    *,
    last_day: int,
    scenario: str,
    is_inflow: bool,
) -> int:
    first, last = _timing_range(timing, last_day)
    if scenario == "central":
        return (first + last) // 2
    choose_late = (scenario == "conservative" and is_inflow) or (
        scenario == "favorable" and not is_inflow
    )
    return last if choose_late else first


def _monthly_revenue_timing(value: RevenueTiming) -> CashTiming:
    if value is RevenueTiming.MONTH_START:
        return CashTiming.EARLY
    if value is RevenueTiming.MONTH_MIDDLE:
        return CashTiming.MIDDLE
    return CashTiming.LATE


def _split_amount(amount: int, count: int) -> list[int]:
    base, remainder = divmod(amount, count)
    return [base + (1 if index < remainder else 0) for index in range(count)]


def _revenue_events(
    data: QuickModeInput,
    *,
    year: int,
    month: int,
    month_index: int,
    scenario: str,
) -> list[CashEvent]:
    last_day = calendar.monthrange(year, month)[1]
    if data.revenue_timing is RevenueTiming.DAILY:
        days = list(range(1, last_day + 1))
    elif data.revenue_timing is RevenueTiming.WEEKLY:
        weekday = {"conservative": 4, "central": 2, "favorable": 0}[scenario]
        days = [day for day in range(1, last_day + 1) if date(year, month, day).weekday() == weekday]
    else:
        timing = _monthly_revenue_timing(data.revenue_timing)
        days = [
            _pick_day(timing, last_day=last_day, scenario=scenario, is_inflow=True)
        ]
    amounts = _split_amount(data.resolved_monthly_revenue(), len(days))
    return [
        CashEvent(
            event_id=f"quick-{scenario}-revenue-{month_index}-{index}",
            event_date=date(year, month, day),
            event_type="operating_inflow",
            amount=amount,
            description="간편모드 월 매출유입",
            source=f"re8_quick_{scenario}",
        )
        for index, (day, amount) in enumerate(zip(days, amounts, strict=True), start=1)
    ]


def build_quick_schedules(data: QuickModeInput) -> dict[str, DetailedCashflowInput]:
    """Return conservative, central and favorable exact-date schedules."""

    schedules: dict[str, DetailedCashflowInput] = {}
    for scenario in ("conservative", "central", "favorable"):
        events: list[CashEvent] = []
        for month_index in range(6):
            month_date = add_months(data.reference_date, month_index)
            year, month = month_date.year, month_date.month
            last_day = calendar.monthrange(year, month)[1]
            events.extend(
                _revenue_events(
                    data,
                    year=year,
                    month=month,
                    month_index=month_index + 1,
                    scenario=scenario,
                )
            )
            expense_day = _pick_day(
                data.expense_timing,
                last_day=last_day,
                scenario=scenario,
                is_inflow=False,
            )
            for prefix, event_type, amount, expense_type, description in (
                ("rent", "fixed_cost", data.monthly_rent, "rent", "월 임대료"),
                ("labor", "fixed_cost", data.monthly_labor_cost, "labor", "월 인건비"),
                ("variable", "variable_cost", data.monthly_variable_cost, "purchase", "월 필수매입"),
            ):
                events.append(
                    CashEvent(
                        event_id=f"quick-{scenario}-{prefix}-{month_index + 1}",
                        event_date=date(year, month, expense_day),
                        event_type=event_type,
                        amount=amount,
                        expense_type=expense_type,
                        description=description,
                        source=f"re8_quick_{scenario}",
                    )
                )
        loans: list[LoanInput] = []
        if data.total_loan_balance:
            last_day = calendar.monthrange(data.reference_date.year, data.reference_date.month)[1]
            payment_day = _pick_day(
                data.debt_timing,
                last_day=last_day,
                scenario=scenario,
                is_inflow=False,
            )
            maturity = add_months(data.reference_date, data.remaining_term_months)
            loans.append(
                LoanInput(
                    loan_id="quick-existing-loan",
                    principal=data.total_loan_balance,
                    annual_interest_rate_percent=data.annual_interest_rate_percent,
                    repayment_method="equal_principal",
                    payment_day=payment_day,
                    maturity_date=date(
                        maturity.year,
                        maturity.month,
                        min(payment_day, calendar.monthrange(maturity.year, maturity.month)[1]),
                    ),
                )
            )
        schedules[scenario] = DetailedCashflowInput(
            reference_date=data.reference_date,
            opening_cash=data.opening_cash,
            safe_cash_threshold=data.safe_cash_threshold,
            events=events,
            loans=loans,
        )
    return schedules
