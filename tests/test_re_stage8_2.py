import hashlib
import sqlite3
from datetime import date
from io import BytesIO
from urllib.error import HTTPError

from fastapi.testclient import TestClient

from app.main import app
from src.rag.hybrid_search import DATABASE_PATH, HybridPolicySearchIndex
from src.rag.openai_embeddings import OpenAIEmbeddingError
from src.rag.openai_embeddings import OpenAIEmbeddingClient
from src.policy.discovery import DiscoveryEligibilityEngine, staged_questions
from src.policy.eligibility import SessionEligibilityProfile
from src.policy.re_stage8_2_events import DynamicPolicyScenario, build_dynamic_policy_plan
from src.policy.schemas import ValueSource
from src.integration.re_stage8 import FINANCIAL_POLICY_NEEDS, _sanitize_external_text
from src.integration.re_stage8 import SampleCompareRequest, _dynamic_policy_alternatives, _load_sample
from scripts.build_re_stage7_examples import build_hero


client = TestClient(app)


def test_markdown_is_canonical_and_html_is_link_only() -> None:
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        sources = connection.execute(
            "SELECT markdown_path, markdown_sha256, html_path, official_url, ingestion_mode "
            "FROM policy_sources"
        ).fetchall()
        metadata = dict(connection.execute("SELECT key, value FROM metadata"))
        html_text_hits = connection.execute(
            "SELECT COUNT(*) FROM policy_chunks WHERE source_type != 'official_user_reviewed_markdown' "
            "OR lower(source_path) LIKE '%.html'"
        ).fetchone()[0]
    finally:
        connection.close()

    assert len(sources) == 17
    assert metadata["canonical_body"] == "user_reviewed_markdown"
    assert metadata["html_body_indexed"] == "false"
    assert html_text_hits == 0
    for markdown_path, stored_hash, _html_path, official_url, mode in sources:
        payload = open(markdown_path, "rb").read()
        assert hashlib.sha256(payload).hexdigest() == stored_hash
        assert official_url.startswith("https://")
        assert mode == "markdown_body_html_link_only"


def test_bm25_search_covers_new_policy_markdown() -> None:
    result = HybridPolicySearchIndex().search(
        "자영업자 고용보험료 실업급여 지원",
        mode="bm25",
        top_k=5,
        max_chunks_per_policy=1,
    )
    assert result.retrieval_mode == "bm25"
    assert "POL_SEMAS_EMPLOYMENT_INSURANCE_2026" in {
        item.chunk.policy_id for item in result.results
    }


def test_new_policy_markdown_and_official_links_are_in_database() -> None:
    expected = {
        "POL_SEOUL_YELLOW_UMBRELLA_2026": "https://news.seoul.go.kr/economy/archives/568855",
        "POL_SEOUL_HOSPITAL_LIVING_EXPENSE_2026": "https://news.seoul.go.kr/economy/archives/508129",
        "POL_SEOUL_PRIVATE_CHILDCARE_2026": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000122913",
        "POL_JUNGGU_CUSTOM_SUPPORT_2026": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000121649",
    }
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        rows = dict(
            connection.execute(
                "SELECT policy_id, official_url FROM policy_sources "
                "WHERE policy_id IN (?, ?, ?, ?)",
                tuple(expected),
            )
        )
    finally:
        connection.close()
    assert rows == expected


def test_chat_default_search_stays_within_business_finance_scope(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_EMBEDDING_MODEL", raising=False)
    response = client.post(
        "/api/v1/ai/ask",
        json={
            "policy_id": None,
            "question": "현재 대출의 이자와 월 상환 부담을 줄일 정책이 있나요?",
            "history": [],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    discovered_ids = {item["policy_id"] for item in payload["discovered_policies"]}
    assert discovered_ids
    assert discovered_ids <= set(FINANCIAL_POLICY_NEEDS)
    assert "POL_SEOUL_HOSPITAL_LIVING_EXPENSE_2026" not in discovered_ids
    assert "POL_SEOUL_PRIVATE_CHILDCARE_2026" not in discovered_ids


def test_chat_rejects_more_than_five_user_questions(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = client.post(
        "/api/v1/ai/ask",
        json={
            "question": "한 번 더 질문할 수 있나요?",
            "history": [
                {"role": "user", "content": f"질문 {index}"}
                for index in range(5)
            ],
        },
    )
    assert response.status_code == 400


def test_hybrid_failure_falls_back_to_bm25(monkeypatch) -> None:
    def fail_embed(*_args, **_kwargs):
        raise OpenAIEmbeddingError("test outage")

    monkeypatch.setattr("src.rag.hybrid_search.OpenAIEmbeddingClient.embed", fail_embed)
    result = HybridPolicySearchIndex().search(
        "고금리 대출을 갈아타고 싶다",
        mode="hybrid",
        model="text-embedding-3-large",
        top_k=5,
    )
    assert result.retrieval_mode == "bm25_fallback"
    assert result.results
    assert result.fallback_reason == "OpenAIEmbeddingError"


def test_compare_exposes_policy_discovery_without_raw_amounts(monkeypatch) -> None:
    def fail_embed(*_args, **_kwargs):
        raise OpenAIEmbeddingError("test outage")

    monkeypatch.setattr("src.rag.hybrid_search.OpenAIEmbeddingClient.embed", fail_embed)
    response = client.post(
        "/api/v1/alternatives/compare",
        json={
            "sample_id": "declining_cash_shortage",
            "direct_shock_13_week_percent": -12,
            "direct_shock_6_month_percent": -18,
            "goal": "최소부채",
        },
    )
    assert response.status_code == 200
    discovery = response.json()["policy_discovery"]
    assert discovery["retrieval_mode"] == "bm25_fallback"
    assert len(discovery["candidates"]) == 6
    assert all(item["official_url"].startswith("https://") for item in discovery["candidates"])
    assert {item["policy_id"] for item in discovery["candidates"]} <= set(FINANCIAL_POLICY_NEEDS)
    assert all(item["need_group"] in set(FINANCIAL_POLICY_NEEDS.values()) for item in discovery["candidates"])
    assert all(item["match_reason"] for item in discovery["candidates"])
    assert all("지원 대상 확정은 아닙니다." in item["match_reason"] for item in discovery["candidates"])
    labels = " ".join(discovery["situation_labels"])
    assert "원" not in labels
    assert "우선" not in labels


def test_embedding_retries_only_once_then_fails(monkeypatch) -> None:
    attempts = 0

    def fail_urlopen(*_args, **_kwargs):
        nonlocal attempts
        attempts += 1
        raise HTTPError("https://api.openai.com/v1/embeddings", 500, "test", {}, BytesIO())

    monkeypatch.setattr("src.rag.openai_embeddings.urlopen", fail_urlopen)
    client = OpenAIEmbeddingClient(api_key="test-key", max_attempts=2)
    try:
        client.embed(["retry-test-unique-text"])
    except OpenAIEmbeddingError as exc:
        assert "attempts=2" in str(exc)
    else:
        raise AssertionError("Embedding failure was expected")
    assert attempts == 2


def test_embedding_does_not_retry_non_retryable_error(monkeypatch) -> None:
    attempts = 0

    def fail_urlopen(*_args, **_kwargs):
        nonlocal attempts
        attempts += 1
        raise HTTPError("https://api.openai.com/v1/embeddings", 401, "test", {}, BytesIO())

    monkeypatch.setattr("src.rag.openai_embeddings.urlopen", fail_urlopen)
    client = OpenAIEmbeddingClient(api_key="test-key", max_attempts=2)
    try:
        client.embed(["auth-test-unique-text"])
    except OpenAIEmbeddingError as exc:
        assert "attempts=1" in str(exc)
    else:
        raise AssertionError("Embedding failure was expected")
    assert attempts == 1


def test_new_policy_rules_exclude_ineligible_and_closed() -> None:
    engine = DiscoveryEligibilityEngine()
    ineligible = engine.evaluate(
        "POL_SEOUL_YELLOW_UMBRELLA_2026",
        SessionEligibilityProfile(
            business_scale="소상공인",
            policy_answers={"annual_sales_le_300m": "no", "new_yellow_umbrella_member": "yes"},
        ),
        district="",
        as_of=date(2026, 8, 17),
    )
    closed = engine.evaluate(
        "POL_SEOUL_PRIVATE_CHILDCARE_2026",
        SessionEligibilityProfile(
            business_scale="소상공인",
            employee_count=1,
            policy_loan_restricted_industry="no",
            policy_answers={
                "childcare_seoul_household": "yes",
                "childcare_child_age_met": "yes",
                "childcare_no_prior_support": "yes",
            },
        ),
        district="",
        as_of=date(2026, 8, 17),
    )
    assert ineligible["candidate_state"] == "제외"
    assert ineligible["eligibility_status"] == "부적격"
    assert closed["candidate_state"] == "제외"
    assert closed["availability_status"] == "접수기간 종료"


def test_staged_questions_include_core_and_candidate_specific_fields() -> None:
    questions = staged_questions(
        ["POL_SEMAS_EMPLOYMENT_INSURANCE_2026"],
        SessionEligibilityProfile(),
    )
    fields = {item["field"] for item in questions}
    assert {"business_scale", "employee_count", "self_employed_insurance_enrolled"}.issubset(fields)


def test_dynamic_events_use_user_sources_and_keep_personal_support_out() -> None:
    family = build_dynamic_policy_plan(
        DynamicPolicyScenario(
            policy_id="POL_SEOUL_FAMILY_FRIENDLY_EMPLOYER_2026",
            approved_support_amount=900_000,
            payment_date=date(2026, 10, 20),
        ),
        reference_date=date(2026, 8, 17),
    )
    assert family.events[0].amount_source is ValueSource.USER_INPUT
    try:
        DynamicPolicyScenario(policy_id="POL_SEOUL_HOSPITAL_LIVING_EXPENSE_2026")
    except ValueError as exc:
        assert "사업체 현금 그래프" in str(exc)
    else:
        raise AssertionError("Personal living cash must not become a business cash event")


def test_track2_dynamic_event_requires_user_amounts_and_dates() -> None:
    plan = build_dynamic_policy_plan(
        DynamicPolicyScenario(
            policy_id="POL_SEOUL_CRISIS_TRACK2_2026H2",
            approved_support_amount=2_000_000,
            expense_amount=2_500_000,
            expense_date=date(2026, 9, 20),
            payment_date=date(2026, 11, 20),
        ),
        reference_date=date(2026, 8, 17),
    )
    assert [item.amount for item in plan.events] == [2_500_000, 2_000_000]
    assert all(item.amount_source is ValueSource.USER_INPUT for item in plan.events)
    assert plan.calculation_status == "ready_with_user_amount_and_date"


def test_dynamic_stability_voucher_uses_confirmed_baseline_expense() -> None:
    plan = build_dynamic_policy_plan(
        DynamicPolicyScenario(
            policy_id="POL_SEMAS_STABILITY_VOUCHER_2026",
            approved_support_amount=250_000,
            expense_amount=800_000,
            expense_date=date(2026, 9, 29),
            expense_already_in_baseline=True,
        ),
        reference_date=date(2026, 9, 1),
    )

    assert plan.summary["cost_reduction"] == 250_000
    assert plan.summary["cash_inflow"] == 0
    assert all(event.effect_kind.value != "new_debt_principal" for event in plan.events)


def test_reviewed_dynamic_event_reaches_re7_alternative_comparison() -> None:
    scenario = DynamicPolicyScenario(
        policy_id="POL_SEOUL_FAMILY_FRIENDLY_EMPLOYER_2026",
        approved_support_amount=900_000,
        payment_date=date(2026, 10, 20),
    )
    request = SampleCompareRequest(policy_scenarios=[scenario])
    alternatives = _dynamic_policy_alternatives(
        request,
        {
            "candidates": [
                {
                    "policy_id": scenario.policy_id,
                    "candidate_state": "확인 후 비교",
                    "eligibility_status": "추가 확인 필요",
                    "availability_status": "기준일상 접수 가능",
                    "reason_summary": "검수 Rule의 미입력 조건 확인 필요",
                    "items_to_confirm": ["서류심사 통과"],
                }
            ]
        },
        reference_date=date(2026, 8, 17),
    )
    result, _ = build_hero(
        _load_sample("declining_cash_shortage"),
        additional_alternatives=alternatives,
    )
    dynamic = next(
        item for item in result.alternatives
        if item.alternative_id == "dynamic_pol_seoul_family_friendly_employer_2026"
    )
    assert dynamic.metrics is not None
    assert dynamic.ranking_eligible is False
    assert dynamic.metrics.support_or_cost_reduction == 900_000


def test_external_text_sanitizer_removes_approved_sensitive_patterns() -> None:
    sanitized = _sanitize_external_text(
        "상호명: 좋은가게, 이태원 관광특구, 서울특별시 중구 세종대로 110 3층, 010-1234-5678, 300만원"
    )
    assert "좋은가게" not in sanitized
    assert "세종대로 110" not in sanitized
    assert "010-1234-5678" not in sanitized
    assert "300만원" not in sanitized
    assert "이태원 관광특구" not in sanitized


def v2_quick_request(**updates):
    payload = {
        "v2_mode": True,
        "direct_shock_13_week_percent": 0,
        "direct_shock_6_month_percent": 0,
        "goal": "최장생존",
        "quick_input": {
            "reference_date": "2026-09-01",
            "opening_cash": 5_000_000,
            "safe_cash_threshold": 0,
            "recent_monthly_revenues": [7_000_000, 7_600_000, 8_200_000, 8_800_000, 9_400_000, 10_000_000],
            "revenue_timing": "daily",
            "monthly_rent": 1_000_000,
            "monthly_labor_cost": 1_500_000,
            "monthly_variable_cost": 1_000_000,
            "monthly_other_fixed_cost": 500_000,
            "expense_timing": "early",
            "total_loan_balance": 0,
            "annual_interest_rate_percent": 0,
            "remaining_term_months": 1,
            "debt_timing": "late",
        },
    }
    payload.update(updates)
    return payload


def test_v2_compares_only_user_confirmed_alternatives(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.rag.hybrid_search.OpenAIEmbeddingClient.embed",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OpenAIEmbeddingError("offline")),
    )
    response = client.post("/api/v1/alternatives/compare", json=v2_quick_request())
    assert response.status_code == 200
    payload = response.json()
    assert payload["v2"]["enabled"] is True
    assert [item["alternative_id"] for item in payload["intervention_results"]] == ["no_action"]
    assert all("5%" not in item["label"] for item in payload["intervention_results"])
    assert payload["dynamic_policy_alternative_ids"] == []
    assert payload["v2"]["confirmed_cost_reduction"] is None
    no_action = payload["intervention_results"][0]
    cash_need = max(
        0,
        payload["safe_cash"]["suggested_amount"]
        - no_action["metrics"]["week13_minimum_cash"],
    )
    assert cash_need >= 0


def test_v2_requested_conditional_policy_graph_is_simulated_but_unranked(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.rag.hybrid_search.OpenAIEmbeddingClient.embed",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OpenAIEmbeddingError("offline")),
    )
    request = v2_quick_request(
        selected_policy_ids=["POL_SEOUL_FUND_2026"],
        conditional_policy_ids=["POL_SEOUL_FUND_2026"],
        eligibility_profile={
            "business_scale": "소상공인",
            "fund_restricted_industry": "no",
            "subfund_selected": "no",
        },
    )
    response = client.post("/api/v1/alternatives/compare", json=request)
    assert response.status_code == 200
    payload = response.json()
    fund = next(
        item for item in payload["intervention_results"]
        if item["alternative_id"] == "conditional_pol_seoul_fund_2026"
    )
    candidate = next(
        item for item in payload["policy_discovery"]["candidates"]
        if item["policy_id"] == "POL_SEOUL_FUND_2026"
    )
    assert fund["simulated"] is True
    assert fund["ranking_eligible"] is False
    assert fund["candidate_state"] == "확인 후 비교"
    assert fund["metrics"]["net_new_borrowing"] > 0
    assert fund["alternative_id"] not in payload["comparison_result"]["ordered_alternative_ids"]
    assert candidate["eligibility_status"] == "추가 확인 필요"
    assert candidate["application_readiness"]["status"] == "준비하면 신청 가능"
    assert candidate["application_readiness"]["hard_failures"] == []


def test_v2_other_fixed_cost_and_confirmed_reduction_reach_cash_engine(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.rag.hybrid_search.OpenAIEmbeddingClient.embed",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OpenAIEmbeddingError("offline")),
    )
    request = v2_quick_request(
        cost_reduction_plan={
            "rent": 100_000,
            "labor": 150_000,
            "purchase": 100_000,
            "other_fixed": 50_000,
        }
    )
    response = client.post("/api/v1/alternatives/compare", json=request)
    assert response.status_code == 200
    payload = response.json()
    custom = next(
        item for item in payload["intervention_results"]
        if item["alternative_id"] == "cost_reduction_custom"
    )
    assert custom["metrics"]["support_or_cost_reduction"] == 2_400_000
    assert payload["v2"]["confirmed_cost_reduction"]["other_fixed"] == 50_000
    other_events = [
        item for item in payload["baseline_input"]["events"]
        if item["description"] == "월 기타 고정비"
    ]
    assert len(other_events) == 6
    assert all(item["amount"] == 500_000 for item in other_events)


def test_v2_action_brief_is_local_without_external_consent(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.rag.hybrid_search.OpenAIEmbeddingClient.embed",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OpenAIEmbeddingError("offline")),
    )
    request = v2_quick_request(
        cost_reduction_plan={"rent": 100_000, "labor": 0, "purchase": 0, "other_fixed": 0}
    )
    response = client.post(
        "/api/v2/ai/action-brief",
        json={
            "comparison": request,
            "selected_alternative_id": "cost_reduction_custom",
            "consent_to_external_ai": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["answer_source"] == "local_deterministic"
    assert payload["fact_lock_status"] == "not_called"
    assert "13주 뒤 현금" in payload["action_brief"]


def test_v2_web_preserves_mvp_assets_and_adds_policy_workbench() -> None:
    html = client.get("/").text
    javascript = client.get("/static/app.js").text
    for preserved in (
        'id="area-map"',
        'id="presentation-presets"',
        'id="baseline-chart"',
        'id="comparison-chart"',
        'id="global-loading"',
    ):
        assert preserved in html
    for added in (
        'id="monthly-other-fixed"',
        'id="policy-question-form"',
        'id="policy-scenario-form"',
        'id="action-brief-content"',
        'id="ai-brief-consent"',
    ):
        assert added in html
    assert "v2_mode: true" in javascript
    assert "cost_reduction_custom" in javascript
    assert 'byId("diagnosis-next").addEventListener("click", () => { enableSelectedPolicyPreviews(); runComparison("decision"); })' in javascript
