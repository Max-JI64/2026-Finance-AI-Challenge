"""Scenario inputs and auditable outputs for RE Stage 4."""

from __future__ import annotations

import math
from datetime import date
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, field_validator, model_validator

from src.cashflow.schemas import ExpenseType, LoanInput, RepaymentMethod


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ScenarioStatus(StrEnum):
    ASSUMED_APPROVED = "assumed_approved"
    NOT_APPROVED = "not_approved"


class ValueSource(StrEnum):
    OFFICIAL = "official"
    USER_INPUT = "user_input"
    EXPLICIT_SCENARIO_ASSUMPTION = "explicit_scenario_assumption"
    CALCULATED = "calculated"
    UNCONFIRMED = "unconfirmed"


class CashDirection(StrEnum):
    INFLOW = "inflow"
    OUTFLOW = "outflow"
    NONE = "none"


class EffectKind(StrEnum):
    SUPPORT_CASH_INFLOW = "support_cash_inflow"
    COST_REDUCTION = "cost_reduction"
    USER_CONTRIBUTION = "user_contribution"
    NEW_DEBT_PRINCIPAL = "new_debt_principal"
    PROJECT_EXPENSE = "project_expense"
    EXISTING_DEBT_PAYOFF = "existing_debt_payoff"
    EXISTING_PRINCIPAL_PAYMENT_REVERSAL = "existing_principal_payment_reversal"
    EXISTING_INTEREST_PAYMENT_REVERSAL = "existing_interest_payment_reversal"
    DEBT_PRINCIPAL_REPAYMENT = "debt_principal_repayment"
    DEBT_INTEREST = "debt_interest"
    INTEREST_REDUCTION = "interest_reduction"
    GUARANTEE_FEE = "guarantee_fee"
    GUARANTEE_FEE_SUPPORT = "guarantee_fee_support"
    OTHER_FEE = "other_fee"
    INFORMATION_ONLY = "information_only"


class AssumptionEntry(StrictModel):
    field: str
    value: Any
    source: ValueSource
    reason: str


class PolicyFinancialEvent(StrictModel):
    policy_id: str
    policy_version: str
    event_id: str
    linked_event_id: str | None = None
    deduplication_key: str
    sequence: StrictInt = Field(ge=1)
    effect_kind: EffectKind
    cash_direction: CashDirection
    event_date: date | None = None
    amount: StrictInt | None = Field(default=None, ge=0)
    amount_source: ValueSource
    description: str

    @model_validator(mode="after")
    def validate_monetary_event(self) -> "PolicyFinancialEvent":
        if self.cash_direction is CashDirection.NONE:
            return self
        if self.event_date is None or self.amount is None:
            raise ValueError("cash event requires event_date and amount")
        return self


class PolicyPlan(StrictModel):
    policy_id: str
    policy_version: str
    event_id: str
    event_name: str
    support_kind: str
    scenario_status: ScenarioStatus
    calculation_status: str
    deduplication_key: str
    linked_event_id: str | None = None
    conditional_notice: str
    events: list[PolicyFinancialEvent]
    assumptions: list[AssumptionEntry]
    unconfirmed_conditions: list[str]
    summary: dict[str, Any]


class BaseScenario(StrictModel):
    policy_id: str
    event_id: str
    scenario_status: ScenarioStatus


class GrantScenario(BaseScenario):
    approved_support_amount: StrictInt | None = Field(default=None, ge=0)
    approved_support_amount_source: ValueSource = ValueSource.USER_INPUT
    payment_date: date | None = None
    payment_date_source: ValueSource = ValueSource.EXPLICIT_SCENARIO_ASSUMPTION
    total_project_cost: StrictInt | None = Field(default=None, ge=0)
    eligible_expense_amount: StrictInt | None = Field(default=None, ge=0)
    vat_amount: StrictInt = Field(default=0, ge=0)
    expense_date: date | None = None
    expense_already_in_baseline: StrictBool = False

    @model_validator(mode="after")
    def validate_approved(self) -> "GrantScenario":
        if self.scenario_status is ScenarioStatus.ASSUMED_APPROVED:
            if self.approved_support_amount is None or self.payment_date is None:
                raise ValueError("approved grant scenario requires amount and payment_date")
        return self


class VoucherExpense(StrictModel):
    expense_id: str = Field(min_length=1, max_length=100)
    expense_date: date
    expense_type: ExpenseType | str
    amount: StrictInt = Field(ge=0)
    description: str = Field(default="", max_length=300)


class VoucherScenario(BaseScenario):
    awarded_amount: StrictInt | None = Field(default=None, ge=0)
    awarded_amount_source: ValueSource = ValueSource.USER_INPUT
    activation_date: date | None = None
    expiry_date: date | None = None
    active_period_source: ValueSource = ValueSource.EXPLICIT_SCENARIO_ASSUMPTION
    expenses: list[VoucherExpense] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_approved(self) -> "VoucherScenario":
        if self.scenario_status is ScenarioStatus.ASSUMED_APPROVED:
            if self.awarded_amount is None or self.activation_date is None or self.expiry_date is None:
                raise ValueError("approved voucher scenario requires amount and active dates")
        return self


class LoanScenario(BaseScenario):
    approved_principal: StrictInt | None = Field(default=None, gt=0)
    approved_principal_source: ValueSource = ValueSource.USER_INPUT
    execution_date: date | None = None
    execution_date_source: ValueSource = ValueSource.EXPLICIT_SCENARIO_ASSUMPTION
    payment_day: StrictInt | None = Field(default=None, ge=1, le=31)
    term_months: StrictInt | None = Field(default=None, gt=0)
    grace_months: StrictInt = Field(default=0, ge=0)
    repayment_method: RepaymentMethod | None = None
    bank_interest_rate_percent: float | None = Field(default=None, ge=0, le=100)
    reference_interest_rate_percent: float | None = Field(default=None, ge=0, le=100)
    upfront_fee: StrictInt = Field(default=0, ge=0)
    guarantee_fee: StrictInt = Field(default=0, ge=0)

    @field_validator("bank_interest_rate_percent", "reference_interest_rate_percent")
    @classmethod
    def finite_rate(cls, value: float | None) -> float | None:
        if value is not None and not math.isfinite(value):
            raise ValueError("interest rate must be finite")
        return value

    @model_validator(mode="after")
    def validate_approved(self) -> "LoanScenario":
        if self.scenario_status is ScenarioStatus.ASSUMED_APPROVED:
            required = (
                self.approved_principal,
                self.execution_date,
                self.payment_day,
                self.term_months,
                self.repayment_method,
            )
            if any(value is None for value in required):
                raise ValueError("approved loan scenario requires amount, execution date, payment day, term and method")
            assert self.term_months is not None
            if self.repayment_method is not RepaymentMethod.BULLET and self.grace_months >= self.term_months:
                raise ValueError("grace_months must be shorter than term_months")
            if self.repayment_method is RepaymentMethod.BULLET and self.grace_months != 0:
                raise ValueError("bullet repayment requires grace_months=0")
        return self


class RefinanceScenario(BaseScenario):
    execution_date: date | None = None
    execution_date_source: ValueSource = ValueSource.EXPLICIT_SCENARIO_ASSUMPTION
    existing_refinanced_loan: LoanInput | None = None
    replacement_loan: LoanInput | None = None
    upfront_fee: StrictInt = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_approved(self) -> "RefinanceScenario":
        if self.scenario_status is ScenarioStatus.ASSUMED_APPROVED:
            if self.execution_date is None or self.existing_refinanced_loan is None or self.replacement_loan is None:
                raise ValueError("approved refinance requires execution date and both loan contracts")
            if self.existing_refinanced_loan.principal != self.replacement_loan.principal:
                raise ValueError(
                    "existing_refinanced_loan must describe exactly the principal tranche being fully refinanced"
                )
        return self


class GuaranteeScenario(BaseScenario):
    linked_loan_scenario: LoanScenario | None = None
    guarantee_fee_amount: StrictInt = Field(default=0, ge=0)
    guarantee_fee_date: date | None = None
    guarantee_fee_support_amount: StrictInt = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_fee_date(self) -> "GuaranteeScenario":
        if (self.guarantee_fee_amount > 0 or self.guarantee_fee_support_amount > 0) and self.guarantee_fee_date is None:
            raise ValueError("guarantee fee or support requires guarantee_fee_date")
        return self
