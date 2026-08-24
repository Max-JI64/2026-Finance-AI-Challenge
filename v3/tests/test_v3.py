from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app as v2_app
from src.policy.eligibility import SessionEligibilityProfile
from src.rag.luna_client import WhatIfInterpretationResult
from v3.main import app as v3_app


v3 = TestClient(v3_app)
v2 = TestClient(v2_app)


def comparison_payload() -> dict[str, object]:
    return {
        "area_code": "3001496",
        "industry_code": "CS100001",
        "sample_id": "default",
        "simple_input": None,
        "quick_input": {
            "reference_date": "2026-09-01",
            "opening_cash": 5_000_000,
            "safe_cash_threshold": 0,
            "monthly_revenue": None,
            "recent_monthly_revenues": [
                7_000_000,
                7_600_000,
                8_200_000,
                8_800_000,
                9_400_000,
                10_000_000,
            ],
            "revenue_timing": "daily",
            "monthly_rent": 1_800_000,
            "monthly_labor_cost": 3_500_000,
            "monthly_variable_cost": 2_800_000,
            "monthly_other_fixed_cost": 800_000,
            "expense_timing": "early",
            "total_loan_balance": 20_000_000,
            "annual_interest_rate_percent": 6.5,
            "remaining_term_months": 36,
            "debt_timing": "early",
        },
        "existing_loan_rate_percent": 6.5,
        "existing_loan_term_months": 36,
        "direct_shock_13_week_percent": 0,
        "direct_shock_6_month_percent": 0,
        "safe_cash_override": None,
        "goal": "최소부채",
        "market_scenario": "central",
        "assume_conditional": True,
        "eligibility_profile": {"policy_answers": {}},
        "policy_scenarios": [],
        "v2_mode": True,
        "selected_policy_ids": [],
        "conditional_policy_ids": [],
        "cost_reduction_plan": None,
    }


def test_v3_is_independent_and_v2_health_remains_available() -> None:
    v3_health = v3.get("/health")
    v2_health = v2.get("/health")
    assert v3_health.status_code == 200
    assert v3_health.json()["version"] == "v3-api-v1.0"
    assert v3_health.json()["v2_preserved"] is True
    assert v2_health.status_code == 200
    assert v2_health.json()["versions"]["api"] == "v2-api-v1.0"


def test_v3_root_serves_the_v2_copied_four_stage_experience_with_v3_extensions() -> None:
    response = v3.get("/")
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "버팀AI" in html
    assert "큰 원은 자치구, 중간 원은 행정동, 작은 원은 개별 상권" in html
    assert "진단·정책 확인" in html
    assert "V3 실행계획" in html
    assert "AI What-if" in html
    assert "입력 가능한 조건" in html
    assert "현재 비용 상승은 지원하지 않습니다" in html
    assert "v3-what-if-dialog" in html
    assert "방금 적용한 가정 되돌리기" in html
    assert "질문은 하나씩, 답변은 묶어서 반영합니다" in html
    assert "비슷한 상황 예시" in html
    assert "data-situation-example" in html
    assert "체크한 내용을 입력에 반영" in html


def test_v3_exposes_v2_compatibility_routes_for_the_copied_screen() -> None:
    response = v3.get("/api/v1/catalog/area-map")
    assert response.status_code == 200
    assert response.json()["items"]


def test_situation_interpreter_requires_confirmation_and_does_not_invent_area() -> None:
    response = v3.post(
        "/api/v3/situation/interpret",
        json={"text": "성수동에서 카페를 하는데 매출이 줄고 대출 상환이 걱정돼요."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["external_ai_used"] is False
    assert data["confirmation_required"] is True
    assert data["suggested_area_code"] is None
    assert data["suggested_industry_code"] == "CS100010"
    assert "최근 월매출" in data["missing_for_cash_diagnosis"]


def test_situation_interpreter_finds_applyable_exact_inputs_and_signals() -> None:
    response = v3.post(
        "/api/v3/situation/interpret",
        json={
            "text": "성수동카페거리에서 카페를 운영하고 있고 임대료와 인건비 같은 고정비가 부담돼요."
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["suggested_area_code"] == "3110131"
    assert data["suggested_industry_code"] == "CS100010"
    understood_keys = {item["key"] for item in data["understood"]}
    assert {"area", "industry", "fixed_cost_concern"}.issubset(understood_keys)


def test_confirmed_situation_reaches_question_selection_and_action_plan() -> None:
    response = v3.post(
        "/api/v3/orchestrate",
        json={
            "comparison": comparison_payload(),
            "answered_fields": [],
            "asked_fields": [],
            "situation_context": {
                "original_text": "대출 이자와 월 상환 부담을 줄이고 싶어요.",
                "confirmed_area_code": "3001496",
                "confirmed_industry_code": "CS100001",
                "signals": ["debt_concern"],
                "confirmed_goal": "최소상환",
            },
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["v3"]["situation_context"]["signals"] == ["debt_concern"]
    assert any(
        "문장에서 대출 부담" in item
        for item in data["v3"]["action_plan"]["today"]
    )
    assert data["v3"]["external_ai_used"] is False


def test_orchestrator_returns_two_bounded_question_batches_without_auto_policy_selection() -> None:
    first = v3.post(
        "/api/v3/orchestrate",
        json={
            "comparison": comparison_payload(),
            "answered_fields": [],
            "asked_fields": [],
        },
    )
    assert first.status_code == 200, first.text
    initial = first.json()
    first_batch = initial["v3"]["next_questions"]
    assert 1 <= len(first_batch) <= 4
    assert initial["v3"]["next_question"] == first_batch[0]
    assert initial["v3"]["question_state"]["round"] == 0
    assert initial["v3"]["question_state"]["batch_limit"] == 4
    assert initial["v3"]["automatic_policy_selection"] is False
    assert initial["v3"]["external_ai_used"] is False
    assert initial["policy_discovery"]["retrieval_mode"] == "bm25"
    assert initial["v2"]["selected_policy_ids"] == []

    value_by_type = {
        "tri_state": "yes",
        "date": "2020-01-01",
        "number": 1,
    }
    profile: dict[str, object] = {"policy_answers": {}}
    for question in first_batch:
        answer_value = value_by_type.get(question["input_type"])
        if answer_value is None:
            first_option = question.get("options", ["yes"])[0]
            answer_value = (
                first_option.get("value", first_option.get("label"))
                if isinstance(first_option, dict)
                else first_option
            )
        if question["field"] in SessionEligibilityProfile.model_fields:
            profile[question["field"]] = answer_value
        else:
            profile["policy_answers"][question["field"]] = answer_value
    payload = comparison_payload()
    payload["eligibility_profile"] = profile
    first_fields = [question["field"] for question in first_batch]
    second = v3.post(
        "/api/v3/orchestrate",
        json={
            "comparison": payload,
            "answered_fields": first_fields,
            "asked_fields": first_fields,
            "question_round": 1,
        },
    )
    assert second.status_code == 200, second.text
    updated = second.json()
    second_batch = updated["v3"]["next_questions"]
    assert len(second_batch) <= 3
    assert updated["v3"]["question_state"]["answered_count"] == len(first_batch)
    assert updated["v3"]["question_state"]["round"] == 1
    assert updated["v3"]["question_state"]["batch_limit"] == 3
    assert not set(first_fields).intersection(question["field"] for question in second_batch)

    final = v3.post(
        "/api/v3/orchestrate",
        json={
            "comparison": payload,
            "answered_fields": first_fields,
            "asked_fields": first_fields,
            "question_round": 2,
        },
    )
    assert final.status_code == 200, final.text
    assert final.json()["v3"]["next_questions"] == []
    assert final.json()["v3"]["question_state"]["max_rounds"] == 2


def test_supported_what_if_changes_revenue_and_recalculates() -> None:
    response = v3.post(
        "/api/v3/what-if",
        json={
            "comparison": comparison_payload(),
            "prompt": "매출이 10% 더 떨어지면?",
            "answered_fields": [],
            "asked_fields": [],
            "situation_context": {
                "original_text": "최근 매출이 줄고 현금이 걱정돼요.",
                "signals": ["sales_decline", "cash_concern"],
            },
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["applied"] is True
    assert data["committed"] is False
    assert data["requires_confirmation"] is True
    assert data["interpretation_source"] == "local_rule"
    assert data["external_ai_used"] is False
    assert data["comparison"]["quick_input"]["recent_monthly_revenues"][0] == 6_300_000
    assert data["change_details"][0] == {
        "label": "최근 월매출 평균",
        "before": 8_500_000,
        "after": 7_650_000,
        "display_type": "money",
    }
    assert data["result"]["v3"]["session_persistence"] == "none"
    assert data["result"]["v3"]["situation_context"]["signals"] == [
        "sales_decline",
        "cash_concern",
    ]


def test_unsupported_what_if_returns_bounded_examples() -> None:
    response = v3.post(
        "/api/v3/what-if",
        json={
            "comparison": comparison_payload(),
            "prompt": "가장 좋은 걸 알아서 해줘",
            "answered_fields": [],
            "asked_fields": [],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["applied"] is False
    assert data["requires_confirmation"] is True
    assert data["supported_examples"]
    assert data["clarification_question"]


def test_cost_increase_is_rejected_once_before_luna(monkeypatch) -> None:
    def fail_if_called(_: str) -> WhatIfInterpretationResult:
        raise AssertionError("unsupported cost increase must not call Luna")

    monkeypatch.setattr("v3.orchestrator.interpret_what_if_with_luna", fail_if_called)
    response = v3.post(
        "/api/v3/what-if",
        json={
            "comparison": comparison_payload(),
            "prompt": "만약 매출이 20%가 늘었는데 월세가 100만원이 상승했다면?",
            "answered_fields": [],
            "asked_fields": [],
            "consent_to_external_ai": True,
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["applied"] is False
    assert data["unsupported"] is True
    assert data["requires_confirmation"] is False
    assert data["clarification_question"] is None
    assert data["external_ai_used"] is False
    assert data["interpretation_source"] == "local_scope_guard"


def test_local_what_if_accepts_the_visible_monthly_rent_example() -> None:
    response = v3.post(
        "/api/v3/what-if",
        json={
            "comparison": comparison_payload(),
            "prompt": "임대료를 월 100만원 줄이면?",
            "answered_fields": [],
            "asked_fields": [],
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["applied"] is True
    assert data["comparison"]["cost_reduction_plan"]["rent"] == 1_000_000
    assert data["committed"] is False


def test_luna_what_if_intent_is_validated_then_calculated_locally(monkeypatch) -> None:
    def fake_luna(_: str) -> WhatIfInterpretationResult:
        return WhatIfInterpretationResult(
            {
                "status": "ready",
                "summary": "임차 비용 절감 가정으로 이해했습니다.",
                "clarification_question": None,
                "operations": [
                    {
                        "kind": "cost_reduction",
                        "cost_key": "rent",
                        "amount_won": 1_000_000,
                    }
                ],
            },
            "openai",
            "gpt-5.6-luna",
        )

    monkeypatch.setattr("v3.orchestrator.interpret_what_if_with_luna", fake_luna)
    response = v3.post(
        "/api/v3/what-if",
        json={
            "comparison": comparison_payload(),
            "prompt": "가게 자리 비용에서 매달 백만 원 정도 아낄 수 있다면?",
            "answered_fields": [],
            "asked_fields": [],
            "consent_to_external_ai": True,
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["applied"] is True
    assert data["committed"] is False
    assert data["interpretation_source"] == "luna"
    assert data["external_ai_used"] is True
    assert data["comparison"]["cost_reduction_plan"]["rent"] == 1_000_000
    assert data["result"]["v3"]["external_ai_used"] is False


def test_luna_can_request_one_clarifying_answer(monkeypatch) -> None:
    monkeypatch.setattr(
        "v3.orchestrator.interpret_what_if_with_luna",
        lambda _: WhatIfInterpretationResult(
            {
                "status": "clarification_needed",
                "summary": "변경 폭이 필요합니다.",
                "clarification_question": "매출을 몇 퍼센트 낮춰 볼까요?",
                "operations": [],
            },
            "openai",
            "gpt-5.6-luna",
        ),
    )
    response = v3.post(
        "/api/v3/what-if",
        json={
            "comparison": comparison_payload(),
            "prompt": "매출이 더 나빠지면?",
            "answered_fields": [],
            "asked_fields": [],
            "consent_to_external_ai": True,
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["applied"] is False
    assert data["external_ai_used"] is True
    assert data["clarification_question"] == "매출을 몇 퍼센트 낮춰 볼까요?"


def test_selected_refinance_preview_does_not_block_page_four() -> None:
    payload = comparison_payload()
    payload.update(
        {
            "area_code": "3120047",
            "market_scenario": "recovery",
            "selected_policy_ids": [
                "POL_SEMAS_STABILITY_VOUCHER_2026",
                "POL_SEMAS_RECHALLENGE_2026",
                "POL_SEMAS_REFINANCE_2026",
            ],
            "conditional_policy_ids": [
                "POL_SEMAS_RECHALLENGE_2026",
                "POL_SEMAS_REFINANCE_2026",
            ],
        }
    )
    response = v3.post(
        "/api/v3/orchestrate",
        json={"comparison": payload, "answered_fields": [], "asked_fields": []},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["v3"]["suppressed_conditional_policy_ids"] == [
        "POL_SEMAS_REFINANCE_2026"
    ]
    assert "POL_SEMAS_REFINANCE_2026" not in data["v2"]["conditional_policy_ids"]
    refinance = next(
        item
        for item in data["policy_discovery"]["candidates"]
        if item["policy_id"] == "POL_SEMAS_REFINANCE_2026"
    )
    assert refinance["application_readiness"]["conditional_graph_supported"] is False
    assert (
        refinance["application_readiness"]["conditional_graph_status"]
        == "calculation_unavailable"
    )
