"""Build frozen detailed samples and RE7 representative comparison evidence."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.cashflow.loans import add_months
from src.cashflow.schemas import CashEvent, DetailedCashflowInput, LoanInput, SimpleCashflowInput
from src.policy import (
    GrantScenario,
    LoanScenario,
    PolicyCatalog,
    RefinanceScenario,
    convert_grant,
    convert_loan,
    convert_refinance,
)
from src.recommendation import (
    AlternativeKind,
    AlternativeSpec,
    CandidateContext,
    CandidateState,
    MarketScenario,
    compare_alternatives,
    suggest_safe_cash,
)


SAMPLE_DIR = PROJECT_ROOT / "data/samples/re_stage7"
PROCESSED_DIR = PROJECT_ROOT / "data/processed_re/re_stage7"
REPORT_DIR = PROJECT_ROOT / "reports/re_stage7"
AS_OF = date(2026, 8, 16)


def won(value: Decimal | int | float) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_simple(name: str) -> SimpleCashflowInput:
    path = PROJECT_ROOT / "data/samples/re_stage3" / name
    return SimpleCashflowInput.model_validate_json(path.read_text(encoding="utf-8"))


def month_pairs(reference: date) -> list[tuple[int, int]]:
    return [(add_months(reference, index).year, add_months(reference, index).month) for index in range(6)]


def as_detailed(
    source: SimpleCashflowInput,
    *,
    loan_rate: float,
    loan_term_months: int,
    source_label: str = "frozen_re7_detailed_sample",
) -> DetailedCashflowInput:
    revenue = source.resolved_monthly_revenue()
    variable = (
        source.monthly_variable_cost
        if source.monthly_variable_cost is not None
        else won(Decimal(revenue) * Decimal(str(source.variable_cost_rate_percent)) / Decimal(100))
    )
    events: list[CashEvent] = []
    for index, (year, month) in enumerate(month_pairs(source.reference_date), start=1):
        rows = [
            ("revenue", source.revenue_receipt_day, "operating_inflow", revenue, None, "월 매출입금"),
            ("rent", source.rent_payment_day, "fixed_cost", source.monthly_rent, "rent", "월 임대료"),
            ("labor", source.labor_payment_day, "fixed_cost", source.monthly_labor_cost, "labor", "월 인건비"),
            ("variable", source.variable_cost_payment_day, "variable_cost", variable, "purchase", "월 필수매입"),
        ]
        for prefix, day, event_type, amount, expense_type, description in rows:
            event_date = date(year, month, min(day, 28 if month == 2 else 30 if month in {4, 6, 9, 11} else 31))
            events.append(
                CashEvent(
                    event_id=f"{prefix}-{index}",
                    event_date=event_date,
                    event_type=event_type,
                    amount=amount,
                    expense_type=expense_type,
                    description=description,
                    source=source_label,
                )
            )
        for fixed_index, fixed in enumerate(source.other_fixed_costs, start=1):
            event_date = date(year, month, min(fixed.payment_day, 28 if month == 2 else 30 if month in {4, 6, 9, 11} else 31))
            events.append(
                CashEvent(
                    event_id=f"other-{fixed_index}-{index}",
                    event_date=event_date,
                    event_type="fixed_cost",
                    amount=fixed.amount,
                    expense_type=fixed.expense_type,
                    description=fixed.name,
                    source=source_label,
                )
            )
    loans = []
    if source.total_loan_balance:
        maturity = add_months(source.reference_date, loan_term_months)
        maturity = date(maturity.year, maturity.month, min(source.debt_payment_day, 28))
        loans.append(
            LoanInput(
                loan_id="existing-loan",
                principal=source.total_loan_balance,
                annual_interest_rate_percent=loan_rate,
                repayment_method="equal_principal",
                payment_day=source.debt_payment_day,
                maturity_date=maturity,
            )
        )
    return DetailedCashflowInput(
        reference_date=source.reference_date,
        opening_cash=source.opening_cash,
        safe_cash_threshold=source.safe_cash_threshold,
        events=events,
        loans=loans,
    )


def conditional_context(policy_id: str, version: str, notice: str, application: str) -> CandidateContext:
    return CandidateContext(
        policy_id=policy_id,
        policy_version=version,
        eligibility_status="입력 기준 적격 후보",
        availability_status="접수 가능 여부 확인 필요",
        candidate_state=CandidateState.CONDITIONAL,
        reason_summary="가상 입력 기준 자격후보이나 기준일 현재 잔여예산·접수상태 확인 필요",
        items_to_confirm=["기준일 현재 접수 가능 여부", "최종 자격과 승인금액"],
        as_of=AS_OF,
        official_notice_url=notice,
        application_url=application,
    )


def build_hero(
    hero: DetailedCashflowInput,
    *,
    market: MarketScenario | None = None,
    safe_cash_override: int | None = None,
    assume_conditional: bool = True,
    additional_alternatives: list[AlternativeSpec] | None = None,
):
    market = market or MarketScenario(
        target_a_percent=-12,
        target_b_percent=-18,
        model_version="re5-lightgbm-quantile-v1",
    )
    crisis_url = "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000123842"
    fund_url = "https://www.seoul.go.kr/news/news_notice.do?nttNo=457365"
    refinance_url = "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000124909"
    crisis_context = conditional_context(
        "POL_SEOUL_CRISIS_TRACK2_2026H2", "2026-06-30", crisis_url, "https://www.seoulsbdc.or.kr"
    )
    fund_context = conditional_context(
        "POL_SEOUL_FUND_2026", "2026-05-04-change", fund_url, "https://www.seoulshinbo.co.kr"
    )
    refinance_context = conditional_context(
        "POL_SEMAS_REFINANCE_2026", "2026-07-29-change4", refinance_url, "https://ols.semas.or.kr"
    )
    grant = convert_grant(
        GrantScenario(
            policy_id="POL_SEOUL_CRISIS_TRACK2_2026H2",
            event_id="CRISIS_SOLUTION",
            scenario_status="assumed_approved",
            approved_support_amount=3_000_000,
            payment_date=date(2026, 11, 15),
            total_project_cost=3_750_000,
            eligible_expense_amount=3_000_000,
            expense_date=date(2026, 9, 15),
        )
    )
    refinance = None
    if hero.loans:
        existing = hero.loans[0]
        refinance_profile = PolicyCatalog().get(
            "POL_SEMAS_REFINANCE_2026", "SEMAS_REFINANCE"
        )
        assert refinance_profile.maximum_amount is not None
        refinanced_principal = min(
            existing.principal, refinance_profile.maximum_amount
        )
        refinanced_segment = existing.model_copy(
            update={
                "principal": refinanced_principal,
            }
        )
        replacement = LoanInput(
            loan_id="replacement-refinance",
            principal=refinanced_principal,
            annual_interest_rate_percent=4.5,
            repayment_method="equal_principal",
            payment_day=5,
            maturity_date=date(2036, 8, 5),
        )
        refinance = convert_refinance(
            RefinanceScenario(
                policy_id="POL_SEMAS_REFINANCE_2026",
                event_id="SEMAS_REFINANCE",
                scenario_status="assumed_approved",
                execution_date=hero.reference_date,
                existing_refinanced_loan=refinanced_segment,
                replacement_loan=replacement,
            )
        )
    safe = suggest_safe_cash(hero, user_override=safe_cash_override)
    assert safe.suggested_amount is not None
    # The approved composite uses non-debt support + 5% cost reduction + a loan
    # sized from the 13-week safe-cash gap. This is a mechanical QA amount, not
    # an advertised result and not an approval prediction.
    preliminary = compare_alternatives(
        hero,
        market,
        [
            AlternativeSpec(
                alternative_id="preliminary_non_debt",
                label="비차입 지원 + 비용 5% 절감",
                kind=AlternativeKind.COMBINED,
                plans=[grant],
                candidate_contexts=[crisis_context],
                explicit_condition_assumption=True,
                cost_reduction_rate_percent=5,
            )
        ],
        as_of=AS_OF,
    )
    preliminary_metrics = preliminary.alternatives[1].metrics
    assert preliminary_metrics is not None
    minimum_principal = max(1, safe.suggested_amount - preliminary_metrics.week13_minimum_cash)
    loan = convert_loan(
        LoanScenario(
            policy_id="POL_SEOUL_FUND_2026",
            event_id="SEOUL_EMERGENCY",
            scenario_status="assumed_approved",
            approved_principal=minimum_principal,
            execution_date=hero.reference_date,
            payment_day=5,
            term_months=60,
            grace_months=12,
            repayment_method="equal_principal",
        )
    )
    alternatives = [
        AlternativeSpec(
            alternative_id="cost_reduction_5",
            label="비용 5% 절감",
            kind=AlternativeKind.COST_REDUCTION,
            cost_reduction_rate_percent=5,
            assumptions=["사용자 실행 가능한 운영비 절감률 5%"],
        ),
        AlternativeSpec(
            alternative_id="track2_reimbursement",
            label="위기 소상공인 Track2 사후정산",
            kind=AlternativeKind.NON_DEBT_SUPPORT,
            plans=[grant],
            candidate_contexts=[crisis_context],
            explicit_condition_assumption=assume_conditional,
            application_deadline=date(2026, 11, 30),
            estimated_days_to_effect=75,
            required_documents=["사업자등록증", "매출감소 증빙", "임대차계약서", "선지출 증빙"],
            inquiry="서울신용보증재단 1577-6119",
            official_urls=[crisis_url, "https://www.seoulsbdc.or.kr"],
            assumptions=["지원금 300만원", "선지출 375만원", "2026-11-15 사후정산 지급 가정"],
        ),
        AlternativeSpec(
            alternative_id="emergency_loan",
            label="서울시 긴급자영업자금",
            kind=AlternativeKind.POLICY_LOAN,
            plans=[loan],
            candidate_contexts=[fund_context],
            explicit_condition_assumption=assume_conditional,
            estimated_days_to_effect=14,
            required_documents=["사업자등록증", "자금용도 증빙", "대출·보증 상담서류"],
            inquiry="서울신용보증재단 1577-6119",
            official_urls=[fund_url, "https://www.seoulshinbo.co.kr"],
            assumptions=[f"안전현금 격차 기반 대출원금 {minimum_principal:,}원"],
        ),
        AlternativeSpec(
            alternative_id="combined_safe_cash",
            label="비차입 지원 + 비용 5% 절감 + 안전현금 최소대출",
            kind=AlternativeKind.COMBINED,
            plans=[grant, loan],
            candidate_contexts=[crisis_context, fund_context],
            explicit_condition_assumption=assume_conditional,
            explicit_combination_assumption=assume_conditional,
            cost_reduction_rate_percent=5,
            estimated_days_to_effect=14,
            required_documents=["Track2와 긴급자영업자금 동시수혜 가능 여부 확인", "각 정책 신청서류"],
            inquiry="서울신용보증재단 1577-6119",
            official_urls=[crisis_url, fund_url],
            assumptions=["공식 동시수혜 근거 미확인으로 조건부 비교만 수행"],
        ),
    ]
    if refinance is not None:
        alternatives.insert(
            2,
            AlternativeSpec(
                alternative_id="refinance",
                label="소상공인 정책자금 대환대출",
                kind=AlternativeKind.REFINANCE,
                plans=[refinance],
                candidate_contexts=[refinance_context],
                explicit_condition_assumption=assume_conditional,
                estimated_days_to_effect=30,
                required_documents=["기존 대출내역", "NCB 구간 확인", "만기연장 애로 증빙"],
                inquiry="소상공인통합콜센터 1533-0100 내선 1",
                official_urls=[refinance_url, "https://ols.semas.or.kr"],
            ),
        )
    alternatives.extend(additional_alternatives or [])
    result = compare_alternatives(
        hero,
        market,
        alternatives,
        as_of=AS_OF,
        safe_cash_override=safe_cash_override,
    )
    return result, minimum_principal


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    samples = {
        "01_declining_low_debt_detailed.json": as_detailed(load_simple("01_declining_low_debt.json"), loan_rate=10, loan_term_months=36),
        "02_stable_high_debt_detailed.json": as_detailed(load_simple("02_stable_high_debt.json"), loan_rate=8, loan_term_months=42),
        "03_declining_cash_shortage_detailed.json": as_detailed(load_simple("03_declining_cash_shortage.json"), loan_rate=12, loan_term_months=60),
    }
    for name, sample in samples.items():
        write_json(SAMPLE_DIR / name, sample.model_dump(mode="json"))

    hero = samples["03_declining_cash_shortage_detailed.json"]
    result, minimum_principal = build_hero(hero)
    result_path = PROCESSED_DIR / "hero_decision_result.json"
    write_json(result_path, result.model_dump(mode="json"))

    table_path = PROCESSED_DIR / "comparison_table.csv"
    fields = [
        "alternative_id", "label", "candidate_state", "combination_status", "ranking_eligible",
        "week13_ending_cash", "month6_ending_cash", "week13_minimum_cash", "month6_minimum_cash",
        "survival_days_13_week", "survival_days_6_month", "net_new_borrowing",
        "maximum_monthly_debt_service", "total_interest_through_maturity",
        "total_repayment_obligation", "support_or_cost_reduction", "payment_delay_days",
        "confirmation_item_count", "dominated_by",
    ]
    with table_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for item in result.alternatives:
            metrics = item.metrics.model_dump(mode="json") if item.metrics else {}
            writer.writerow(
                {
                    "alternative_id": item.alternative_id,
                    "label": item.label,
                    "candidate_state": item.candidate_state.value,
                    "combination_status": item.combination_status.value,
                    "ranking_eligible": item.ranking_eligible,
                    **{field: metrics.get(field) for field in fields if field in metrics},
                    "dominated_by": ";".join(item.dominated_by),
                }
            )

    rows = []
    for item in result.alternatives:
        if item.metrics is None:
            continue
        m = item.metrics
        rows.append(
            f"| {item.label} | {item.candidate_state.value} | {m.week13_ending_cash:,} | {m.month6_ending_cash:,} | "
            f"{m.survival_days_13_week} | {m.net_new_borrowing:,} | {m.maximum_monthly_debt_service:,} | "
            f"{(f'{m.total_interest_through_maturity:,}' if m.total_interest_through_maturity is not None else '분해 불가')} | {m.confirmation_item_count} |"
        )
    ranking_rows = [
        f"- {rank.goal.value}: `{rank.top_alternative_id}` — {rank.meaning}"
        + (" (13주 비고갈 기본정렬 후보가 없어 생존일 기준 Fallback)" if rank.fallback_used else "")
        for rank in result.rankings
    ]
    report = f"""# RE Stage 7 대표 시나리오 보고서

## 표본 계약

- 기준 표본: `data/samples/re_stage7/03_declining_cash_shortage_detailed.json`
- 원형: `data/samples/re_stage3/03_declining_cash_shortage.json`
- 상세화: 원형의 현금·월 매출·비용·부채잔액을 보존하고 6개월 지급일정과 기존 대출 원리금 일정을 명시했다.
- 상권환경 참고 스트레스: 13주 Target A `-12%`, 6개월 Target B `-18%`, 적용률 `100%`.
- 생존 정의: 계산 기간 중 일말 현금잔액이 0원 이상인 기간이다. 실제 존속·폐업 예측이 아니다.
- 안전현금 권장값: 향후 28일 필수지출 합계 `{result.safe_cash.suggested_amount:,}원`.
- 복합안 최소대출: 비차입 지원과 비용 5% 절감 후, 정책 실행 전 opening cash를 제외한 13주 일말 잔액의 안전현금 격차를 채우는 기계적 금액 `{minimum_principal:,}원`.

정책 승인·승인금액·지급일은 예측하지 않는다. 세 정책 모두 기준일 현재 접수상태 재확인이 필요해 `확인 후 비교`이며, 명시적 가정으로 계산했지만 기본 목표별 1순위에서는 제외했다. Track2와 서울 긴급자금의 동시수혜 공식 근거는 확인되지 않아 복합안도 조건부다.

## 동일 기준 비교

| 대안 | 후보상태 | 13주 말 현금 | 6개월 말 현금 | 13주 생존일 | 순신규차입 | 월 최대 원리금 | 만기까지 총이자 | 확인항목 수 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(rows)}

## 목표별 결정론 결과

{chr(10).join(ranking_rows)}

목표별 정렬은 임의 가중합이나 적합도 백분율을 사용하지 않는다. `최소부채`, `최소상환`, `빠른실행`은 먼저 13주 비고갈 여부를 비교하고 그 다음 각 목표의 원 단위·일 단위 값을 사전식으로 비교한다. 조건부 정책은 표시와 계산은 가능하지만 기본 정렬에서 제외한다.

## 해석 경계

- 13주와 6개월은 각각 RE5 Target A와 Target B를 독립 적용한 참고 스트레스 계산이다.
- 사후정산 지원은 선지출과 지급 지연을 함께 표시한다.
- 대환과 신규대출은 당장 현금효과뿐 아니라 남은 원금·월 원리금·만기까지 총이자를 함께 표시한다.
- 이 결과는 개인 매출예측, 승인확률, 정책 인과효과, AI 최적 정책이 아니다.
"""
    (REPORT_DIR / "representative_scenarios.md").write_text(report, encoding="utf-8")

    sample_manifest = []
    for name in samples:
        path = SAMPLE_DIR / name
        sample_manifest.append({"path": path.relative_to(PROJECT_ROOT).as_posix(), "sha256": sha256(path)})
    manifest = {
        "stage": "RE Stage 7",
        "engine_version": "re7-v1",
        "contract_version": "re7-contract-v1",
        "generated_as_of": AS_OF.isoformat(),
        "sample_count": len(samples),
        "alternative_count_including_no_action": len(result.alternatives),
        "simulated_count": sum(item.simulated for item in result.alternatives),
        "ranking_eligible_count": sum(item.ranking_eligible for item in result.alternatives),
        "conditional_simulated_count": sum(item.simulated and item.candidate_state is CandidateState.CONDITIONAL for item in result.alternatives),
        "goal_ranking_count": len(result.rankings),
        "pareto_frontier_count": len(result.pareto_frontier_ids),
        "minimum_safe_cash_loan": minimum_principal,
        "prohibited_fit_percentage_fields": 0,
        "hero_visible_curve_ids": [
            "no_action",
            "track2_reimbursement",
            "emergency_loan",
            "combined_safe_cash",
        ],
        "hero_toggle_ids": ["cost_reduction_5", "refinance"],
        "samples": sample_manifest,
        "outputs": [
            {"path": result_path.relative_to(PROJECT_ROOT).as_posix(), "sha256": sha256(result_path)},
            {"path": table_path.relative_to(PROJECT_ROOT).as_posix(), "sha256": sha256(table_path)},
            {"path": "reports/re_stage7/representative_scenarios.md", "sha256": sha256(REPORT_DIR / "representative_scenarios.md")},
        ],
    }
    write_json(REPORT_DIR / "manifest.json", manifest)


if __name__ == "__main__":
    main()
