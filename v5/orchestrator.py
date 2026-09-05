"""Bounded V5 orchestration over the reviewed deterministic finance engines."""

from __future__ import annotations

import hashlib
import json
import re
import warnings
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from typing import Any, Literal
from uuid import uuid4
from unittest.mock import patch

from pydantic import BaseModel, ConfigDict, Field

import src.integration.re_stage8 as re_stage8
from src.integration.re_stage8 import (
    SampleCompareRequest,
    area_map_catalog,
    compare_sample,
    industry_catalog,
)
from src.policy.discovery import POLICY_FIELDS, QUESTIONS
from src.policy.re_stage8_2_events import DynamicPolicyScenario
from src.rag.luna_client import interpret_what_if_with_luna


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SituationRequest(StrictModel):
    text: str = Field(min_length=2, max_length=1200)


class SituationContext(StrictModel):
    original_text: str = Field(min_length=2, max_length=1200)
    confirmed_area_code: str | None = None
    confirmed_industry_code: str | None = None
    signals: list[
        Literal["sales_decline", "debt_concern", "fixed_cost_concern", "cash_concern"]
    ] = Field(default_factory=list, max_length=4)
    confirmed_goal: Literal["최소부채", "최장생존", "최소상환", "빠른실행"] | None = None


ReviewLensValue = Literal["cash_runway", "debt_relief", "fixed_cost", "policy_choice", "unsure"]
ConfirmedReviewLens = Literal["cash_runway", "debt_relief", "fixed_cost", "policy_choice"]
ReviewLensSource = Literal["user", "suggested", "confirmed_suggestion", "changed"]


class DetectedSignal(StrictModel):
    key: Literal[
        "cash_gap_28d",
        "negative_cash_within_13w",
        "sales_direction",
        "high_interest_debt_present",
        "fixed_cost_pressure",
        "new_debt_sensitivity",
        "policy_route_uncertainty",
    ]
    status: Literal["present", "absent", "unknown"]
    value: int | float | str | bool | None = None
    display_text: str = Field(min_length=2, max_length=300)
    reason: str = Field(min_length=2, max_length=400)


class ReviewPlan(StrictModel):
    review_lens: ConfirmedReviewLens | None = None
    review_lens_source: ReviewLensSource
    requires_confirmation: bool
    suggested_review_lens: ConfirmedReviewLens | None = None
    goal_label: str = Field(min_length=2, max_length=100)
    detected_signal_keys: list[str] = Field(max_length=10)
    first_effect: str = Field(min_length=2, max_length=300)
    metric_order: list[str] = Field(min_length=3, max_length=3)
    summary: str = Field(min_length=2, max_length=1200)


class PolicyReviewItem(StrictModel):
    policy_id: str = Field(min_length=2, max_length=100)
    policy_name: str = Field(min_length=2, max_length=200)
    review_position: int = Field(ge=1, le=3)
    rank_position: int | None = Field(default=None, ge=1)
    mechanism: str = Field(min_length=2, max_length=80)
    review_reason: str = Field(min_length=2, max_length=500)


class NoticeFieldPriority(StrictModel):
    key: Literal["publication_date", "application_period", "application_path", "financing_terms", "required_documents", "contact"]
    position: int = Field(ge=1, le=6)
    reason: str = Field(min_length=2, max_length=300)


class ToolExecutionTrace(StrictModel):
    trace_id: str = Field(min_length=8, max_length=80)
    tool_name: Literal["finance_diagnosis", "review_lens", "policy_preparation", "policy_discovery", "policy_simulator"]
    tool_version: str = Field(min_length=2, max_length=40)
    input_schema_version: str = Field(min_length=2, max_length=40)
    output_schema_version: str = Field(min_length=2, max_length=40)
    started_at: str = Field(min_length=20, max_length=40)
    finished_at: str = Field(min_length=20, max_length=40)
    status: Literal["success", "fallback", "fail_closed"]
    policy_ids: list[str] = Field(max_length=20)
    source_digests: list[str] = Field(max_length=20)
    displayed_reason: str = Field(min_length=2, max_length=500)


class OrchestrateRequest(StrictModel):
    comparison: SampleCompareRequest
    answered_fields: list[str] = Field(default_factory=list, max_length=80)
    asked_fields: list[str] = Field(default_factory=list, max_length=80)
    situation_context: SituationContext | None = None
    question_round: int = Field(default=0, ge=0, le=2)
    review_lens: ReviewLensValue
    review_lens_source: ReviewLensSource = "user"
    confirmed_review_lens: ConfirmedReviewLens | None = None


class WhatIfRequest(StrictModel):
    comparison: SampleCompareRequest
    prompt: str = Field(min_length=2, max_length=800)
    answered_fields: list[str] = Field(default_factory=list, max_length=80)
    asked_fields: list[str] = Field(default_factory=list, max_length=80)
    situation_context: SituationContext | None = None
    consent_to_external_ai: bool = False
    question_round: int = Field(default=2, ge=0, le=2)
    review_lens: ReviewLensValue
    review_lens_source: ReviewLensSource = "user"
    confirmed_review_lens: ConfirmedReviewLens | None = None


class WhatIfOperation(StrictModel):
    kind: Literal["revenue_percent", "cost_reduction", "market_scenario", "goal"]
    direction: Literal["decrease", "increase"] | None = None
    percent: float | None = Field(default=None, gt=0, le=100)
    cost_key: Literal["rent", "labor", "purchase", "other_fixed"] | None = None
    amount_won: int | None = Field(default=None, ge=0, le=1_000_000_000)
    value: str | None = Field(default=None, max_length=30)


class WhatIfIntent(StrictModel):
    status: Literal["ready", "clarification_needed"]
    summary: str = Field(default="", max_length=300)
    clarification_question: str | None = Field(default=None, max_length=300)
    operations: list[WhatIfOperation] = Field(default_factory=list, max_length=4)


REPRESENTATIVE_DEMO_ALTERNATIVES = (
    ("no_action", "무대응"),
    ("track2_reimbursement", "비차입 지원"),
    ("emergency_loan", "신규 정책자금"),
)


def _first_cash_shortage_week(alternative: dict[str, Any]) -> int | None:
    for row in alternative.get("weekly_13", []):
        if int(row.get("minimum_cash", 0)) < 0:
            return int(row["period"])
    return None


def _demo_metric(alternative: dict[str, Any], key: str) -> int:
    metrics = alternative.get("metrics") or {}
    value = metrics.get(key)
    if value is None:
        raise ValueError(f"대표 사례 계산 결과에 {key} 지표가 없습니다.")
    return int(value)


def _change_sentence(subject: str, amount: int, baseline: str = "무대응") -> str:
    if amount > 0:
        return f"{subject} {baseline}보다 {amount:,}원 늘어납니다"
    if amount < 0:
        return f"{subject} {baseline}보다 {abs(amount):,}원 줄어듭니다"
    return f"{subject} {baseline}과 같습니다"


def _change_amount(amount: int) -> str:
    if amount > 0:
        return f"{amount:,}원 늘어납니다"
    if amount < 0:
        return f"{abs(amount):,}원 줄어듭니다"
    return "같습니다"


@lru_cache(maxsize=1)
def representative_demo() -> dict[str, Any]:
    """Return one fixed fictional case calculated by the existing finance engine."""

    calculated = compare_sample(SampleCompareRequest(
        sample_id="declining_cash_shortage",
        direct_shock_13_week_percent=-12,
        direct_shock_6_month_percent=-18,
        goal="최소부채",
        assume_conditional=True,
        v2_mode=False,
    ))
    alternatives = {
        str(item.get("alternative_id")): item
        for item in calculated.get("intervention_results", [])
    }
    missing = [alternative_id for alternative_id, _ in REPRESENTATIVE_DEMO_ALTERNATIVES if alternative_id not in alternatives]
    if missing:
        raise ValueError(f"대표 사례 대안이 누락되었습니다: {', '.join(missing)}")

    baseline = alternatives["no_action"]
    scenarios: list[dict[str, Any]] = []
    for alternative_id, display_label in REPRESENTATIVE_DEMO_ALTERNATIVES:
        alternative = alternatives[alternative_id]
        metrics = alternative.get("metrics") or {}
        scenarios.append({
            "alternative_id": alternative_id,
            "label": display_label,
            "policy_label": alternative.get("label"),
            "first_cash_shortage_week": _first_cash_shortage_week(alternative),
            "week13_ending_cash": _demo_metric(alternative, "week13_ending_cash"),
            "month6_remaining_principal": _demo_metric(alternative, "month6_remaining_principal"),
            "maximum_monthly_debt_service": _demo_metric(alternative, "maximum_monthly_debt_service"),
            "total_interest_through_maturity": _demo_metric(alternative, "total_interest_through_maturity"),
            "net_new_borrowing": _demo_metric(alternative, "net_new_borrowing"),
            "support_or_cost_reduction": int(metrics.get("support_or_cost_reduction") or 0),
            "week13_cash_change_vs_no_action": (
                _demo_metric(alternative, "week13_ending_cash")
                - _demo_metric(baseline, "week13_ending_cash")
            ),
            "month6_debt_change_vs_no_action": (
                _demo_metric(alternative, "month6_remaining_principal")
                - _demo_metric(baseline, "month6_remaining_principal")
            ),
            "is_conditional": alternative_id != "no_action",
        })

    non_debt = scenarios[1]
    policy_loan = scenarios[2]
    summary = (
        "비차입 지원은 신규 부채가 0원이며, "
        f"{_change_sentence('13주 현금은', non_debt['week13_cash_change_vs_no_action'])}. "
        "신규 정책자금은 같은 기준에서 "
        f"13주 현금이 {_change_amount(policy_loan['week13_cash_change_vs_no_action'])}. "
        f"6개월 뒤 남은 부채도 {_change_amount(policy_loan['month6_debt_change_vs_no_action'])}."
    )
    baseline_input = calculated["baseline_input"]
    reference_month = str(baseline_input["reference_date"])[:7]
    first_month_events = [
        item
        for item in baseline_input["events"]
        if str(item["event_date"]).startswith(reference_month)
    ]
    return {
        "schema_version": "v5-representative-demo-v1.0",
        "sample_id": "declining_cash_shortage",
        "title": "현금 부족과 기존 부채가 함께 있는 가상 음식점",
        "is_synthetic": True,
        "calculation_authority": "deterministic_rule_event_cashflow_ranking_only",
        "input_summary": {
            "reference_date": baseline_input["reference_date"],
            "opening_cash": int(baseline_input["opening_cash"]),
            "monthly_revenue": sum(
                int(item["amount"])
                for item in first_month_events
                if item["event_type"] == "operating_inflow"
            ),
            "monthly_fixed_and_variable_cost": sum(
                int(item["amount"])
                for item in first_month_events
                if item["event_type"] in {"fixed_cost", "variable_cost"}
            ),
            "existing_loan_balance": sum(int(item["principal"]) for item in baseline_input["loans"]),
        },
        "scenarios": scenarios,
        "summary": summary,
        "limitations": [
            "실제 사업장이 아닌 고정 가상 사례입니다.",
            "정책 지원과 대출은 승인되고 표시된 시점에 실행된 경우를 가정한 계산입니다.",
            "현재 접수 여부, 실제 승인과 최종 조건은 공식기관에서 확인해야 합니다.",
        ],
    }


INDUSTRY_ALIASES = {
    "카페": ("커피", "카페"),
    "커피": ("커피", "카페"),
    "음식점": ("한식", "음식점"),
    "식당": ("한식", "음식점"),
    "치킨": ("치킨",),
    "미용실": ("미용",),
    "편의점": ("편의점",),
    "학원": ("학원",),
    "의류": ("의류",),
}


GOAL_SIGNALS = {
    "최소부채": ("빚을 늘리고 싶지", "부채를 늘리고 싶지", "대출을 더 받고 싶지", "빚 없이"),
    "최장생존": ("오래 버티", "생존기간", "언제까지 버", "현금이 버"),
    "최소상환": ("상환 부담", "월 상환", "원리금", "이자 부담"),
    "빠른실행": ("빨리", "급해", "이번 주", "즉시", "당장"),
}


QUESTION_TERMS_BY_SIGNAL = {
    "sales_decline": ("매출", "영업", "운영", "업력"),
    "debt_concern": ("대출", "상환", "연체", "채무", "신용", "대환"),
    "fixed_cost_concern": ("임대", "인건비", "고용", "보험", "비용"),
    "cash_concern": ("현금", "자금", "지급", "매출", "운영"),
}


LENS_LABELS: dict[str, str] = {
    "cash_runway": "현금 생존",
    "debt_relief": "부채 부담",
    "fixed_cost": "비용 절감",
    "policy_choice": "정책 유형 비교",
}

METRIC_ORDER: dict[str, list[str]] = {
    "cash_runway": ["week13_ending_cash", "week13_minimum_cash", "cash_gap_28d"],
    "debt_relief": ["maximum_monthly_debt_service", "month6_remaining_principal", "net_new_borrowing"],
    "fixed_cost": ["support_or_cost_reduction", "week13_ending_cash", "net_new_borrowing"],
    "policy_choice": ["week13_ending_cash", "net_new_borrowing", "maximum_monthly_debt_service"],
}

POLICY_MECHANISMS: dict[str, str] = {
    "POL_SEMAS_STABILITY_VOUCHER_2026": "cost_reduction",
    "POL_SEMAS_REFINANCE_2026": "refinance",
    "POL_SEMAS_RECHALLENGE_2026": "new_loan",
    "POL_SEOUL_FUND_2026": "new_loan",
    "POL_SEOUL_CRISIS_TRACK2_2026H2": "grant",
    "POL_SEMAS_EMPLOYMENT_INSURANCE_2026": "cost_offset",
    "POL_SEOUL_FAMILY_FRIENDLY_EMPLOYER_2026": "grant",
    "POL_SEOUL_DIGITAL_MIDLIFE_2026H2": "grant",
    "POL_SEOUL_ZERO_MARKET_2026_2": "cost_offset",
    "POL_SEOUL_CLOSURE_2026": "grant",
    "POL_SEOUL_RESTART_2026": "mixed",
}

MECHANISM_LABELS: dict[str, str] = {
    "grant": "상환 의무가 없는 지원",
    "cost_reduction": "직접 비용 절감",
    "cost_offset": "지출 비용 보전",
    "refinance": "기존 대출 대환",
    "new_loan": "신규 정책융자",
    "mixed": "복합 지원",
    "other": "기타 금융지원",
}

POLICY_ALTERNATIVE_IDS: dict[str, tuple[str, ...]] = {
    "POL_SEMAS_STABILITY_VOUCHER_2026": ("dynamic_pol_semas_stability_voucher_2026",),
    "POL_SEMAS_REFINANCE_2026": ("refinance", "conditional_pol_semas_refinance_2026"),
    "POL_SEMAS_RECHALLENGE_2026": ("conditional_pol_semas_rechallenge_2026",),
    "POL_SEOUL_FUND_2026": ("emergency_loan", "conditional_pol_seoul_fund_2026"),
    "POL_SEOUL_CRISIS_TRACK2_2026H2": ("track2_reimbursement", "conditional_pol_seoul_crisis_track2_2026h2"),
}

LENS_MECHANISM_ORDER: dict[str, tuple[str, ...]] = {
    "cash_runway": ("grant", "cost_reduction", "cost_offset", "new_loan", "refinance", "mixed", "other"),
    "debt_relief": ("refinance", "cost_reduction", "cost_offset", "grant", "mixed", "new_loan", "other"),
    "fixed_cost": ("cost_reduction", "cost_offset", "grant", "mixed", "refinance", "new_loan", "other"),
    "policy_choice": ("grant", "cost_reduction", "refinance", "new_loan", "cost_offset", "mixed", "other"),
}

def _longest_catalog_match(text: str, fields: tuple[str, ...]) -> dict[str, Any] | None:
    matches: list[tuple[int, dict[str, Any]]] = []
    for item in area_map_catalog():
        for field in fields:
            value = str(item.get(field, "")).strip()
            if len(value) >= 2 and value in text:
                matches.append((len(value), item))
    return max(matches, key=lambda pair: pair[0])[1] if matches else None


def _industry_match(text: str) -> dict[str, str] | None:
    industries = industry_catalog()
    exact = [item for item in industries if len(item["name"]) >= 2 and item["name"] in text]
    if exact:
        return max(exact, key=lambda item: len(item["name"]))
    for alias, keywords in INDUSTRY_ALIASES.items():
        if alias not in text:
            continue
        for item in industries:
            if any(keyword in item["name"] for keyword in keywords):
                return item
    return None


def interpret_situation(request: SituationRequest) -> dict[str, Any]:
    """Safely structure a free-text situation without inventing money values."""

    text = request.text.strip()
    # A district or dong name can match several market areas. Only an exact
    # market-area name is safe to preselect; broader matches stay as hints.
    area = _longest_catalog_match(text, ("name",))
    location_hint = area or _longest_catalog_match(text, ("administrative_dong", "district"))
    industry = _industry_match(text)
    signals: list[dict[str, str]] = []
    if "매출" in text and any(token in text for token in ("줄", "감소", "하락", "떨어")):
        signals.append({"key": "sales_decline", "label": "매출 감소를 걱정하고 있음"})
    if any(token in text for token in ("대출", "상환", "원리금", "이자")):
        signals.append({"key": "debt_concern", "label": "기존 대출·상환 부담을 언급함"})
    if any(token in text for token in ("임대료", "월세", "인건비", "고정비", "매입비")):
        signals.append({"key": "fixed_cost_concern", "label": "고정 지출 부담을 언급함"})
    if any(token in text for token in ("현금", "자금", "돈이 부족", "버티")):
        signals.append({"key": "cash_concern", "label": "현금 부족 또는 생존기간을 걱정함"})

    suggested_goal = None
    for goal, phrases in GOAL_SIGNALS.items():
        if any(phrase in text for phrase in phrases):
            suggested_goal = goal
            break

    understood = []
    if location_hint:
        understood.append({"key": "area", "label": "사업장 후보", "value": f"{location_hint['district']} {location_hint['administrative_dong']} · {location_hint['name']}", "confirmed": False})
    if industry:
        understood.append({"key": "industry", "label": "업종 후보", "value": industry["name"], "confirmed": False})
    understood.extend(
        {"key": item["key"], "label": "상황 신호", "value": item["label"], "confirmed": False}
        for item in signals
    )
    if suggested_goal:
        understood.append({"key": "goal", "label": "우선 기준 후보", "value": suggested_goal, "confirmed": False})

    missing = []
    if not area:
        missing.append("서울 상권")
    if not industry:
        missing.append("업종")
    missing.extend(["최근 월매출", "현재 보유 현금", "월 지출", "대출 조건"])
    return {
        "source": "local_bounded_interpreter",
        "external_ai_used": False,
        "original_text": text,
        "understood": understood,
        "suggested_area_code": area["code"] if area else None,
        "suggested_industry_code": industry["code"] if industry else None,
        "suggested_goal": suggested_goal,
        "missing_for_cash_diagnosis": missing,
        "confirmation_required": True,
        "notice": "문장에서 찾은 후보일 뿐 계산값이 아닙니다. 위치·업종·목표를 확인하거나 수정해 주세요.",
    }


def _candidate_groups(candidates: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups = {"comparable": [], "preparable": [], "official_check": [], "excluded": []}
    for candidate in candidates:
        state = str(candidate.get("candidate_state", ""))
        eligibility = str(candidate.get("eligibility_status", ""))
        if state == "제외" or eligibility == "부적격":
            groups["excluded"].append(candidate)
        elif state == "지금 비교 가능":
            groups["comparable"].append(candidate)
        elif state == "확인 후 비교":
            groups["preparable"].append(candidate)
        else:
            groups["official_check"].append(candidate)
    return groups


def _action_plan(
    result: dict[str, Any],
    situation_signals: set[str] | None = None,
) -> dict[str, Any]:
    candidates = result.get("policy_discovery", {}).get("candidates", [])
    today = ["현재 현금과 앞으로 28일의 필수지출·대출 상환액을 다시 확인합니다."]
    signal_actions = {
        "sales_decline": "문장에서 매출 감소를 확인했으므로 최근 6개월 월매출 실제값을 먼저 확인합니다.",
        "debt_concern": "문장에서 대출 부담을 확인했으므로 대출 잔액·금리·상환기간을 먼저 확인합니다.",
        "fixed_cost_concern": "문장에서 고정비 부담을 확인했으므로 임대료·인건비·필수 매입비를 먼저 확인합니다.",
        "cash_concern": "문장에서 현금 부족 우려를 확인했으므로 현재 보유 현금과 다음 28일 지출을 먼저 확인합니다.",
    }
    for signal in situation_signals or set():
        action = signal_actions.get(signal)
        if action and action not in today:
            today.append(action)
    for candidate in candidates[:3]:
        for item in candidate.get("items_to_confirm", [])[:1]:
            if item and item not in today:
                today.append(str(item))
    seven_days = []
    for candidate in candidates[:3]:
        name = candidate.get("policy_name") or candidate.get("title") or candidate.get("policy_id")
        state = candidate.get("candidate_state", "공식 확인 필요")
        seven_days.append(f"{name}: {state} 상태와 접수 여부를 공식 공고에서 확인합니다.")
    before = [
        "실제 승인금액·금리·지급일·상환조건을 기관에서 확인합니다.",
        "조건부 점선 효과는 승인 예측이나 추천 순위가 아님을 다시 확인합니다.",
    ]
    return {
        "today": today[:4],
        "within_seven_days": seven_days[:3] or ["비교할 정책 경로를 선택하고 공식 문의 질문을 준비합니다."],
        "before_application": before,
    }


def _detected_signals(
    request: OrchestrateRequest,
    result: dict[str, Any],
    questions: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
) -> list[DetectedSignal]:
    quick = request.comparison.quick_input
    no_action = next(
        (
            item
            for item in result.get("intervention_results", [])
            if item.get("alternative_id") == "no_action" and item.get("metrics")
        ),
        None,
    )
    safe_cash = int(result.get("safe_cash", {}).get("suggested_amount") or 0)
    opening_cash = int(getattr(quick, "opening_cash", 0) or 0) if quick else 0
    cash_gap = max(0, safe_cash - opening_cash)
    minimum_cash = int((no_action or {}).get("metrics", {}).get("week13_minimum_cash") or 0)

    revenues = list(getattr(quick, "recent_monthly_revenues", []) or []) if quick else []
    if len(revenues) >= 2 and revenues[-1] > 0:
        sales_change = (revenues[0] - revenues[-1]) / revenues[-1]
        sales_direction = "decline" if sales_change <= -0.1 else "recovery" if sales_change >= 0.1 else "stable"
        sales_status = "present"
        sales_reason = "기존 최근 월매출 방향 계산을 사용했습니다."
    else:
        sales_direction = "unknown"
        sales_status = "unknown"
        sales_reason = "비교할 월매출 기간이 부족해 방향을 확정하지 않았습니다."

    loan_balance = int(getattr(quick, "total_loan_balance", 0) or 0) if quick else 0
    loan_rate = float(getattr(quick, "annual_interest_rate_percent", 0) or 0) if quick else 0
    high_interest = loan_balance > 0 and loan_rate >= 7
    if quick:
        monthly_revenue = max(1, int(quick.resolved_monthly_revenue()))
        fixed_ratio = (int(quick.monthly_rent) + int(quick.monthly_labor_cost)) / monthly_revenue
        fixed_pressure = fixed_ratio >= 0.45
        fixed_status = "present" if fixed_pressure else "absent"
        fixed_reason = "기존 정책 검색의 임대료·인건비 대 월매출 45% 기준을 재사용했습니다."
    else:
        fixed_ratio = None
        fixed_status = "unknown"
        fixed_reason = "간편 재무 입력이 없어 기존 고정비 부담 신호를 계산하지 않았습니다."

    active_ids = {
        str(item.get("policy_id"))
        for item in candidates
        if item.get("candidate_state") != "제외" and item.get("eligibility_status") != "부적격"
    }
    unresolved_policy_conditions = sum(
        1
        for question in questions
        if active_ids.intersection(str(policy_id) for policy_id in question.get("policy_ids") or [])
    )
    new_debt_relevant = request.review_lens in {"debt_relief", "policy_choice"} or request.confirmed_review_lens in {"debt_relief", "policy_choice"}
    sales_display = {
        "decline": "최근 월매출이 이전보다 감소",
        "stable": "최근 월매출이 비슷한 수준을 유지",
        "recovery": "최근 월매출이 이전보다 회복",
        "unknown": "월매출 방향을 판단할 기간이 부족",
    }[sales_direction]
    return [
        DetectedSignal(
            key="cash_gap_28d",
            status="present" if cash_gap > 0 else "absent",
            value=cash_gap,
            display_text=(
                f"앞으로 28일 필요현금이 {cash_gap:,}원 부족"
                if cash_gap > 0
                else "현재 현금이 앞으로 28일 필요현금 이상"
            ),
            reason="현재 보유 현금과 기존 28일 필요현금 계산의 차이입니다.",
        ),
        DetectedSignal(
            key="negative_cash_within_13w",
            status="present" if minimum_cash < 0 else "absent",
            value=minimum_cash,
            display_text=(
                "13주 안에 현금이 0원 아래로 내려감"
                if minimum_cash < 0
                else "13주 안에 현금이 0원 아래로 내려가지 않음"
            ),
            reason="무대응 13주 기준선의 최저 현금으로 확인했습니다.",
        ),
        DetectedSignal(
            key="sales_direction",
            status=sales_status,
            value=sales_direction,
            display_text=sales_display,
            reason=sales_reason,
        ),
        DetectedSignal(
            key="high_interest_debt_present",
            status="present" if high_interest else "absent",
            value=loan_rate if loan_balance else 0,
            display_text=(
                f"연 {loan_rate:g}% 대출이 있어 대환 조건 확인 필요"
                if high_interest
                else "현재 입력에서 대환 우선 금리 조건은 감지되지 않음"
            ),
            reason="기존 대환 검토 계약의 연 7% 이상 고금리 기준을 재사용했습니다.",
        ),
        DetectedSignal(
            key="fixed_cost_pressure",
            status=fixed_status,
            value=fixed_ratio,
            display_text=(
                f"임대료와 인건비가 월매출의 약 {fixed_ratio * 100:.0f}%"
                if fixed_ratio is not None
                else "고정비 부담을 계산할 입력이 부족"
            ),
            reason=fixed_reason,
        ),
        DetectedSignal(
            key="new_debt_sensitivity",
            status="present" if new_debt_relevant else "absent",
            value=new_debt_relevant,
            display_text=(
                "정책 비교에서 새로 생기는 부채도 함께 확인"
                if new_debt_relevant
                else "현재 검토에서는 신규 부채를 첫 지표로 두지 않음"
            ),
            reason="선택한 검토 렌즈가 신규 부채 지표를 우선하는지 표시합니다.",
        ),
        DetectedSignal(
            key="policy_route_uncertainty",
            status="present" if unresolved_policy_conditions else "absent",
            value=unresolved_policy_conditions,
            display_text=(
                f"선택할 내용이 남은 정책 조건 {unresolved_policy_conditions}개"
                if unresolved_policy_conditions
                else "추가로 선택할 정책 조건 없음"
            ),
            reason="현재 활성 정책 후보와 연결된 미응답 조건 수입니다.",
        ),
    ]


def _suggest_review_lens(signals: list[DetectedSignal]) -> ConfirmedReviewLens:
    by_key = {item.key: item for item in signals}
    if by_key["cash_gap_28d"].status == "present" or by_key["negative_cash_within_13w"].status == "present":
        return "cash_runway"
    if by_key["high_interest_debt_present"].status == "present":
        return "debt_relief"
    if by_key["fixed_cost_pressure"].status == "present":
        return "fixed_cost"
    return "policy_choice"


def _effective_review_lens(request: OrchestrateRequest, signals: list[DetectedSignal]) -> tuple[ConfirmedReviewLens | None, ConfirmedReviewLens | None]:
    if request.review_lens != "unsure":
        return request.review_lens, None
    suggestion = _suggest_review_lens(signals)
    if request.confirmed_review_lens is not None:
        return request.confirmed_review_lens, suggestion
    return None, suggestion


def _metric_order(review_lens: ConfirmedReviewLens | None, suggested: ConfirmedReviewLens | None) -> list[str]:
    return list(METRIC_ORDER[review_lens or suggested or "policy_choice"])


def _review_plan(
    request: OrchestrateRequest,
    signals: list[DetectedSignal],
    review_lens: ConfirmedReviewLens | None,
    suggested_lens: ConfirmedReviewLens | None,
) -> ReviewPlan:
    plan_lens = review_lens or suggested_lens or "policy_choice"
    financial_signal_keys = {
        "cash_gap_28d",
        "negative_cash_within_13w",
        "sales_direction",
        "high_interest_debt_present",
        "fixed_cost_pressure",
    }
    present_signals = [
        item
        for item in signals
        if item.status == "present" and item.key in financial_signal_keys
    ]
    present = [item.key for item in present_signals]
    signal_text = ", ".join(item.display_text for item in present_signals[:3]) if present_signals else "뚜렷한 우선 신호 없음"
    effect_text = {
        "cash_runway": "13주 현금과 28일 필요현금 차이",
        "debt_relief": "월 상환액과 6개월 부채, 신규 부채",
        "fixed_cost": "비용 절감액과 13주 현금",
        "policy_choice": "지원 방식별 현금과 신규 부채 차이",
    }[plan_lens]
    requires_confirmation = review_lens is None
    source: ReviewLensSource = "suggested" if requires_confirmation else request.review_lens_source
    summary = (
        f"{LENS_LABELS[plan_lens]} 기준으로 검토합니다. "
        f"재무 입력에서 확인한 상태는 {signal_text}입니다. 먼저 비교할 항목은 {effect_text}입니다."
    )
    return ReviewPlan(
        review_lens=review_lens,
        review_lens_source=source,
        requires_confirmation=requires_confirmation,
        suggested_review_lens=suggested_lens,
        goal_label=LENS_LABELS[plan_lens],
        detected_signal_keys=present,
        first_effect=effect_text,
        metric_order=_metric_order(review_lens, suggested_lens),
        summary=summary,
    )


def order_policy_reviews(
    candidates: list[dict[str, Any]],
    selected_policy_ids: list[str],
    review_lens: ConfirmedReviewLens,
    ordered_alternative_ids: list[str] | None = None,
) -> list[PolicyReviewItem]:
    selected = set(selected_policy_ids[:3])
    candidate_rows = [item for item in candidates if str(item.get("policy_id")) in selected]
    priority = {mechanism: index for index, mechanism in enumerate(LENS_MECHANISM_ORDER[review_lens])}
    candidate_rows.sort(
        key=lambda item: (
            priority.get(POLICY_MECHANISMS.get(str(item.get("policy_id")), "other"), 99),
            candidates.index(item),
        )
    )
    ordered_alternative_ids = ordered_alternative_ids or []
    rank_by_policy: dict[str, int] = {}
    for position, alternative_id in enumerate(ordered_alternative_ids, start=1):
        for policy_id, alternative_ids in POLICY_ALTERNATIVE_IDS.items():
            if alternative_id in alternative_ids and policy_id not in rank_by_policy:
                rank_by_policy[policy_id] = position
    rows: list[PolicyReviewItem] = []
    for position, candidate in enumerate(candidate_rows, start=1):
        policy_id = str(candidate.get("policy_id"))
        mechanism = POLICY_MECHANISMS.get(policy_id, "other")
        mechanism_label = MECHANISM_LABELS.get(mechanism, MECHANISM_LABELS["other"])
        rows.append(
            PolicyReviewItem(
                policy_id=policy_id,
                policy_name=str(candidate.get("policy_name") or candidate.get("title") or policy_id),
                review_position=position,
                rank_position=rank_by_policy.get(policy_id),
                mechanism=mechanism,
                review_reason=(
                    f"{LENS_LABELS[review_lens]}을 먼저 보기 위해 {mechanism_label} 방식인 이 정책을 "
                    f"검토 {position}번에 배치했습니다. 자격, 금액, 계산 결과와 기존 순위는 바뀌지 않습니다."
                ),
            )
        )
    return rows


def notice_field_priority(review_lens: ConfirmedReviewLens) -> list[NoticeFieldPriority]:
    reasons = {
        "application_period": "현재 신청 가능 여부와 기간은 가장 먼저 공식 확인해야 합니다.",
        "financing_terms": f"{LENS_LABELS[review_lens]} 검토와 직접 연결되는 금융조건입니다.",
        "application_path": "신청을 이어갈 공식 경로를 확인합니다.",
        "required_documents": "조건을 확인한 뒤 필요한 서류를 준비합니다.",
        "contact": "공고에서 해결되지 않은 항목의 문의처입니다.",
        "publication_date": "저장 공고의 버전과 게시 시점을 확인합니다.",
    }
    keys = ["application_period", "financing_terms", "application_path", "required_documents", "contact", "publication_date"]
    return [NoticeFieldPriority(key=key, position=index, reason=reasons[key]) for index, key in enumerate(keys, start=1)]


def _stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _authority_invariants(request: OrchestrateRequest, result: dict[str, Any]) -> dict[str, str]:
    candidates = result.get("policy_discovery", {}).get("candidates", [])
    eligibility = [
        {
            "policy_id": item.get("policy_id"),
            "eligibility_status": item.get("eligibility_status"),
            "candidate_state": item.get("candidate_state"),
            "rule_results": item.get("rule_results"),
        }
        for item in candidates
    ]
    parts = {
        "candidate_policy_ids": sorted(str(item.get("policy_id")) for item in candidates),
        "eligibility": eligibility,
        "policy_scenarios": request.comparison.policy_scenarios,
        "intervention_results": result.get("intervention_results", []),
        "ranking": result.get("comparison_result", {}),
    }
    hashes = {key: _stable_hash(value) for key, value in parts.items()}
    hashes["combined"] = _stable_hash(hashes)
    return hashes


def _tool_trace(tool_name: str, policy_ids: list[str], displayed_reason: str, *, status: str = "success") -> ToolExecutionTrace:
    now = datetime.now(timezone.utc).isoformat()
    return ToolExecutionTrace(
        trace_id=f"tool-{uuid4().hex[:20]}",
        tool_name=tool_name,
        tool_version="v5-p0-1",
        input_schema_version="v5-orchestrate-v1",
        output_schema_version="v5-orchestrate-v1",
        started_at=now,
        finished_at=now,
        status=status,
        policy_ids=policy_ids,
        source_digests=[],
        displayed_reason=displayed_reason,
    )


def orchestrate_state(request: OrchestrateRequest) -> dict[str, Any]:
    policy_scenarios = list(request.comparison.policy_scenarios)
    scenario_ids = {item.policy_id for item in policy_scenarios}
    quick = request.comparison.quick_input
    voucher_id = "POL_SEMAS_STABILITY_VOUCHER_2026"
    voucher_requested = (
        voucher_id in request.comparison.selected_policy_ids
        and voucher_id in request.comparison.conditional_policy_ids
    )
    if quick is not None and voucher_requested and voucher_id not in scenario_ids:
        expense_date = quick.reference_date + timedelta(days=28)
        if quick.monthly_other_fixed_cost > 0 and expense_date <= date(2026, 12, 31):
            support = min(250_000, quick.monthly_other_fixed_cost)
            policy_scenarios.append(DynamicPolicyScenario(
                policy_id=voucher_id,
                approved_support_amount=support,
                expense_amount=quick.monthly_other_fixed_cost,
                expense_date=expense_date,
                expense_already_in_baseline=True,
            ))
    comparison = request.comparison.model_copy(
        update={
            "v2_mode": True,
            "policy_scenarios": policy_scenarios,
        }
    )
    # V4 makes no external AI call before the user explicitly requests an
    # action brief. The deterministic calculation engine is reused while policy
    # search stays on the local SQLite BM25 path inside this process.
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="X does not have valid feature names, but LGBMRegressor was fitted with feature names",
            category=UserWarning,
        )
        with patch.object(
            re_stage8,
            "_retrieval_runtime",
            return_value=("local-sqlite-bm25", "bm25"),
        ):
            result = compare_sample(comparison)
    discovery = result.get("policy_discovery", {})
    candidates = discovery.get("candidates", [])
    for candidate in candidates:
        if candidate.get("policy_id") != voucher_id:
            continue
        readiness = candidate.get("application_readiness") or {}
        if readiness.get("conditional_graph_status") != "structural_block":
            expense_date = quick.reference_date + timedelta(days=28) if quick else None
            can_calculate = bool(
                quick
                and quick.monthly_other_fixed_cost > 0
                and expense_date is not None
                and expense_date <= date(2026, 12, 31)
            )
            readiness["conditional_graph_supported"] = can_calculate
            readiness["conditional_graph_status"] = (
                "available" if can_calculate else "calculation_unavailable"
            )
            readiness["conditional_graph_reason"] = (
                "현재 입력한 월 기타 고정비 중 적격 비용 최대 25만원을 줄이는 조건부 비교입니다."
                if can_calculate
                else "월 기타 고정비가 0원이거나 바우처 소진기한 뒤라 현재 입력으로는 조건부 비용 절감액을 계산할 수 없습니다."
            )
        candidate["application_readiness"] = readiness
    for candidate in candidates:
        policy_id = str(candidate.get("policy_id", ""))
        candidate["preparation_questions"] = [
            QUESTIONS[field].public([policy_id])
            for field in POLICY_FIELDS.get(policy_id, ())
            if field in QUESTIONS
        ]
    questions = discovery.get("staged_questions", [])
    answered = set(request.answered_fields)
    asked = set(request.asked_fields)
    situation_signals = set(request.situation_context.signals) if request.situation_context else set()
    detected_signals = _detected_signals(request, result, questions, candidates)
    review_lens, suggested_lens = _effective_review_lens(request, detected_signals)
    next_questions: list[dict[str, Any]] = []
    next_question = None
    question_trace = None
    plan = _review_plan(request, detected_signals, review_lens, suggested_lens)
    review_order = (
        order_policy_reviews(
            candidates,
            list(request.comparison.selected_policy_ids),
            review_lens,
            result.get("comparison_result", {}).get("ordered_alternative_ids", []),
        )
        if review_lens is not None
        else []
    )
    metric_order = _metric_order(review_lens, suggested_lens)
    field_priority = notice_field_priority(review_lens or suggested_lens or "policy_choice")
    current_fields = {str(item.get("field")) for item in questions}
    skipped = sorted(asked.difference(current_fields).difference(answered))
    groups = _candidate_groups(candidates)
    status_counts = Counter(str(item.get("candidate_state", "확인 필요")) for item in candidates)
    selected_policy_ids = [item.policy_id for item in review_order]
    conditional_policy_fallbacks = result.get("conditional_policy_fallbacks", [])
    suppressed_conditional_policy_ids = [
        str(item.get("policy_id"))
        for item in conditional_policy_fallbacks
        if item.get("policy_id")
    ]
    authority_invariants = _authority_invariants(request, result)
    tool_traces = [
        _tool_trace("finance_diagnosis", selected_policy_ids, "기존 13주·6개월 계산을 그대로 사용했습니다."),
        _tool_trace("review_lens", selected_policy_ids, plan.summary),
        _tool_trace(
            "policy_preparation",
            selected_policy_ids,
            "사용자 답변은 선택한 정책의 준비 화면에서 정책별 선택지로 표시합니다.",
            status="success" if review_lens is not None else "fallback",
        ),
        _tool_trace("policy_discovery", selected_policy_ids, "기존 로컬 정책 검색과 공식 Rule 결과를 사용했습니다."),
        _tool_trace(
            "policy_simulator",
            selected_policy_ids,
            (
                "일부 정책 계산 오류는 해당 정책만 제외하고 무대응 기준선과 나머지 정책으로 비교했습니다."
                if suppressed_conditional_policy_ids
                else "기존 Event와 현금흐름 대안을 변경하지 않았습니다."
            ),
            status="fallback" if suppressed_conditional_policy_ids else "success",
        ),
    ]
    result["v3"] = {
        "version": "v5-api-v1.0",
        "next_question": next_question,
        "next_questions": next_questions,
        "question_state": {
            "answered_count": len(answered),
            "remaining_count": len([item for item in questions if item.get("field") not in answered]),
            "skipped_fields": skipped,
            "fixed_total_hidden": True,
            "round": 0,
            "max_rounds": 0,
            "batch_size": len(next_questions),
            "batch_limit": 0,
            "display_location": "selected_policy_preparation",
        },
        "policy_groups": groups,
        "status_counts": dict(status_counts),
        "recommended_review_policy_ids": selected_policy_ids or [item.get("policy_id") for item in candidates[:3]],
        "automatic_policy_selection": False,
        "suppressed_conditional_policy_ids": suppressed_conditional_policy_ids,
        "external_ai_used": False,
        "policy_retrieval": "local_sqlite_bm25",
        "situation_context": (
            request.situation_context.model_dump(mode="json")
            if request.situation_context
            else None
        ),
        "decision_trace": [
            "사용자 재무값으로 13주·6개월 현금흐름 계산",
            "상황 기반 정책 후보 재검색",
            "공식 Rule로 자격·확인 필요·제외 재평가",
            "선택한 정책의 준비 화면에서 필요한 답변을 선택지로 확인",
            "검토 렌즈는 질문·정책·지표 표시 순서만 변경",
            "확정값 대안만 순위 비교하고 조건부 효과는 분리",
        ],
        "action_plan": _action_plan(result, situation_signals),
        "session_persistence": "none",
    }
    result["detected_signals"] = [item.model_dump(mode="json") for item in detected_signals]
    result["review_plan"] = plan.model_dump(mode="json")
    result["next_question"] = next_question
    result["question_trace"] = question_trace.model_dump(mode="json") if question_trace else None
    result["review_order"] = [item.model_dump(mode="json") for item in review_order]
    result["focused_policy_id"] = review_order[0].policy_id if review_order else None
    result["metric_order"] = metric_order
    result["notice_field_priority"] = [item.model_dump(mode="json") for item in field_priority]
    result["authority_invariants"] = authority_invariants
    result["tool_execution_trace"] = [item.model_dump(mode="json") for item in tool_traces]
    return result


def _percent_from_prompt(prompt: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*%", prompt)
    return float(match.group(1)) if match else None


def _won_from_prompt(prompt: str, label: str) -> int | None:
    match = re.search(rf"{label}(?:를|을|이|가)?\s*(?:월\s*)?([\d,.]+)\s*만\s*원?.*?(?:줄|절감)", prompt)
    if not match:
        return None
    return round(float(match.group(1).replace(",", "")) * 10_000)


def _local_what_if_intent(prompt: str) -> WhatIfIntent | None:
    operations: list[WhatIfOperation] = []
    percent = _percent_from_prompt(prompt)
    if percent is not None and "매출" in prompt:
        if any(token in prompt for token in ("떨어", "줄", "감소", "하락")):
            operations.append(WhatIfOperation(kind="revenue_percent", direction="decrease", percent=percent))
        elif any(token in prompt for token in ("늘", "증가", "회복", "오르")):
            operations.append(WhatIfOperation(kind="revenue_percent", direction="increase", percent=percent))

    for label, value in {"하방": "downside", "기준": "central", "회복": "recovery"}.items():
        if label in prompt and ("시나리오" in prompt or "범위" in prompt):
            operations.append(WhatIfOperation(kind="market_scenario", value=value))
            break

    goal_map = {
        "빚": "최소부채", "부채": "최소부채", "오래": "최장생존",
        "생존": "최장생존", "상환": "최소상환", "빨리": "빠른실행", "빠른": "빠른실행",
    }
    for token, goal in goal_map.items():
        if token in prompt and any(word in prompt for word in ("우선", "기준", "만 보여", "중심")):
            operations.append(WhatIfOperation(kind="goal", value=goal))
            break

    for label, cost_key in {"임대료": "rent", "인건비": "labor", "매입비": "purchase", "고정비": "other_fixed"}.items():
        amount = _won_from_prompt(prompt, label)
        if amount is not None:
            operations.append(WhatIfOperation(kind="cost_reduction", cost_key=cost_key, amount_won=amount))
    if not operations:
        return None
    return WhatIfIntent(status="ready", summary="입력 문장에서 계산 가능한 가정을 찾았습니다.", operations=operations[:4])


def _validated_operations(intent: WhatIfIntent) -> list[WhatIfOperation]:
    if intent.status == "clarification_needed":
        if not intent.clarification_question or intent.operations:
            raise ValueError("Invalid clarification response")
        return []
    if not intent.operations:
        raise ValueError("No What-if operations")
    scenario_values = {"downside", "central", "recovery"}
    goal_values = {"최소부채", "최장생존", "최소상환", "빠른실행"}
    for operation in intent.operations:
        if operation.kind == "revenue_percent" and (operation.direction is None or operation.percent is None):
            raise ValueError("Invalid revenue operation")
        if operation.kind == "cost_reduction" and (operation.cost_key is None or operation.amount_won is None):
            raise ValueError("Invalid cost operation")
        if operation.kind == "market_scenario" and operation.value not in scenario_values:
            raise ValueError("Invalid scenario operation")
        if operation.kind == "goal" and operation.value not in goal_values:
            raise ValueError("Invalid goal operation")
    return intent.operations


def _what_if_intent(request: WhatIfRequest) -> tuple[WhatIfIntent | None, str, bool, str | None, str | None]:
    if request.consent_to_external_ai:
        luna = interpret_what_if_with_luna(request.prompt.strip())
        if luna.payload is not None:
            try:
                intent = WhatIfIntent.model_validate(luna.payload)
                _validated_operations(intent)
                return intent, "luna", True, luna.model, None
            except ValueError:
                pass
        fallback_reason = luna.fallback_reason or "invalid_luna_response"
    else:
        fallback_reason = "consent_not_given"
    return _local_what_if_intent(request.prompt.strip()), "local_rule", False, None, fallback_reason


def _unsupported_what_if(prompt: str) -> str | None:
    cost_labels = ("임대료", "월세", "인건비", "매입비", "고정비")
    increase_pattern = r"(?:상승|올랐|오르면|증가|늘었|늘어나)"
    for label in cost_labels:
        if re.search(rf"{label}(?:가|이|는|을|를)?[^?.\n]{{0,40}}{increase_pattern}", prompt):
            return (
                "현재 What-if는 비용 상승을 계산하지 않습니다. 비용은 절감액만 입력할 수 있으며, "
                "매출 증감률·상권 시나리오·비교 기준 변경을 함께 사용할 수 있습니다."
            )
    return None


def apply_what_if(request: WhatIfRequest) -> dict[str, Any]:
    examples = [
        "매출이 10% 더 떨어지면?",
        "매출이 10% 늘어나면?",
        "임대료를 월 100만원 줄이면?",
        "하방 시나리오로 바꾸면?",
        "추가부채 최소화 기준으로만 보여줘.",
    ]
    unsupported_reason = _unsupported_what_if(request.prompt.strip())
    if unsupported_reason:
        return {
            "applied": False,
            "committed": False,
            "unsupported": True,
            "requires_confirmation": False,
            "clarification_question": None,
            "message": unsupported_reason,
            "supported_examples": examples,
            "interpretation_source": "local_scope_guard",
            "external_ai_used": False,
            "external_ai_model": None,
        }
    intent, source, external_ai_used, model, fallback_reason = _what_if_intent(request)
    if intent and intent.status == "clarification_needed":
        return {
            "applied": False,
            "committed": False,
            "requires_confirmation": True,
            "clarification_question": intent.clarification_question,
            "message": intent.summary or "가정을 정확히 계산하려면 한 가지 확인이 필요합니다.",
            "interpretation_source": source,
            "external_ai_used": external_ai_used,
            "external_ai_model": model,
            "supported_examples": examples,
        }
    if intent is None:
        return {
            "applied": False,
            "committed": False,
            "requires_confirmation": True,
            "clarification_question": "어떤 값을 얼마만큼 바꿔 볼까요? 금액이나 비율을 함께 적어 주세요.",
            "message": "계산 가능한 변경값을 찾지 못했습니다.",
            "supported_examples": examples,
            "interpretation_source": source,
            "external_ai_used": False,
            "external_ai_model": None,
            "fallback_reason": fallback_reason,
        }

    operations = _validated_operations(intent)
    payload = request.comparison.model_dump(mode="json")
    quick = payload.get("quick_input")
    changes: list[str] = []
    change_details: list[dict[str, Any]] = []
    scenario_labels = {"downside": "하방 범위", "central": "기준 범위", "recovery": "회복 범위"}
    cost_fields = {
        "rent": ("임대료", "monthly_rent"),
        "labor": ("인건비", "monthly_labor_cost"),
        "purchase": ("매입비", "monthly_variable_cost"),
        "other_fixed": ("고정비", "monthly_other_fixed_cost"),
    }
    cost_plan = dict(payload.get("cost_reduction_plan") or {"rent": 0, "labor": 0, "purchase": 0, "other_fixed": 0})
    for operation in operations:
        if operation.kind == "revenue_percent" and quick:
            values = quick.get("recent_monthly_revenues") or []
            before_values = list(values) if values else [quick.get("monthly_revenue")]
            before_values = [int(value) for value in before_values if value is not None]
            if not before_values:
                continue
            factor = 1 - float(operation.percent) / 100 if operation.direction == "decrease" else 1 + float(operation.percent) / 100
            after_values = [max(0, round(value * factor)) for value in before_values]
            if values:
                quick["recent_monthly_revenues"] = after_values
            else:
                quick["monthly_revenue"] = after_values[0]
            direction_label = "감소" if operation.direction == "decrease" else "증가"
            changes.append(f"월매출 {operation.percent:g}% {direction_label} 가정")
            change_details.append({
                "label": "최근 월매출 평균",
                "before": round(sum(before_values) / len(before_values)),
                "after": round(sum(after_values) / len(after_values)),
                "display_type": "money",
            })
        elif operation.kind == "cost_reduction" and quick and operation.cost_key:
            label, input_key = cost_fields[operation.cost_key]
            before = int(cost_plan.get(operation.cost_key) or 0)
            available = int(quick.get(input_key) or 0)
            after = min(int(operation.amount_won or 0), available)
            cost_plan[operation.cost_key] = after
            changes.append(f"{label} 월 {after // 10_000:,}만원 절감 가정")
            change_details.append({"label": f"월 {label} 절감액", "before": before, "after": after, "display_type": "money"})
        elif operation.kind == "market_scenario" and operation.value:
            before = str(payload.get("market_scenario") or "central")
            payload["market_scenario"] = operation.value
            changes.append(f"상권 시나리오를 {scenario_labels[operation.value]}로 변경")
            change_details.append({"label": "상권 시나리오", "before": scenario_labels.get(before, before), "after": scenario_labels[operation.value], "display_type": "text"})
        elif operation.kind == "goal" and operation.value:
            before = str(payload.get("goal") or "최소부채")
            payload["goal"] = operation.value
            changes.append(f"비교 기준을 {operation.value}으로 변경")
            change_details.append({"label": "비교 기준", "before": before, "after": operation.value, "display_type": "text"})

    if any(cost_plan.values()):
        payload["cost_reduction_plan"] = cost_plan
    if not changes:
        return {
            "applied": False,
            "committed": False,
            "requires_confirmation": True,
            "clarification_question": "현재 입력에서 바꿀 수 있는 금액이나 비율을 다시 알려 주세요.",
            "message": "해석한 조건을 현재 입력에 적용할 수 없습니다.",
            "supported_examples": examples,
            "interpretation_source": source,
            "external_ai_used": external_ai_used,
            "external_ai_model": model,
        }

    updated = SampleCompareRequest.model_validate(payload)
    result = orchestrate_state(
        OrchestrateRequest(
            comparison=updated,
            answered_fields=request.answered_fields,
            asked_fields=request.asked_fields,
            situation_context=request.situation_context,
            question_round=request.question_round,
            review_lens=request.review_lens,
            review_lens_source=request.review_lens_source,
            confirmed_review_lens=request.confirmed_review_lens,
        )
    )
    return {
        "applied": True,
        "committed": False,
        "requires_confirmation": True,
        "interpretation_source": source,
        "interpretation_summary": intent.summary,
        "external_ai_used": external_ai_used,
        "external_ai_model": model,
        "fallback_reason": fallback_reason,
        "changes": changes,
        "change_details": change_details,
        "comparison": updated.model_dump(mode="json"),
        "result": result,
        "notice": "아직 현재 입력에는 적용하지 않은 임시 계산입니다. 실제 실행 전 금액과 날짜를 다시 확인해 주세요.",
    }
