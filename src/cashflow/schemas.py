"""Pydantic input contracts for simple and detailed RE Stage 3 calculations."""

from __future__ import annotations

import math
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class RepaymentMethod(StrEnum):
    EQUAL_PRINCIPAL = "equal_principal"
    EQUAL_PAYMENT = "equal_payment"
    BULLET = "bullet"


class EventType(StrEnum):
    HISTORICAL_REVENUE = "historical_revenue"
    OPERATING_INFLOW = "operating_inflow"
    ACCOUNTS_RECEIVABLE = "accounts_receivable"
    FIXED_COST = "fixed_cost"
    VARIABLE_COST = "variable_cost"
    TAX_UTILITY = "tax_utility"
    ACCOUNTS_PAYABLE = "accounts_payable"
    ONE_TIME_EXPENSE = "one_time_expense"


class ExpenseType(StrEnum):
    RENT = "rent"
    LABOR = "labor"
    PURCHASE = "purchase"
    TAX = "tax"
    UTILITY = "utility"
    SOCIAL_INSURANCE = "social_insurance"
    VEHICLE_FUEL = "vehicle_fuel"
    EQUIPMENT = "equipment"
    REPAIR = "repair"
    OTHER = "other"


class OtherFixedCost(InputModel):
    name: str = Field(min_length=1, max_length=100)
    amount: StrictInt = Field(ge=0)
    payment_day: StrictInt = Field(ge=1, le=31)
    expense_type: ExpenseType = ExpenseType.OTHER


class SimpleCashflowInput(InputModel):
    reference_date: date
    opening_cash: StrictInt = Field(ge=0)
    safe_cash_threshold: StrictInt = Field(ge=0)
    monthly_revenue: StrictInt | None = Field(default=None, ge=0)
    recent_monthly_revenues: list[StrictInt] | None = None
    revenue_receipt_day: StrictInt = Field(ge=1, le=31)
    monthly_rent: StrictInt = Field(ge=0)
    rent_payment_day: StrictInt = Field(ge=1, le=31)
    monthly_labor_cost: StrictInt = Field(ge=0)
    labor_payment_day: StrictInt = Field(ge=1, le=31)
    monthly_variable_cost: StrictInt | None = Field(default=None, ge=0)
    variable_cost_rate_percent: float | None = Field(default=None, ge=0, le=100)
    variable_cost_payment_day: StrictInt = Field(ge=1, le=31)
    other_fixed_costs: list[OtherFixedCost] = Field(default_factory=list)
    total_loan_balance: StrictInt = Field(ge=0)
    monthly_debt_payment: StrictInt = Field(ge=0)
    debt_payment_day: StrictInt = Field(ge=1, le=31)

    @field_validator("recent_monthly_revenues")
    @classmethod
    def validate_recent_revenues(
        cls, value: list[int] | None
    ) -> list[int] | None:
        if value is None:
            return value
        if not 1 <= len(value) <= 12:
            raise ValueError("recent_monthly_revenues must contain 1 to 12 months")
        if any(item < 0 for item in value):
            raise ValueError("recent_monthly_revenues cannot contain negative amounts")
        return value

    @field_validator("variable_cost_rate_percent")
    @classmethod
    def finite_rate(cls, value: float | None) -> float | None:
        if value is not None and not math.isfinite(value):
            raise ValueError("variable_cost_rate_percent must be finite")
        return value

    @model_validator(mode="after")
    def validate_exclusive_fields(self) -> "SimpleCashflowInput":
        revenue_sources = int(self.monthly_revenue is not None) + int(
            self.recent_monthly_revenues is not None
        )
        if revenue_sources != 1:
            raise ValueError(
                "provide exactly one of monthly_revenue or recent_monthly_revenues"
            )
        variable_sources = int(self.monthly_variable_cost is not None) + int(
            self.variable_cost_rate_percent is not None
        )
        if variable_sources != 1:
            raise ValueError(
                "provide exactly one of monthly_variable_cost or "
                "variable_cost_rate_percent"
            )
        if self.total_loan_balance == 0 and self.monthly_debt_payment > 0:
            raise ValueError(
                "monthly_debt_payment cannot be positive when total_loan_balance is zero"
            )
        names = [item.name.casefold() for item in self.other_fixed_costs]
        if len(names) != len(set(names)):
            raise ValueError("other_fixed_costs contains a duplicate name")
        return self

    def resolved_monthly_revenue(self) -> int:
        if self.monthly_revenue is not None:
            return self.monthly_revenue
        assert self.recent_monthly_revenues is not None
        average = Decimal(sum(self.recent_monthly_revenues)) / Decimal(
            len(self.recent_monthly_revenues)
        )
        return int(average.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


class CashEvent(InputModel):
    event_id: str = Field(min_length=1, max_length=100)
    event_date: date
    event_type: EventType
    amount: StrictInt = Field(ge=0)
    expense_type: ExpenseType | None = None
    description: str = Field(default="", max_length=300)
    source: str = Field(default="user", max_length=100)

    @model_validator(mode="after")
    def validate_expense_type(self) -> "CashEvent":
        expense_events = {
            EventType.FIXED_COST,
            EventType.VARIABLE_COST,
            EventType.TAX_UTILITY,
            EventType.ACCOUNTS_PAYABLE,
            EventType.ONE_TIME_EXPENSE,
        }
        if self.event_type in expense_events and self.expense_type is None:
            raise ValueError("expense_type is required for an expense event")
        if self.event_type not in expense_events and self.expense_type is not None:
            raise ValueError("expense_type is only allowed for an expense event")
        return self


class LoanInput(InputModel):
    loan_id: str = Field(min_length=1, max_length=100)
    principal: StrictInt = Field(gt=0)
    annual_interest_rate_percent: float = Field(ge=0, le=100)
    repayment_method: RepaymentMethod
    payment_day: StrictInt = Field(ge=1, le=31)
    maturity_date: date
    grace_months: StrictInt = Field(default=0, ge=0)

    @field_validator("annual_interest_rate_percent")
    @classmethod
    def finite_interest_rate(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("annual_interest_rate_percent must be finite")
        return value

    @model_validator(mode="after")
    def validate_bullet_grace(self) -> "LoanInput":
        if self.repayment_method is RepaymentMethod.BULLET and self.grace_months != 0:
            raise ValueError("bullet repayment already defers principal; grace_months must be 0")
        return self


class DetailedCashflowInput(InputModel):
    reference_date: date
    opening_cash: StrictInt = Field(ge=0)
    safe_cash_threshold: StrictInt = Field(ge=0)
    events: list[CashEvent]
    loans: list[LoanInput] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_uniqueness_and_dates(self) -> "DetailedCashflowInput":
        event_ids = [event.event_id for event in self.events]
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("events contains a duplicate event_id")
        loan_ids = [loan.loan_id for loan in self.loans]
        if len(loan_ids) != len(set(loan_ids)):
            raise ValueError("loans contains a duplicate loan_id")
        duplicated_cost_keys: set[tuple[date, EventType, int, ExpenseType | None, str]] = set()
        for event in self.events:
            if event.event_type in {
                EventType.FIXED_COST,
                EventType.VARIABLE_COST,
                EventType.TAX_UTILITY,
                EventType.ACCOUNTS_PAYABLE,
                EventType.ONE_TIME_EXPENSE,
            }:
                key = (
                    event.event_date,
                    event.event_type,
                    event.amount,
                    event.expense_type,
                    event.description.casefold(),
                )
                if key in duplicated_cost_keys:
                    raise ValueError("events contains a probable duplicate cost")
                duplicated_cost_keys.add(key)
        for loan in self.loans:
            if loan.maturity_date < self.reference_date:
                raise ValueError(f"loan {loan.loan_id} matures before reference_date")
        return self
