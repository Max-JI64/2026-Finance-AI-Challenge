import json
import sqlite3
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from app.main import app
from src.cashflow.quick_mode import QuickModeInput, build_quick_schedules
from src.rag.local_db import DATABASE_PATH, SQLitePolicySearchIndex
from src.rag.luna_client import explain_with_luna


client = TestClient(app)


def sample_request(**overrides):
    payload = {
        "sample_id": "declining_cash_shortage",
        "direct_shock_13_week_percent": -12,
        "direct_shock_6_month_percent": -18,
        "safe_cash_override": None,
        "goal": "최소부채",
    }
    payload.update(overrides)
    return payload


def test_re8_health_contract_and_catalogs() -> None:
    health = client.get("/health").json()
    contract = client.get("/api/v1/service-contract").json()
    areas = client.get("/api/v1/catalog/areas").json()
    industries = client.get("/api/v1/catalog/industries").json()
    policies = client.get("/api/v1/catalog/policies").json()

    assert health["status"] == "ok"
    assert health["versions"]["rag_engine"] == "re8.2-sqlite-hybrid-v1"
    assert contract["service_name"] == "정책금융 영향 시뮬레이터"
    assert any("승인확률" in item for item in contract["does_not"])
    assert areas["items"] and industries["items"]
    assert len(policies["items"]) == 17


def test_sample_comparison_is_deterministic_and_numbers_agree() -> None:
    first = client.post("/api/v1/alternatives/compare", json=sample_request())
    second = client.post("/api/v1/alternatives/compare", json=sample_request())
    assert first.status_code == 200
    assert second.status_code == 200
    left = first.json()
    right = second.json()
    left.pop("request_id")
    right.pop("request_id")
    assert left == right

    no_action = next(
        item for item in left["intervention_results"] if item["alternative_id"] == "no_action"
    )
    assert no_action["weekly_13"][-1]["closing_cash"] == no_action["metrics"]["week13_ending_cash"]
    assert no_action["monthly_6"][-1]["closing_cash"] == no_action["metrics"]["month6_ending_cash"]
    assert left["comparison_result"]["selected_goal"] == "최소부채"
    assert left["sample"]["is_synthetic"] is True


def test_direct_shock_and_goal_change_recompute_result() -> None:
    base = client.post("/api/v1/alternatives/compare", json=sample_request()).json()
    recovery = client.post(
        "/api/v1/alternatives/compare",
        json=sample_request(
            direct_shock_13_week_percent=-2,
            direct_shock_6_month_percent=-3,
            goal="최장생존",
        ),
    ).json()
    base_no_action = next(item for item in base["intervention_results"] if item["alternative_id"] == "no_action")
    recovery_no_action = next(item for item in recovery["intervention_results"] if item["alternative_id"] == "no_action")
    assert recovery_no_action["metrics"]["week13_ending_cash"] > base_no_action["metrics"]["week13_ending_cash"]
    assert recovery["comparison_result"]["selected_goal"] == "최장생존"


def test_high_debt_sample_uses_official_partial_refinance_cap() -> None:
    response = client.post(
        "/api/v1/alternatives/compare",
        json=sample_request(sample_id="stable_high_debt"),
    )
    assert response.status_code == 200
    payload = response.json()
    refinance = next(
        item
        for item in payload["intervention_results"]
        if item["alternative_id"] == "refinance"
    )
    assert refinance["metrics"]["refinanced_principal"] == 50_000_000
    assert refinance["metrics"]["net_new_borrowing"] == 0
    assert any(
        item["field"] == "existing_refinanced_loan"
        and "부분대환" in item["reason"]
        for item in refinance["assumption_ledger"]
    )


def test_quick_input_runs_full_comparison_and_allows_zero_existing_debt() -> None:
    quick = {
        "reference_date": "2026-09-01",
        "opening_cash": 3000000,
        "safe_cash_threshold": 2000000,
        "monthly_revenue": 5000000,
        "recent_monthly_revenues": None,
        "revenue_receipt_day": 25,
        "monthly_rent": 1200000,
        "rent_payment_day": 5,
        "monthly_labor_cost": 1700000,
        "labor_payment_day": 5,
        "monthly_variable_cost": 800000,
        "variable_cost_rate_percent": None,
        "variable_cost_payment_day": 5,
        "other_fixed_costs": [],
        "total_loan_balance": 0,
        "monthly_debt_payment": 0,
        "debt_payment_day": 5,
    }
    response = client.post(
        "/api/v1/alternatives/compare",
        json=sample_request(simple_input=quick, assume_conditional=False),
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["sample"]["is_synthetic"] is False
    assert "일정 보완 입력" in payload["sample"]["input_precision"]
    assert not any(item["alternative_id"] == "refinance" for item in payload["intervention_results"])
    conditional = [
        item for item in payload["intervention_results"] if item["candidate_state"] == "확인 후 비교"
    ]
    assert conditional and all(item["simulated"] is False for item in conditional)


def test_approved_quick_mode_builds_conservative_central_favorable_dates() -> None:
    quick = QuickModeInput(
        reference_date="2026-09-01",
        opening_cash=1_000_000,
        safe_cash_threshold=2_000_000,
        monthly_revenue=3_500_000,
        revenue_timing="month_end",
        monthly_rent=1_500_000,
        monthly_labor_cost=2_200_000,
        monthly_variable_cost=900_000,
        expense_timing="early",
        total_loan_balance=30_000_000,
        annual_interest_rate_percent=12,
        remaining_term_months=60,
        debt_timing="early",
    )
    schedules = build_quick_schedules(quick)
    assert set(schedules) == {"conservative", "central", "favorable"}

    def first_day(scenario: str, prefix: str) -> int:
        event = next(
            item for item in schedules[scenario].events if prefix in item.event_id
        )
        return event.event_date.day

    assert [first_day(name, "revenue") for name in schedules] == [30, 25, 21]
    assert [first_day(name, "rent") for name in schedules] == [1, 5, 10]
    assert [schedules[name].loans[0].payment_day for name in schedules] == [1, 5, 10]


def test_quick_mode_api_returns_range_and_uses_central_for_policy_comparison() -> None:
    quick = {
        "reference_date": "2026-09-01",
        "opening_cash": 1000000,
        "safe_cash_threshold": 2000000,
        "monthly_revenue": 3500000,
        "revenue_timing": "month_end",
        "monthly_rent": 1500000,
        "monthly_labor_cost": 2200000,
        "monthly_variable_cost": 900000,
        "expense_timing": "early",
        "total_loan_balance": 30000000,
        "annual_interest_rate_percent": 12,
        "remaining_term_months": 60,
        "debt_timing": "early",
    }
    response = client.post(
        "/api/v1/alternatives/compare",
        json=sample_request(quick_input=quick),
    )
    payload = response.json()
    assert response.status_code == 200
    assert set(payload["quick_mode_range"]) == {"conservative", "central", "favorable"}
    assert payload["baseline_cashflow"] == payload["quick_mode_range"]["central"]
    assert "보수적-기준-완화" in payload["sample"]["input_precision"]


def test_csv_baseline_uses_in_memory_text() -> None:
    response = client.post(
        "/api/v1/cashflow/csv",
        json={
            "reference_date": "2026-09-01",
            "opening_cash": 2000000,
            "safe_cash_threshold": 1000000,
            "events_csv": (
                "event_id,event_date,event_type,amount,expense_type,description\n"
                "sale-1,2026-09-10,operating_inflow,3000000,,매출\n"
                "rent-1,2026-09-05,fixed_cost,1000000,rent,임대료\n"
            ),
            "loans_csv": "",
        },
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["input_precision"] == "상세 CSV 지급일정 기반"
    assert payload["baseline_cashflow"]["weekly_13"]


def test_korean_csv_template_is_accepted() -> None:
    response = client.post(
        "/api/v1/cashflow/csv",
        json={
            "reference_date": "2026-09-01",
            "opening_cash": 2_000_000,
            "safe_cash_threshold": 0,
            "events_csv": (
                "거래번호,거래일,구분,금액,비용종류,메모\n"
                "매출-1,2026-09-10,매출입금,3000000,,카드매출\n"
                "임대료-1,2026-09-05,고정비,1000000,임대료,9월 임대료\n"
            ),
            "loans_csv": (
                "대출명,잔액,연이율,상환방식,상환일,만기일,거치개월\n"
                "대출-1,10000000,5.2,원리금균등,25,2028-09-25,0\n"
            ),
        },
    )
    assert response.status_code == 200
    assert response.json()["baseline_cashflow"]["debt_summary"]["initial_principal"] == 10_000_000


def test_utf8_sig_ten_thousand_won_templates_are_accepted() -> None:
    response = client.post(
        "/api/v1/cashflow/csv",
        json={
            "reference_date": "2026-09-01",
            "opening_cash": 2_000_000,
            "safe_cash_threshold": 0,
            "events_csv": (
                "\ufeff거래번호,거래일,구분,금액(만원),비용종류,메모\n"
                "매출-1,2026-09-10,매출입금,300,,카드매출\n"
                "임대료-1,2026-09-05,고정비,100,임대료,9월 임대료\n"
            ),
            "loans_csv": (
                "\ufeff대출명,잔액(만원),연이율,상환방식,상환일,만기일,거치개월\n"
                "대출-1,1000,5.2,원리금균등,25,2028-09-25,0\n"
            ),
        },
    )
    assert response.status_code == 200
    assert response.json()["baseline_cashflow"]["debt_summary"]["initial_principal"] == 10_000_000


def test_download_templates_are_utf8_sig_and_use_ten_thousand_won() -> None:
    for name, header in (
        ("거래내역_입력양식.csv", "금액(만원)"),
        ("대출_입력양식.csv", "잔액(만원)"),
    ):
        response = client.get(f"/static/templates/{name}")
        assert response.status_code == 200
        assert response.content.startswith(b"\xef\xbb\xbf")
        assert header in response.content.decode("utf-8-sig")


def test_area_map_catalog_has_current_service_points() -> None:
    payload = client.get("/api/v1/catalog/area-map").json()
    items = payload["items"]
    assert len(items) == 1596
    assert len({item["district"] for item in items}) == 25
    assert all(37 < item["latitude"] < 38 for item in items)
    assert all(126 < item["longitude"] < 128 for item in items)
    assert all(item["area_m2"] > 0 and item["radius_m"] > 0 for item in items)
    assert all(item["administrative_dong"] for item in items)


def test_re5_market_scenarios_are_exposed_for_known_pair() -> None:
    response = client.get("/api/v1/market-scenarios/3001491/CS100001")
    payload = response.json()["market_scenario"]
    assert response.status_code == 200
    assert payload["available"] is True
    assert payload["reference_period"] == "20254"
    assert set(payload["scenarios"]) == {"downside", "central", "recovery"}
    for horizon in ("thirteen_week_percent", "six_month_percent"):
        assert payload["scenarios"]["downside"][horizon] <= payload["scenarios"]["central"][horizon]
        assert payload["scenarios"]["central"][horizon] <= payload["scenarios"]["recovery"][horizon]


def test_compare_returns_all_market_cash_paths_with_fixed_safe_cash() -> None:
    response = client.post(
        "/api/v1/alternatives/compare",
        json=sample_request(area_code="3001491", industry_code="CS100001"),
    )
    assert response.status_code == 200
    market_rows = response.json()["market_scenario_comparison"]
    assert [item["scenario"] for item in market_rows] == ["downside", "central", "recovery"]
    assert len({item["week13_ending_cash"] for item in market_rows}) == 3
    assert len({item["month6_ending_cash"] for item in market_rows}) == 3
    assert len({item["safe_cash_suggested_amount"] for item in market_rows}) == 1


def test_recent_month_revenues_use_rounded_average() -> None:
    quick = QuickModeInput(
        reference_date="2026-09-01",
        opening_cash=1_000_000,
        safe_cash_threshold=0,
        recent_monthly_revenues=[3_000_000, 4_000_000, 5_000_001],
        revenue_timing="month_end",
        monthly_rent=0,
        monthly_labor_cost=0,
        monthly_variable_cost=0,
        expense_timing="early",
        total_loan_balance=0,
        annual_interest_rate_percent=0,
        remaining_term_months=1,
        debt_timing="early",
    )
    assert quick.resolved_monthly_revenue() == 4_000_000


def test_public_response_hides_internal_retrieval_fields() -> None:
    payload = client.post("/api/v1/alternatives/compare", json=sample_request()).text
    assert "chunk_id" not in payload
    assert "bm25_score" not in payload.lower()
    assert "search_rank" not in payload
    assert "sk-proj" not in payload


def test_unsupported_area_returns_sanitized_error() -> None:
    response = client.post(
        "/api/v1/alternatives/compare",
        json=sample_request(area_code="NOT-A-REAL-AREA"),
    )
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_request"
    assert "NOT-A-REAL-AREA" not in response.text


def test_local_policy_database_contains_only_frozen_chunks() -> None:
    assert DATABASE_PATH.is_file()
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        chunk_count = connection.execute("SELECT COUNT(*) FROM policy_chunks").fetchone()[0]
        policy_count = connection.execute("SELECT COUNT(DISTINCT policy_id) FROM policy_chunks").fetchone()[0]
        embedding_count = connection.execute("SELECT COUNT(*) FROM policy_embeddings").fetchone()[0]
        embedding_specs = connection.execute(
            "SELECT model, MIN(dimensions), MAX(dimensions), COUNT(*) "
            "FROM policy_embeddings GROUP BY model ORDER BY model"
        ).fetchall()
        html_chunk_count = connection.execute(
            "SELECT COUNT(*) FROM policy_chunks WHERE lower(source_path) LIKE '%.html'"
        ).fetchone()[0]
        source_modes = {
            row[0] for row in connection.execute("SELECT DISTINCT ingestion_mode FROM policy_sources")
        }
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        connection.close()
    assert chunk_count == 817
    assert policy_count == 17
    assert embedding_count == 1634
    assert embedding_specs == [
        ("text-embedding-3-large", 3072, 3072, 817),
        ("text-embedding-3-small", 1536, 1536, 817),
    ]
    assert html_chunk_count == 0
    assert source_modes == {"markdown_body_html_link_only"}
    assert tables == {"metadata", "policy_sources", "policy_chunks", "policy_embeddings"}


def test_policy_pdf_pipeline_is_text_only() -> None:
    source = (Path("scripts/extract_re_stage2_policy_docs.py")).read_text(encoding="utf-8")
    assert "PdfReader" in source
    assert "page.extract_text()" in source
    assert "fitz" not in source
    assert "get_pixmap" not in source
    assert "contact_sheet" not in source


def test_local_retrieval_is_deterministic() -> None:
    index = SQLitePolicySearchIndex()
    first = index.search("지원금 지급 신청", policy_id="POL_SEOUL_CRISIS_TRACK2_2026H2")
    second = index.search("지원금 지급 신청", policy_id="POL_SEOUL_CRISIS_TRACK2_2026H2")
    assert first
    assert [(item.chunk.chunk_id, item.score) for item in first] == [
        (item.chunk.chunk_id, item.score) for item in second
    ]


def test_ai_endpoint_keeps_local_fallback_without_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = client.post(
        "/api/v1/ai/ask",
        json={
            "policy_id": "POL_SEOUL_CRISIS_TRACK2_2026H2",
            "question": "지원금 지급 방식은 무엇인가요?",
        },
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["answer_source"] == "local_fallback"
    assert payload["fact_lock_status"] == "not_called"
    assert payload["official_evidence"]
    assert "chunk_id" not in response.text


def test_luna_fact_lock_accepts_grounded_answer_and_discards_new_number(monkeypatch) -> None:
    index = SQLitePolicySearchIndex()
    evidence = index.search("지원금 신청", policy_id="POL_SEOUL_CRISIS_TRACK2_2026H2", top_k=2)
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-not-a-real-secret")

    allowed_number = next(iter(__import__("re").findall(r"\d[\d,.%]*", " ".join(item.chunk.text for item in evidence))), None)
    grounded_text = "공식 근거 범위에서 신청 조건을 확인해야 합니다."
    if allowed_number:
        grounded_text += f" 근거에는 {allowed_number} 값이 포함됩니다."

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["model"] == "gpt-5.6-luna"
        assert body["store"] is False
        return httpx.Response(200, json={"output": [{"content": [{"type": "output_text", "text": grounded_text}]}]})

    passed = explain_with_luna("신청 조건은?", evidence, transport=httpx.MockTransport(handler))
    assert passed.source == "openai"
    assert passed.fact_lock_status == "passed"

    def bad_handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"output": [{"content": [{"type": "output_text", "text": "지원금은 987654321원입니다."}]}]})

    discarded = explain_with_luna("지원금은?", evidence, transport=httpx.MockTransport(bad_handler))
    assert discarded.source == "local_fallback"
    assert discarded.fact_lock_status == "discarded"


def test_validation_response_does_not_echo_sensitive_input() -> None:
    marker = "991122-sensitive-marker"
    response = client.post(
        "/api/v1/policies/eligibility",
        json={"profile": {"region": marker, "employee_count": -1}},
    )
    assert response.status_code == 422
    assert marker not in response.text


def test_web_has_four_user_steps_map_and_no_design_dash() -> None:
    html = client.get("/").text
    for screen in ("business", "finance", "diagnosis", "decision"):
        assert f'id="{screen}"' in html
    assert 'id="area-map"' in html
    assert 'id="dong-select"' in html
    assert 'id="industry-major-select"' in html
    assert html.count('data-preset=') == 5
    assert '<details class="presentation-presets"' in html
    assert html.count('data-question-example=') == 5
    assert 'id="execution-section"' not in html
    assert "데모" not in html
    assert "샘플" not in html
    assert "—" not in html
    assert "–" not in html


def test_map_keeps_level_layers_and_permanent_group_labels() -> None:
    html = client.get("/").text
    javascript = client.get("/static/app.js").text
    styles = client.get("/static/styles.css").text
    assert "구·동 이름, 상권 수와 개별 상권명이 항상 표시" in html
    assert "aggregateDongs(items)" in javascript
    assert 'item.district === district' in javascript
    assert 'if (zoom <= 12)' in javascript
    assert 'resetMapToSeoul(false)' in javascript
    assert "nearestAreaToMapCenter" in javascript
    assert "renderDongCircles(false, nearest.district)" in javascript
    assert 'className: `map-circle-label map-circle-label--${level}`' in javascript
    assert 'className: "map-circle-label map-circle-label--area"' in javascript
    assert "if (query) return state.areaPoints.filter" in javascript
    assert html.index('id="area-search"') < html.index('id="district-select"')
    assert "evidenceLinks(payload.official_evidence)" in javascript
    assert 'runComparison("diagnosis", false)' in javascript
    assert 'state.revenueMonths: 6' not in javascript
    assert 'revenueMonths: 6' in javascript
    assert 'result.scrollIntoView({ behavior: "smooth", block: "start" })' in javascript
    assert 'questionExample.dataset.questionExample' in javascript
    assert 'id="chat-thread"' in html
    assert 'id="chat-question"' in html
    assert 'id="chat-send"' in html
    assert "state.chatTurns >= 5" in javascript
    assert "state.chatMessages.slice(-8)" in javascript
    assert "localStorage" not in javascript
    assert "sessionStorage" not in javascript
    assert 'scenario-chart-legend' in styles
    assert 'is-scenario-sensitive' in styles
    assert 'byId("alternative-dialog").addEventListener("click"' in javascript
    assert "if (!inside) dialog.close()" in javascript
    assert 'if (zoom <= 14)' in javascript
    assert 'if (zoom <= 16)' in javascript
    assert 'selectArea(nearest.code, false, true, false)' in javascript
    assert 'id="ranking-notice"' in html
    assert "renderRankingNotice(alternatives, top)" in javascript
    assert "state.selectedAlternative" in javascript
    assert "goalPresentations" in javascript
    assert "ordered_alternative_ids" in javascript
    assert "이 대안에서 확인할 사항" in javascript
    assert "현재 목표 순위" in html
    assert "map-circle-label" in styles
    for retired_color in ("#a83b23", "#ee6b45", "#b93961", "#ef7898", "#8f2046", "#ba3159", "#d94772", "#f48ba8"):
        assert retired_color not in javascript


def test_request_size_limit() -> None:
    response = client.post(
        "/api/v1/ai/ask",
        content=b"{}",
        headers={"content-type": "application/json", "content-length": str(2 * 1024 * 1024 + 1)},
    )
    assert response.status_code == 413
