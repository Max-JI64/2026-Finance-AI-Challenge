"""RE8 application service layer.

The module joins frozen RE3-RE7 engines without allowing the LLM to calculate,
decide eligibility, or alter rankings.
"""

from __future__ import annotations

import csv
import json
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
from src.policy.eligibility import EligibilityEngine, SessionEligibilityProfile
from src.rag.local_db import DATABASE_PATH, SQLitePolicySearchIndex
from src.rag.luna_client import explain_with_luna
from src.recommendation import MarketScenario, UserGoal
from src.settings import PROJECT_ROOT


API_VERSION = "re8-api-v1.2"
SERVICE_NAME = "정책금융 영향 시뮬레이터"
POLICY_DATA_VERSION = "re6-v1-2026-08-16"
BASE_AS_OF = date(2026, 8, 16)
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
    "rag_engine": "re8-sqlite-bm25-v1",
    "policy_data": POLICY_DATA_VERSION,
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


class EligibilityRequest(StrictModel):
    profile: SessionEligibilityProfile
    policy_ids: list[str] = Field(default_factory=list, max_length=10)
    as_of: date = BASE_AS_OF


class PolicyQuestionRequest(StrictModel):
    policy_id: str = Field(min_length=1, max_length=100)
    policy_version: str | None = Field(default=None, max_length=100)
    question: str = Field(min_length=2, max_length=500)
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
        privacy="입력은 현재 요청 처리에만 사용하며 서버 로그, DB, 검색 인덱스에 저장하지 않습니다.",
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
    result, minimum_principal = build_hero(
        baseline,
        market=market,
        safe_cash_override=request.safe_cash_override,
        assume_conditional=request.assume_conditional,
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
        baseline_cashflow=run_detailed_cashflow(baseline).to_dict(),
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
        eligibility_results=[
            {
                **HERO_POLICY_BY_ALTERNATIVE[alternative.alternative_id],
                "eligibility_status": "추가 확인 필요",
                "availability_status": "접수 가능 여부 확인 필요",
                "candidate_state": alternative.candidate_state,
                "reason_summary": alternative.reason_summary,
                "items_to_confirm": alternative.items_to_confirm,
                "as_of_date": BASE_AS_OF.isoformat(),
                "official_urls": alternative.official_urls,
                "application_deadline": (
                    alternative.metrics.application_deadline.isoformat()
                    if alternative.metrics and alternative.metrics.application_deadline
                    else None
                ),
            }
            for alternative in result.alternatives
            if alternative.alternative_id in HERO_POLICY_BY_ALTERNATIVE
        ],
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
    engine = EligibilityEngine()
    policy_ids = request.policy_ids or sorted(engine.policy_by_id)
    unknown = sorted(set(policy_ids).difference(engine.policy_by_id))
    if unknown:
        raise ValueError(f"지원하지 않는 정책 ID: {', '.join(unknown)}")
    results = []
    for policy_id in policy_ids:
        decision = engine.evaluate(policy_id, request.profile, as_of=request.as_of)
        reasons = [
            {
                "condition": item.official_condition,
                "result": item.result,
                "reason": item.reason,
            }
            for item in decision.rule_results
        ]
        results.append(
            {
                "policy_id": policy_id,
                "policy_version": decision.policy_version,
                "eligibility_status": decision.eligibility_status,
                "availability_status": decision.availability_status,
                "candidate_state": (
                    "제외"
                    if decision.eligibility_status == "부적격"
                    or decision.availability_status == "접수기간 종료"
                    else "확인 후 비교"
                    if decision.eligibility_status == "추가 확인 필요"
                    or decision.availability_status == "접수 가능 여부 확인 필요"
                    else "지금 비교 가능"
                ),
                "reason_summary": decision.overall_status,
                "items_to_confirm": [item["reason"] for item in reasons if item["result"] == "unknown"],
                "conditions": reasons,
                "as_of_date": request.as_of.isoformat(),
                "official_notice_url": decision.official_notice_url,
                "application_url": decision.application_url,
            }
        )
    return envelope(
        eligibility_results=results,
        limitations=[decision.final_check_notice if results else "공식기관 최종 확인 필요"],
    )


def ask_policy(request: PolicyQuestionRequest) -> dict[str, Any]:
    try:
        search = SQLitePolicySearchIndex(DATABASE_PATH)
        evidence = search.search(
            request.question,
            policy_id=request.policy_id,
            policy_version=request.policy_version,
            as_of=request.as_of,
            top_k=4,
        )
        explanation = explain_with_luna(request.question, evidence)
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
    return envelope(
        answer=explanation.answer,
        answer_source=explanation.source,
        explanation_model=explanation.model,
        fact_lock_status=explanation.fact_lock_status,
        fallback_reason=explanation.fallback_reason,
        official_evidence=public_evidence,
        limitations=[
            "AI는 계산, 자격판정, 순위를 생성하거나 변경하지 않음",
            "공식 공고와 신청기관에서 최신 상태를 최종 확인해야 함",
        ],
    )


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
