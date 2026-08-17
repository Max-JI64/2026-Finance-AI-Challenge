"""Reviewed financial-event adapters for the seven RE8.2 overlay policies."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.cashflow.loans import add_months
from src.policy.schemas import (
    AssumptionEntry,
    CashDirection,
    EffectKind,
    PolicyFinancialEvent,
    PolicyPlan,
    ScenarioStatus,
    ValueSource,
)


class DynamicPolicyScenario(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    policy_id: str
    employment_insurance_grade: int | None = Field(default=None, ge=1, le=7)
    expense_already_in_baseline: bool | None = None
    approved_support_amount: int | None = Field(default=None, gt=0, le=10_000_000)
    expense_amount: int | None = Field(default=None, gt=0, le=100_000_000)
    expense_date: date | None = None
    payment_date: date | None = None

    @model_validator(mode="after")
    def validate_policy_fields(self) -> "DynamicPolicyScenario":
        if self.policy_id == "POL_SEMAS_EMPLOYMENT_INSURANCE_2026":
            if self.employment_insurance_grade is None or self.expense_already_in_baseline is None:
                raise ValueError("고용보험료 비교에는 가입등급과 기준현금 포함 여부가 필요합니다.")
        elif self.policy_id == "POL_SEOUL_FAMILY_FRIENDLY_EMPLOYER_2026":
            if self.approved_support_amount is None or self.payment_date is None:
                raise ValueError("기업지원금 비교에는 실제 신청금액과 지급예정일이 필요합니다.")
            if self.approved_support_amount > 4_500_000:
                raise ValueError("기업지원금 공고상 최대 비교액은 450만원입니다.")
        elif self.policy_id == "POL_JUNGGU_CUSTOM_SUPPORT_2026":
            if self.expense_amount is None or self.expense_date is None or self.payment_date is None:
                raise ValueError("중구 비용지원 비교에는 적격비용·지출일·지급예정일이 필요합니다.")
        else:
            raise ValueError("현재 사업체 현금 그래프에 연결할 수 없는 정책입니다.")
        return self


EMPLOYMENT_PREMIUM = {
    1: 40_950,
    2: 46_800,
    3: 52_650,
    4: 58_500,
    5: 64_350,
    6: 70_200,
    7: 76_050,
}
EMPLOYMENT_REFUND = {
    1: 32_760,
    2: 37_440,
    3: 31_590,
    4: 35_100,
    5: 32_175,
    6: 35_100,
    7: 38_025,
}


def _event(
    *,
    policy_id: str,
    version: str,
    event_id: str,
    sequence: int,
    kind: EffectKind,
    direction: CashDirection,
    when: date,
    amount: int,
    description: str,
    amount_source: ValueSource = ValueSource.OFFICIAL,
) -> PolicyFinancialEvent:
    return PolicyFinancialEvent(
        policy_id=policy_id,
        policy_version=version,
        event_id=event_id,
        deduplication_key=f"{policy_id}:{event_id}",
        sequence=sequence,
        effect_kind=kind,
        cash_direction=direction,
        event_date=when,
        amount=amount,
        amount_source=amount_source,
        description=description,
    )


def build_dynamic_policy_plan(
    scenario: DynamicPolicyScenario, *, reference_date: date
) -> PolicyPlan:
    if scenario.policy_id == "POL_SEMAS_EMPLOYMENT_INSURANCE_2026":
        assert scenario.employment_insurance_grade is not None
        assert scenario.expense_already_in_baseline is not None
        grade = scenario.employment_insurance_grade
        events: list[PolicyFinancialEvent] = []
        sequence = 1
        for month in range(6):
            premium_date = add_months(reference_date, month)
            premium_date = date(premium_date.year, premium_date.month, min(10, 28))
            if not scenario.expense_already_in_baseline:
                events.append(_event(
                    policy_id=scenario.policy_id, version="2025-12-29",
                    event_id="EMPLOYMENT_INSURANCE_REFUND", sequence=sequence,
                    kind=EffectKind.PROJECT_EXPENSE, direction=CashDirection.OUTFLOW,
                    when=premium_date, amount=EMPLOYMENT_PREMIUM[grade],
                    description=f"자영업자 고용보험 {grade}등급 월 보험료",
                    amount_source=ValueSource.OFFICIAL,
                ))
                sequence += 1
            refund_base = add_months(premium_date, 2)
            refund_date = date(refund_base.year, refund_base.month, 23)
            events.append(_event(
                policy_id=scenario.policy_id, version="2025-12-29",
                event_id="EMPLOYMENT_INSURANCE_REFUND", sequence=sequence,
                kind=EffectKind.SUPPORT_CASH_INFLOW, direction=CashDirection.INFLOW,
                when=refund_date, amount=EMPLOYMENT_REFUND[grade],
                description=f"납부 확인 약 2개월 후 {grade}등급 보험료 환급",
            ))
            sequence += 1
        support = EMPLOYMENT_REFUND[grade] * 6
        return PolicyPlan(
            policy_id=scenario.policy_id,
            policy_version="2025-12-29",
            event_id="EMPLOYMENT_INSURANCE_REFUND",
            event_name="자영업자 고용보험료 환급",
            support_kind="reimbursement_recurring",
            scenario_status=ScenarioStatus.ASSUMED_APPROVED,
            calculation_status="ready_with_user_grade",
            deduplication_key=f"{scenario.policy_id}:EMPLOYMENT_INSURANCE_REFUND",
            conditional_notice="가입등급과 실제 납부 여부를 전제로 한 일정 비교이며 승인 가능성을 뜻하지 않습니다.",
            events=events,
            assumptions=[
                AssumptionEntry(field="employment_insurance_grade", value=grade, source=ValueSource.USER_INPUT, reason="사용자가 선택한 기준보수 등급"),
                AssumptionEntry(field="expense_already_in_baseline", value=scenario.expense_already_in_baseline, source=ValueSource.USER_INPUT, reason="보험료의 기준 현금흐름 중복 반영 방지"),
                AssumptionEntry(field="refund_delay", value="약 2개월", source=ValueSource.OFFICIAL, reason="공고의 납부 확인 후 환급 예시"),
            ],
            unconfirmed_conditions=["실제 보험료 납부 확인", "기준일 현재 예산 잔여"],
            summary={"support_amount": support, "new_debt_principal": 0},
        )

    if scenario.policy_id == "POL_SEOUL_FAMILY_FRIENDLY_EMPLOYER_2026":
        assert scenario.approved_support_amount is not None
        assert scenario.payment_date is not None
        event = _event(
            policy_id=scenario.policy_id, version="2026-03-11",
            event_id="FAMILY_LEAVE_EMPLOYER_REFUND", sequence=1,
            kind=EffectKind.SUPPORT_CASH_INFLOW, direction=CashDirection.INFLOW,
            when=scenario.payment_date, amount=scenario.approved_support_amount,
            description="사용자가 입력한 실제 4대보험료 사업주 부담금 기준 지원 신청액",
            amount_source=ValueSource.USER_INPUT,
        )
        return PolicyPlan(
            policy_id=scenario.policy_id,
            policy_version="2026-03-11",
            event_id="FAMILY_LEAVE_EMPLOYER_REFUND",
            event_name="육아휴직·출산휴가 기업지원금",
            support_kind="reimbursement_grant",
            scenario_status=ScenarioStatus.ASSUMED_APPROVED,
            calculation_status="ready_with_user_amount_and_date",
            deduplication_key=f"{scenario.policy_id}:FAMILY_LEAVE_EMPLOYER_REFUND",
            conditional_notice="실제 신청금액과 지급예정일을 사용한 조건부 비교입니다.",
            events=[event],
            assumptions=[
                AssumptionEntry(field="approved_support_amount", value=scenario.approved_support_amount, source=ValueSource.USER_INPUT, reason="실제 사업주 부담액 기준 신청금액"),
                AssumptionEntry(field="payment_date", value=scenario.payment_date, source=ValueSource.USER_INPUT, reason="접수 차수에 따른 지급예정일"),
            ],
            unconfirmed_conditions=["서류심사 통과", "실제 인정 보험료"],
            summary={"support_amount": scenario.approved_support_amount, "new_debt_principal": 0},
        )

    assert scenario.policy_id == "POL_JUNGGU_CUSTOM_SUPPORT_2026"
    assert scenario.expense_amount is not None
    assert scenario.expense_date is not None
    assert scenario.payment_date is not None
    reimbursement = min(1_000_000, round(scenario.expense_amount * 0.9))
    events = [
        _event(
            policy_id=scenario.policy_id, version="2026-04-30",
            event_id="JUNGGU_IMPROVEMENT_REFUND", sequence=1,
            kind=EffectKind.PROJECT_EXPENSE, direction=CashDirection.OUTFLOW,
            when=scenario.expense_date, amount=scenario.expense_amount,
            description="VAT 제외 적격 시설개선·온라인전환 비용",
            amount_source=ValueSource.USER_INPUT,
        ),
        _event(
            policy_id=scenario.policy_id, version="2026-04-30",
            event_id="JUNGGU_IMPROVEMENT_REFUND", sequence=2,
            kind=EffectKind.SUPPORT_CASH_INFLOW, direction=CashDirection.INFLOW,
            when=scenario.payment_date, amount=reimbursement,
            description="적격비용 90%, 최대 100만원 사후정산",
        ),
    ]
    return PolicyPlan(
        policy_id=scenario.policy_id,
        policy_version="2026-04-30",
        event_id="JUNGGU_IMPROVEMENT_REFUND",
        event_name="중구 시설개선·온라인전환 비용 지원",
        support_kind="reimbursement_grant",
        scenario_status=ScenarioStatus.ASSUMED_APPROVED,
        calculation_status="closed_as_of_date",
        deduplication_key=f"{scenario.policy_id}:JUNGGU_IMPROVEMENT_REFUND",
        conditional_notice="공고 접수기간이 종료되어 신규 실행 가능한 대안으로 사용할 수 없습니다.",
        events=events,
        assumptions=[],
        unconfirmed_conditions=["접수기간 종료"],
        summary={"support_amount": reimbursement, "new_debt_principal": 0},
    )
