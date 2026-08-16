"""Monthly loan repayment schedules with won-level event rounding."""

from __future__ import annotations

import calendar
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from .errors import CashflowInputError
from .schemas import LoanInput, RepaymentMethod


WON = Decimal("1")


def round_won(value: Decimal | float | int) -> int:
    return int(Decimal(str(value)).quantize(WON, rounding=ROUND_HALF_UP))


def month_date(year: int, month: int, day: int) -> date:
    return date(year, month, min(day, calendar.monthrange(year, month)[1]))


def add_months(value: date, months: int) -> date:
    index = value.year * 12 + (value.month - 1) + months
    year, zero_month = divmod(index, 12)
    return month_date(year, zero_month + 1, value.day)


def first_monthly_date(reference_date: date, payment_day: int) -> date:
    candidate = month_date(reference_date.year, reference_date.month, payment_day)
    if candidate >= reference_date:
        return candidate
    following = add_months(date(reference_date.year, reference_date.month, 1), 1)
    return month_date(following.year, following.month, payment_day)


def payment_dates(reference_date: date, payment_day: int, maturity_date: date) -> list[date]:
    first = first_monthly_date(reference_date, payment_day)
    if maturity_date < first:
        return [maturity_date] if maturity_date >= reference_date else []
    dates: list[date] = []
    current = first
    while current <= maturity_date:
        dates.append(current)
        current = add_months(current, 1)
    if dates[-1] != maturity_date:
        dates.append(maturity_date)
    return dates


@dataclass(frozen=True)
class LoanPayment:
    loan_id: str
    payment_number: int
    payment_date: date
    opening_principal: int
    principal: int
    interest: int
    total_payment: int
    closing_principal: int
    is_grace_period: bool

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["payment_date"] = self.payment_date.isoformat()
        return payload


def build_loan_schedule(loan: LoanInput, reference_date: date) -> list[LoanPayment]:
    """Create a deterministic monthly schedule from the current principal.

    Interest is `opening principal * annual rate / 12` for every scheduled
    payment. There is intentionally no day-count accrual. Each principal and
    interest event is rounded independently to the nearest won using half-up.
    """

    dates = payment_dates(reference_date, loan.payment_day, loan.maturity_date)
    if not dates:
        raise CashflowInputError(
            "INVALID_MATURITY_DATE",
            f"loans.{loan.loan_id}.maturity_date",
            "만기는 기준일 이후여야 합니다.",
        )
    if loan.repayment_method is not RepaymentMethod.BULLET and loan.grace_months >= len(dates):
        raise CashflowInputError(
            "INVALID_GRACE_PERIOD",
            f"loans.{loan.loan_id}.grace_months",
            "거치개월은 전체 남은 납부회수보다 작아야 합니다.",
        )

    monthly_rate = Decimal(str(loan.annual_interest_rate_percent)) / Decimal("1200")
    amortizing_periods = len(dates) - loan.grace_months
    original = Decimal(loan.principal)
    equal_principal = (
        original / Decimal(amortizing_periods) if amortizing_periods else Decimal(0)
    )
    if loan.repayment_method is RepaymentMethod.EQUAL_PAYMENT:
        if monthly_rate == 0:
            level_payment = original / Decimal(amortizing_periods)
        else:
            factor = (Decimal(1) + monthly_rate) ** amortizing_periods
            level_payment = original * monthly_rate * factor / (factor - Decimal(1))
    else:
        level_payment = Decimal(0)

    remaining = loan.principal
    schedule: list[LoanPayment] = []
    for index, payment_date in enumerate(dates, start=1):
        opening = remaining
        interest = round_won(Decimal(opening) * monthly_rate)
        in_grace = index <= loan.grace_months
        is_final = index == len(dates)

        if loan.repayment_method is RepaymentMethod.BULLET:
            principal = remaining if is_final else 0
        elif in_grace:
            principal = 0
        elif is_final:
            principal = remaining
        elif loan.repayment_method is RepaymentMethod.EQUAL_PRINCIPAL:
            principal = min(remaining, round_won(equal_principal))
        else:
            principal = min(remaining, max(0, round_won(level_payment) - interest))

        remaining -= principal
        schedule.append(
            LoanPayment(
                loan_id=loan.loan_id,
                payment_number=index,
                payment_date=payment_date,
                opening_principal=opening,
                principal=principal,
                interest=interest,
                total_payment=principal + interest,
                closing_principal=remaining,
                is_grace_period=in_grace,
            )
        )

    if schedule[-1].closing_principal != 0:
        raise AssertionError("loan schedule did not clear principal at maturity")
    return schedule
