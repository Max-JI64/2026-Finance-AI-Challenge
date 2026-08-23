"""Deterministic RE6 eligibility evaluation over reviewed official rules."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.settings import PROJECT_ROOT


RULES_PATH = PROJECT_ROOT / "data/processed_re/policy/re_stage2/eligibility_rules.csv"
POLICY_PATH = PROJECT_ROOT / "data/processed_re/policy/re_stage2/policy_metadata.csv"


class TriState(StrEnum):
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"


class RuleResult(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"
    INFORMATIONAL = "informational"


class EligibilityStatus(StrEnum):
    ELIGIBLE_CANDIDATE = "입력 기준 적격 후보"
    INELIGIBLE = "부적격"
    NEEDS_CONFIRMATION = "추가 확인 필요"


class AvailabilityStatus(StrEnum):
    AVAILABLE_AS_OF_DATE = "기준일상 접수 가능"
    CLOSED = "접수기간 종료"
    NEEDS_CURRENT_CHECK = "접수 가능 여부 확인 필요"


class RepresentativeAgeBand(StrEnum):
    UNDER_40 = "40세 미만"
    AGE_40_TO_49 = "40~49세"
    AGE_50_OR_OVER = "50세 이상"
    UNKNOWN = "모름"


class SessionEligibilityProfile(BaseModel):
    """Session-only policy facts. The caller must not persist the raw model."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    region: str | None = None
    industry_code: str | None = None
    industry_section: str | None = None
    business_scale: str | None = None
    opening_date: date | None = None
    business_age_months: int | None = Field(default=None, ge=0)
    representative_age_band: RepresentativeAgeBand = RepresentativeAgeBand.UNKNOWN
    sales_2024: int | None = Field(default=None, ge=0)
    sales_2025: int | None = Field(default=None, ge=0)
    sales_2025_h1: int | None = Field(default=None, ge=0)
    sales_2025_h2: int | None = Field(default=None, ge=0)
    annual_sales_2025: int | None = Field(default=None, ge=0)
    employee_count: int | None = Field(default=None, ge=0)
    closure_planned_date: date | None = None
    loan_origination_date: date | None = None
    existing_interest_rate_percent: float | None = Field(default=None, ge=0, le=100)
    multiple_business_count: int | None = Field(default=None, ge=0)

    rented_exclusive_place: TriState = TriState.UNKNOWN
    self_owned_place: TriState = TriState.UNKNOWN
    is_operating: TriState = TriState.UNKNOWN
    sales_decreased: TriState = TriState.UNKNOWN
    disaster_document: TriState = TriState.UNKNOWN
    tax_paid: TriState = TriState.UNKNOWN
    fund_restricted_industry: TriState = TriState.UNKNOWN
    policy_loan_restricted_industry: TriState = TriState.UNKNOWN
    prior_crisis_support: TriState = TriState.UNKNOWN
    prior_closure_support: TriState = TriState.UNKNOWN
    prior_digital_support: TriState = TriState.UNKNOWN
    subfund_selected: TriState = TriState.UNKNOWN
    zero_market_operation: TriState = TriState.UNKNOWN
    eligible_business_registration: TriState = TriState.UNKNOWN
    shared_office_only: TriState = TriState.UNKNOWN
    consignment_only: TriState = TriState.UNKNOWN
    duplicate_public_support: TriState = TriState.UNKNOWN
    safety_product_business: TriState = TriState.UNKNOWN
    recovery_completed: TriState = TriState.UNKNOWN
    foundation_debt_repaid: TriState = TriState.UNKNOWN
    restarted_business: TriState = TriState.UNKNOWN
    ncb_839_or_below: TriState = TriState.UNKNOWN
    ncb_919_or_below: TriState = TriState.UNKNOWN
    maturity_extension_difficulty: TriState = TriState.UNKNOWN
    common_loan_restriction: TriState = TriState.UNKNOWN
    restart_education_completed: TriState = TriState.UNKNOWN
    restart_education_within_one_year: TriState = TriState.UNKNOWN
    restart_education_hours: int | None = Field(default=None, ge=0)
    restart_initial_stage: TriState = TriState.UNKNOWN
    debt_adjustment_compliant: TriState = TriState.UNKNOWN
    recovery_program_selected: TriState = TriState.UNKNOWN
    restart_business_age_months: int | None = Field(default=None, ge=0)
    growth_condition_met: TriState = TriState.UNKNOWN
    direct_loan_repayment_good: TriState = TriState.UNKNOWN
    policy_answers: dict[str, TriState] = Field(default_factory=dict)

    @field_validator("policy_answers")
    @classmethod
    def validate_policy_answers(cls, value: dict[str, TriState]) -> dict[str, TriState]:
        if len(value) > 40:
            raise ValueError("정책별 확인 응답은 40개를 초과할 수 없습니다.")
        if any(not key or len(key) > 80 for key in value):
            raise ValueError("정책별 확인 항목 키가 올바르지 않습니다.")
        return value


class RuleEvaluation(BaseModel):
    rule_id: str
    rule_group: str
    category: str
    result: RuleResult
    official_condition: str
    source_locator: str
    reason: str


class EligibilityDecision(BaseModel):
    policy_id: str
    policy_version: str
    eligibility_status: EligibilityStatus
    availability_status: AvailabilityStatus
    overall_status: str
    as_of: date
    rule_results: list[RuleEvaluation]
    passed_rule_ids: list[str]
    failed_rule_ids: list[str]
    unknown_rule_ids: list[str]
    official_notice_url: str
    application_url: str
    final_check_notice: str = (
        "이 결과는 입력값과 공개 자격조건의 일치 여부이며 승인 가능성을 뜻하지 않습니다. "
        "접수 상태와 최종 자격은 공식 기관에서 다시 확인하세요."
    )


def _tri(value: TriState, *, positive_reason: str, negative_reason: str) -> tuple[RuleResult, str]:
    if value is TriState.YES:
        return RuleResult.PASS, positive_reason
    if value is TriState.NO:
        return RuleResult.FAIL, negative_reason
    return RuleResult.UNKNOWN, "입력값이 없어 확인이 필요합니다."


def _exclude(value: TriState, label: str) -> tuple[RuleResult, str]:
    if value is TriState.YES:
        return RuleResult.FAIL, f"제외조건에 해당합니다: {label}"
    if value is TriState.NO:
        return RuleResult.PASS, f"제외조건에 해당하지 않습니다: {label}"
    return RuleResult.UNKNOWN, f"제외조건 확인이 필요합니다: {label}"


def _compare(value: Any, operator: str, threshold: Any, label: str) -> tuple[RuleResult, str]:
    if value is None:
        return RuleResult.UNKNOWN, f"{label} 입력이 필요합니다."
    checks = {
        ">=": value >= threshold,
        "<=": value <= threshold,
        ">": value > threshold,
        "<": value < threshold,
    }
    passed = checks[operator]
    return (
        RuleResult.PASS if passed else RuleResult.FAIL,
        f"{label}={value}, 기준 {operator} {threshold}",
    )


@dataclass(frozen=True)
class ReviewedRule:
    policy_id: str
    rule_id: str
    rule_group: str
    category: str
    operator: str
    value: str
    source_locator: str


class EligibilityEngine:
    def __init__(self, rules_path: Path = RULES_PATH, policy_path: Path = POLICY_PATH) -> None:
        with rules_path.open("r", encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        with policy_path.open("r", encoding="utf-8-sig", newline="") as stream:
            policies = list(csv.DictReader(stream))
        self.rules = tuple(
            ReviewedRule(
                policy_id=row["policy_id"],
                rule_id=row["rule_id"],
                rule_group=row["rule_group"],
                category=row["category"],
                operator=row["operator"],
                value=row["value"],
                source_locator=row["source_locator"],
            )
            for row in rows
        )
        self.policy_by_id = {row["policy_id"]: row for row in policies}
        if len(self.rules) != 56 or len(self.policy_by_id) != 10:
            raise ValueError("RE6 requires 56 reviewed rules across 10 policies")

    def _evaluate_condition(
        self, rule: ReviewedRule, profile: SessionEligibilityProfile
    ) -> tuple[RuleResult, str]:
        rid = rule.rule_id
        if rid.endswith("ALL_01") and rule.category == "region":
            if profile.region is None:
                return RuleResult.UNKNOWN, "소재지 입력이 필요합니다."
            passed = profile.region in {"서울", "서울특별시"}
            return (RuleResult.PASS if passed else RuleResult.FAIL, f"소재지={profile.region}")
        if rid == "FUND_ALL_02":
            if profile.business_scale is None:
                return RuleResult.UNKNOWN, "기업규모 입력이 필요합니다."
            passed = profile.business_scale in {"소상공인", "중소기업"}
            return (RuleResult.PASS if passed else RuleResult.FAIL, f"기업규모={profile.business_scale}")
        if rid == "FUND_EX_01":
            known_code = profile.industry_code == "56211"
            state = TriState.YES if known_code else profile.fund_restricted_industry
            return _exclude(state, "서울시 융자지원 제한업종")
        if rid == "FUND_VARIANT":
            if profile.subfund_selected is TriState.YES:
                return RuleResult.PASS, "하위 자금 선택 완료"
            return RuleResult.UNKNOWN, "세부 자금을 아직 선택하지 않았습니다. 자금 용도와 현금 부족 규모에 맞는 하위 자금 확인이 필요합니다."

        if rid == "CRISIS_ALL_02":
            return _tri(profile.rented_exclusive_place, positive_reason="유상 임차 고정점포", negative_reason="임차 고정점포 요건 불충족")
        if rid == "CRISIS_ALL_03":
            return _compare(profile.business_age_months, ">=", 24, "업력(개월)")
        if rid == "CRISIS_ANY_01":
            state = profile.sales_decreased
            if state is TriState.UNKNOWN:
                if profile.sales_2024 is not None and profile.sales_2025 is not None:
                    state = TriState.YES if profile.sales_2025 < profile.sales_2024 else TriState.NO
                elif profile.sales_2025_h1 is not None and profile.sales_2025_h2 is not None:
                    state = TriState.YES if profile.sales_2025_h2 < profile.sales_2025_h1 else TriState.NO
            return _tri(state, positive_reason="공고상 매출감소 경로 충족", negative_reason="매출감소 경로 불충족")
        if rid == "CRISIS_ANY_02":
            return _tri(profile.disaster_document, positive_reason="유효한 재해 확인서 보유", negative_reason="재해 확인서 없음")
        if rid == "CRISIS_EX_01":
            state = TriState.NO if profile.is_operating is TriState.YES else TriState.YES if profile.is_operating is TriState.NO else TriState.UNKNOWN
            return _exclude(state, "휴업·폐업")
        if rid == "CRISIS_EX_02":
            return _exclude(profile.prior_crisis_support, "2025~2026 서울시 중복 비용지원")

        if rid == "CLOSE_ALL_02":
            if profile.is_operating is TriState.NO:
                return RuleResult.FAIL, "신청일 현재 영업 중이 아닙니다."
            if profile.is_operating is TriState.UNKNOWN or profile.closure_planned_date is None:
                return RuleResult.UNKNOWN, "영업상태와 폐업예정일 확인이 필요합니다."
            return RuleResult.PASS, "영업 중인 폐업 예정자"
        if rid == "CLOSE_ALL_03":
            return _compare(profile.business_age_months, ">=", 6, "업력(개월)")
        if rid == "CLOSE_ALL_04":
            return _compare(profile.closure_planned_date, "<=", date(2026, 10, 31), "폐업예정일")
        if rid == "CLOSE_EX_01":
            return _exclude(profile.self_owned_place, "자가 사업장")
        if rid == "CLOSE_EX_02":
            return _exclude(profile.prior_closure_support, "2025~2026 재단 비용지원사업")

        if rid == "DIGI_ALL_02":
            if profile.representative_age_band is RepresentativeAgeBand.UNKNOWN:
                return RuleResult.UNKNOWN, "대표자 연령구간 입력이 필요합니다."
            passed = profile.representative_age_band is not RepresentativeAgeBand.UNDER_40
            return RuleResult.PASS if passed else RuleResult.FAIL, f"대표자 연령구간={profile.representative_age_band.value}"
        if rid == "DIGI_ALL_03":
            return _compare(profile.opening_date, "<", date(2025, 7, 1), "개업일")
        if rid == "DIGI_PREF_01":
            preferred = profile.representative_age_band is RepresentativeAgeBand.AGE_50_OR_OVER
            reason = f"대표자 연령구간={profile.representative_age_band.value}"
            return RuleResult.INFORMATIONAL, reason + (" (우대)" if preferred else "")
        if rid == "DIGI_PREF_02":
            preferred = {"숙박·음식점업", "제조업", "수리·기타서비스업"}
            reason = "업종 우대 여부 확인 필요" if profile.industry_section is None else f"업종={profile.industry_section}"
            return RuleResult.INFORMATIONAL, reason + (" (우대)" if profile.industry_section in preferred else "")
        if rid == "DIGI_EX_01":
            return _exclude(profile.prior_digital_support, "동일·서울시 종합지원 중복수혜")

        if rid == "ZERO_ALL_02":
            return _tri(profile.zero_market_operation, positive_reason="제로마켓 운영방식 충족", negative_reason="제로마켓 운영방식 불충족")
        if rid == "ZERO_ALL_03":
            return _tri(profile.eligible_business_registration, positive_reason="판매·조리 가능 사업자등록", negative_reason="사업자등록 업종 요건 불충족")
        if rid == "ZERO_EX_01":
            state = TriState.NO if profile.is_operating is TriState.YES else TriState.YES if profile.is_operating is TriState.NO else TriState.UNKNOWN
            return _exclude(state, "폐업·사실상 폐업·휴업")
        if rid == "ZERO_EX_02":
            if TriState.YES in {profile.shared_office_only, profile.consignment_only}:
                return RuleResult.FAIL, "주소만 공유오피스 또는 위탁판매 제외조건"
            if TriState.UNKNOWN in {profile.shared_office_only, profile.consignment_only}:
                return RuleResult.UNKNOWN, "공유오피스·위탁판매 여부 확인 필요"
            return RuleResult.PASS, "온라인 운영 제외조건 비해당"
        if rid == "ZERO_EX_03":
            return _exclude(profile.duplicate_public_support, "동일·유사 국비·시비 지원")

        if rid == "SAFE_ALL_02":
            return _tri(profile.safety_product_business, positive_reason="생활용품·어린이제품 관련 업종", negative_reason="지원 업종 아님")
        if rid == "SAFE_ALL_03":
            return _tri(profile.tax_paid, positive_reason="국세·지방세 완납", negative_reason="국세·지방세 미완납")
        if rid == "SAFE_CHILD_01":
            return _compare(profile.annual_sales_2025, "<", 104_000_000, "2025 연매출")

        if rid == "RESTART_ANY_01":
            return _tri(profile.recovery_completed, positive_reason="성실실패 요건 충족", negative_reason="성실실패 요건 불충족")
        if rid == "RESTART_ANY_02":
            return _tri(profile.foundation_debt_repaid, positive_reason="재단 채무 전액 성실상환", negative_reason="성실상환 요건 불충족")
        if rid == "RESTART_ANY_03":
            return _tri(profile.restarted_business, positive_reason="과거 폐업 후 재창업", negative_reason="재창업 요건 불충족")

        if rid == "REFI_ALL_01":
            return _tri(profile.ncb_919_or_below, positive_reason="NCB 919 이하 확인", negative_reason="NCB 919 이하 요건 불충족")
        if rid == "REFI_ALL_02":
            return _compare(profile.loan_origination_date, "<=", date(2025, 6, 30), "기존대출 실행일")
        if rid == "REFI_ANY_01":
            return _compare(profile.existing_interest_rate_percent, ">=", 7.0, "기존대출 금리(%)")
        if rid == "REFI_ANY_02":
            return _tri(profile.maturity_extension_difficulty, positive_reason="만기연장 애로 확인", negative_reason="만기연장 애로 미확인")
        if rid == "REFI_EX_01":
            return _exclude(profile.common_loan_restriction, "공통 대출 제한사유")

        if rid == "RECH_ANY_01":
            states = (profile.restart_education_completed, profile.restart_education_within_one_year)
            if TriState.NO in states:
                return RuleResult.FAIL, "재창업교육 수료·기간 요건 불충족"
            if TriState.UNKNOWN in states or profile.restart_education_hours is None:
                return RuleResult.UNKNOWN, "재창업교육 수료·기간·시간 확인 필요"
            return _compare(profile.restart_education_hours, ">=", 25, "재창업교육 시간")
        if rid == "RECH_ANY_02":
            return _tri(profile.restart_initial_stage, positive_reason="재창업 초기단계 요건 충족", negative_reason="재창업 초기단계 요건 불충족")
        if rid == "RECH_ANY_03":
            return _tri(profile.debt_adjustment_compliant, positive_reason="채무조정 후 성실상환 요건 충족", negative_reason="채무조정 경로 요건 불충족")
        if rid == "RECH_HOPE_01":
            return _tri(profile.recovery_program_selected, positive_reason="희망형 재기사업화 경로 충족", negative_reason="희망형 경로 불충족")
        if rid == "RECH_LEAP_01":
            return _compare(profile.restart_business_age_months, ">=", 24, "재창업 업력(개월)")
        if rid == "RECH_LEAP_02":
            return _tri(profile.growth_condition_met, positive_reason="도약형 성장요건 충족", negative_reason="도약형 성장요건 불충족")
        if rid == "RECH_LEAP_03":
            return _tri(profile.direct_loan_repayment_good, positive_reason="직접대출 성실상환 요건 충족", negative_reason="직접대출 상환요건 불충족")
        if rid == "RECH_EX_01":
            return _exclude(profile.common_loan_restriction, "공통 대출 제한사유")

        if rid == "VOUCH_ALL_01":
            return _compare(profile.annual_sales_2025, ">", 0, "2025 연매출")
        if rid == "VOUCH_ALL_02":
            return _compare(profile.annual_sales_2025, "<", 104_000_000, "2025 연매출")
        if rid == "VOUCH_ALL_03":
            return _compare(profile.opening_date, "<=", date(2025, 12, 31), "개업일")
        if rid == "VOUCH_ALL_04":
            return _tri(profile.is_operating, positive_reason="신청일 현재 영업 중", negative_reason="신청일 현재 영업 중이 아님")
        if rid == "VOUCH_EX_01":
            return _exclude(profile.policy_loan_restricted_industry, "소상공인 정책자금 융자제외업종")
        if rid == "VOUCH_LIMIT_01":
            return _compare(profile.multiple_business_count, "<=", 1, "대표자 사업체 수")

        raise KeyError(f"No deterministic evaluator for reviewed rule {rid}")

    @staticmethod
    def _alternative_result(groups: dict[str, list[RuleResult]]) -> RuleResult | None:
        if "any" in groups:
            values = groups["any"]
            if RuleResult.PASS in values:
                return RuleResult.PASS
            if RuleResult.UNKNOWN in values:
                return RuleResult.UNKNOWN
            return RuleResult.FAIL
        if any(name in groups for name in ("general_any", "hope", "leap_all")):
            paths: list[RuleResult] = []
            for name in ("general_any", "hope"):
                values = groups.get(name, [])
                if values:
                    paths.append(RuleResult.PASS if RuleResult.PASS in values else RuleResult.UNKNOWN if RuleResult.UNKNOWN in values else RuleResult.FAIL)
            leap = groups.get("leap_all", [])
            if leap:
                paths.append(RuleResult.FAIL if RuleResult.FAIL in leap else RuleResult.UNKNOWN if RuleResult.UNKNOWN in leap else RuleResult.PASS)
            if RuleResult.PASS in paths:
                return RuleResult.PASS
            if RuleResult.UNKNOWN in paths:
                return RuleResult.UNKNOWN
            return RuleResult.FAIL
        return None

    def evaluate(
        self,
        policy_id: str,
        profile: SessionEligibilityProfile,
        *,
        as_of: date,
        rule_ids: Iterable[str] | None = None,
        check_availability: bool = True,
    ) -> EligibilityDecision:
        policy = self.policy_by_id[policy_id]
        selected = set(rule_ids) if rule_ids is not None else None
        rules = [rule for rule in self.rules if rule.policy_id == policy_id and (selected is None or rule.rule_id in selected)]
        evaluations: list[RuleEvaluation] = []
        groups: dict[str, list[RuleResult]] = {}
        for rule in rules:
            result, reason = self._evaluate_condition(rule, profile)
            evaluations.append(RuleEvaluation(rule_id=rule.rule_id, rule_group=rule.rule_group, category=rule.category, result=result, official_condition=rule.value, source_locator=rule.source_locator, reason=reason))
            if result is not RuleResult.INFORMATIONAL:
                groups.setdefault(rule.rule_group, []).append(result)

        hard = [value for name, values in groups.items() if name in {"all", "child_product", "variant", "limit"} for value in values]
        exclusions = groups.get("exclude", [])
        alternative = self._alternative_result(groups)
        if RuleResult.FAIL in hard or RuleResult.FAIL in exclusions or alternative is RuleResult.FAIL:
            eligibility = EligibilityStatus.INELIGIBLE
        elif RuleResult.UNKNOWN in hard or RuleResult.UNKNOWN in exclusions or alternative is RuleResult.UNKNOWN:
            eligibility = EligibilityStatus.NEEDS_CONFIRMATION
        else:
            eligibility = EligibilityStatus.ELIGIBLE_CANDIDATE

        availability = self._availability(policy, as_of) if check_availability else AvailabilityStatus.AVAILABLE_AS_OF_DATE
        if eligibility is EligibilityStatus.INELIGIBLE:
            overall = eligibility.value
        elif availability is AvailabilityStatus.CLOSED:
            overall = availability.value
        elif availability is AvailabilityStatus.NEEDS_CURRENT_CHECK:
            overall = availability.value
        else:
            overall = eligibility.value
        return EligibilityDecision(
            policy_id=policy_id,
            policy_version=policy["policy_version"],
            eligibility_status=eligibility,
            availability_status=availability,
            overall_status=overall,
            as_of=as_of,
            rule_results=evaluations,
            passed_rule_ids=[item.rule_id for item in evaluations if item.result is RuleResult.PASS],
            failed_rule_ids=[item.rule_id for item in evaluations if item.result is RuleResult.FAIL],
            unknown_rule_ids=[item.rule_id for item in evaluations if item.result is RuleResult.UNKNOWN],
            official_notice_url=policy["official_notice_url"],
            application_url=policy["application_url"],
        )

    @staticmethod
    def _availability(policy: dict[str, str], as_of: date) -> AvailabilityStatus:
        end = policy["application_end"]
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", end) and date.fromisoformat(end) < as_of:
            return AvailabilityStatus.CLOSED
        effective_to = policy["effective_to"]
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", effective_to) and date.fromisoformat(effective_to) < as_of:
            return AvailabilityStatus.CLOSED
        status = policy["application_status_as_of"]
        if any(token in status for token in ("재확인", "개별 상담", "미확인", "소진")) or end in {"예산소진시", "자금소진시", "모집마감시"}:
            return AvailabilityStatus.NEEDS_CURRENT_CHECK
        return AvailabilityStatus.AVAILABLE_AS_OF_DATE


def profile_from_reviewed_example(raw: str) -> SessionEligibilityProfile:
    """Translate the reviewed RE2 example notation without retaining exact NCB scores."""

    values: dict[str, Any] = {}
    pairs = dict(part.split("=", 1) for part in raw.split(";") if "=" in part)
    yes = lambda key: TriState.YES if pairs.get(key) == "yes" else TriState.NO if pairs.get(key) == "no" else TriState.UNKNOWN
    if "서울" in pairs:
        values["region"] = "서울특별시" if pairs["서울"] == "yes" else "서울특별시 외"
    if "소상공인" in pairs:
        values["business_scale"] = "소상공인" if pairs["소상공인"] == "yes" else "기타"
    if "업종" in pairs:
        values["industry_code"] = pairs["업종"]
    if "하위자금" in pairs:
        values["subfund_selected"] = TriState.UNKNOWN if pairs["하위자금"] == "모름" else yes("하위자금")
    if "임차점포" in pairs:
        values["rented_exclusive_place"] = yes("임차점포")
    if "업력" in pairs:
        number = int(re.search(r"\d+", pairs["업력"]).group())
        values["business_age_months"] = number * 12 if "년" in pairs["업력"] else number
    if "매출감소" in pairs:
        values["sales_decreased"] = yes("매출감소")
    if "영업중" in pairs:
        values["is_operating"] = yes("영업중")
    if "폐업예정" in pairs:
        values["closure_planned_date"] = date.fromisoformat(pairs["폐업예정"] + "-01")
    if "나이" in pairs:
        age = int(pairs["나이"])
        values["representative_age_band"] = (
            RepresentativeAgeBand.UNDER_40
            if age < 40
            else RepresentativeAgeBand.AGE_40_TO_49
            if age < 50
            else RepresentativeAgeBand.AGE_50_OR_OVER
        )
    if "개업일" in pairs:
        values["opening_date"] = date.fromisoformat(pairs["개업일"])
    if "리필스테이션" in pairs:
        values["zero_market_operation"] = yes("리필스테이션")
    if "사업자등록" in pairs:
        values["eligible_business_registration"] = yes("사업자등록")
    if "공유오피스주소만" in pairs:
        values["shared_office_only"] = yes("공유오피스주소만")
    if "위탁판매" in pairs:
        values["consignment_only"] = yes("위탁판매")
    if "어린이제품" in pairs:
        values["safety_product_business"] = yes("어린이제품")
    if "매출" in pairs:
        values["annual_sales_2025"] = int(pairs["매출"])
    if "세금완납" in pairs:
        values["tax_paid"] = yes("세금완납")
    if "국세완납" in pairs:
        values["tax_paid"] = yes("국세완납")
    if "과거폐업" in pairs and pairs["과거폐업"] == "yes":
        values["restarted_business"] = yes("재창업")
    elif "재창업" in pairs:
        values["restarted_business"] = TriState.UNKNOWN if pairs["재창업"] == "모름" else yes("재창업")
    if "성실실패" in pairs:
        values["recovery_completed"] = TriState.UNKNOWN if pairs["성실실패"] == "모름" else yes("성실실패")
    if "성실상환" in pairs:
        values["foundation_debt_repaid"] = TriState.UNKNOWN if pairs["성실상환"] == "모름" else yes("성실상환")
    if "NCB" in pairs:
        score = int(pairs["NCB"])
        values["ncb_839_or_below"] = TriState.YES if score <= 839 else TriState.NO
        values["ncb_919_or_below"] = TriState.YES if score <= 919 else TriState.NO
    if "실행일" in pairs:
        values["loan_origination_date"] = date.fromisoformat(pairs["실행일"])
    if "기존금리" in pairs:
        values["existing_interest_rate_percent"] = float(pairs["기존금리"].rstrip("%"))
    if "교육수료" in pairs:
        values["restart_education_completed"] = yes("교육수료")
    if "수료시점" in pairs:
        values["restart_education_within_one_year"] = TriState.YES if pairs["수료시점"] == "최근1년" else TriState.NO
    if "시간" in pairs:
        values["restart_education_hours"] = int(pairs["시간"])
    if "채무조정" in pairs:
        values["debt_adjustment_compliant"] = TriState.UNKNOWN if pairs["채무조정"] == "모름" else yes("채무조정")
    if "재기사업화" in pairs:
        values["recovery_program_selected"] = TriState.UNKNOWN if pairs["재기사업화"] == "모름" else yes("재기사업화")
    return SessionEligibilityProfile(**values)
