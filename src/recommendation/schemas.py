"""Strict RE Stage 7 contracts for policy-alternative comparison."""

from __future__ import annotations

import math
from datetime import date
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, field_validator, model_validator

from src.policy.schemas import PolicyPlan, ValueSource


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CandidateState(StrEnum):
    ACTIONABLE = "지금 비교 가능"
    CONDITIONAL = "확인 후 비교"
    EXCLUDED = "제외"


class CombinationStatus(StrEnum):
    COMPATIBLE = "조합 가능"
    NEEDS_CONFIRMATION = "확인 필요"
    PROHIBITED = "조합 불가"


class UserGoal(StrEnum):
    MINIMUM_DEBT = "최소부채"
    LONGEST_SURVIVAL = "최장생존"
    MINIMUM_REPAYMENT = "최소상환"
    FAST_EXECUTION = "빠른실행"


class AlternativeKind(StrEnum):
    NO_ACTION = "no_action"
    COST_REDUCTION = "cost_reduction"
    NON_DEBT_SUPPORT = "non_debt_support"
    REFINANCE = "refinance"
    POLICY_LOAN = "policy_loan"
    COMBINED = "combined"


class CandidateContext(StrictModel):
    policy_id: str
    policy_version: str
    eligibility_status: str
    availability_status: str
    candidate_state: CandidateState
    reason_summary: str
    items_to_confirm: list[str] = Field(default_factory=list)
    as_of: date
    official_notice_url: str = ""
    application_url: str = ""


class CombinationRule(StrictModel):
    policy_ids: tuple[str, str]
    status: CombinationStatus
    reason: str
    evidence: str = ""

    @model_validator(mode="after")
    def normalize_pair(self) -> "CombinationRule":
        if self.policy_ids[0] == self.policy_ids[1]:
            raise ValueError("combination rule requires two different policy IDs")
        return self


class MarketScenario(StrictModel):
    target_a_percent: float | None = None
    target_b_percent: float | None = None
    application_ratio: float = Field(default=1.0, ge=0, le=3)
    direct_shock_13_week_percent: float | None = None
    direct_shock_6_month_percent: float | None = None
    model_version: str | None = None

    @field_validator(
        "target_a_percent",
        "target_b_percent",
        "direct_shock_13_week_percent",
        "direct_shock_6_month_percent",
    )
    @classmethod
    def validate_shock(cls, value: float | None) -> float | None:
        if value is not None and (not math.isfinite(value) or value < -100 or value > 1000):
            raise ValueError("market shock must be finite and between -100 and 1000 percent")
        return value

    @model_validator(mode="after")
    def require_each_horizon(self) -> "MarketScenario":
        if self.direct_shock_13_week_percent is None and self.target_a_percent is None:
            raise ValueError("13-week Target A or a direct 13-week shock is required")
        if self.direct_shock_6_month_percent is None and self.target_b_percent is None:
            raise ValueError("6-month Target B or a direct 6-month shock is required")
        return self

    def selected_shock(self, horizon: str) -> tuple[float, ValueSource, str]:
        if horizon == "13_week":
            direct = self.direct_shock_13_week_percent
            modeled = self.target_a_percent
            target = "target_a_next_quarter_yoy"
        elif horizon == "6_month":
            direct = self.direct_shock_6_month_percent
            modeled = self.target_b_percent
            target = "target_b_next_two_quarter_yoy"
        else:
            raise ValueError(f"unsupported horizon: {horizon}")
        if direct is not None:
            return direct, ValueSource.USER_INPUT, f"{horizon} 사용자 직접 충격률"
        assert modeled is not None
        return (
            modeled * self.application_ratio,
            ValueSource.EXPLICIT_SCENARIO_ASSUMPTION,
            f"{target} x 적용률 {self.application_ratio:.4g}",
        )


class AlternativeSpec(StrictModel):
    alternative_id: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=100)
    kind: AlternativeKind
    plans: list[PolicyPlan] = Field(default_factory=list)
    candidate_contexts: list[CandidateContext] = Field(default_factory=list)
    explicit_condition_assumption: StrictBool = False
    explicit_combination_assumption: StrictBool = False
    cost_reduction_rate_percent: float = Field(default=0, ge=0, le=100)
    payment_delay_days: StrictInt = Field(default=0, ge=0, le=365)
    application_deadline: date | None = None
    estimated_days_to_effect: StrictInt = Field(default=0, ge=0, le=3650)
    required_documents: list[str] = Field(default_factory=list)
    inquiry: str = ""
    official_urls: list[str] = Field(default_factory=list)
    same_expense_support_keys: dict[str, list[str]] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_kind(self) -> "AlternativeSpec":
        if self.kind is AlternativeKind.NO_ACTION and (
            self.plans or self.cost_reduction_rate_percent
        ):
            raise ValueError("no-action alternative cannot contain interventions")
        if self.kind is AlternativeKind.COST_REDUCTION and not self.cost_reduction_rate_percent:
            raise ValueError("cost-reduction alternative requires a positive rate")
        plan_policy_ids = {plan.policy_id for plan in self.plans}
        context_policy_ids = {context.policy_id for context in self.candidate_contexts}
        if plan_policy_ids != context_policy_ids:
            raise ValueError("every policy plan requires exactly one policy candidate context")
        return self


class SafeCashSuggestion(StrictModel):
    status: str
    suggested_amount: StrictInt | None = Field(default=None, ge=0)
    source: ValueSource
    horizon_days: StrictInt = 28
    included_event_ids: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    explanation: str


class AlternativeMetrics(StrictModel):
    week13_ending_cash: StrictInt
    month6_ending_cash: StrictInt
    week13_minimum_cash: StrictInt
    month6_minimum_cash: StrictInt
    week13_depletion_date: date | None
    month6_depletion_date: date | None
    survival_days_13_week: StrictInt = Field(ge=0)
    survival_days_6_month: StrictInt = Field(ge=0)
    survives_13_weeks: StrictBool
    survives_6_months: StrictBool
    net_new_borrowing: StrictInt
    refinanced_principal: StrictInt = Field(ge=0)
    month6_remaining_principal: StrictInt | None = Field(default=None, ge=0)
    maximum_monthly_debt_service: StrictInt = Field(ge=0)
    first_policy_monthly_payment: StrictInt = Field(ge=0)
    total_interest_through_maturity: StrictInt | None
    total_repayment_obligation: StrictInt | None
    support_or_cost_reduction: StrictInt = Field(ge=0)
    payment_delay_days: StrictInt = Field(ge=0)
    application_deadline: date | None
    confirmation_item_count: StrictInt = Field(ge=0)
    days_to_first_effect: StrictInt = Field(ge=0)
    cash_needed_before_payment: StrictInt = Field(ge=0)


class AlternativeResult(StrictModel):
    alternative_id: str
    label: str
    kind: AlternativeKind
    candidate_state: CandidateState
    combination_status: CombinationStatus
    simulated: StrictBool
    ranking_eligible: StrictBool
    reason_summary: str
    items_to_confirm: list[str]
    metrics: AlternativeMetrics | None = None
    weekly_13: list[dict[str, Any]] = Field(default_factory=list)
    monthly_6: list[dict[str, Any]] = Field(default_factory=list)
    assumption_ledger: list[dict[str, Any]] = Field(default_factory=list)
    official_urls: list[str] = Field(default_factory=list)
    warnings: list[dict[str, str]] = Field(default_factory=list)
    dominated_by: list[str] = Field(default_factory=list)


class GoalRanking(StrictModel):
    goal: UserGoal
    meaning: str
    ordered_alternative_ids: list[str]
    top_alternative_id: str | None
    fallback_used: StrictBool = False


class ExecutionPlan(StrictModel):
    alternative_id: str
    conditions_to_check_now: list[str]
    application_deadline: date | None
    required_documents: list[str]
    cash_needed_before_payment: StrictInt = Field(ge=0)
    fallback_alternative_id: str | None
    minimum_loan_amount: StrictInt = Field(ge=0)
    inquiry: str
    official_urls: list[str]


class DecisionResult(StrictModel):
    engine_version: str = "re7-v1"
    as_of: date
    comparison_basis: str
    alternatives: list[AlternativeResult]
    rankings: list[GoalRanking]
    pareto_frontier_ids: list[str]
    execution_plans: list[ExecutionPlan]
    safe_cash: SafeCashSuggestion
    prohibited_claims: list[str]
