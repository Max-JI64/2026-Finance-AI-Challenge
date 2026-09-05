"""RE8 application service layer.

The module joins frozen RE3-RE7 engines without allowing the LLM to calculate,
decide eligibility, or alter rankings.
"""

from __future__ import annotations

import csv
import json
import os
import re
import sqlite3
from datetime import date, timedelta
from functools import lru_cache
from io import StringIO
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from scripts.build_re_stage7_examples import as_detailed, build_hero
from src.cashflow import DetailedCashflowInput, LoanInput, SimpleCashflowInput
from src.cashflow.engine import run_detailed_cashflow, run_simple_cashflow
from src.cashflow.errors import CashflowInputError
from src.cashflow.loans import add_months, build_loan_schedule, first_monthly_date
from src.cashflow.quick_mode import QuickModeInput, build_quick_schedules
from src.models.re_stage5_scenario_service import predict_market_scenarios
from src.policy import (
    GrantScenario,
    LoanScenario,
    RefinanceScenario,
    convert_grant,
    convert_loan,
    convert_refinance,
)
from src.policy.eligibility import EligibilityEngine, SessionEligibilityProfile, TriState
from src.policy.discovery import QUESTIONS, DiscoveryEligibilityEngine, policy_metadata, staged_questions
from src.policy.re_stage8_2_events import DynamicPolicyScenario, build_dynamic_policy_plan
from src.rag.hybrid_search import DATABASE_PATH, HybridPolicySearchIndex
from src.rag.openai_embeddings import DEFAULT_EMBEDDING_MODEL, load_local_openai_env
from src.rag.policy_index import SearchResult
from src.rag.luna_client import explain_action_brief_with_luna, explain_with_luna
from src.recommendation import (
    AlternativeKind,
    AlternativeSpec,
    CandidateContext,
    CandidateState,
    MarketScenario,
    UserGoal,
    compare_alternatives,
    suggest_safe_cash,
)
from src.settings import PROJECT_ROOT


API_VERSION = "v2-api-v1.0"
SERVICE_NAME = "정책금융 영향 시뮬레이터"
POLICY_DATA_VERSION = "re8.2-markdown-2026-08-17"
BASE_AS_OF = date(2026, 8, 17)
SEMAS_REFERENCE_RATE_2026_Q3 = 3.85
SAMPLE_DIR = PROJECT_ROOT / "data/samples/re_stage7"
AREA_PATH = PROJECT_ROOT / "reports/stage6/area_catalog.csv"
INDUSTRY_PATH = PROJECT_ROOT / "reports/stage6/industry_catalog.csv"
AREA_MAP_PATH = PROJECT_ROOT / "data/processed_re/re_stage8/commercial_area_points.json"
SAMPLE_NAMES = {
    "declining_low_debt": "01_declining_low_debt_detailed.json",
    "stable_high_debt": "02_stable_high_debt_detailed.json",
    "declining_cash_shortage": "03_declining_cash_shortage_detailed.json",
}

CONDITIONAL_PREVIEW_POLICY_IDS = {
    "POL_SEOUL_FUND_2026",
    "POL_SEOUL_CRISIS_TRACK2_2026H2",
    "POL_SEMAS_REFINANCE_2026",
    "POL_SEMAS_RECHALLENGE_2026",
}

RULE_ANSWER_FIELDS: dict[str, tuple[str, ...]] = {
    "FUND_ALL_02": ("business_scale",),
    "FUND_EX_01": ("fund_restricted_industry",),
    "FUND_VARIANT": ("subfund_selected",),
    "CRISIS_ALL_02": ("rented_exclusive_place",),
    "CRISIS_ALL_03": ("opening_date",),
    "CRISIS_ANY_01": ("sales_decreased",),
    "CRISIS_ANY_02": ("disaster_document",),
    "CRISIS_EX_01": ("is_operating",),
    "CRISIS_EX_02": ("prior_crisis_support",),
    "CLOSE_ALL_02": ("is_operating",),
    "CLOSE_ALL_03": ("opening_date",),
    "CLOSE_EX_01": ("self_owned_place",),
    "CLOSE_EX_02": ("prior_closure_support",),
    "DIGI_ALL_03": ("opening_date",),
    "DIGI_EX_01": ("prior_digital_support",),
    "ZERO_ALL_02": ("zero_market_operation",),
    "ZERO_ALL_03": ("eligible_business_registration",),
    "ZERO_EX_01": ("is_operating",),
    "ZERO_EX_02": ("shared_office_only", "consignment_only"),
    "ZERO_EX_03": ("duplicate_public_support",),
    "SAFE_ALL_02": ("safety_product_business",),
    "SAFE_ALL_03": ("tax_paid",),
    "REFI_ALL_01": ("ncb_919_or_below",),
    "REFI_ANY_02": ("maturity_extension_difficulty",),
    "REFI_EX_01": ("common_loan_restriction",),
    "RECH_EX_01": ("common_loan_restriction",),
    "VOUCH_ALL_03": ("opening_date",),
    "VOUCH_ALL_04": ("is_operating",),
    "VOUCH_EX_01": ("policy_loan_restricted_industry",),
}

STRUCTURAL_ANSWER_FIELDS = {
    "business_scale",
    "fund_restricted_industry",
    "policy_loan_restricted_industry",
    "prior_crisis_support",
    "prior_closure_support",
    "prior_digital_support",
    "self_owned_place",
    "duplicate_public_support",
    "zero_market_operation",
    "eligible_business_registration",
    "safety_product_business",
}
VERSIONS = {
    "api": API_VERSION,
    "cashflow_engine": "re3-v1",
    "policy_event_engine": "re4-v1",
    "market_model": "re5-lightgbm-quantile-v1",
    "eligibility_engine": "re6-v1",
    "recommendation_engine": "re7-v1",
    "rag_engine": "re8.2-sqlite-hybrid-v1",
    "policy_data": "re8.2-markdown-2026-08-17",
    "embedding_models": ["text-embedding-3-small", "text-embedding-3-large"],
    "explanation_model": "gpt-5.6-luna",
}
HERO_POLICY_BY_ALTERNATIVE = {
    "track2_reimbursement": {
        "policy_id": "POL_SEOUL_CRISIS_TRACK2_2026H2",
        "policy_version": "2026-06-30",
    },
    "refinance": {
        "policy_id": "POL_SEMAS_REFINANCE_2026",
        "policy_version": "2026-07-29-change4",
    },
    "emergency_loan": {
        "policy_id": "POL_SEOUL_FUND_2026",
        "policy_version": "2026-05-04-change",
    },
    "combined_safe_cash": {
        "policy_id": "POL_SEOUL_CRISIS_TRACK2_2026H2 + POL_SEOUL_FUND_2026",
        "policy_version": "2026-06-30 + 2026-05-04-change",
    },
}

FINANCIAL_POLICY_NEEDS = {
    "POL_SEOUL_FUND_2026": "현금 확보",
    "POL_SEOUL_CRISIS_TRACK2_2026H2": "현금 확보",
    "POL_SEMAS_STABILITY_VOUCHER_2026": "현금 확보",
    "POL_SEMAS_REFINANCE_2026": "대출 부담 완화",
    "POL_SEMAS_RECHALLENGE_2026": "대출 부담 완화",
    "POL_SEMAS_EMPLOYMENT_INSURANCE_2026": "운영비 절감",
    "POL_SEOUL_FAMILY_FRIENDLY_EMPLOYER_2026": "운영비 절감",
    "POL_SEOUL_DIGITAL_MIDLIFE_2026H2": "운영비 절감",
    "POL_SEOUL_ZERO_MARKET_2026_2": "운영비 절감",
    "POL_SEOUL_CLOSURE_2026": "재기·전환",
    "POL_SEOUL_RESTART_2026": "재기·전환",
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CostReductionPlan(StrictModel):
    """Monthly reductions explicitly confirmed by the user, in won."""

    rent: int = Field(default=0, ge=0, le=10_000_000_000)
    labor: int = Field(default=0, ge=0, le=10_000_000_000)
    purchase: int = Field(default=0, ge=0, le=10_000_000_000)
    other_fixed: int = Field(default=0, ge=0, le=10_000_000_000)

    def total(self) -> int:
        return self.rent + self.labor + self.purchase + self.other_fixed


class SampleCompareRequest(StrictModel):
    area_code: str | None = Field(default=None, max_length=30)
    industry_code: str | None = Field(default=None, max_length=30)
    sample_id: str = "declining_cash_shortage"
    simple_input: SimpleCashflowInput | None = None
    quick_input: QuickModeInput | None = None
    existing_loan_rate_percent: float = Field(default=12, ge=0, le=100)
    existing_loan_term_months: int = Field(default=60, ge=1, le=360)
    direct_shock_13_week_percent: float = Field(default=-12, ge=-100, le=1000)
    direct_shock_6_month_percent: float = Field(default=-18, ge=-100, le=1000)
    safe_cash_override: int | None = Field(default=None, ge=0, le=10_000_000_000)
    goal: UserGoal = UserGoal.MINIMUM_DEBT
    market_scenario: Literal["downside", "central", "recovery"] = "central"
    assume_conditional: bool = True
    eligibility_profile: SessionEligibilityProfile | None = None
    policy_scenarios: list[DynamicPolicyScenario] = Field(default_factory=list, max_length=6)
    v2_mode: bool = False
    selected_policy_ids: list[str] = Field(default_factory=list, max_length=3)
    conditional_policy_ids: list[str] = Field(default_factory=list, max_length=3)
    cost_reduction_plan: CostReductionPlan | None = None


class EligibilityRequest(StrictModel):
    profile: SessionEligibilityProfile
    policy_ids: list[str] = Field(default_factory=list, max_length=17)
    district: str = Field(default="", max_length=20)
    as_of: date = BASE_AS_OF


class PolicyChatMessage(StrictModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1200)


class PolicyQuestionRequest(StrictModel):
    policy_id: str | None = Field(default=None, min_length=1, max_length=100)
    policy_version: str | None = Field(default=None, max_length=100)
    question: str = Field(min_length=2, max_length=500)
    history: list[PolicyChatMessage] = Field(default_factory=list, max_length=8)
    as_of: date = BASE_AS_OF


class ActionBriefRequest(StrictModel):
    comparison: SampleCompareRequest
    selected_alternative_id: str = Field(min_length=1, max_length=150)
    consent_to_external_ai: bool = False


class CsvCashflowRequest(StrictModel):
    reference_date: date
    opening_cash: int = Field(ge=0)
    safe_cash_threshold: int = Field(ge=0)
    events_csv: str = Field(max_length=1_500_000)
    loans_csv: str = Field(default="", max_length=500_000)


def envelope(**payload: Any) -> dict[str, Any]:
    return {
        "request_id": str(uuid4()),
        "as_of_date": BASE_AS_OF.isoformat(),
        "service_name": SERVICE_NAME,
        "versions": VERSIONS,
        **payload,
    }


def service_contract() -> dict[str, Any]:
    return envelope(
        does=[
            "13주와 6개월 기준 현금흐름 계산",
            "무대응과 정책금융 개입안의 현금 및 부채 비교",
            "공식 근거 기반 자격조건 확인과 실행계획 제공",
        ],
        does_not=[
            "개인 점포의 미래 매출 또는 폐업 예측",
            "정책 승인확률 또는 대출 승인 가능성 산출",
            "정책 수혜의 인과효과 보장",
            "AI가 계산하거나 최종 정책을 결정",
        ],
        privacy=(
            "입력은 현재 요청 처리에만 사용하며 서비스 DB·검색 인덱스에 저장하지 않습니다. "
            "승인된 범주형 상황과 민감정보 패턴을 제거한 정책질문만 OpenAI API에 전송되며, "
            "기본 악용 모니터링 로그에는 최대 30일 포함될 수 있습니다."
        ),
        differentiators=[
            "정책 목록을 보여주는 데서 끝나지 않고 지급일과 상환일을 같은 현금흐름 축에 반영합니다.",
            "신규 현금 유입과 함께 6개월 부채, 월상환, 총이자를 동시에 비교합니다.",
        ],
        sample_mode=True,
    )


def _catalog(path: Path, code_key: str, name_key: str) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return [
            {"code": row[code_key], "name": row[name_key]}
            for row in csv.DictReader(stream)
        ]


def area_catalog() -> list[dict[str, str]]:
    return _catalog(AREA_PATH, "상권_코드", "상권_코드_명")


def industry_catalog() -> list[dict[str, str]]:
    return _catalog(INDUSTRY_PATH, "서비스_업종_코드", "서비스_업종_코드_명")


def policy_catalog() -> list[dict[str, str]]:
    return HybridPolicySearchIndex(DATABASE_PATH).policy_catalog()


def _retrieval_runtime() -> tuple[str, str]:
    """Use the user-approved large Hybrid model with deterministic fallback."""

    load_local_openai_env()
    model = os.getenv("OPENAI_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL).strip()
    return (model or DEFAULT_EMBEDDING_MODEL, "hybrid")


SENSITIVE_EXTERNAL_PATTERNS = (
    re.compile(r"\b\d{3}-\d{2}-\d{5}\b"),
    re.compile(r"\b\d{2,4}-\d{3,4}-\d{4}\b"),
    re.compile(r"\b\d{2,6}-\d{2,6}-\d{2,8}\b"),
    re.compile(r"\b\d[\d,]*(?:\.\d+)?\s*(?:원|만원|억원)\b"),
    re.compile(r"\b\d{6}-?[1-4]\d{6}\b"),
    re.compile(r"(?:상호명|업체명|사업체명)\s*[:：]?\s*[^,.;\n]{1,40}"),
    re.compile(r"(?:서울특별시\s+)?[가-힣]{1,12}(?:구|군)\s+[가-힣0-9·\-]{1,20}(?:로|길)\s*\d+(?:-\d+)?(?:\s*\d+층)?"),
)


def _sanitize_external_text(value: str) -> str:
    """Remove approved high-risk patterns before any external model call."""

    sanitized = value
    for pattern in SENSITIVE_EXTERNAL_PATTERNS:
        sanitized = pattern.sub("[민감정보 제거]", sanitized)
    for item in area_map_catalog():
        area_name = str(item.get("name") or "").strip()
        if len(area_name) >= 2:
            sanitized = sanitized.replace(area_name, "[상권명 제거]")
    return re.sub(r"\s+", " ", sanitized).strip()[:500]


def _district_for_area(area_code: str | None) -> str:
    if not area_code:
        return ""
    return next(
        (str(item["district"]) for item in area_map_catalog() if item["code"] == area_code),
        "",
    )


def _resolved_eligibility_profile(
    request: SampleCompareRequest, *, district: str
) -> SessionEligibilityProfile:
    profile = request.eligibility_profile or SessionEligibilityProfile()
    updates: dict[str, Any] = {
        "region": "서울특별시" if district else profile.region,
        "industry_code": request.industry_code or profile.industry_code,
    }
    if request.quick_input is not None:
        updates["existing_interest_rate_percent"] = (
            request.quick_input.annual_interest_rate_percent
            if request.quick_input.total_loan_balance
            else None
        )
        revenues = request.quick_input.recent_monthly_revenues
        if revenues and revenues[-1] > 0:
            updates["sales_decreased"] = (
                TriState.YES if (revenues[0] - revenues[-1]) / revenues[-1] <= -0.1 else profile.sales_decreased
            )
    return profile.model_copy(update=updates)


def _situation_summary(
    request: SampleCompareRequest,
    *,
    minimum_cash: int,
    depletion_date: date | None,
    district: str,
) -> tuple[str, list[str]]:
    """Create a de-identified categorical summary for semantic retrieval."""

    labels: list[str] = [f"서울 {district} 소재" if district else "서울 소재"]
    labels.append(
        next(
            (item["name"] for item in industry_catalog() if item["code"] == request.industry_code),
            "업종 확인 필요",
        )
    )
    quick = request.quick_input
    if quick is not None:
        revenues = quick.recent_monthly_revenues
        if revenues and revenues[-1] > 0:
            # UI order is newest month first and oldest month last.
            change = (revenues[0] - revenues[-1]) / revenues[-1]
            labels.append(
                "최근 매출 감소"
                if change <= -0.1
                else "최근 매출 증가"
                if change >= 0.1
                else "최근 매출 보합"
            )
        else:
            labels.append("매출 추세 추가 확인")
        monthly_revenue = max(1, quick.resolved_monthly_revenue())
        fixed_ratio = (quick.monthly_rent + quick.monthly_labor_cost) / monthly_revenue
        labels.append("고정비 부담 높음" if fixed_ratio >= 0.45 else "고정비 부담 보통")
        if quick.total_loan_balance:
            labels.append(
                "고금리 기존 대출 대환 필요"
                if quick.annual_interest_rate_percent >= 7
                else "기존 대출 상환 부담"
            )
        else:
            labels.append("기존 대출 없음")
    if depletion_date is not None or minimum_cash < 0:
        labels.append("13주 내 현금 부족 위험")
    elif quick is not None and minimum_cash < quick.safe_cash_threshold:
        labels.append("안전현금 부족")
    else:
        labels.append("단기 현금 유지")
    return ". ".join(labels), labels


def _policy_match_reason(need_group: str, labels: list[str]) -> str:
    """Explain retrieval with store signals without implying eligibility."""

    priorities = {
        "현금 확보": ("13주 내 현금 부족 위험", "안전현금 부족", "최근 매출 감소", "고정비 부담 높음"),
        "대출 부담 완화": ("고금리 기존 대출 대환 필요", "기존 대출 상환 부담", "13주 내 현금 부족 위험", "최근 매출 감소"),
        "운영비 절감": ("고정비 부담 높음", "최근 매출 감소", "13주 내 현금 부족 위험", "안전현금 부족"),
        "재기·전환": ("최근 매출 감소", "13주 내 현금 부족 위험", "안전현금 부족", "고정비 부담 높음"),
    }
    matched = [label for label in priorities.get(need_group, ()) if label in labels][:2]
    if not matched:
        matched = labels[:2]
    context = "·".join(matched) if matched else "현재 점포 조건"
    return f"{context} 상황에서 {need_group}와 관련된 정책 경로로 찾았습니다. 지원 대상 확정은 아닙니다."


def _readiness_answer(value: Any) -> str:
    text = str(value or "").strip()
    return {
        "yes": "예",
        "no": "아니오",
        "unknown": "모름",
        "pass": "충족",
        "fail": "불충족",
    }.get(text.lower(), text or "입력 없음")


def _profile_answer(profile: SessionEligibilityProfile | None, field: str) -> Any:
    if profile is None or not field:
        return None
    if field in profile.policy_answers:
        value = profile.policy_answers[field]
    else:
        value = getattr(profile, field, None)
    if hasattr(value, "value"):
        value = value.value
    if isinstance(value, date):
        return value.isoformat()
    return value


def _answer_label(field: str, value: Any) -> str:
    question = QUESTIONS.get(field)
    normalized = "unknown" if value in (None, "") else str(value)
    if question is not None:
        option = next((label for candidate, label in question.options if candidate == normalized), None)
        if option:
            return option
    return _readiness_answer(normalized)


def _readiness_answers(
    item: dict[str, Any], profile: SessionEligibilityProfile | None
) -> list[dict[str, Any]]:
    fields = tuple(
        field for field in (
            item.get("field"),
            *RULE_ANSWER_FIELDS.get(item.get("rule_id", ""), ()),
        ) if field
    )
    answers = []
    for field in dict.fromkeys(fields):
        question = QUESTIONS.get(field)
        if question is None:
            continue
        answers.append({
            "field": field,
            "question": question.label,
            "answer": _answer_label(field, _profile_answer(profile, field)),
            "editable": True,
        })
    return answers


def _failure_resolution(condition: str) -> tuple[str, str]:
    """Turn a failed official condition into a concrete, non-promissory next step."""

    if any(keyword in condition for keyword in ("매출", "재해", "피해")):
        return (
            "증빙 준비",
            "매출 비교자료나 재해·피해 확인서가 실제로 있는지 확인하고, 있다면 해당 답변을 수정해 증빙을 준비하세요. 실제로 해당하지 않으면 이 정책은 현재 신청할 수 없습니다.",
        )
    if any(keyword in condition for keyword in ("재창업", "채무조정", "교육", "수료", "업력")):
        return (
            "재도전 요건 확인",
            "재창업·채무조정 유형과 교육 수료내역·기간을 공식 증빙으로 확인하세요. 아직 충족하지 않았다면 공고가 인정하는 교육이나 준비 절차부터 진행해야 합니다.",
        )
    if any(keyword in condition for keyword in ("제한사유", "제한 업종", "중복", "기존 지원", "과거 지원")):
        return (
            "제한사유 해소·예외 확인",
            "현재 제한사유가 실제로 적용되는지 공식기관에 확인하세요. 제한이 사실이면 해소 또는 공고상 예외 인정 전에는 신청할 수 없으므로 다른 정책도 함께 비교하세요.",
        )
    if any(keyword in condition for keyword in ("신용", "NCB", "만기연장", "고금리")):
        return (
            "대출 조건 증빙",
            "신용평점 확인서와 기존 대출내역, 만기연장 애로 증빙을 준비해 공고 기준에 해당하는지 확인하세요. 기준과 다르면 이 대환 경로는 이용할 수 없습니다.",
        )
    if any(keyword in condition for keyword in ("기업 규모", "소상공인", "소기업", "상시근로자")):
        return (
            "기업 규모 재확인",
            "소상공인확인서와 상시근로자 수를 기준으로 기업 규모를 다시 확인하세요. 입력이 맞고 공고 기준을 벗어나면 이 정책은 신청할 수 없습니다.",
        )
    if any(keyword in condition for keyword in ("소재지", "사업장", "임차", "영업", "개업")):
        return (
            "사업장 자격 재확인",
            "사업자등록증·임대차계약서·영업 상태로 공식 조건을 다시 확인하세요. 입력이 맞고 조건을 충족하지 않으면 이 정책 대신 가능한 다른 정책을 선택해야 합니다.",
        )
    return (
        "공식 조건 재확인",
        "공식 증빙을 기준으로 현재 답변이 맞는지 확인하세요. 입력이 잘못됐다면 답변을 수정하고, 실제로 조건을 충족하지 않으면 다른 정책을 비교하세요.",
    )


def _application_readiness(
    policy_id: str,
    decision: dict[str, Any],
    profile: SessionEligibilityProfile | None = None,
) -> dict[str, Any]:
    """Separate fixed eligibility failures from preparation and official checks."""

    rule_results = decision.get("rule_results", [])
    failed = [item for item in rule_results if item.get("result") == "fail"]
    unknown = [item for item in rule_results if item.get("result") == "unknown"]
    blocking_details = []
    for item in failed:
        condition = item.get("condition", "")
        category, action = _failure_resolution(condition)
        answers = _readiness_answers(item, profile)
        is_structural = any(answer["field"] in STRUCTURAL_ANSWER_FIELDS for answer in answers)
        if not answers and "소재지" in condition:
            is_structural = True
        blocking_details.append({
            "condition": condition or "공식 자격조건",
            "current_answer": answers[0]["answer"] if len(answers) == 1 else _readiness_answer(item.get("reason")),
            "answers": answers,
            "category": category,
            "action": action,
            "remediation_type": "structural" if is_structural else "remediable",
        })
    confirmation_details = []
    for item in unknown:
        answers = _readiness_answers(item, profile)
        if answers:
            confirmation_details.append({
                "condition": item.get("condition") or "공식 확인 항목",
                "answers": answers,
            })
    preparation: list[str] = []
    if policy_id == "POL_SEOUL_FUND_2026" and any(
        item.get("rule_id") == "FUND_VARIANT" for item in unknown
    ):
        preparation.extend([
            "13주 추가 필요 현금과 자금 용도에 맞는 세부 자금 선택",
            "선택한 세부 자금의 한도·금리·추가 자격 확인",
        ])
    official_checks = [
        item.get("reason") or item.get("condition", "")
        for item in unknown
        if not _readiness_answers(item, profile)
    ]
    if "확인 필요" in decision.get("availability_status", ""):
        official_checks.append("기준일 현재 접수 가능 여부와 잔여 예산 확인")
    official_checks = list(dict.fromkeys(item for item in official_checks if item))

    if failed:
        status = "현재 조건으로 지원 불가"
        next_actions = [
            *(item["action"] for item in blocking_details),
            "해결할 수 없는 조건이면 현재 조건으로 가능한 다른 정책 후보를 비교하세요.",
        ]
    elif preparation:
        status = "준비하면 신청 가능"
        next_actions = [*preparation, *official_checks]
    elif unknown or official_checks:
        status = "공식 확인 필요"
        next_actions = official_checks
    else:
        status = "입력 기준 지원 후보"
        next_actions = ["공식 공고에서 현재 접수 여부와 제출서류 확인"]
    has_structural_failure = any(
        item["remediation_type"] == "structural" for item in blocking_details
    )
    base_preview_supported = policy_id in CONDITIONAL_PREVIEW_POLICY_IDS
    if has_structural_failure:
        graph_status = "structural_block"
        graph_reason = "현재 답변에 업종·기업규모·소재지·중복수혜 등 구조적 제외조건이 있어 조건부 그래프에서 제외합니다."
    elif base_preview_supported:
        graph_status = "available"
        graph_reason = "보완 가능한 조건 또는 공식 확인 항목을 충족하고 승인·실행된 경우를 가정해 비교합니다."
    else:
        graph_status = "calculation_unavailable"
        graph_reason = "검수된 금액·지급일·상환기간 가정이 없어 임의 조건부 그래프를 만들지 않습니다."
    return {
        "status": status,
        "hard_failures": [item.get("condition", "") for item in failed if item.get("condition")],
        "blocking_details": blocking_details,
        "confirmation_details": confirmation_details,
        "preparation_items": preparation,
        "official_checks": official_checks,
        "next_actions": list(dict.fromkeys(next_actions)),
        "conditional_graph_supported": base_preview_supported and not has_structural_failure,
        "conditional_graph_status": graph_status,
        "conditional_graph_reason": graph_reason,
    }


def _discover_policies(
    request: SampleCompareRequest,
    *,
    minimum_cash: int,
    depletion_date: date | None,
    district: str,
    profile: SessionEligibilityProfile,
) -> dict[str, Any]:
    summary, labels = _situation_summary(
        request,
        minimum_cash=minimum_cash,
        depletion_date=depletion_date,
        district=district,
    )
    search = HybridPolicySearchIndex(DATABASE_PATH)
    embedding_model, retrieval_mode = _retrieval_runtime()
    outcome = search.search(
        summary,
        policy_ids=set(FINANCIAL_POLICY_NEEDS),
        as_of=BASE_AS_OF,
        district=district or None,
        top_k=6,
        model=embedding_model,
        mode=retrieval_mode,
        max_chunks_per_policy=1,
    )
    catalog = {item["policy_id"]: item for item in search.policy_catalog()}
    eligibility_engine = DiscoveryEligibilityEngine()
    metadata = policy_metadata()
    candidates = []
    for item in outcome.results:
        policy = catalog[item.chunk.policy_id]
        need_group = FINANCIAL_POLICY_NEEDS[item.chunk.policy_id]
        decision = eligibility_engine.evaluate(
            item.chunk.policy_id, profile, district=district, as_of=BASE_AS_OF
        )
        event_status = metadata[item.chunk.policy_id]["event_status"]
        readiness = _application_readiness(item.chunk.policy_id, decision, profile)
        candidates.append(
            {
                "policy_id": item.chunk.policy_id,
                "policy_name": policy["policy_name"],
                "policy_version": policy["policy_version"],
                "need_group": need_group,
                "matched_section": item.chunk.page_or_section,
                "match_explanation": item.chunk.text[:240],
                "match_reason": _policy_match_reason(need_group, labels),
                "official_url": policy["official_url"],
                **decision,
                "eligibility_readiness": f"{decision['eligibility_status']} · {decision['availability_status']}",
                "application_readiness": readiness,
                "simulation_readiness": {
                    "reviewed_event": "검수 Event와 사용자 시나리오가 있으면 현금 비교 가능",
                    "reviewed_event_requires_grade": "고용보험 등급 확인 후 현금 비교 가능",
                    "reviewed_event_requires_amount_date": "실제 신청금액·지급일 확인 후 현금 비교 가능",
                    "reviewed_event_closed": "접수 종료로 신규 실행 대안 제외",
                    "outside_six_month_cash_horizon": "지원효과가 기본 6개월 현금축 밖에 있음",
                    "restricted_savings_not_business_cash": "공제계정 적립으로 사업체 가용현금과 분리",
                    "personal_living_cash_not_business_cash": "개인 생활비로 사업체 현금과 분리",
                    "service_subsidy_not_business_cash": "개인 돌봄서비스 지원으로 사업체 현금과 분리",
                    "blocked_event_terms": "금융조건 미확인으로 현금 계산 차단",
                }.get(event_status, "금융조건 확인 후 비교 가능"),
            }
        )
    candidate_ids = [item["policy_id"] for item in candidates]
    return {
        "situation_labels": labels,
        "retrieval_mode": outcome.retrieval_mode,
        "embedding_model": outcome.embedding_model,
        "fallback_reason": outcome.fallback_reason,
        "candidates": candidates,
        "staged_questions": staged_questions(candidate_ids, profile),
        "privacy": (
            "자치구·업종과 범주형 상황만 Embedding API에 전송합니다. 원금액·상호·상권명·상세주소·식별번호는 전송하지 않으며, "
            "로컬에는 저장하지 않습니다. OpenAI 기본 악용 모니터링 로그에는 최대 30일 포함될 수 있습니다."
        ),
    }


def _dynamic_policy_alternatives(
    request: SampleCompareRequest,
    discovery: dict[str, Any],
    *,
    reference_date: date,
) -> list[AlternativeSpec]:
    """Create alternatives only from searched candidates and explicit event inputs."""

    candidates = {item["policy_id"]: item for item in discovery["candidates"]}
    catalog = {item["policy_id"]: item for item in policy_catalog()}
    alternatives: list[AlternativeSpec] = []
    selected_policy_ids = set(request.selected_policy_ids)
    for scenario in request.policy_scenarios:
        if request.v2_mode and scenario.policy_id not in selected_policy_ids:
            continue
        candidate = candidates.get(scenario.policy_id)
        if candidate is None or candidate["candidate_state"] == "제외":
            continue
        if (
            request.v2_mode
            and candidate.get("application_readiness", {}).get("conditional_graph_status")
            == "structural_block"
        ):
            continue
        plan = build_dynamic_policy_plan(scenario, reference_date=reference_date)
        policy = catalog[scenario.policy_id]
        context = CandidateContext(
            policy_id=scenario.policy_id,
            policy_version=policy["policy_version"],
            eligibility_status=candidate["eligibility_status"],
            availability_status=candidate["availability_status"],
            candidate_state=CandidateState(candidate["candidate_state"]),
            reason_summary=candidate["reason_summary"],
            items_to_confirm=candidate["items_to_confirm"],
            as_of=BASE_AS_OF,
            official_notice_url=policy["official_url"],
            application_url=policy["official_url"],
        )
        alternatives.append(
            AlternativeSpec(
                alternative_id=f"dynamic_{scenario.policy_id.lower()}",
                label=f"{policy['policy_name']} · 입력 조건",
                kind=AlternativeKind.NON_DEBT_SUPPORT,
                plans=[plan],
                candidate_contexts=[context],
                explicit_condition_assumption=request.assume_conditional,
                application_deadline=(
                    date.fromisoformat(policy["application_end"])
                    if policy.get("application_end")
                    else None
                ),
                estimated_days_to_effect=(
                    max(0, (scenario.payment_date - reference_date).days)
                    if scenario.payment_date
                    else 60
                ),
                required_documents=["공고상 자격 증빙", "사용자 입력 금융조건 증빙"],
                inquiry="공식 공고 문의처 확인",
                official_urls=[policy["official_url"]],
                assumptions=["사용자가 입력한 금액·일정만 사용", "미입력 금융조건은 계산하지 않음"],
            )
        )
    return alternatives


def _v2_cost_reduction_alternative(
    request: SampleCompareRequest,
) -> AlternativeSpec | None:
    """Build a cost alternative only from user-confirmed category amounts."""

    plan = request.cost_reduction_plan
    if plan is None or plan.total() == 0:
        return None
    if request.quick_input is None:
        raise ValueError("V2 비용 절감 비교에는 간편 재무 입력이 필요합니다.")
    monthly_cost = (
        request.quick_input.monthly_rent
        + request.quick_input.monthly_labor_cost
        + request.quick_input.monthly_variable_cost
        + request.quick_input.monthly_other_fixed_cost
    )
    if monthly_cost <= 0 or plan.total() > monthly_cost:
        raise ValueError("줄일 비용은 입력한 월 지출 합계를 넘을 수 없습니다.")
    rate = plan.total() / monthly_cost * 100
    details = [
        f"임대료 {plan.rent:,}원",
        f"인건비 {plan.labor:,}원",
        f"필수매입비 {plan.purchase:,}원",
        f"기타 고정비 {plan.other_fixed:,}원",
    ]
    return AlternativeSpec(
        alternative_id="cost_reduction_custom",
        label=f"확정 비용 월 {plan.total():,}원 절감",
        kind=AlternativeKind.COST_REDUCTION,
        cost_reduction_rate_percent=rate,
        assumptions=[
            "사용자가 실제로 줄일 수 있다고 확정한 월 비용만 반영",
            ", ".join(details),
        ],
    )


def _conditional_candidate_context(candidate: dict[str, Any]) -> CandidateContext:
    return CandidateContext(
        policy_id=candidate["policy_id"],
        policy_version=candidate["policy_version"],
        eligibility_status=candidate["eligibility_status"],
        availability_status=candidate["availability_status"],
        candidate_state=CandidateState.CONDITIONAL,
        reason_summary="조건부 그래프이며 최종 자격·접수·승인·실행을 확정하지 않습니다.",
        items_to_confirm=list(dict.fromkeys([
            *candidate.get("items_to_confirm", []),
            *candidate.get("application_readiness", {}).get("next_actions", []),
        ])),
        as_of=BASE_AS_OF,
        official_notice_url=candidate["official_url"],
        application_url=candidate["official_url"],
    )


def _build_v2_conditional_policy_alternatives_unchecked(
    request: SampleCompareRequest,
    discovery: dict[str, Any],
    baseline: DetailedCashflowInput,
    market: MarketScenario,
) -> list[AlternativeSpec]:
    """Build explicitly requested, clearly conditional graphs outside rankings."""

    requested = set(request.conditional_policy_ids)
    selected = set(request.selected_policy_ids)
    if not requested.issubset(selected):
        raise ValueError("조건부 그래프는 먼저 선택한 정책에 대해서만 만들 수 있습니다.")
    if not requested:
        return []
    candidates = {item["policy_id"]: item for item in discovery["candidates"]}
    baseline_only = compare_alternatives(
        baseline,
        market,
        [],
        as_of=BASE_AS_OF,
        safe_cash_override=request.safe_cash_override,
    )
    no_action = baseline_only.alternatives[0]
    assert no_action.metrics is not None
    safe_cash = suggest_safe_cash(baseline, user_override=request.safe_cash_override)
    assert safe_cash.suggested_amount is not None
    cash_need = max(0, safe_cash.suggested_amount - no_action.metrics.week13_minimum_cash)
    alternatives: list[AlternativeSpec] = []

    for policy_id in request.conditional_policy_ids:
        candidate = candidates.get(policy_id)
        if candidate is None:
            continue
        if not candidate.get("application_readiness", {}).get("conditional_graph_supported", False):
            continue
        context = _conditional_candidate_context(candidate)
        if policy_id == "POL_SEOUL_FUND_2026" and cash_need > 0:
            principal = min(cash_need, 50_000_000)
            execution_date = baseline.reference_date + timedelta(days=28)
            plan = convert_loan(LoanScenario(
                policy_id=policy_id,
                event_id="SEOUL_EMERGENCY",
                scenario_status="assumed_approved",
                approved_principal=principal,
                execution_date=execution_date,
                payment_day=5,
                term_months=60,
                grace_months=12,
                repayment_method="equal_principal",
            ))
            alternatives.append(AlternativeSpec(
                alternative_id="conditional_pol_seoul_fund_2026",
                label="서울시 긴급자영업자금 · 조건부 그래프",
                kind=AlternativeKind.POLICY_LOAN,
                plans=[plan],
                candidate_contexts=[context],
                explicit_condition_assumption=True,
                estimated_days_to_effect=28,
                required_documents=["세부 자금 적격 확인", "자금 용도 증빙", "대출·보증 상담서류"],
                inquiry="서울신용보증재단 1577-6119",
                official_urls=[candidate["official_url"]],
                assumptions=[
                    f"13주 추가 필요 현금 기준 원금 {principal:,}원(공식 한도 5천만원 이내)",
                    "사용자가 조건부 그래프 보기를 선택해 4주 후 실행을 가정",
                    "60개월·12개월 거치·원금균등 조건부 비교",
                ],
            ))
        elif policy_id == "POL_SEOUL_CRISIS_TRACK2_2026H2":
            support = min(max(cash_need, 1), 3_000_000)
            project_cost = (support * 125 + 99) // 100
            expense_date = baseline.reference_date + timedelta(days=7)
            payment_date = max(date(2026, 11, 30), expense_date)
            plan = convert_grant(GrantScenario(
                policy_id=policy_id,
                event_id="CRISIS_SOLUTION",
                scenario_status="assumed_approved",
                approved_support_amount=support,
                payment_date=payment_date,
                total_project_cost=project_cost,
                eligible_expense_amount=support,
                expense_date=expense_date,
            ))
            alternatives.append(AlternativeSpec(
                alternative_id="conditional_pol_seoul_crisis_track2_2026h2",
                label="위기 소상공인 지원 · 조건부 그래프",
                kind=AlternativeKind.NON_DEBT_SUPPORT,
                plans=[plan],
                candidate_contexts=[context],
                explicit_condition_assumption=True,
                estimated_days_to_effect=max(0, (payment_date - baseline.reference_date).days),
                required_documents=["매출감소 또는 재해 증빙", "임대차계약서", "선지출 증빙"],
                inquiry="서울신용보증재단 1577-6119",
                official_urls=[candidate["official_url"]],
                assumptions=[
                    f"13주 추가 필요 현금과 공고상 최대 300만원 중 작은 지원액 {support:,}원",
                    f"지원액의 125%인 선지출 {project_cost:,}원",
                    f"선지출 {expense_date.isoformat()}·공고상 비용지원 종료시점 {payment_date.isoformat()} 지급 가정",
                ],
            ))
        elif policy_id == "POL_SEMAS_RECHALLENGE_2026" and cash_need > 0:
            principal = min(cash_need, 70_000_000)
            execution_date = baseline.reference_date + timedelta(days=28)
            plan = convert_loan(LoanScenario(
                policy_id=policy_id,
                event_id="SEMAS_RECHALLENGE_GENERAL",
                scenario_status="assumed_approved",
                approved_principal=principal,
                execution_date=execution_date,
                payment_day=5,
                term_months=60,
                grace_months=24,
                repayment_method="equal_principal",
                reference_interest_rate_percent=SEMAS_REFERENCE_RATE_2026_Q3,
            ))
            alternatives.append(AlternativeSpec(
                alternative_id="conditional_pol_semas_rechallenge_2026",
                label="소상공인 재도전특별자금 일반형 · 조건부 그래프",
                kind=AlternativeKind.POLICY_LOAN,
                plans=[plan],
                candidate_contexts=[context],
                explicit_condition_assumption=True,
                estimated_days_to_effect=28,
                required_documents=["재창업·채무조정 유형 증빙", "재창업교육 수료내역", "공통 대출 제한사유 확인"],
                inquiry="소상공인통합콜센터 1533-0100 내선 1",
                official_urls=[candidate["official_url"]],
                assumptions=[
                    f"13주 추가 필요 현금과 일반형 공식 한도 7천만원 중 작은 원금 {principal:,}원",
                    "사용자가 선택한 정책의 조건을 충족하고 승인·실행된 경우를 4주 후 실행으로 가정",
                    "2026년 3분기 정책자금 기준금리 3.85% + 일반형 가산금리 1.6%p = 연 5.45%",
                    "60개월·24개월 거치·원금균등 조건부 비교",
                ],
            ))
        elif policy_id == "POL_SEMAS_REFINANCE_2026" and baseline.loans:
            existing = baseline.loans[0]
            execution_date = baseline.reference_date + timedelta(days=28)
            remaining = existing.principal
            for payment in build_loan_schedule(existing, baseline.reference_date):
                if payment.payment_date >= execution_date:
                    break
                remaining = payment.closing_principal
            if remaining <= 0:
                continue
            principal = min(remaining, 50_000_000)
            refinanced_segment = existing.model_copy(update={"principal": principal})
            payment_day = 5
            first_payment = first_monthly_date(execution_date, payment_day)
            maturity = add_months(first_payment, 119)
            replacement = LoanInput(
                loan_id="v2-conditional-refinance",
                principal=principal,
                annual_interest_rate_percent=4.5,
                repayment_method="equal_principal",
                payment_day=payment_day,
                maturity_date=maturity,
            )
            plan = convert_refinance(RefinanceScenario(
                policy_id=policy_id,
                event_id="SEMAS_REFINANCE",
                scenario_status="assumed_approved",
                execution_date=execution_date,
                existing_refinanced_loan=refinanced_segment,
                replacement_loan=replacement,
            ))
            alternatives.append(AlternativeSpec(
                alternative_id="conditional_pol_semas_refinance_2026",
                label="소상공인 대환대출 · 조건부 그래프",
                kind=AlternativeKind.REFINANCE,
                plans=[plan],
                candidate_contexts=[context],
                explicit_condition_assumption=True,
                estimated_days_to_effect=28,
                required_documents=["기존 대출내역", "NCB 구간 확인", "만기연장 애로 증빙"],
                inquiry="소상공인통합콜센터 1533-0100 내선 1",
                official_urls=[candidate["official_url"]],
                assumptions=[
                    f"기존 대출과 공식 한도 5천만원 중 작은 대환원금 {principal:,}원",
                    "사용자가 조건부 그래프 보기를 선택해 4주 후 실행을 가정",
                    "연 4.5%·120개월 원금균등 조건부 비교",
                ],
            ))
    return alternatives


def _v2_conditional_policy_alternatives(
    request: SampleCompareRequest,
    discovery: dict[str, Any],
    baseline: DetailedCashflowInput,
    market: MarketScenario,
    *,
    fallback_events: list[dict[str, str]] | None = None,
) -> list[AlternativeSpec]:
    """Build each conditional policy independently and fail open to comparison.

    A policy-specific official-term or schedule mismatch must not prevent the
    baseline diagnosis and the other valid policies from reaching the user.
    Invalid user input is validated before this boundary and is not swallowed.
    """

    alternatives: list[AlternativeSpec] = []
    for policy_id in request.conditional_policy_ids:
        policy_request = request.model_copy(
            update={"conditional_policy_ids": [policy_id]}
        )
        try:
            alternatives.extend(
                _build_v2_conditional_policy_alternatives_unchecked(
                    policy_request,
                    discovery,
                    baseline,
                    market,
                )
            )
        except CashflowInputError as exc:
            if fallback_events is not None:
                fallback_events.append(
                    {
                        "policy_id": policy_id,
                        "error_code": exc.code,
                        "field": exc.field,
                        "fallback": "baseline_and_remaining_policies",
                    }
                )
    return alternatives


def _build_v2_decision(
    request: SampleCompareRequest,
    baseline: DetailedCashflowInput,
    market: MarketScenario,
    dynamic_alternatives: list[AlternativeSpec],
    conditional_alternatives: list[AlternativeSpec],
):
    """Compare no-action and only explicitly confirmed V2 alternatives."""

    alternatives: list[AlternativeSpec] = []
    cost_alternative = _v2_cost_reduction_alternative(request)
    if cost_alternative is not None:
        alternatives.append(cost_alternative)
    alternatives.extend(dynamic_alternatives)
    alternatives.extend(conditional_alternatives)
    return compare_alternatives(
        baseline,
        market,
        alternatives,
        as_of=BASE_AS_OF,
        safe_cash_override=request.safe_cash_override,
    )


def _market_scenario_comparison(
    baseline: DetailedCashflowInput,
    prediction: dict[str, Any] | None,
    *,
    selected_scenario: str,
    selected_result: Any,
    safe_cash_override: int | None,
) -> list[dict[str, Any]]:
    """Return no-action cash paths for all available aggregate market ranges."""

    if not prediction or not prediction.get("available"):
        return []
    rows: list[dict[str, Any]] = []
    for scenario_name in ("downside", "central", "recovery"):
        scenario = prediction["scenarios"][scenario_name]
        if scenario_name == selected_scenario:
            scenario_result = selected_result
        else:
            scenario_result = compare_alternatives(
                baseline,
                MarketScenario(
                    target_a_percent=scenario["thirteen_week_percent"],
                    target_b_percent=scenario["six_month_percent"],
                    model_version=prediction["model_version"],
                ),
                [],
                as_of=BASE_AS_OF,
                safe_cash_override=safe_cash_override,
            )
        no_action = next(
            item
            for item in scenario_result.alternatives
            if item.alternative_id == "no_action" and item.metrics
        )
        rows.append(
            {
                "scenario": scenario_name,
                "thirteen_week_percent": scenario["thirteen_week_percent"],
                "six_month_percent": scenario["six_month_percent"],
                "week13_ending_cash": no_action.metrics.week13_ending_cash,
                "month6_ending_cash": no_action.metrics.month6_ending_cash,
                "safe_cash_suggested_amount": scenario_result.safe_cash.suggested_amount,
                "weekly_13": list(no_action.weekly_13),
            }
        )
    return rows


@lru_cache(maxsize=1)
def area_map_catalog() -> list[dict[str, Any]]:
    if not AREA_MAP_PATH.is_file():
        raise FileNotFoundError(AREA_MAP_PATH)
    payload = json.loads(AREA_MAP_PATH.read_text(encoding="utf-8"))
    return list(payload["items"])


def market_scenario(area_code: str, industry_code: str) -> dict[str, Any]:
    return envelope(market_scenario=predict_market_scenarios(area_code, industry_code))


def calculate_simple_baseline(data: SimpleCashflowInput) -> dict[str, Any]:
    result = run_simple_cashflow(data)
    return envelope(
        input_precision="월 금액과 지정 지급일을 반복한 일정 기반 계산",
        uncertainty=(
            "실제 입출금일이 다르면 고갈 시점도 달라집니다. 정확한 주차 데모에는 상세 일정을 사용하세요."
        ),
        baseline_cashflow=result.to_dict(),
        assumptions=[
            {
                "field": "simple_input_schedule",
                "source": "사용자 입력",
                "reason": "월 금액과 입력한 날짜를 13주 및 6개월 일정으로 반복",
            }
        ],
        limitations=["개별 점포 미래매출 예측이 아님", "정책 지급 또는 승인 미반영"],
    )


def _load_sample(sample_id: str) -> DetailedCashflowInput:
    if sample_id not in SAMPLE_NAMES:
        raise ValueError("지원하지 않는 샘플입니다.")
    path = SAMPLE_DIR / SAMPLE_NAMES[sample_id]
    return DetailedCashflowInput.model_validate(json.loads(path.read_text(encoding="utf-8")))


def compare_sample(request: SampleCompareRequest) -> dict[str, Any]:
    valid_areas = {item["code"] for item in area_catalog()}
    valid_industries = {item["code"] for item in industry_catalog()}
    if request.area_code is not None and request.area_code not in valid_areas:
        raise ValueError("지원하지 않는 서울 상권입니다.")
    if request.industry_code is not None and request.industry_code not in valid_industries:
        raise ValueError("지원하지 않는 업종입니다.")
    if request.quick_input is not None and request.simple_input is not None:
        raise ValueError("simple_input과 quick_input은 동시에 사용할 수 없습니다.")
    quick_schedules = build_quick_schedules(request.quick_input) if request.quick_input else None
    baseline = (
        quick_schedules["central"]
        if quick_schedules is not None
        else as_detailed(
            request.simple_input,
            loan_rate=request.existing_loan_rate_percent,
            loan_term_months=request.existing_loan_term_months,
            source_label="re8_quick_input_schedule",
        )
        if request.simple_input is not None
        else _load_sample(request.sample_id)
    )
    prediction: dict[str, Any] | None = None
    if request.area_code and request.industry_code:
        try:
            prediction = predict_market_scenarios(request.area_code, request.industry_code)
        except (FileNotFoundError, KeyError, TypeError, ValueError):
            prediction = None
    if prediction and prediction.get("available"):
        selected = prediction["scenarios"][request.market_scenario]
        market = MarketScenario(
            target_a_percent=selected["thirteen_week_percent"],
            target_b_percent=selected["six_month_percent"],
            model_version=prediction["model_version"],
        )
        scenario_source = "선택한 상권·업종의 집계 LightGBM 시나리오"
    else:
        market = MarketScenario(
            direct_shock_13_week_percent=request.direct_shock_13_week_percent,
            direct_shock_6_month_percent=request.direct_shock_6_month_percent,
            model_version=None,
        )
        selected = {
            "thirteen_week_percent": request.direct_shock_13_week_percent,
            "six_month_percent": request.direct_shock_6_month_percent,
        }
        scenario_source = "모델자료 없음 시 직접 입력 Fallback"
    baseline_result = run_detailed_cashflow(baseline)
    district = _district_for_area(request.area_code)
    eligibility_profile = _resolved_eligibility_profile(request, district=district)
    discovery = _discover_policies(
        request,
        minimum_cash=baseline_result.weekly_summary.minimum_cash,
        depletion_date=baseline_result.weekly_summary.first_cash_depletion_date,
        district=district,
        profile=eligibility_profile,
    )
    dynamic_alternatives = _dynamic_policy_alternatives(
        request, discovery, reference_date=baseline.reference_date
    )
    conditional_policy_fallbacks: list[dict[str, str]] = []
    conditional_alternatives = _v2_conditional_policy_alternatives(
        request,
        discovery,
        baseline,
        market,
        fallback_events=conditional_policy_fallbacks,
    ) if request.v2_mode else []
    fallback_policy_ids = {
        item["policy_id"] for item in conditional_policy_fallbacks
    }
    for candidate in discovery["candidates"]:
        if candidate.get("policy_id") not in fallback_policy_ids:
            continue
        readiness = candidate.get("application_readiness") or {}
        readiness.update(
            {
                "conditional_graph_supported": False,
                "conditional_graph_status": "calculation_unavailable",
                "conditional_graph_reason": (
                    "이번 입력에서는 이 정책의 조건부 그래프를 제외하고 "
                    "무대응 기준선과 나머지 정책 결과를 계산했습니다."
                ),
            }
        )
        candidate["application_readiness"] = readiness
    if request.v2_mode:
        result = _build_v2_decision(
            request,
            baseline,
            market,
            dynamic_alternatives,
            conditional_alternatives,
        )
        minimum_principal = 0
    else:
        result, minimum_principal = build_hero(
            baseline,
            market=market,
            safe_cash_override=request.safe_cash_override,
            assume_conditional=request.assume_conditional,
            additional_alternatives=dynamic_alternatives,
        )
    ranking = next(item for item in result.rankings if item.goal is request.goal)
    return envelope(
        sample={
            "sample_id": None if request.simple_input is not None or request.quick_input is not None else request.sample_id,
            "is_synthetic": request.simple_input is None and request.quick_input is None,
            "notice": (
                "월 금액과 시기범주를 보수적·기준·완화의 날짜별 일정으로 변환했습니다."
                if request.quick_input is not None
                else
                "사용자 간편 입력을 지정 날짜의 6개월 일정으로 변환했습니다."
                if request.simple_input is not None
                else "실제 사업장이 아닌 검증용 가상 사업장입니다."
            ),
            "input_precision": (
                "월 금액과 시기범주의 보수적-기준-완화 일정 범위"
                if request.quick_input is not None
                else
                "월 금액과 일정범주를 날짜로 변환한 일정 보완 입력"
                if request.simple_input is not None
                else "상세 지급일정 기반"
            ),
        },
        quick_mode_range=(
            {
                scenario: run_detailed_cashflow(schedule).to_dict()
                for scenario, schedule in quick_schedules.items()
            }
            if quick_schedules is not None
            else None
        ),
        baseline_cashflow=baseline_result.to_dict(),
        baseline_input=baseline.model_dump(mode="json"),
        external_scenario={
            "source": scenario_source,
            "selected_scenario": request.market_scenario,
            "thirteen_week_percent": selected["thirteen_week_percent"],
            "six_month_percent": selected["six_month_percent"],
            "model_available": bool(prediction and prediction.get("available")),
            "reference_period": prediction.get("reference_period") if prediction else None,
            "limitation": "선택한 상권·업종 전체의 전년 같은 기간 대비 참고 변화율이며 내 가게 예상매출이 아닙니다.",
        },
        market_scenario_comparison=_market_scenario_comparison(
            baseline,
            prediction,
            selected_scenario=request.market_scenario,
            selected_result=result,
            safe_cash_override=request.safe_cash_override,
        ),
        eligibility_results=discovery["candidates"],
        intervention_results=[item.model_dump(mode="json") for item in result.alternatives],
        comparison_result={
            "selected_goal": request.goal,
            "goal_meaning": ranking.meaning,
            "ordered_alternative_ids": ranking.ordered_alternative_ids,
            "top_alternative_id": ranking.top_alternative_id,
            "goal_rankings": {
                item.goal.value: {
                    "goal_meaning": item.meaning,
                    "ordered_alternative_ids": item.ordered_alternative_ids,
                    "top_alternative_id": item.top_alternative_id,
                    "fallback_used": item.fallback_used,
                }
                for item in result.rankings
            },
            "pareto_frontier_ids": result.pareto_frontier_ids,
        },
        execution_plan=[item.model_dump(mode="json") for item in result.execution_plans],
        safe_cash=result.safe_cash.model_dump(mode="json"),
        policy_discovery=discovery,
        dynamic_policy_alternative_ids=[item.alternative_id for item in dynamic_alternatives],
        conditional_policy_alternative_ids=[
            item.alternative_id for item in conditional_alternatives
        ],
        conditional_policy_fallbacks=conditional_policy_fallbacks,
        v2={
            "enabled": request.v2_mode,
            "selected_policy_ids": request.selected_policy_ids,
            "conditional_policy_ids": request.conditional_policy_ids,
            "confirmed_cost_reduction": (
                request.cost_reduction_plan.model_dump(mode="json")
                if request.cost_reduction_plan is not None
                else None
            ),
            "comparison_rule": "확정값 대안만 순위 비교하고, 사용자가 연 조건부 그래프는 점선으로 표시하되 순위에서 제외",
        },
        minimum_policy_loan_for_sample=minimum_principal,
        assumption_ledger=[
            item
            for alternative in result.alternatives
            for item in alternative.assumption_ledger
        ],
        official_evidence=[
            url
            for alternative in result.alternatives
            for url in alternative.official_urls
        ],
        limitations=[
            "자격판정은 승인 가능성이 아님",
            "정책 지급일과 승인금액은 명시적 가정",
            "조건부 정책은 기본 순위와 빠른실행 1순위에서 제외",
            "가상 사업장 기능 검증이며 실제 사용자 검증이 아님",
        ],
    )


def eligibility_results(request: EligibilityRequest) -> dict[str, Any]:
    engine = DiscoveryEligibilityEngine()
    all_policy_ids = set(policy_metadata())
    policy_ids = request.policy_ids or sorted(all_policy_ids)
    unknown = sorted(set(policy_ids).difference(all_policy_ids))
    if unknown:
        raise ValueError(f"지원하지 않는 정책 ID: {', '.join(unknown)}")
    results = [
        engine.evaluate(
            policy_id,
            request.profile,
            district=request.district,
            as_of=request.as_of,
        )
        for policy_id in policy_ids
    ]
    return envelope(
        eligibility_results=results,
        limitations=["입력값과 공개 자격조건의 일치 여부이며 승인 가능성을 뜻하지 않습니다."],
    )


def ask_policy(request: PolicyQuestionRequest) -> dict[str, Any]:
    if sum(item.role == "user" for item in request.history) > 4:
        raise ValueError("정책 상담은 현재 페이지에서 최대 5회까지 가능합니다.")

    sanitized_question = _sanitize_external_text(request.question)
    sanitized_history = [
        {"role": item.role, "content": _sanitize_external_text(item.content)}
        for item in request.history
    ]
    retrieval_query = _expand_policy_chat_query(sanitized_question)
    retrieval_mode = "unavailable"
    try:
        search = HybridPolicySearchIndex(DATABASE_PATH)
        embedding_model, requested_mode = _retrieval_runtime()
        search_all_policies = request.policy_id is None
        outcome = search.search(
            retrieval_query,
            policy_id=request.policy_id,
            policy_ids=set(FINANCIAL_POLICY_NEEDS) if search_all_policies else None,
            policy_version=request.policy_version,
            as_of=request.as_of,
            top_k=6 if search_all_policies else 4,
            model=embedding_model,
            mode=requested_mode,
            max_chunks_per_policy=1 if search_all_policies else 4,
        )
        retrieval_mode = outcome.retrieval_mode
        evidence = [
            SearchResult(chunk=item.chunk, score=max(0.0, item.combined_score))
            for item in outcome.results
        ]
        explanation = explain_with_luna(
            sanitized_question,
            evidence,
            history=sanitized_history,
        )
        catalog = {item["policy_id"]: item for item in search.policy_catalog()}
        public_evidence = [
            {
                "policy_id": item.chunk.policy_id,
                "policy_version": item.chunk.policy_version,
                "source_url": item.chunk.source_url,
                "page_or_section": item.chunk.page_or_section,
                "excerpt": item.chunk.text[:300],
            }
            for item in evidence
        ]
        discovered_policies = []
        seen_policy_ids: set[str] = set()
        for item in evidence:
            policy_id = item.chunk.policy_id
            if policy_id in seen_policy_ids:
                continue
            seen_policy_ids.add(policy_id)
            policy = catalog[policy_id]
            discovered_policies.append(
                {
                    "policy_id": policy_id,
                    "policy_name": policy["policy_name"],
                    "policy_version": policy["policy_version"],
                    "official_url": policy["official_url"],
                    "matched_section": item.chunk.page_or_section,
                }
            )
    except (FileNotFoundError, sqlite3.Error, ValueError) as exc:
        explanation = type(
            "Fallback",
            (),
            {
                "answer": "근거 검색을 사용할 수 없습니다. 구조화 계산결과와 공식 링크를 확인해 주세요.",
                "source": "local_fallback",
                "model": None,
                "fact_lock_status": "not_called",
                "fallback_reason": type(exc).__name__,
            },
        )()
        public_evidence = []
        discovered_policies = []
    answer = _policy_chat_answer_with_guidance(
        explanation.answer,
        sanitized_question,
        [item.chunk.policy_id for item in evidence] if "evidence" in locals() else [],
    )
    return envelope(
        answer=answer,
        answer_source=explanation.source,
        explanation_model=explanation.model,
        fact_lock_status=explanation.fact_lock_status,
        fallback_reason=explanation.fallback_reason,
        official_evidence=public_evidence,
        discovered_policies=discovered_policies,
        limitations=[
            "AI는 계산, 자격판정, 순위를 생성하거나 변경하지 않음",
            f"공식근거 검색 방식: {retrieval_mode}",
            "금액·전화번호·계좌·사업자번호·주민번호 패턴은 외부 전송 전에 제거",
            "OpenAI 기본 악용 모니터링 로그에는 최대 30일 포함될 수 있음",
            "공식 공고와 신청기관에서 최신 상태를 최종 확인해야 함",
        ],
    )


def action_brief(request: ActionBriefRequest) -> dict[str, Any]:
    """Recompute facts locally, then optionally ask Luna to rewrite them."""

    comparison = compare_sample(request.comparison)
    alternatives = [item for item in comparison["intervention_results"] if item.get("metrics")]
    selected = next(
        (
            item
            for item in alternatives
            if item["alternative_id"] == request.selected_alternative_id
        ),
        None,
    )
    if selected is None:
        raise ValueError("선택한 대안이 현재 비교 결과에 없습니다.")
    metrics = selected["metrics"]
    selected_ids = set(request.comparison.selected_policy_ids)
    selected_candidates = [
        item
        for item in comparison["policy_discovery"]["candidates"]
        if item["policy_id"] in selected_ids
    ]
    plan = next(
        (
            item
            for item in comparison["execution_plan"]
            if item["alternative_id"] == selected["alternative_id"]
        ),
        {},
    )
    checks = list(
        dict.fromkeys(
            [
                *selected.get("items_to_confirm", []),
                *plan.get("conditions_to_check_now", []),
            ]
        )
    )
    policy_status = ", ".join(
        f"{item['policy_name']} {item['eligibility_readiness']}"
        for item in selected_candidates
    ) or "선택 정책 없음"
    next_action = (
        f"다음 행동: {checks[0]}을 공식 공고 또는 담당기관에서 확인하세요."
        if checks
        else "다음 행동: 입력한 절감액 또는 정책 조건을 실행 가능한지 확인하고 공식 공고를 여세요."
    )
    facts = [
        f"현재 선택 대안은 {selected['label']}입니다.",
        f"13주 뒤 현금은 {metrics['week13_ending_cash']:,}원이고 6개월 뒤 현금은 {metrics['month6_ending_cash']:,}원입니다.",
        f"새로 생기는 빚은 {metrics['net_new_borrowing']:,}원이고 월 최대 상환액은 {metrics['maximum_monthly_debt_service']:,}원입니다.",
        f"선택 정책 상태: {policy_status}.",
        next_action,
    ]
    evidence: list[SearchResult] = []
    retrieval_mode = "not_requested"
    if request.consent_to_external_ai:
        try:
            search = HybridPolicySearchIndex(DATABASE_PATH)
            embedding_model, requested_mode = _retrieval_runtime()
            outcome = search.search(
                "선택 정책 신청 조건 서류 지급 시점 확인",
                policy_ids=selected_ids or None,
                as_of=BASE_AS_OF,
                top_k=4,
                model=embedding_model,
                mode=requested_mode,
                max_chunks_per_policy=2,
            )
            retrieval_mode = outcome.retrieval_mode
            evidence = [
                SearchResult(chunk=item.chunk, score=max(0.0, item.combined_score))
                for item in outcome.results
            ]
        except (FileNotFoundError, sqlite3.Error, ValueError):
            retrieval_mode = "unavailable"
    explanation = (
        explain_action_brief_with_luna(facts, evidence)
        if request.consent_to_external_ai
        else type(
            "LocalBrief",
            (),
            {
                "answer": "\n".join(facts),
                "source": "local_deterministic",
                "model": None,
                "fact_lock_status": "not_called",
                "fallback_reason": "consent_not_given",
            },
        )()
    )
    return envelope(
        action_brief=explanation.answer,
        answer_source=explanation.source,
        explanation_model=explanation.model,
        fact_lock_status=explanation.fact_lock_status,
        fallback_reason=explanation.fallback_reason,
        deterministic_facts=facts,
        official_evidence=[
            {
                "policy_id": item.chunk.policy_id,
                "policy_version": item.chunk.policy_version,
                "source_url": item.chunk.source_url,
                "page_or_section": item.chunk.page_or_section,
            }
            for item in evidence
        ],
        limitations=[
            "계산·자격·순위는 서버가 다시 계산하며 LLM이 변경하지 않음",
            f"공식근거 검색 방식: {retrieval_mode}",
            "외부 AI 동의가 없거나 호출이 실패하면 로컬 결정론적 브리프를 사용",
        ],
    )


ELIGIBILITY_QUESTION_TERMS = (
    "지원받을 수", "지원 받을 수", "지원 가능", "받을 수 있", "신청할 수", "신청 가능", "대상인가", "대상인지", "자격",
)


def _policy_chat_answer_with_guidance(
    answer: str, question: str, policy_ids: list[str]
) -> str:
    """Add actionable, policy-specific checks to eligibility questions."""

    if not any(term in question.replace("?", "") for term in ELIGIBILITY_QUESTION_TERMS):
        return answer
    unique_policy_ids = list(dict.fromkeys(policy_ids))
    questions = staged_questions(unique_policy_ids, SessionEligibilityProfile())
    labels = [item["label"] for item in questions[:4]]
    if not labels:
        labels = ["사업장 소재지", "업종과 기업 규모", "최근 연매출", "현재 영업 여부"]
    checks = "\n".join(f"- {label}" for label in labels)
    guidance = (
        f"확인을 위해 알려주세요:\n{checks}\n"
        "이 정보를 알려주시면 공식 조건과 대조해 확인된 조건과 남은 조건을 나눠 안내할 수 있습니다. "
        "최종 자격과 현재 접수 가능 여부는 공고와 담당기관에서 확인해야 합니다."
    )
    base = answer.rstrip()[: max(0, 1198 - len(guidance))]
    return f"{base}\n\n{guidance}" if base else guidance


POLICY_CHAT_QUERY_EXPANSIONS = (
    (
        ("대출", "이자", "상환", "빚"),
        "대환대출 정책자금 융자 금리 상환부담 채무조정 소상공인",
    ),
    (
        ("현금", "자금", "매출", "유동성"),
        "운영자금 긴급자금 현금부족 매출감소 경영안정 소상공인",
    ),
    (
        ("운영비", "고정비", "비용", "보험료"),
        "운영비 고정비 비용절감 고용보험료 지원 환급 소상공인",
    ),
    (
        ("아프", "질병", "부상", "입원", "병원", "건강검진", "치료"),
        "입원 입원 입원 생활비 생활비 생활비 질병 질병 부상 입원연계 외래진료 건강검진 소득공백",
    ),
    (
        ("육아", "양육", "아이", "자녀", "돌봄"),
        "아이돌봄 아이돌봄 아이돌봄 민간아이돌봄서비스 육아 육아 양육 자녀 출산",
    ),
    (
        ("산재", "산업재해", "다쳤", "사고"),
        "산재보험료 산업재해 보험료 지원 소상공인",
    ),
    (
        ("폐업", "가게를 접", "정리하고", "장사를 그만"),
        "폐업지원 사업정리 원상복구 재기 재창업 소상공인",
    ),
    (
        ("보험료", "사회보험", "고용보험"),
        "고용보험료 지원 자영업자 보험료 환급 사회안전망",
    ),
)


def _expand_policy_chat_query(question: str) -> str:
    """Add deterministic Korean situation terms only for local retrieval."""

    additions = [
        terms
        for triggers, terms in POLICY_CHAT_QUERY_EXPANSIONS
        if any(trigger in question for trigger in triggers)
    ]
    return " ".join([question, *additions])


def parse_combined_csv(request: CsvCashflowRequest) -> DetailedCashflowInput:
    """Parse two UTF-8 CSV strings without persisting uploaded contents."""

    def normalized_rows(text: str) -> list[dict[str, str]]:
        rows = list(csv.DictReader(StringIO(text.lstrip("\ufeff"))))
        return [
            {(key or "").lstrip("\ufeff"): value for key, value in row.items()}
            for row in rows
        ]

    event_rows = normalized_rows(request.events_csv)
    loan_rows = normalized_rows(request.loans_csv) if request.loans_csv.strip() else []
    event_type_aliases = {
        "매출입금": "operating_inflow",
        "외상매출입금": "accounts_receivable",
        "고정비": "fixed_cost",
        "변동비": "variable_cost",
        "세금공과금": "tax_utility",
        "외상매입금": "accounts_payable",
        "일회성지출": "one_time_expense",
    }
    expense_type_aliases = {
        "임대료": "rent",
        "인건비": "labor",
        "필수매입": "purchase",
        "세금": "tax",
        "공과금": "utility",
        "사회보험": "social_insurance",
        "차량유류": "vehicle_fuel",
        "장비": "equipment",
        "수리": "repair",
        "기타": "other",
    }
    repayment_aliases = {
        "원금균등": "equal_principal",
        "원리금균등": "equal_payment",
        "만기일시": "bullet",
    }

    def value(row: dict[str, str], english: str, korean: str, default: str = "") -> str:
        return (row.get(english) or row.get(korean) or default).strip()

    def amount_value(
        row: dict[str, str], english: str, korean_won: str, korean_ten_thousand: str
    ) -> int:
        ten_thousand = (row.get(korean_ten_thousand) or "").strip()
        if ten_thousand:
            return round(float(ten_thousand.replace(",", "")) * 10_000)
        return int(value(row, english, korean_won, "0").replace(",", ""))

    payload = {
        "reference_date": request.reference_date,
        "opening_cash": request.opening_cash,
        "safe_cash_threshold": request.safe_cash_threshold,
        "events": [
            {
                "event_id": value(row, "event_id", "거래번호"),
                "event_date": value(row, "event_date", "거래일"),
                "event_type": event_type_aliases.get(
                    value(row, "event_type", "구분"), value(row, "event_type", "구분")
                ),
                "amount": amount_value(row, "amount", "금액", "금액(만원)"),
                "expense_type": expense_type_aliases.get(
                    value(row, "expense_type", "비용종류"),
                    value(row, "expense_type", "비용종류") or None,
                ),
                "description": value(row, "description", "메모"),
                "source": "csv_upload",
            }
            for row in event_rows
        ],
        "loans": [
            {
                "loan_id": value(row, "loan_id", "대출명"),
                "principal": amount_value(row, "principal", "잔액", "잔액(만원)"),
                "annual_interest_rate_percent": float(
                    value(row, "annual_interest_rate_percent", "연이율", "0")
                ),
                "repayment_method": repayment_aliases.get(
                    value(row, "repayment_method", "상환방식"),
                    value(row, "repayment_method", "상환방식"),
                ),
                "payment_day": int(value(row, "payment_day", "상환일", "0")),
                "maturity_date": value(row, "maturity_date", "만기일"),
                "grace_months": int(value(row, "grace_months", "거치개월", "0") or 0),
            }
            for row in loan_rows
        ],
    }
    return DetailedCashflowInput.model_validate(payload)


def calculate_csv_baseline(request: CsvCashflowRequest) -> dict[str, Any]:
    result = run_detailed_cashflow(parse_combined_csv(request))
    return envelope(
        input_precision="상세 CSV 지급일정 기반",
        baseline_cashflow=result.to_dict(),
        assumptions=[],
        limitations=["CSV 입력값의 정확성은 사용자가 확인해야 함"],
    )
