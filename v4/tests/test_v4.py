from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from app.main import app as v2_app
from src.rag.policy_index import PolicyChunk, content_hash
from v4.copilot import (
    NoticeExtractionRequest,
    NoticeLunaOutput,
    _NOTICE_EXTRACTION_CACHE,
    _canonical_notice_evidence,
    _validated_notice_fields,
    extract_notice_with_luna,
)
from v4.main import app as v4_app


ROOT = Path(__file__).resolve().parents[2]
v4 = TestClient(v4_app)
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
            "recent_monthly_revenues": [7_000_000, 7_600_000, 8_200_000, 8_800_000, 9_400_000, 10_000_000],
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


def test_v4_is_independent_and_v2_health_is_preserved() -> None:
    health = v4.get("/health")
    assert health.status_code == 200
    assert health.json()["version"] == "v4-api-v1.0"
    assert health.json()["session_persistence"] == "browser_session_only"
    assert health.json()["notice_extraction_cache"] == "local_persistent_public_notice_only"
    assert health.json()["application_document_upload"] == "not_supported"
    assert v2.get("/health").json()["versions"]["api"] == "v2-api-v1.0"


def test_root_has_five_stages_and_preserves_csv_input() -> None:
    html = v4.get("/").content.decode("utf-8")
    assert html.count('class="step-button') == 5
    assert "정책 비교·선택" in html
    assert "신청 준비" in html
    assert "data-v4-concern" in html
    assert html.count("data-v4-concern") == 5
    assert 'class="v3-assistant-panel" hidden' in html
    assert "거래내역 파일" in html and "대출 파일, 선택" in html
    assert "여러 재무값을 문장으로 붙여넣기" not in html
    assert 'class="v4-no-loan"' in html
    assert "v4-input-ledger" in html
    assert "v4-extension.js" in html


def test_csv_templates_and_compatibility_route_remain_available() -> None:
    assert v4.get("/static/templates/거래내역_입력양식.csv").status_code == 200
    assert v4.get("/static/templates/대출_입력양식.csv").status_code == 200
    assert v4.get("/api/v1/catalog/area-map").status_code == 200
    response = v4.post(
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


def test_removed_structured_input_has_no_ui_or_api_route() -> None:
    html = v4.get("/").content.decode("utf-8")
    extension = (ROOT / "v4/static/v4-extension.js").read_text(encoding="utf-8")
    css = (ROOT / "v4/static/v4-extension.css").read_text(encoding="utf-8")
    response = v4.post(
        "/api/v4/input/structure",
        json={"text": "현재 현금 500"},
    )
    assert response.status_code == 404
    assert "v4-structured-input" not in html
    assert "structureV4Input" not in extension
    assert ".v4-no-loan input" in css
    assert "width:18px!important" in css


def test_removed_application_plan_and_inquiry_draft_routes_return_404() -> None:
    assert v4.post("/api/v4/application/plan", json={}).status_code == 404
    assert v4.post("/api/v4/application/draft", json={}).status_code == 404


def test_luna_extracts_notice_fields_with_exact_stored_evidence(monkeypatch) -> None:
    output = {
        "publication_date": {
            "status": "found",
            "value": "2026.01.28",
            "items": [],
            "evidence": [{
                "chunk_id": "POL_SEMAS_STABILITY_VOUCHER_2026::chunk::001",
                "quote": "소상공인 경영안정 바우처 지원사업 시행 공고 2026.01.28",
            }],
        },
        "application_period": {
            "status": "found",
            "value": "2026-02-09 09:00 ~ 2026-12-18 18:00",
            "items": [],
            "evidence": [{
                "chunk_id": "POL_SEMAS_STABILITY_VOUCHER_2026::metadata::001",
                "quote": "신청기간: 2026-02-09 09:00 ~ 2026-12-18 18:00",
            }],
        },
        "application_path": {
            "status": "found",
            "value": "https://www.sbiz24.kr",
            "items": [],
            "evidence": [{
                "chunk_id": "POL_SEMAS_STABILITY_VOUCHER_2026::metadata::001",
                "quote": "신청페이지: https://www.sbiz24.kr",
            }],
        },
        "financing_terms": {
            "status": "found",
            "value": "바우처 지원",
            "items": ["소상공인 1개사당 25만원 한도"],
            "evidence": [{
                "chunk_id": "POL_SEMAS_STABILITY_VOUCHER_2026::chunk::002::source::907b7fa9",
                "quote": "지원 금액)소상공인1개사당25만원한도로바우처사용가능",
            }],
        },
        "required_documents": {
            "status": "found",
            "value": "일반 신청은 별도 실물서류 제출 없음",
            "items": [],
            "evidence": [{
                "chunk_id": "POL_SEMAS_STABILITY_VOUCHER_2026::chunk::004",
                "quote": "요건판단은국세청과세정보를활용하므로별도실물서류제출없음",
            }],
        },
        "contact": {
            "status": "found",
            "value": "경영안정 바우처 1533-0600",
            "items": [],
            "evidence": [{
                "chunk_id": "POL_SEMAS_STABILITY_VOUCHER_2026::metadata::001",
                "quote": "문의처: 경영안정 바우처 1533-0600",
            }],
        },
    }
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content.decode("utf-8")))
        sent_input = json.loads(captured["input"])
        chunks = sent_input["untrusted_complete_stored_notice"]
        for field in output.values():
            for evidence in field["evidence"]:
                normalized_quote = " ".join(evidence["quote"].split())
                match = next(
                    item for item in chunks
                    if normalized_quote in " ".join(item["text"].split())
                )
                evidence["chunk_id"] = match["chunk_id"]
        return httpx.Response(
            200,
            json={"output": [{"content": [{"type": "output_text", "text": json.dumps(output, ensure_ascii=False)}]}]},
        )

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.6-luna")
    notice_text = "\n".join(
        evidence["quote"]
        for field in output.values()
        for evidence in field["evidence"]
    )
    chunk = PolicyChunk(
        policy_id="POL_SEMAS_STABILITY_VOUCHER_2026",
        policy_version="2026-01-28",
        chunk_id="POL_SEMAS_STABILITY_VOUCHER_2026::test::001",
        source_type="official_notice_test",
        source_path="test-notice.txt",
        source_url="https://example.org/voucher",
        page_or_section="검수 공고",
        effective_from=None,
        effective_to=None,
        retrieved_at=date(2026, 8, 15),
        content_hash=content_hash(notice_text),
        text=notice_text,
    )
    monkeypatch.setattr("v4.copilot._load_complete_notice", lambda _: ([chunk], "test-digest"))
    _NOTICE_EXTRACTION_CACHE.clear()
    request = NoticeExtractionRequest(
        policy_id="POL_SEMAS_STABILITY_VOUCHER_2026",
        policy_name="소상공인 경영안정 바우처 지원사업",
        policy_version="2026-01-28",
        official_url="https://example.org/voucher",
    )
    result = extract_notice_with_luna(request, transport=httpx.MockTransport(handler))

    assert result["analysis_status"] == "completed", result
    assert result["external_ai_used"] is True
    assert result["analyzed_chunk_count"] == 1
    fields = {field["key"]: field for field in result["fields"]}
    assert fields["publication_date"]["value"] == "2026.01.28"
    assert fields["financing_terms"]["items"] == ["소상공인 1개사당 25만원 한도"]
    assert fields["publication_date"]["evidence"][0]["section"]
    assert captured["store"] is False
    assert captured["text"]["format"]["type"] == "json_schema"
    schema = captured["text"]["format"]["schema"]
    assert schema["properties"]["required_documents"]["properties"]["evidence"]["maxItems"] == 4
    sent_input = json.loads(captured["input"])
    assert len(sent_input["untrusted_complete_stored_notice"]) == 1
    assert "opening_cash" not in captured["input"]
    assert "confirmation" not in captured["input"]


def test_notice_extraction_cache_survives_memory_clear_and_supports_refresh(monkeypatch, tmp_path: Path) -> None:
    chunk = PolicyChunk(
        policy_id="POL_CACHE",
        policy_version="2026",
        chunk_id="POL_CACHE::chunk::001",
        source_type="official_notice_test",
        source_path="cache-test.txt",
        source_url="https://example.org/cache",
        page_or_section="공고",
        effective_from=None,
        effective_to=None,
        retrieved_at=date(2026, 8, 26),
        content_hash=content_hash("공고 게시일 2026년 8월 1일"),
        text="공고 게시일 2026년 8월 1일",
    )
    empty = {"status": "not_found", "value": "", "items": [], "evidence": []}
    output = {
        "publication_date": {
            "status": "found",
            "value": "2026년 8월 1일",
            "items": [],
            "evidence": [{"chunk_id": chunk.chunk_id, "quote": chunk.text}],
        },
        "application_period": empty,
        "application_path": empty,
        "financing_terms": empty,
        "required_documents": empty,
        "contact": empty,
    }
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={"output": [{"content": [{"type": "output_text", "text": json.dumps(output, ensure_ascii=False)}]}]})

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.6-luna")
    monkeypatch.setattr("v4.copilot._load_complete_notice", lambda _: ([chunk], "cache-digest"))
    cache_path = tmp_path / "notice-cache.sqlite"
    request = NoticeExtractionRequest(
        policy_id="POL_CACHE",
        policy_name="캐시 검수 정책",
        policy_version="2026",
        official_url="https://example.org/cache",
    )
    _NOTICE_EXTRACTION_CACHE.clear()
    first = extract_notice_with_luna(
        request,
        transport=httpx.MockTransport(handler),
        cache_path=cache_path,
        persist_cache=True,
    )
    assert first["cache_status"] == "fresh"
    assert cache_path.exists()
    assert calls == 1

    _NOTICE_EXTRACTION_CACHE.clear()
    second = extract_notice_with_luna(
        request,
        transport=httpx.MockTransport(handler),
        cache_path=cache_path,
        persist_cache=True,
    )
    assert second["cache_status"] == "persistent"
    assert calls == 1

    refreshed = extract_notice_with_luna(
        request.model_copy(update={"force_refresh": True}),
        transport=httpx.MockTransport(handler),
        cache_path=cache_path,
        persist_cache=True,
    )
    assert refreshed["cache_status"] == "fresh"
    assert calls == 2


def test_notice_extraction_fails_closed_without_luna_key(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    _NOTICE_EXTRACTION_CACHE.clear()
    response = v4.post(
        "/api/v4/application/notice-extract",
        json={
            "policy_id": "POL_SEMAS_RECHALLENGE_2026",
            "policy_name": "소상공인 재도전특별자금",
            "policy_version": "2026-07-29-change4",
            "official_url": "https://example.org/rechallenge",
            "force_refresh": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["analysis_status"] == "unavailable"
    assert data["external_ai_used"] is False
    assert data["fallback_reason"] == "missing_api_key"
    assert all(field["status"] == "not_found" for field in data["fields"])


def test_notice_evidence_canonicalization_allows_only_ocr_whitespace_difference() -> None:
    assert _canonical_notice_evidence("국세청 과세정보\n활용") == _canonical_notice_evidence("국세청과세정보 활용")
    assert _canonical_notice_evidence("25만원") != _canonical_notice_evidence("35만원")


def test_notice_evidence_failure_closes_only_the_unsupported_field() -> None:
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
    output = NoticeLunaOutput.model_validate({
        "publication_date": {
            "status": "found", "value": "2026년 1월 2일", "items": [],
            "evidence": [{"chunk_id": chunk.chunk_id, "quote": "공고일 2026년 1월 2일"}],
        },
        "application_period": empty,
        "application_path": empty,
        "financing_terms": empty,
        "required_documents": empty,
        "contact": {
            "status": "found", "value": "1533-0600, 1357", "items": [],
            "evidence": [{"chunk_id": chunk.chunk_id, "quote": "문의 1533-0600"}],
        },
    })
    fields = {field["key"]: field for field in _validated_notice_fields(output, [chunk])}
    assert fields["publication_date"]["status"] == "found"
    assert fields["contact"]["status"] == "not_found"
    assert fields["contact"]["validation_status"] == "evidence_validation_failed"


def test_policy_change_applies_only_explicitly_approved_fields() -> None:
    response = v4.post(
        "/api/v4/change/reconcile",
        json={
            "previous": {"deadline": "A", "rate": "4.0"},
            "candidate": {"deadline": "B", "rate": "4.5"},
            "approved_fields": ["deadline"],
        },
    )
    data = response.json()
    assert set(data["detected_changes"]) == {"deadline", "rate"}
    assert set(data["applied_changes"]) == {"deadline"}
    assert data["unapproved_change_count"] == 1
    assert data["requires_recalculation"] is True


def test_orchestration_uses_v4_route_and_preserves_deterministic_engine() -> None:
    response = v4.post(
        "/api/v4/orchestrate",
        json={
            "comparison": comparison_payload(),
            "answered_fields": [],
            "asked_fields": [],
            "situation_context": {
                "original_text": "걱정 버튼: 대출 상환 부담",
                "confirmed_area_code": "3001496",
                "confirmed_industry_code": "CS100001",
                "signals": ["debt_concern"],
                "confirmed_goal": None,
            },
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["v3"]["version"] == "v4-api-v1.0"
    assert data["v3"]["external_ai_used"] is False
    assert data["policy_discovery"]["retrieval_mode"] == "bm25"
    assert data["comparison_result"]["selected_goal"] == "최소부채"


def test_v4_selected_policy_graphs_cover_voucher_refinance_and_rechallenge() -> None:
    policy_ids = [
        "POL_SEMAS_STABILITY_VOUCHER_2026",
        "POL_SEMAS_REFINANCE_2026",
        "POL_SEMAS_RECHALLENGE_2026",
    ]
    comparison = comparison_payload()
    comparison["selected_policy_ids"] = policy_ids
    comparison["conditional_policy_ids"] = policy_ids
    comparison["quick_input"]["total_loan_balance"] = 50_000_000
    comparison["quick_input"]["annual_interest_rate_percent"] = 9
    comparison["existing_loan_rate_percent"] = 9
    response = v4.post(
        "/api/v4/orchestrate",
        json={
            "comparison": comparison,
            "answered_fields": [],
            "asked_fields": [],
            "situation_context": {
                "original_text": "현금 부족과 고금리 대출 상환이 걱정됩니다.",
                "confirmed_area_code": "3001496",
                "confirmed_industry_code": "CS100001",
                "signals": ["cash_concern", "debt_concern"],
                "confirmed_goal": "최소상환",
            },
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()
    alternatives = {item["alternative_id"]: item for item in data["intervention_results"]}
    expected = {
        "dynamic_pol_semas_stability_voucher_2026",
        "conditional_pol_semas_refinance_2026",
        "conditional_pol_semas_rechallenge_2026",
    }
    assert expected.issubset(alternatives)
    assert all(alternatives[item]["ranking_eligible"] is False for item in expected)
    assert alternatives["dynamic_pol_semas_stability_voucher_2026"]["metrics"]["support_or_cost_reduction"] == 250_000
    assert alternatives["conditional_pol_semas_refinance_2026"]["metrics"]["net_new_borrowing"] == 0
    readiness = {
        item["policy_id"]: item["application_readiness"]
        for item in data["policy_discovery"]["candidates"]
        if item["policy_id"] in policy_ids
    }
    assert readiness["POL_SEMAS_STABILITY_VOUCHER_2026"]["conditional_graph_supported"] is True
    assert readiness["POL_SEMAS_REFINANCE_2026"]["conditional_graph_supported"] is True


def test_frontend_uses_session_storage_and_v4_api_only() -> None:
    app_js = (ROOT / "v4/static/app.js").read_text(encoding="utf-8")
    index_html = (ROOT / "v4/static/index.html").read_text(encoding="utf-8")
    extension_js = (ROOT / "v4/static/v4-extension.js").read_text(encoding="utf-8")
    extension_css = (ROOT / "v4/static/v4-extension.css").read_text(encoding="utf-8")
    assert "/api/v3/" not in app_js
    assert "/api/v4/orchestrate" in app_js
    assert "sessionStorage" in extension_js
    assert "localStorage" not in extension_js
    assert "buttimaiv4:session:v3" in extension_js
    assert 'finance.revenues = [...document.querySelectorAll(".revenue-input")].map((node) => node.value)' in extension_js
    assert "const revenueValuesInTenThousandWon = revenueInputs.map((input) => Number(input.value));" in extension_js
    assert "v4-monthly-ledger" in extension_js
    assert ".v4-monthly-ledger" in extension_css
    assert "현재 입력과 가정 적용 후 결과" in app_js
    assert "각 항목의 왼쪽은 현재 입력값으로 계산한 결과" in app_js
    assert "무대응의 결과 차이" not in app_js
    what_if_position = index_html.index('class="v3-what-if-panel v4-what-if-panel"')
    chart_position = index_html.index('id="comparison-panel"')
    focus_position = index_html.index('id="v4-policy-focus"')
    preparation_position = index_html.index('id="preparation"')
    conditions_position = index_html.index('id="v4-policy-conditions"')
    chat_position = index_html.index('id="qa-section"')
    assert what_if_position < chart_position < focus_position < preparation_position < conditions_position < chat_position
    for removed_id in (
        "action-brief-panel",
        "v3-action-plan-panel",
        "goal-selector-panel",
        "ranking-notice",
        "alternative-cards",
        "comparison-detail-table",
        "decision-policy-opportunities",
        "v4-application-launcher",
        "v4-change-panel",
    ):
        assert removed_id not in index_html
    assert 'id="alternative-dialog"' not in index_html
    assert "무대응과 선택 정책의 13주 현금 비교" in index_html
    assert "이 정책을 신청하기 전에 확인할 내용" in index_html
    assert "지원이 어려운 이유와 입력 확인" in app_js
    assert 'data-v4-start-application="${escapeHtml(candidate.policy_id)}"' in app_js
    assert "data-toggle-conditional-policy" not in app_js
    assert "조건부 그래프 제거" not in app_js
    assert "enableSelectedPolicyPreviews" in app_js
    assert "renderV4PolicyConditions" in extension_js
    assert "앞에서 입력한 답변" in extension_js
    assert "입력한 답변 기준 제외조건에 해당하지 않음" in extension_js
    assert "/api/v4/application/plan" not in extension_js
    assert "기존 Rule 결과" not in extension_js
    assert "dynamic_pol_semas_stability_voucher_2026" in app_js
    assert ".v4-policy-deltas" in extension_css
    assert ".v4-policy-metrics" in extension_css
    assert ".v4-condition-answer" in extension_css
    assert 'id="v4-progress"' not in index_html
    assert 'id="v4-task-list"' not in index_html
    assert 'id="v4-notice-review"' in index_html
    assert "data-v4-confirm-notice-field" in extension_js
    assert "noticeFieldConfirmations" in extension_js
    assert ".v4-field-confirm" in extension_css
    assert "신청 준비 내용을 불러오지 못했습니다" in extension_js
    assert "/api/v4/application/notice-extract" in extension_js
    assert "function v4SelectedNoticeCandidates()" in extension_js
    assert "return candidates.slice(0, 3);" in extension_js
    assert 'return !extraction || extraction.analysis_status !== "completed";' in extension_js
    assert "await Promise.all(pending.map(async (candidate)" in extension_js
    assert "저장된 분석 결과를 확인하고 있습니다" in extension_js
    assert "공고가 바뀌었거나 저장된 결과가 없을 때만 Luna가 다시 분석합니다" in extension_js
    assert "force_refresh: true" in extension_js
    assert "공고 다시 분석" in extension_js
    assert "Luna가 추출한 신청 핵심정보" in extension_js
    assert "공고에서 확인되지 않음" in extension_js
    assert "추출 근거 ${field.evidence.length}건 보기" not in extension_js
    assert ".v4-notice-evidence" not in extension_css
    assert ".v4-notice-field-grid" in extension_css
    assert "기관 문의 필요" not in extension_js
    assert "v4-create-draft" not in index_html
    assert "/api/v4/application/draft" not in extension_js
    assert "consent_to_external_ai" not in extension_js
    assert "v4-complete-task" not in index_html
    assert "v4-hold-task" not in index_html
    assert "v4-complete-task" not in extension_js
    assert "v4-hold-task" not in extension_js
    assert ".v4-task-actions" not in extension_css
    assert ".v4-confirmation-form" not in extension_css
    assert ".v4-task-evidence" not in extension_css
    assert ".v4-task-panel" not in extension_css
    assert ".v4-draft-panel" not in extension_css
    assert "v4-draft-question" not in index_html
    assert "기관 문의문 초안 검토" not in extension_js
    assert "var(--primary)" not in extension_css
    assert "var(--ink)" not in extension_css
    assert "v4-demo-document" not in index_html
    assert "v4-demo-fields" not in extension_js
    assert "loadV4DemoDocument" not in extension_js
    assert "verifiedFields" not in extension_js


def test_all_presentation_presets_keep_revenue_values_in_ten_thousand_won() -> None:
    app_js = (ROOT / "v4/static/app.js").read_text(encoding="utf-8")
    preset_block = app_js.split("const presentationPresets = {", 1)[1].split("};", 1)[0]
    expected_revenues = (
        "revenues: [1800, 1780, 1760, 1740, 1710, 1680]",
        "revenues: [1200, 1190, 1210, 1180, 1200, 1190]",
        "revenues: [700, 760, 820, 880, 940, 1000]",
        "revenues: [1000, 1020, 1040, 1060, 1080, 1100]",
        "revenues: [1100, 1120, 1140, 1160, 1180, 1200]",
    )
    assert all(revenues in preset_block for revenues in expected_revenues)
    assert "state.revenueMonths = preset.revenues.length; renderRevenueMonths(preset.revenues);" in app_js
    assert "<b>만원</b>" in app_js


def test_v3_source_hashes_still_match_the_recorded_copy_baseline() -> None:
    expected = {
        "main.py": "a4ef803b650fcdd824dec6762c4c7a8c6e7c6767747b816d81920c338b9099e1",
        "orchestrator.py": "04e3e17baf1668f637dd03249a4eb20293063b34d29705b1c68fb3204339ae31",
        "static/app.js": "5872ba4c13334eaa219c8d0935af00475e3a4c875d8cb3b74ce700b3499c5811",
        "static/index.html": "39332ea2f263496d7e4e9616974c87d294ac5e0507930ad89db974750390af8d",
        "static/styles.css": "83c8d80ab3348382057ed65c3f2c3381daa353760ec230a6b6298d0c2d461c71",
    }
    import hashlib

    for relative, digest in expected.items():
        assert hashlib.sha256((ROOT / "v3" / relative).read_bytes()).hexdigest() == digest
