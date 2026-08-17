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
from datetime import date
from functools import lru_cache
from io import StringIO
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from scripts.build_re_stage7_examples import as_detailed, build_hero
from src.cashflow import DetailedCashflowInput, SimpleCashflowInput
from src.cashflow.engine import run_detailed_cashflow, run_simple_cashflow
from src.cashflow.quick_mode import QuickModeInput, build_quick_schedules
from src.models.re_stage5_scenario_service import predict_market_scenarios
from src.policy.eligibility import EligibilityEngine, SessionEligibilityProfile, TriState
from src.policy.discovery import DiscoveryEligibilityEngine, policy_metadata, staged_questions
from src.policy.re_stage8_2_events import DynamicPolicyScenario, build_dynamic_policy_plan
from src.rag.hybrid_search import DATABASE_PATH, HybridPolicySearchIndex
from src.rag.openai_embeddings import DEFAULT_EMBEDDING_MODEL, load_local_openai_env
from src.rag.policy_index import SearchResult
from src.rag.luna_client import explain_with_luna
from src.recommendation import (
    AlternativeKind,
    AlternativeSpec,
    CandidateContext,
    CandidateState,
    MarketScenario,
    UserGoal,
)
from src.settings import PROJECT_ROOT


API_VERSION = "re8-api-v1.4"
SERVICE_NAME = "정책금융 영향 시뮬레이터"
POLICY_DATA_VERSION = "re8.2-markdown-2026-08-17"
BASE_AS_OF = date(2026, 8, 17)
SAMPLE_DIR = PROJECT_ROOT / "data/samples/re_stage7"
AREA_PATH = PROJECT_ROOT / "reports/stage6/area_catalog.csv"
INDUSTRY_PATH = PROJECT_ROOT / "reports/stage6/industry_catalog.csv"
AREA_MAP_PATH = PROJECT_ROOT / "data/processed_re/re_stage8/commercial_area_points.json"
SAMPLE_NAMES = {
    "declining_low_debt": "01_declining_low_debt_detailed.json",
    "stable_high_debt": "02_stable_high_debt_detailed.json",
    "declining_cash_shortage": "03_declining_cash_shortage_detailed.json",
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


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


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
    labels.append(
        {
            UserGoal.MINIMUM_DEBT: "신규 부채 최소화 우선",
            UserGoal.LONGEST_SURVIVAL: "현금 생존기간 우선",
            UserGoal.MINIMUM_REPAYMENT: "월 상환부담 최소화 우선",
            UserGoal.FAST_EXECUTION: "지원 효과가 시작되는 시점 우선",
        }[request.goal]
    )
    return ". ".join(labels), labels


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
        decision = eligibility_engine.evaluate(
            item.chunk.policy_id, profile, district=district, as_of=BASE_AS_OF
        )
        event_status = metadata[item.chunk.policy_id]["event_status"]
        candidates.append(
            {
                "policy_id": item.chunk.policy_id,
                "policy_name": policy["policy_name"],
                "policy_version": policy["policy_version"],
                "matched_section": item.chunk.page_or_section,
                "match_explanation": item.chunk.text[:240],
                "official_url": policy["official_url"],
                **decision,
                "eligibility_readiness": f"{decision['eligibility_status']} · {decision['availability_status']}",
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
    for scenario in request.policy_scenarios:
        candidate = candidates.get(scenario.policy_id)
        if candidate is None or candidate["candidate_state"] == "제외":
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


def _market_scenario_comparison(
    baseline: DetailedCashflowInput,
    prediction: dict[str, Any] | None,
    *,
    selected_scenario: str,
    selected_result: Any,
    safe_cash_override: int | None,
    assume_conditional: bool,
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
            scenario_result, _ = build_hero(
                baseline,
                market=MarketScenario(
                    target_a_percent=scenario["thirteen_week_percent"],
                    target_b_percent=scenario["six_month_percent"],
                    model_version=prediction["model_version"],
                ),
                safe_cash_override=safe_cash_override,
                assume_conditional=assume_conditional,
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
            assume_conditional=request.assume_conditional,
        ),
        eligibility_results=discovery["candidates"],
        intervention_results=[item.model_dump(mode="json") for item in result.alternatives],
        comparison_result={
            "selected_goal": request.goal,
            "goal_meaning": ranking.meaning,
            "ordered_alternative_ids": ranking.ordered_alternative_ids,
            "top_alternative_id": ranking.top_alternative_id,
            "pareto_frontier_ids": result.pareto_frontier_ids,
        },
        execution_plan=[item.model_dump(mode="json") for item in result.execution_plans],
        safe_cash=result.safe_cash.model_dump(mode="json"),
        policy_discovery=discovery,
        dynamic_policy_alternative_ids=[item.alternative_id for item in dynamic_alternatives],
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
    return envelope(
        answer=explanation.answer,
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


POLICY_CHAT_QUERY_EXPANSIONS = (
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
