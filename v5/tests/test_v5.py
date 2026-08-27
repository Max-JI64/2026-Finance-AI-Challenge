from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app as v2_app
from src.policy.discovery import POLICY_FIELDS
from src.rag.policy_index import PolicyChunk, content_hash
from v4.main import app as v4_app
from v5.copilot import (
    NoticeLunaOutput,
    NOTICE_EXTRACTION_CACHE_PATH,
    _canonical_notice_evidence,
    _validated_notice_fields,
)
from v5.main import app as v5_app
from v5.orchestrator import METRIC_ORDER, order_policy_reviews


ROOT = Path(__file__).resolve().parents[2]
V5 = TestClient(v5_app)
V4 = TestClient(v4_app)
V2 = TestClient(v2_app)
EVALUATION = ROOT / "reports/v5/evaluation"


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
            "recent_monthly_revenues": [7_000_000, 7_600_000, 8_200_000, 8_800_000, 9_400_000, 10_000_000],
            "revenue_timing": "daily",
            "monthly_rent": 1_800_000,
            "monthly_labor_cost": 3_500_000,
            "monthly_variable_cost": 2_800_000,
            "monthly_other_fixed_cost": 800_000,
            "expense_timing": "early",
            "total_loan_balance": 20_000_000,
            "annual_interest_rate_percent": 8.5,
            "remaining_term_months": 36,
            "debt_timing": "early",
        },
        "existing_loan_rate_percent": 8.5,
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
        "selected_policy_ids": [
            "POL_SEMAS_STABILITY_VOUCHER_2026",
            "POL_SEMAS_REFINANCE_2026",
            "POL_SEMAS_RECHALLENGE_2026",
        ],
        "conditional_policy_ids": [
            "POL_SEMAS_STABILITY_VOUCHER_2026",
            "POL_SEMAS_REFINANCE_2026",
            "POL_SEMAS_RECHALLENGE_2026",
        ],
        "cost_reduction_plan": None,
    }


def orchestrate_payload(review_lens: str = "debt_relief", **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "comparison": comparison_payload(),
        "answered_fields": [],
        "asked_fields": [],
        "question_round": 0,
        "review_lens": review_lens,
        "review_lens_source": "user",
        "confirmed_review_lens": None,
    }
    payload.update(overrides)
    return payload


def test_v5_health_scope_and_older_versions_are_preserved() -> None:
    health = V5.get("/health")
    assert health.status_code == 200
    body = health.json()
    assert body["version"] == body["api_version"] == "v5-api-v1.0"
    assert body["deterministic_financial_authority"] is True
    assert body["session_persistence"] == "browser_session_only"
    assert body["notice_extraction_cache"] == "local_persistent_public_notice_only"
    assert body["application_document_upload"] == "not_supported"
    assert body["upfront_question_gate"] == "disabled"
    assert body["policy_preparation_choices"] == "enabled"
    scope = V5.get("/scope").json()
    assert scope["financial_authority"] == "deterministic_rule_event_cashflow_ranking_only"
    assert scope["review_order_authority"] == "review_lens_display_order_only"
    assert V4.get("/health").json()["version"] == "v4-api-v1.0"
    assert V2.get("/health").json()["versions"]["api"] == "v2-api-v1.0"


def test_root_exposes_three_user_stages_and_preserves_core_inputs() -> None:
    html = V5.get("/").content.decode("utf-8")
    assert html.count('class="step-button') == 3
    assert all(label in html for label in ("진단", "비교", "준비"))
    assert html.count("data-v5-review-lens") == 5
    assert 'role="radiogroup"' in html
    assert "운영 기간" not in html and "operation-years" not in html
    assert "거래내역 파일" in html and "대출 파일, 선택" in html
    assert "v5-review-plan" in html
    assert "v5-skip-questions" not in html and "policy-questionnaire" not in html
    assert "정책마다 필요한 답변은 준비 화면에서 바로 선택합니다" in html
    assert "v5-extension.js" in html and "v4-extension.js" not in html
    assert re.search(r'<details[^>]*class="presentation-presets"[^>]*id="presentation-presets"[^>]*hidden', html)


def test_compatibility_routes_templates_and_removed_routes() -> None:
    assert V5.get("/static/templates/거래내역_입력양식.csv").status_code == 200
    assert V5.get("/static/templates/대출_입력양식.csv").status_code == 200
    assert V5.get("/api/v1/catalog/area-map").status_code == 200
    assert V5.post("/api/v5/action-brief", json={}).status_code == 404
    assert V5.post("/api/v5/application/plan", json={}).status_code == 404
    assert V5.post("/api/v5/application/draft", json={}).status_code == 404
    response = V5.post(
        "/api/v1/cashflow/csv",
        json={
            "reference_date": "2026-09-01",
            "opening_cash": 5_000_000,
            "safe_cash_threshold": 0,
            "events_csv": "거래번호,거래일,구분,금액(만원),비용종류,메모\n매출-1,2026-09-02,매출입금,100,,카드매출\n",
            "loans_csv": "",
        },
    )
    assert response.status_code == 200, response.text


def test_orchestration_requires_strict_review_lens_schema() -> None:
    missing = V5.post("/api/v5/orchestrate", json={"comparison": comparison_payload()})
    assert missing.status_code == 422
    invalid = V5.post("/api/v5/orchestrate", json=orchestrate_payload("unknown"))
    assert invalid.status_code == 422
    extra = orchestrate_payload()
    extra["unapproved_field"] = True
    assert V5.post("/api/v5/orchestrate", json=extra).status_code == 422


def test_orchestration_returns_policy_specific_preparation_choices_without_upfront_gate() -> None:
    response = V5.post("/api/v5/orchestrate", json=orchestrate_payload())
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["v3"]["version"] == "v5-api-v1.0"
    assert body["v3"]["question_state"]["batch_limit"] == 0
    assert body["v3"]["question_state"]["max_rounds"] == 0
    assert body["v3"]["question_state"]["display_location"] == "selected_policy_preparation"
    assert body["v3"]["next_questions"] == []
    assert body["next_question"] is None
    assert body["question_trace"] is None
    assert body["review_plan"]["review_lens"] == "debt_relief"
    assert body["review_plan"]["requires_confirmation"] is False
    assert len(body["detected_signals"]) == 7
    assert all(item["display_text"].strip() for item in body["detected_signals"])
    raw_signal_keys = {item["key"] for item in body["detected_signals"]}
    assert all(key not in body["review_plan"]["summary"] for key in raw_signal_keys)
    raw_mechanisms = {"cost_reduction", "cost_offset", "refinance", "new_loan", "mixed", "other"}
    assert all(
        mechanism not in item["review_reason"]
        for item in body["review_order"]
        for mechanism in raw_mechanisms
    )
    assert len(body["tool_execution_trace"]) == 5
    assert all(item["status"] in {"success", "fallback", "fail_closed"} for item in body["tool_execution_trace"])
    candidates = body["policy_discovery"]["candidates"]
    preparation_questions = [
        question
        for candidate in candidates
        for question in candidate["preparation_questions"]
    ]
    assert preparation_questions
    assert all(question["policy_ids"] == [candidate["policy_id"]] for candidate in candidates for question in candidate["preparation_questions"])


def test_unsure_lens_requires_user_confirmation() -> None:
    unresolved = V5.post("/api/v5/orchestrate", json=orchestrate_payload("unsure"))
    assert unresolved.status_code == 200, unresolved.text
    body = unresolved.json()
    assert body["review_plan"]["requires_confirmation"] is True
    suggestion = body["review_plan"]["suggested_review_lens"]
    assert suggestion in {"cash_runway", "debt_relief", "fixed_cost", "policy_choice"}
    assert body["next_question"] is None
    assert body["review_order"] == []
    confirmed = V5.post(
        "/api/v5/orchestrate",
        json=orchestrate_payload(
            "unsure",
            review_lens_source="confirmed_suggestion",
            confirmed_review_lens=suggestion,
        ),
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["review_plan"]["requires_confirmation"] is False
    assert confirmed.json()["review_plan"]["review_lens"] == suggestion


def test_review_lens_does_not_change_financial_authority_hashes() -> None:
    cash = V5.post("/api/v5/orchestrate", json=orchestrate_payload("cash_runway"))
    debt = V5.post("/api/v5/orchestrate", json=orchestrate_payload("debt_relief"))
    assert cash.status_code == debt.status_code == 200
    cash_body, debt_body = cash.json(), debt.json()
    assert cash_body["authority_invariants"] == debt_body["authority_invariants"]
    assert cash_body["metric_order"] != debt_body["metric_order"]
    assert {item["policy_id"] for item in cash_body["review_order"]} == {
        item["policy_id"] for item in debt_body["review_order"]
    }


def test_legacy_question_round_never_reopens_an_upfront_question_gate() -> None:
    for round_number in (0, 1, 2):
        body = V5.post(
            "/api/v5/orchestrate",
            json=orchestrate_payload(asked_fields=["business_scale"], question_round=round_number),
        ).json()
        assert body["next_question"] is None
        assert body["v3"]["next_questions"] == []
        assert body["v3"]["question_state"]["batch_size"] == 0
        assert body["v3"]["question_state"]["max_rounds"] == 0


def test_review_lens_oracle_cases_are_25_of_25() -> None:
    payload = json.loads((EVALUATION / "review_lens_cases.json").read_text(encoding="utf-8"))
    cases = payload["cases"]
    assert len(cases) == 25
    for case in cases:
        candidates = case.get("candidates", payload["candidate_profiles"][case["candidate_profile"]])
        rows = order_policy_reviews(
            candidates,
            case["selected_policy_ids"],
            case["effective_review_lens"],
            case.get("ordered_alternative_ids", []),
        )
        assert [item.policy_id for item in rows] == case["expected_policy_order"], case["id"]
        assert list(METRIC_ORDER[case["effective_review_lens"]]) == case["expected_metric_order"], case["id"]
        assert (rows[0].policy_id if rows else None) == case["expected_first_policy_id"], case["id"]


def test_preparation_choices_cover_each_candidate_policy_contract() -> None:
    body = V5.post("/api/v5/orchestrate", json=orchestrate_payload()).json()
    candidates = body["policy_discovery"]["candidates"]
    assert candidates
    for candidate in candidates:
        policy_id = candidate["policy_id"]
        questions = candidate["preparation_questions"]
        assert [item["field"] for item in questions] == list(POLICY_FIELDS.get(policy_id, ()))
        assert all(item["policy_ids"] == [policy_id] for item in questions)


def test_user_flow_personas_are_fixed_eight_and_have_safe_oracles() -> None:
    payload = json.loads((EVALUATION / "user_flow_personas.json").read_text(encoding="utf-8"))
    personas = payload["personas"]
    assert len(personas) == 8
    assert {item["id"] for item in personas} == {f"persona-{index:02d}" for index in range(1, 9)}
    assert all(item["comparison_reachable"] is True for item in personas)
    assert all(item["forbidden_financial_claim_expected"] is False for item in personas)


def test_notice_cache_is_v5_only_and_priority_is_single_next_field() -> None:
    cache_path = str(NOTICE_EXTRACTION_CACHE_PATH).replace("\\", "/")
    assert cache_path.endswith("/v5/runtime/notice_extraction_cache.sqlite")
    assert "/v4/" not in cache_path
    body = V5.post("/api/v5/orchestrate", json=orchestrate_payload("fixed_cost")).json()
    priority = body["notice_field_priority"]
    assert [item["position"] for item in priority] == [1, 2, 3, 4, 5, 6]
    assert priority[0]["key"] == "application_period"
    extension = (ROOT / "v5/static/v5-extension.js").read_text(encoding="utf-8")
    assert "v5-next-notice" in extension
    assert "다음 확인 1개" in extension
    assert "이 정책의 공고 항목" in extension
    assert "정책 개수가 아닙니다" in extension


def test_selected_policy_and_amount_graph_limit_remains_three_across_versions() -> None:
    sources = [
        (ROOT / "app/static/app.js").read_text(encoding="utf-8"),
        (ROOT / "v3/static/app.js").read_text(encoding="utf-8"),
        (ROOT / "v4/static/app.js").read_text(encoding="utf-8"),
        (ROOT / "v5/static/app.js").read_text(encoding="utf-8"),
    ]
    assert all("selectedPolicyIds.size >= 3" in source for source in sources)
    assert "item.alternative_id === \"no_action\" || selectedAlternativeIds.has(item.alternative_id)" in sources[-1]


def test_notice_evidence_validation_fails_closed_per_field() -> None:
    assert _canonical_notice_evidence("국세청 과세정보\n활용") == _canonical_notice_evidence("국세청과세정보 활용")
    assert _canonical_notice_evidence("25만원") != _canonical_notice_evidence("35만원")
    chunk = PolicyChunk(
        policy_id="POL_TEST",
        policy_version="2026",
        chunk_id="POL_TEST::chunk::001",
        source_type="official_notice_test",
        source_path="test.txt",
        source_url="https://example.org/test",
        page_or_section="공고",
        effective_from=None,
        effective_to=None,
        retrieved_at=date(2026, 8, 15),
        content_hash=content_hash("공고일 2026년 1월 2일 문의 1533-0600"),
        text="공고일 2026년 1월 2일 문의 1533-0600",
    )
    empty = {"status": "not_found", "value": "", "items": [], "evidence": []}
    output = NoticeLunaOutput.model_validate(
        {
            "publication_date": {
                "status": "found",
                "value": "2026년 1월 2일",
                "items": [],
                "evidence": [{"chunk_id": chunk.chunk_id, "quote": "공고일 2026년 1월 2일"}],
            },
            "application_period": empty,
            "application_path": empty,
            "financing_terms": empty,
            "required_documents": empty,
            "contact": {
                "status": "found",
                "value": "1533-0600, 1357",
                "items": [],
                "evidence": [{"chunk_id": chunk.chunk_id, "quote": "문의 1533-0600"}],
            },
        }
    )
    fields = {field["key"]: field for field in _validated_notice_fields(output, [chunk])}
    assert fields["publication_date"]["status"] == "found"
    assert fields["contact"]["status"] == "not_found"
    assert fields["contact"]["validation_status"] == "evidence_validation_failed"


def test_frontend_uses_v5_session_api_and_no_long_term_storage() -> None:
    app_js = (ROOT / "v5/static/app.js").read_text(encoding="utf-8")
    html = (ROOT / "v5/static/index.html").read_text(encoding="utf-8")
    extension = (ROOT / "v5/static/v5-extension.js").read_text(encoding="utf-8")
    css = (ROOT / "v5/static/v5-extension.css").read_text(encoding="utf-8")
    assert "/api/v5/orchestrate" in app_js
    assert "/api/v4/" not in app_js and "/api/v4/" not in extension
    assert "buttimaiv5:session:v1" in extension
    assert "sessionStorage" in extension and "localStorage" not in extension
    assert "?demo=1" not in app_js
    assert 'URLSearchParams(window.location.search).get("demo") === "1"' in extension
    assert "reviewLens" in extension and "questionTrace" in extension
    assert ".v5-review-plan" in css and ".v5-next-notice" in css
    assert "이번 선택이 실제로 바꾼 순서" not in extension
    assert "질문 기준" not in html and "질문 기준" not in extension
    assert "data-v5-policy-answer" in extension
    assert "applyV5PreparationAnswer" in extension
    assert "선택하면 자격 상태와 계산 가능한 정책 효과를 바로 다시 확인합니다" in html
    assert "v5-inline-spinner" in extension and "v5-inline-spinner" in css
    assert "AI가 공고를 확인하는 중" in extension
    assert "여기서 확인할 내용은 모두 끝났습니다" in extension
    assert "신청이 완료된 것은 아닙니다" in extension
    assert "현재 접수 여부 확인" in extension and "다른 정책과 다시 비교" in extension
    assert "analyzed_chunk_count" not in extension
    assert "sourceDigest" not in extension
    assert "원문 ${" not in extension
    ids = set(re.findall(r'id="([A-Za-z0-9_-]+)"', html))
    referenced = set(re.findall(r'byId\("([A-Za-z0-9_-]+)"\)', app_js + extension))
    assert not (referenced - ids - {"v5-next-notice-title"}), sorted(referenced - ids)


def test_forbidden_financial_claims_are_absent_from_user_facing_v5() -> None:
    text = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in ("v5/static/index.html", "v5/static/app.js", "v5/static/v5-extension.js", "v5/README.md")
    )
    forbidden = (
        "AI가 가장 좋은 정책을 추천합니다",
        "승인 가능성이 높습니다",
        "이 정책을 받게 됩니다",
        "폐업을 예측합니다",
        "개인 매출을 예측합니다",
        "정책 효과가 보장됩니다",
        "실시간 최신 공고입니다",
        "신청 자격이 확정되었습니다",
        "AI가 금융 결정을 내립니다",
        "여러 에이전트가 토론해 최적 답을 찾았습니다",
    )
    assert all(claim not in text for claim in forbidden)


def test_v4_sources_still_match_v5_copy_baseline() -> None:
    baseline = (ROOT / "v5/V4_COPY_BASELINE_SHA256.md").read_text(encoding="utf-8")
    rows = re.findall(r"\| `([^`]+)` \| `([0-9a-f]{64})` \|", baseline)
    assert len(rows) == 16
    for relative_path, expected_hash in rows:
        actual_hash = hashlib.sha256((ROOT / "v4" / relative_path).read_bytes()).hexdigest()
        assert actual_hash == expected_hash, relative_path
