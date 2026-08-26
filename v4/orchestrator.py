"""Bounded V4 orchestration over the reviewed V2 finance engines."""

from __future__ import annotations

import re
import warnings
from collections import Counter
from datetime import date, timedelta
from typing import Any, Literal
from unittest.mock import patch

from pydantic import BaseModel, ConfigDict, Field

import src.integration.re_stage8 as re_stage8
from src.integration.re_stage8 import (
    SampleCompareRequest,
    area_map_catalog,
    compare_sample,
    industry_catalog,
)
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


class OrchestrateRequest(StrictModel):
    comparison: SampleCompareRequest
    answered_fields: list[str] = Field(default_factory=list, max_length=80)
    asked_fields: list[str] = Field(default_factory=list, max_length=80)
    situation_context: SituationContext | None = None
    question_round: int = Field(default=0, ge=0, le=2)


class WhatIfRequest(StrictModel):
    comparison: SampleCompareRequest
    prompt: str = Field(min_length=2, max_length=800)
    answered_fields: list[str] = Field(default_factory=list, max_length=80)
    asked_fields: list[str] = Field(default_factory=list, max_length=80)
    situation_context: SituationContext | None = None
    consent_to_external_ai: bool = False
    question_round: int = Field(default=2, ge=0, le=2)


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


def _next_question(
    questions: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    answered_fields: set[str],
    situation_signals: set[str] | None = None,
) -> dict[str, Any] | None:
    active_ids = {
        item.get("policy_id")
        for item in candidates
        if item.get("candidate_state") != "제외" and item.get("eligibility_status") != "부적격"
    }
    type_weight = {"tri_state": 4, "select": 3, "date": 2, "number": 1}
    remaining = [item for item in questions if item.get("field") not in answered_fields]
    if not remaining:
        return None

    situation_signals = situation_signals or set()

    def score(question: dict[str, Any]) -> tuple[int, int, int, str]:
        covered = len(active_ids.intersection(question.get("policy_ids") or []))
        question_text = " ".join(
            str(question.get(key, "")) for key in ("field", "label", "reason")
        )
        situation_relevance = sum(
            1
            for signal in situation_signals
            if any(term in question_text for term in QUESTION_TERMS_BY_SIGNAL.get(signal, ()))
        )
        return (
            covered,
            situation_relevance,
            type_weight.get(str(question.get("input_type")), 0),
            str(question.get("field")),
        )

    selected = max(remaining, key=score)
    selected = dict(selected)
    covered, relevance, _, _ = score(selected)
    if covered and relevance:
        selected["selection_reason"] = (
            f"문장에서 확인한 걱정과 관련되며, 현재 남은 정책 경로 {covered}개를 구분하는 질문입니다."
        )
    elif covered:
        selected["selection_reason"] = (
            f"현재 남은 정책 경로 {covered}개를 구분하고 계산 가능 여부를 바꾸는 질문입니다."
        )
    else:
        selected["selection_reason"] = "현재 결과에서 아직 확인되지 않은 핵심 조건입니다."
    return selected


def _question_batch(
    questions: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    answered_fields: set[str],
    situation_signals: set[str] | None,
    limit: int,
) -> list[dict[str, Any]]:
    """Choose a bounded adaptive batch while preserving one-question scoring."""

    selected: list[dict[str, Any]] = []
    excluded = set(answered_fields)
    for _ in range(limit):
        question = _next_question(questions, candidates, excluded, situation_signals)
        if not question:
            break
        selected.append(question)
        excluded.add(str(question.get("field")))
    return selected


def _action_plan(
    result: dict[str, Any],
    next_question: dict[str, Any] | None,
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
    if next_question:
        today.append(f"{next_question['label']} 항목을 확인합니다.")
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
    questions = discovery.get("staged_questions", [])
    answered = set(request.answered_fields)
    asked = set(request.asked_fields)
    situation_signals = set(request.situation_context.signals) if request.situation_context else set()
    batch_limit = 4 if request.question_round == 0 else 3 if request.question_round == 1 else 0
    next_questions = _question_batch(questions, candidates, answered, situation_signals, batch_limit)
    next_question = next_questions[0] if next_questions else None
    current_fields = {str(item.get("field")) for item in questions}
    skipped = sorted(asked.difference(current_fields).difference(answered))
    groups = _candidate_groups(candidates)
    status_counts = Counter(str(item.get("candidate_state", "확인 필요")) for item in candidates)
    result["v3"] = {
        "version": "v4-api-v1.0",
        "next_question": next_question,
        "next_questions": next_questions,
        "question_state": {
            "answered_count": len(answered),
            "remaining_count": len([item for item in questions if item.get("field") not in answered]),
            "skipped_fields": skipped,
            "fixed_total_hidden": True,
            "round": request.question_round,
            "max_rounds": 2,
            "batch_size": len(next_questions),
            "batch_limit": batch_limit,
        },
        "policy_groups": groups,
        "status_counts": dict(status_counts),
        "recommended_review_policy_ids": [item.get("policy_id") for item in candidates[:3]],
        "automatic_policy_selection": False,
        "suppressed_conditional_policy_ids": [],
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
            "현재 후보를 가장 많이 구분하는 질문 묶음을 선택하고 화면에서는 하나씩 제시",
            "확정값 대안만 순위 비교하고 조건부 효과는 분리",
        ],
        "action_plan": _action_plan(result, next_question, situation_signals),
        "session_persistence": "none",
    }
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
