"""Deterministic RE8.2 candidate eligibility and staged-question workflow.

The frozen RE6 engine remains authoritative for its ten reviewed policies.
Seven later Markdown policies are evaluated by a separate reviewed overlay so
search similarity never becomes an eligibility decision.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.policy.eligibility import EligibilityEngine, SessionEligibilityProfile, TriState
from src.settings import PROJECT_ROOT


METADATA_PATH = (
    PROJECT_ROOT / "data/processed_re/policy/re_stage8_2/policy_metadata.csv"
)


@dataclass(frozen=True)
class QuestionSpec:
    field: str
    label: str
    input_type: str
    reason: str
    impact: str
    options: tuple[tuple[str, str], ...] = ()

    def public(self, policy_ids: list[str]) -> dict[str, Any]:
        return {
            "field": self.field,
            "label": self.label,
            "input_type": self.input_type,
            "reason": self.reason,
            "impact": self.impact,
            "options": [
                {"value": value, "label": label} for value, label in self.options
            ],
            "policy_ids": policy_ids,
        }


TRI_OPTIONS = (("yes", "예"), ("no", "아니오"), ("unknown", "모름"))
SCALE_OPTIONS = (
    ("소상공인", "소상공인에 해당"),
    ("중소기업", "중소기업에 해당"),
    ("중견기업", "중견기업에 해당"),
    ("기타", "해당하지 않음"),
    ("unknown", "모름"),
)


QUESTIONS: dict[str, QuestionSpec] = {
    "business_scale": QuestionSpec(
        "business_scale", "공식 확인서 기준 기업 규모", "select",
        "정책마다 소상공인 또는 중소기업 요건이 다릅니다.",
        "해당하지 않으면 정책 후보에서 제외됩니다.", SCALE_OPTIONS,
    ),
    "opening_date": QuestionSpec(
        "opening_date", "사업자등록증상 개업일", "date",
        "업력 또는 특정 기준일 이전 개업 여부를 확인합니다.",
        "기준 미충족 시 해당 정책 후보에서 제외됩니다.",
    ),
    "employee_count": QuestionSpec(
        "employee_count", "현재 상시근로자 수", "number",
        "업종별 소상공인 근로자 수 기준을 확인합니다.",
        "공식 기준 초과 시 추가 확인 또는 제외가 필요합니다.",
    ),
    "is_operating": QuestionSpec(
        "is_operating", "현재 정상 영업 중인가요?", "tri_state",
        "휴업·폐업 상태를 제외하는 정책이 많습니다.",
        "아니오이면 해당 정책은 실행 가능한 후보에서 제외됩니다.", TRI_OPTIONS,
    ),
    "rented_exclusive_place": QuestionSpec(
        "rented_exclusive_place", "유상 임대차계약을 맺은 독점적 고정 점포인가요?", "tri_state",
        "점포형 지원의 임대차 요건을 확인합니다.", "아니오이면 일부 비용지원 정책에서 제외됩니다.", TRI_OPTIONS,
    ),
    "self_owned_place": QuestionSpec(
        "self_owned_place", "자가 소유 사업장에서 영업하나요?", "tri_state",
        "자가 사업장을 제외하는 비용지원 정책이 있습니다.", "예이면 해당 정책에서 제외될 수 있습니다.", TRI_OPTIONS,
    ),
    "sales_decreased": QuestionSpec(
        "sales_decreased", "공고가 정한 비교기간에 매출이 감소했나요?", "tri_state",
        "매출감소형 정책의 공식 요건입니다.", "모름이면 증빙 확인 전까지 추가 확인 상태입니다.", TRI_OPTIONS,
    ),
    "disaster_document": QuestionSpec(
        "disaster_document", "유효한 재해 확인서가 있나요?", "tri_state",
        "일부 정책은 매출감소 대신 재해 증빙을 인정합니다.", "예이면 재해 경로의 조건을 확인할 수 있습니다.", TRI_OPTIONS,
    ),
    "tax_paid": QuestionSpec(
        "tax_paid", "국세·지방세 완납 요건을 충족하나요?", "tri_state",
        "공고의 납세 제한을 확인합니다.", "아니오이면 일부 정책에서 제외됩니다.", TRI_OPTIONS,
    ),
    "fund_restricted_industry": QuestionSpec(
        "fund_restricted_industry", "서울시 융자지원 제한업종에 해당하나요?", "tri_state",
        "지원제한업종 여부는 업종명만으로 단정하지 않습니다.", "예이면 해당 융자 후보에서 제외됩니다.", TRI_OPTIONS,
    ),
    "policy_loan_restricted_industry": QuestionSpec(
        "policy_loan_restricted_industry", "소상공인 정책자금 융자제외업종에 해당하나요?", "tri_state",
        "여러 전국 지원사업이 같은 제한업종 표를 사용합니다.", "예이면 해당 정책에서 제외됩니다.", TRI_OPTIONS,
    ),
    "prior_crisis_support": QuestionSpec(
        "prior_crisis_support", "2025~2026년 서울시 종합지원 비용사업을 이미 받았나요?", "tri_state",
        "중복수혜 제한을 확인합니다.", "예이면 위기지원에서 제외될 수 있습니다.", TRI_OPTIONS,
    ),
    "prior_closure_support": QuestionSpec(
        "prior_closure_support", "2025~2026년 재단 비용지원사업을 이미 받았나요?", "tri_state",
        "폐업지원 중복수혜 제한을 확인합니다.", "예이면 폐업지원에서 제외될 수 있습니다.", TRI_OPTIONS,
    ),
    "prior_digital_support": QuestionSpec(
        "prior_digital_support", "최근 동일 디지털전환 지원을 받은 적이 있나요?", "tri_state",
        "동일사업 중복지원을 확인합니다.", "예이면 디지털전환 지원에서 제외될 수 있습니다.", TRI_OPTIONS,
    ),
    "subfund_selected": QuestionSpec(
        "subfund_selected", "서울시 육성자금의 세부 자금을 선택했나요?", "tri_state",
        "세부 자금마다 한도·금리·자격이 다릅니다.", "모름이면 금융효과 계산을 시작하지 않습니다.", TRI_OPTIONS,
    ),
    "zero_market_operation": QuestionSpec(
        "zero_market_operation", "다회용기·무포장·리필·친환경포장 사업을 운영하나요?", "tri_state",
        "서울제로마켓의 사업내용 요건입니다.", "아니오이면 해당 정책에서 제외됩니다.", TRI_OPTIONS,
    ),
    "eligible_business_registration": QuestionSpec(
        "eligible_business_registration", "물품 또는 음식 판매가 가능한 사업자등록 업종인가요?", "tri_state",
        "제로마켓의 사업자등록 요건입니다.", "아니오이면 해당 정책에서 제외됩니다.", TRI_OPTIONS,
    ),
    "shared_office_only": QuestionSpec(
        "shared_office_only", "주소만 둔 공유오피스 사업자인가요?", "tri_state",
        "실질 영업장 없는 사업을 제외합니다.", "예이면 해당 정책에서 제외됩니다.", TRI_OPTIONS,
    ),
    "consignment_only": QuestionSpec(
        "consignment_only", "위탁판매만 운영하나요?", "tri_state",
        "제로마켓의 제외조건입니다.", "예이면 해당 정책에서 제외됩니다.", TRI_OPTIONS,
    ),
    "duplicate_public_support": QuestionSpec(
        "duplicate_public_support", "동일·유사 공공지원이 이미 결정됐나요?", "tri_state",
        "동일 비용의 중복지원을 방지합니다.", "예이면 해당 정책에서 제외됩니다.", TRI_OPTIONS,
    ),
    "safety_product_business": QuestionSpec(
        "safety_product_business", "생활용품·어린이제품 제조 또는 유통 사업인가요?", "tri_state",
        "안전검사 지원의 대상 업종을 확인합니다.", "아니오이면 해당 정책에서 제외됩니다.", TRI_OPTIONS,
    ),
    "ncb_919_or_below": QuestionSpec(
        "ncb_919_or_below", "공고의 NCB 919점 이하 요건 또는 예외유형을 충족하나요?", "tri_state",
        "정확한 신용점수를 입력받지 않고 공고 기준 충족 여부만 확인합니다.",
        "모름이면 공식 조회 전까지 추가 확인 상태입니다.", TRI_OPTIONS,
    ),
    "maturity_extension_difficulty": QuestionSpec(
        "maturity_extension_difficulty", "은행권 만기연장 애로 확인을 받을 수 있나요?", "tri_state",
        "고금리 조건 대신 인정되는 대환 경로입니다.", "매출·금리 조건과 함께 후보 판정에 사용합니다.", TRI_OPTIONS,
    ),
    "common_loan_restriction": QuestionSpec(
        "common_loan_restriction", "체납·신용정보등록·휴폐업 등 공통 융자제한에 해당하나요?", "tri_state",
        "정책자금 공통 제한을 확인합니다.", "예이면 대출형 정책에서 제외됩니다.", TRI_OPTIONS,
    ),
}


NEW_ANSWER_QUESTIONS = {
    "self_employed_insurance_enrolled": ("자영업자 고용보험에 가입했나요?", "가입자 보험료 환급 대상인지 확인합니다."),
    "small_business_sales_limit_met": ("업종별 소상공인 매출액 기준을 충족하나요?", "근로자 수와 함께 소상공인 여부를 확인합니다."),
    "family_leave_requirement_met": ("3개월 육아휴직·복직 또는 출산휴가 요건을 충족한 근로자가 있나요?", "기업지원금 지급요건을 확인합니다."),
    "family_employer_restriction_absent": ("공고의 체납·임금체불·산재·보조금 제한에 해당하지 않나요?", "기업 신청 제한을 확인합니다."),
    "employment_insurance_workplace": ("고용보험 가입 사업장인가요?", "미가입 사업장은 가족친화 기업지원금 신청이 제한됩니다."),
    "ieum_new_hire_eligible": ("2026년 서울시민 청년 또는 중장년을 신규채용했나요?", "서울형 이음공제 신규채용 요건을 확인합니다."),
    "ieum_insurance_regular_worker": ("해당 근로자가 공고상 정규직·사회보험 요건을 충족하나요?", "공제 가입 대상 근로자인지 확인합니다."),
    "ieum_no_duplicate_support": ("중복 제한 고용장려금·자산형성 지원에 참여하지 않나요?", "중복수혜 제한을 확인합니다."),
    "annual_sales_le_300m": ("연매출이 3억원 이하인가요?", "노란우산 희망장려금 매출 기준입니다."),
    "new_yellow_umbrella_member": ("노란우산공제 신규 가입자인가요?", "기존 가입자는 희망장려금 대상이 아닙니다."),
    "hospital_resident_30d": ("입원·검진 30일 전부터 지급 완료일까지 서울 거주 요건을 충족하나요?", "서울 거주기간 요건을 확인합니다."),
    "hospital_local_health_insurance": ("해당 기간 국민건강보험 지역가입자인가요?", "입원 생활비의 보험 자격 요건입니다."),
    "hospital_business_45d": ("확인기간에 개인사업을 45일 이상 유지했나요?", "1인 사업자 근로활동 요건입니다."),
    "hospital_income_asset_met": ("가구 중위소득 100% 이하·재산 4억원 이하를 모두 충족하나요?", "소득·재산 요건을 확인합니다."),
    "hospital_exclusion_absent": ("중복 생계급여·실업급여·산재급여 등 제외사유가 없나요?", "중복 급여 및 제외 입원 여부를 확인합니다."),
    "childcare_seoul_household": ("사업장·거주지·자녀 주소의 서울 요건을 충족하나요?", "민간 아이돌봄 지역·동거 요건입니다."),
    "childcare_child_age_met": ("자녀가 공고상 3개월~12세 범위인가요?", "지원대상 아동 연령을 확인합니다."),
    "childcare_no_prior_support": ("2024~2025년 동일 사업 선정 후 이용한 적이 없나요?", "기존 이용자 제외조건을 확인합니다."),
    "junggu_no_prior_support": ("공고에 적힌 서울시·중구 기존 비용지원을 받지 않았나요?", "중복 비용지원 제한을 확인합니다."),
}
for key, (label, reason) in NEW_ANSWER_QUESTIONS.items():
    QUESTIONS[key] = QuestionSpec(
        key, label, "tri_state", reason,
        "모름이면 공식 증빙 확인 전까지 추가 확인 상태입니다.", TRI_OPTIONS,
    )


POLICY_FIELDS: dict[str, tuple[str, ...]] = {
    "POL_SEOUL_FUND_2026": ("business_scale", "fund_restricted_industry", "subfund_selected"),
    "POL_SEOUL_CRISIS_TRACK2_2026H2": ("business_scale", "opening_date", "is_operating", "rented_exclusive_place", "sales_decreased", "disaster_document", "prior_crisis_support"),
    "POL_SEOUL_CLOSURE_2026": ("business_scale", "opening_date", "is_operating", "self_owned_place", "prior_closure_support"),
    "POL_SEOUL_DIGITAL_MIDLIFE_2026H2": ("business_scale", "opening_date", "prior_digital_support"),
    "POL_SEOUL_ZERO_MARKET_2026_2": ("is_operating", "zero_market_operation", "eligible_business_registration", "shared_office_only", "consignment_only", "duplicate_public_support"),
    "POL_SEOUL_SAFETY_TEST_2026H2": ("business_scale", "tax_paid", "safety_product_business"),
    "POL_SEOUL_RESTART_2026": ("business_scale",),
    "POL_SEMAS_REFINANCE_2026": ("business_scale", "ncb_919_or_below", "maturity_extension_difficulty", "common_loan_restriction"),
    "POL_SEMAS_RECHALLENGE_2026": ("business_scale", "common_loan_restriction"),
    "POL_SEMAS_STABILITY_VOUCHER_2026": ("business_scale", "opening_date", "is_operating", "policy_loan_restricted_industry"),
    "POL_SEMAS_EMPLOYMENT_INSURANCE_2026": ("business_scale", "employee_count", "self_employed_insurance_enrolled", "small_business_sales_limit_met"),
    "POL_SEOUL_FAMILY_FRIENDLY_EMPLOYER_2026": ("business_scale", "family_leave_requirement_met", "family_employer_restriction_absent", "employment_insurance_workplace"),
    "POL_SEOUL_IEUM_SAVINGS_2026": ("business_scale", "is_operating", "tax_paid", "ieum_new_hire_eligible", "ieum_insurance_regular_worker", "ieum_no_duplicate_support"),
    "POL_SEOUL_YELLOW_UMBRELLA_2026": ("business_scale", "annual_sales_le_300m", "new_yellow_umbrella_member"),
    "POL_SEOUL_HOSPITAL_LIVING_EXPENSE_2026": ("hospital_resident_30d", "hospital_local_health_insurance", "hospital_business_45d", "hospital_income_asset_met", "hospital_exclusion_absent"),
    "POL_SEOUL_PRIVATE_CHILDCARE_2026": ("business_scale", "employee_count", "policy_loan_restricted_industry", "childcare_seoul_household", "childcare_child_age_met", "childcare_no_prior_support"),
    "POL_JUNGGU_CUSTOM_SUPPORT_2026": ("business_scale", "opening_date", "is_operating", "rented_exclusive_place", "self_owned_place", "tax_paid", "fund_restricted_industry", "junggu_no_prior_support"),
}


NEW_POLICY_RULES: dict[str, tuple[tuple[str, str, str], ...]] = {
    "POL_SEMAS_EMPLOYMENT_INSURANCE_2026": (
        ("self_employed_insurance_enrolled", "yes", "자영업자 고용보험 가입"),
        ("small_business_sales_limit_met", "yes", "업종별 소상공인 매출 기준"),
    ),
    "POL_SEOUL_FAMILY_FRIENDLY_EMPLOYER_2026": (
        ("family_leave_requirement_met", "yes", "육아휴직·출산휴가 지급요건"),
        ("family_employer_restriction_absent", "yes", "기업 신청 제한 비해당"),
        ("employment_insurance_workplace", "yes", "고용보험 가입 사업장"),
    ),
    "POL_SEOUL_IEUM_SAVINGS_2026": (
        ("ieum_new_hire_eligible", "yes", "2026년 서울시민 신규채용"),
        ("ieum_insurance_regular_worker", "yes", "정규직·사회보험 요건"),
        ("ieum_no_duplicate_support", "yes", "중복 지원 비해당"),
    ),
    "POL_SEOUL_YELLOW_UMBRELLA_2026": (
        ("annual_sales_le_300m", "yes", "연매출 3억원 이하"),
        ("new_yellow_umbrella_member", "yes", "노란우산 신규 가입"),
    ),
    "POL_SEOUL_HOSPITAL_LIVING_EXPENSE_2026": (
        ("hospital_resident_30d", "yes", "서울 거주기간"),
        ("hospital_local_health_insurance", "yes", "건강보험 지역가입"),
        ("hospital_business_45d", "yes", "개인사업 45일 이상 유지"),
        ("hospital_income_asset_met", "yes", "소득·재산 기준"),
        ("hospital_exclusion_absent", "yes", "중복급여·제외사유 비해당"),
    ),
    "POL_SEOUL_PRIVATE_CHILDCARE_2026": (
        ("childcare_seoul_household", "yes", "사업장·거주지·자녀 서울 요건"),
        ("childcare_child_age_met", "yes", "지원 아동 연령"),
        ("childcare_no_prior_support", "yes", "동일사업 기존 이용 비해당"),
    ),
    "POL_JUNGGU_CUSTOM_SUPPORT_2026": (
        ("junggu_no_prior_support", "yes", "기존 비용지원 비해당"),
    ),
}


NEW_POLICY_CORE_EXPECTATIONS: dict[str, tuple[tuple[str, str, str], ...]] = {
    "POL_SEOUL_IEUM_SAVINGS_2026": (
        ("is_operating", "yes", "현재 영업 중"),
        ("tax_paid", "yes", "국세·지방세 완납"),
    ),
    "POL_SEOUL_PRIVATE_CHILDCARE_2026": (
        ("policy_loan_restricted_industry", "no", "정책자금 융자제외업종 비해당"),
    ),
    "POL_JUNGGU_CUSTOM_SUPPORT_2026": (
        ("is_operating", "yes", "현재 영업 중"),
        ("rented_exclusive_place", "yes", "유상 임차 고정 점포"),
        ("self_owned_place", "no", "자가 사업장 비해당"),
        ("tax_paid", "yes", "국세·지방세 완납"),
        ("fund_restricted_industry", "no", "서울시 융자지원 제한업종 비해당"),
    ),
}


NEW_POLICY_ALLOWED_SCALES: dict[str, set[str]] = {
    "POL_SEMAS_EMPLOYMENT_INSURANCE_2026": {"소상공인"},
    "POL_SEOUL_FAMILY_FRIENDLY_EMPLOYER_2026": {"소상공인", "중소기업"},
    "POL_SEOUL_IEUM_SAVINGS_2026": {"소상공인", "중소기업", "중견기업"},
    "POL_SEOUL_YELLOW_UMBRELLA_2026": {"소상공인"},
    "POL_SEOUL_PRIVATE_CHILDCARE_2026": {"소상공인", "중소기업"},
    "POL_JUNGGU_CUSTOM_SUPPORT_2026": {"소상공인"},
}


@lru_cache(maxsize=1)
def policy_metadata() -> dict[str, dict[str, str]]:
    with METADATA_PATH.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 17 or len({row["policy_id"] for row in rows}) != 17:
        raise ValueError("RE8.2 metadata must contain 17 unique policies")
    return {row["policy_id"]: row for row in rows}


def _is_missing(profile: SessionEligibilityProfile, field: str) -> bool:
    if field in profile.policy_answers:
        return profile.policy_answers[field] is TriState.UNKNOWN
    value = getattr(profile, field, None)
    return value is None or value is TriState.UNKNOWN or value == ""


def staged_questions(
    policy_ids: list[str], profile: SessionEligibilityProfile
) -> list[dict[str, Any]]:
    requested_by_field: dict[str, list[str]] = {}
    for policy_id in policy_ids:
        for field in POLICY_FIELDS.get(policy_id, ()):
            if _is_missing(profile, field):
                requested_by_field.setdefault(field, []).append(policy_id)
    return [
        QUESTIONS[field].public(policy_ids_for_field)
        for field, policy_ids_for_field in requested_by_field.items()
        if field in QUESTIONS
    ]


def _new_policy_decision(
    policy_id: str,
    profile: SessionEligibilityProfile,
    *,
    district: str,
    as_of: date,
) -> dict[str, Any]:
    metadata = policy_metadata()[policy_id]
    reasons: list[dict[str, str]] = []
    failed = False
    unknown = False

    if metadata["search_district"] != "*":
        passed = district == metadata["search_district"]
        failed |= not passed
        reasons.append({
            "condition": f"사업장 소재지 {metadata['search_district']}",
            "result": "pass" if passed else "fail",
            "reason": f"선택 자치구={district or '미선택'}",
            "field": "",
        })
    if policy_id != "POL_SEOUL_HOSPITAL_LIVING_EXPENSE_2026":
        scale = profile.business_scale
        if scale is None:
            unknown = True
            reasons.append({"condition": "기업 규모", "result": "unknown", "reason": "공식 확인서 기준 기업 규모 확인 필요", "field": "business_scale"})
        else:
            allowed = scale in NEW_POLICY_ALLOWED_SCALES[policy_id]
            failed |= not allowed
            reasons.append({"condition": "기업 규모", "result": "pass" if allowed else "fail", "reason": scale, "field": "business_scale"})
    for field, expected, condition in NEW_POLICY_CORE_EXPECTATIONS.get(policy_id, ()):
        answer = getattr(profile, field)
        if answer is TriState.UNKNOWN:
            unknown = True
            result = "unknown"
        else:
            passed = answer.value == expected
            failed |= not passed
            result = "pass" if passed else "fail"
        reasons.append({"condition": condition, "result": result, "reason": answer.value, "field": field})
    for field, expected, condition in NEW_POLICY_RULES[policy_id]:
        answer = profile.policy_answers.get(field, TriState.UNKNOWN)
        if answer is TriState.UNKNOWN:
            unknown = True
            result = "unknown"
        else:
            passed = answer.value == expected
            failed |= not passed
            result = "pass" if passed else "fail"
        reasons.append({"condition": condition, "result": result, "reason": answer.value, "field": field})

    if policy_id == "POL_JUNGGU_CUSTOM_SUPPORT_2026":
        if profile.opening_date is None:
            unknown = True
            reasons.append({"condition": "개업 후 6개월 이상", "result": "unknown", "reason": "개업일 확인 필요", "field": "opening_date"})
        else:
            passed = (as_of - profile.opening_date).days >= 183
            failed |= not passed
            reasons.append({"condition": "개업 후 6개월 이상", "result": "pass" if passed else "fail", "reason": profile.opening_date.isoformat(), "field": "opening_date"})
    needs_small_business_headcount = policy_id == "POL_SEMAS_EMPLOYMENT_INSURANCE_2026" or (
        policy_id == "POL_SEOUL_PRIVATE_CHILDCARE_2026"
        and profile.business_scale == "소상공인"
    )
    if needs_small_business_headcount:
        if profile.employee_count is None:
            unknown = True
            reasons.append({"condition": "업종별 상시근로자 수 기준", "result": "unknown", "reason": "상시근로자 수 확인 필요", "field": "employee_count"})
        else:
            threshold = 10 if (profile.industry_section or "") in {"광업", "제조업", "건설업", "운수업"} else 5
            passed = profile.employee_count < threshold
            failed |= not passed
            reasons.append({"condition": f"상시근로자 {threshold}명 미만", "result": "pass" if passed else "fail", "reason": str(profile.employee_count), "field": "employee_count"})
    availability = metadata["availability_as_of"]
    closed = availability == "접수기간 종료"
    if failed:
        eligibility = "부적격"
    elif unknown:
        eligibility = "추가 확인 필요"
    else:
        eligibility = "입력 기준 적격 후보"
    if failed or closed:
        candidate_state = "제외"
    elif eligibility == "추가 확인 필요" or "확인 필요" in availability:
        candidate_state = "확인 후 비교"
    else:
        candidate_state = "지금 비교 가능"
    return {
        "policy_id": policy_id,
        "policy_version": metadata["policy_version"],
        "eligibility_status": eligibility,
        "availability_status": availability,
        "candidate_state": candidate_state,
        "reason_summary": " / ".join(
            item["condition"] for item in reasons if item["result"] != "pass"
        ) or "입력한 조건이 검수 Rule과 일치합니다.",
        "items_to_confirm": [item["condition"] for item in reasons if item["result"] == "unknown"],
        "rule_results": reasons,
        "as_of_date": as_of.isoformat(),
        "event_status": metadata["event_status"],
    }


class DiscoveryEligibilityEngine:
    def __init__(self) -> None:
        self.base = EligibilityEngine()

    def evaluate(
        self,
        policy_id: str,
        profile: SessionEligibilityProfile,
        *,
        district: str,
        as_of: date,
    ) -> dict[str, Any]:
        if policy_id in self.base.policy_by_id:
            decision = self.base.evaluate(policy_id, profile, as_of=as_of)
            state = (
                "제외"
                if decision.eligibility_status == "부적격"
                or decision.availability_status == "접수기간 종료"
                else "확인 후 비교"
                if decision.eligibility_status == "추가 확인 필요"
                or decision.availability_status == "접수 가능 여부 확인 필요"
                else "지금 비교 가능"
            )
            return {
                "policy_id": policy_id,
                "policy_version": decision.policy_version,
                "eligibility_status": decision.eligibility_status,
                "availability_status": decision.availability_status,
                "candidate_state": state,
                "reason_summary": decision.overall_status,
                "items_to_confirm": [
                    item.reason for item in decision.rule_results if item.result == "unknown"
                ],
                "rule_results": [
                    {
                        "rule_id": item.rule_id,
                        "rule_group": item.rule_group,
                        "condition": item.official_condition,
                        "result": item.result,
                        "reason": item.reason,
                    }
                    for item in decision.rule_results
                ],
                "as_of_date": as_of.isoformat(),
                "event_status": policy_metadata()[policy_id]["event_status"],
            }
        if policy_id not in NEW_POLICY_RULES:
            raise KeyError(policy_id)
        return _new_policy_decision(
            policy_id, profile, district=district, as_of=as_of
        )
