from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_local_review_assets_disable_browser_cache() -> None:
    page = client.get("/")
    styles = client.get("/static/styles.css")
    javascript = client.get("/static/app.js")

    assert page.headers["cache-control"] == "no-store"
    assert styles.headers["cache-control"] == "no-store"
    assert javascript.headers["cache-control"] == "no-store"
    assert "/static/styles.css?v=v2-011" in page.text
    assert "/static/app.js?v=v2-011" in page.text


def test_v2_first_page_hides_internal_ai_role_breakdown() -> None:
    page = client.get("/")

    assert page.status_code == 200
    assert 'class="v2-ai-roles"' not in page.text
    assert 'aria-label="AI 역할"' not in page.text
    assert "규칙·현금 엔진" not in page.text
    assert 'id="v2-hero-title"' in page.text
    assert 'id="business-title"' in page.text


def test_v2_question_wizard_is_single_card_and_connects_to_existing_results() -> None:
    html = client.get("/").text
    javascript = client.get("/static/app.js").text

    assert 'id="policy-questionnaire"' in html
    assert 'id="policy-question-progress"' in html
    assert 'id="policy-question-back"' in html
    assert 'id="policy-question-complete"' in html
    assert 'id="policy-results"' in html
    assert 'id="policy-scenario-inputs"' in html
    assert 'id="cost-reduction-panel"' in html
    assert "function renderQuestionWizard()" in javascript
    assert "function answerWizardQuestion(field, value)" in javascript
    assert "function previousWizardQuestion()" in javascript
    assert "function finishQuestionWizard()" in javascript
    assert 'new Map([["no", 0], ["unknown", 1], ["yes", 2]])' in javascript
    assert 'await runComparison("diagnosis", false)' in javascript
    assert "state.questionWizardResultsVisible = true" in javascript
    assert "renderPolicyResults(discovery)" in javascript
    assert 'byId("diagnosis-next").disabled = false' in javascript
    assert "function enableSelectedPolicyPreviews()" in javascript
    assert 'byId("diagnosis-next").addEventListener("click", () => { enableSelectedPolicyPreviews(); runComparison("decision"); })' in javascript
    assert "data-ask-policy" not in javascript
    assert "askCandidate.dataset.askPolicy" not in javascript


def test_v2_optional_simulation_keeps_unknown_policy_values_out_of_core_flow() -> None:
    html = client.get("/").text
    javascript = client.get("/static/app.js").text

    assert 'id="policy-cash-need"' in html
    assert 'id="optional-comparison-tools"' in html
    assert 'id="open-cost-reduction"' in html
    assert 'id="decision-policy-opportunities"' in html
    assert 'id="goal-selector-panel"' in html
    assert 'id="comparison-panel"' in html
    assert "다음 행동 확인" in html
    assert "function baselineCashNeed()" in javascript
    assert "Math.max(0, safeCash - Number(baseline?.metrics?.week13_minimum_cash || 0))" in javascript
    assert "policyFundingGuidance" in javascript
    assert "function openPolicyScenarioEditor(policyId)" in javascript
    assert "function setCostReductionEditor(open)" in javascript
    assert 'byId("policy-scenario-inputs").hidden = !state.policyScenarioEditorPolicyId' in javascript
    assert 'byId("cost-reduction-panel").hidden = !state.costReductionEditorOpen' in javascript
    assert "function renderDecisionPolicyOpportunities()" in javascript
    assert "function setNumericComparisonVisibility(hasMultipleAlternatives, rankedCount)" in javascript
    assert "conditional_policy_ids: [...state.conditionalPolicyIds]" in javascript
    assert "data-toggle-conditional-policy" in javascript
    assert "data-policy-mini-chart" in javascript
    assert "왜 지금 안 되나요?" in javascript
    assert "신청 가능성을 높이려면" in javascript
    assert "조건을 충족하고 승인·실행됐다면" in javascript
    assert "data-edit-policy-answer" in javascript
    assert "questionWizardReturnPolicyId" in javascript
    assert "조건부 그래프 제외" in javascript
    assert 'detail.remediation_type === "structural"' in javascript
    assert 'state.conditionalPolicyIds.delete(item.policy_id)' in javascript
    assert "조건부 현금효과, 추천 순위 제외" in javascript
    assert "사용자가 열어 본 조건부 가정" not in html


def test_presentation_presets_use_five_distinct_valid_market_areas() -> None:
    javascript = client.get("/static/app.js").text
    area_codes = ("3001496", "3120012", "3001491", "3110131", "3120153")

    assert len(set(area_codes)) == 5
    for area_code in area_codes:
        assert f'areaCode: "{area_code}"' in javascript
        scenario = client.get(f"/api/v1/market-scenarios/{area_code}/CS100001")
        assert scenario.status_code == 200
        assert scenario.json()["market_scenario"]["available"] is True
    assert 'item.code === preset?.areaCode' in javascript
    assert 'item.code === "3001491"' not in javascript


def test_scope_endpoint_keeps_prediction_boundary() -> None:
    response = client.get("/scope")
    payload = response.json()

    assert response.status_code == 200
    assert payload["geography"] == "Seoul"
    assert payload["predicts"] == "다음 분기 상권·업종 매출환경 악화 위험"
    assert "개별 점포 폐업확률" in payload["does_not_predict"]
    assert payload["separates"] == ["상권환경 위험", "사업체 금융부담"]
