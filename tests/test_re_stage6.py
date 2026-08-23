from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.policy.eligibility import (
    AvailabilityStatus,
    EligibilityEngine,
    EligibilityStatus,
    RuleResult,
    SessionEligibilityProfile,
    TriState,
    profile_from_reviewed_example,
)
from src.rag.policy_index import INDEX_PATH, PolicySearchIndex, content_hash
from src.rag.safe_explanation import (
    LockedExplanationFacts,
    build_explanation_packet,
    validate_explanation,
)
from src.settings import PROJECT_ROOT


EXAMPLES_PATH = PROJECT_ROOT / "data/processed_re/policy/re_stage2/eligibility_examples.csv"


@pytest.fixture(scope="module")
def engine() -> EligibilityEngine:
    return EligibilityEngine()


@pytest.fixture(scope="module")
def index() -> PolicySearchIndex:
    return PolicySearchIndex(INDEX_PATH)


def test_all_reviewed_rules_and_policies_are_loaded(engine: EligibilityEngine) -> None:
    assert len(engine.rules) == 56
    assert len(engine.policy_by_id) == 10
    assert len({rule.rule_id for rule in engine.rules}) == 56


def test_all_twenty_reviewed_examples_match(engine: EligibilityEngine) -> None:
    with EXAMPLES_PATH.open("r", encoding="utf-8-sig", newline="") as stream:
        examples = list(csv.DictReader(stream))
    assert len(examples) == 20
    for example in examples:
        decision = engine.evaluate(
            example["policy_id"],
            profile_from_reviewed_example(example["decisive_inputs"]),
            as_of=date(2026, 8, 15),
            rule_ids=example["expected_rule_ids"].split(";"),
            check_availability=False,
        )
        assert decision.eligibility_status.value == example["expected_status"], example["example_id"]
        assert "승인 가능성을 뜻하지 않습니다" in decision.final_check_notice


def test_missing_input_is_not_guessed(engine: EligibilityEngine) -> None:
    decision = engine.evaluate(
        "POL_SEMAS_REFINANCE_2026",
        SessionEligibilityProfile(),
        as_of=date(2026, 8, 16),
        rule_ids=["REFI_ALL_01", "REFI_ALL_02", "REFI_ANY_01", "REFI_ANY_02"],
        check_availability=False,
    )
    assert decision.eligibility_status is EligibilityStatus.NEEDS_CONFIRMATION
    assert set(decision.unknown_rule_ids) == {"REFI_ALL_01", "REFI_ALL_02", "REFI_ANY_01", "REFI_ANY_02"}


def test_profile_accepts_threshold_answers_but_has_no_exact_credit_score_field() -> None:
    assert "credit_score" not in SessionEligibilityProfile.model_fields
    assert "representative_age" not in SessionEligibilityProfile.model_fields
    profile = SessionEligibilityProfile(
        ncb_839_or_below=TriState.NO,
        ncb_919_or_below=TriState.YES,
    )
    assert profile.ncb_919_or_below is TriState.YES


def test_closed_period_and_current_status_are_separate(engine: EligibilityEngine) -> None:
    profile = SessionEligibilityProfile(region="서울특별시")
    closed = engine.evaluate(
        "POL_SEOUL_CRISIS_TRACK2_2026H2",
        profile,
        as_of=date(2027, 1, 1),
        rule_ids=["CRISIS_ALL_01"],
    )
    assert closed.availability_status is AvailabilityStatus.CLOSED
    current_unknown = engine.evaluate(
        "POL_SEOUL_FUND_2026",
        profile,
        as_of=date(2026, 8, 16),
        rule_ids=["FUND_ALL_01"],
    )
    assert current_unknown.availability_status is AvailabilityStatus.NEEDS_CURRENT_CHECK


def test_unselected_seoul_fund_subproduct_is_readiness_not_ineligibility(
    engine: EligibilityEngine,
) -> None:
    decision = engine.evaluate(
        "POL_SEOUL_FUND_2026",
        SessionEligibilityProfile(
            region="서울특별시",
            business_scale="소상공인",
            fund_restricted_industry="no",
            subfund_selected="no",
        ),
        as_of=date(2026, 8, 17),
        check_availability=False,
    )
    variant = next(item for item in decision.rule_results if item.rule_id == "FUND_VARIANT")
    assert decision.eligibility_status is EligibilityStatus.NEEDS_CONFIRMATION
    assert variant.result is RuleResult.UNKNOWN
    assert "세부 자금" in variant.reason


def test_index_has_complete_official_metadata_and_hashes(index: PolicySearchIndex) -> None:
    assert len(index.chunks) == 227
    assert len({chunk.chunk_id for chunk in index.chunks}) == 227
    assert len({chunk.policy_id for chunk in index.chunks}) == 10
    assert all(chunk.source_type.startswith("official_") for chunk in index.chunks)
    assert all(chunk.content_hash == content_hash(chunk.text) for chunk in index.chunks)
    assert all(chunk.source_url and chunk.policy_version and chunk.page_or_section for chunk in index.chunks)


def test_search_requires_policy_filter_and_never_leaks_another_policy(index: PolicySearchIndex) -> None:
    with pytest.raises(ValueError):
        index.search("지원대상", policy_id="")
    results = index.search(
        "지원대상 매출 감소 임차 점포",
        policy_id="POL_SEOUL_CRISIS_TRACK2_2026H2",
        as_of=date(2026, 8, 15),
        top_k=5,
    )
    assert results
    assert all(item.chunk.policy_id == "POL_SEOUL_CRISIS_TRACK2_2026H2" for item in results)
    assert any("매출" in item.chunk.text or "임대차" in item.chunk.text for item in results)


def test_version_filter_excludes_nonmatching_chunks(index: PolicySearchIndex) -> None:
    assert index.search(
        "융자 지원대상",
        policy_id="POL_SEOUL_FUND_2026",
        policy_version="not-a-real-version",
    ) == []


def test_safe_explanation_preserves_locked_facts_and_official_evidence(
    engine: EligibilityEngine, index: PolicySearchIndex
) -> None:
    decision = engine.evaluate(
        "POL_SEOUL_CRISIS_TRACK2_2026H2",
        SessionEligibilityProfile(
            region="서울특별시",
            rented_exclusive_place=TriState.YES,
            business_age_months=36,
            sales_decreased=TriState.YES,
            is_operating=TriState.YES,
            prior_crisis_support=TriState.NO,
        ),
        as_of=date(2026, 8, 15),
        check_availability=False,
    )
    evidence = index.search(
        "지원대상 매출감소 임대차",
        policy_id=decision.policy_id,
        policy_version=decision.policy_version,
        as_of=decision.as_of,
        top_k=3,
    )
    locked = LockedExplanationFacts(
        eligibility_status=decision.eligibility_status.value,
        availability_status=decision.availability_status.value,
        cashflow_change={"week13_ending_cash_delta": 1_000_000},
        debt_interest_change={"month6_debt_delta": 0, "month6_interest_delta": 0},
    )
    packet = build_explanation_packet(
        decision,
        used_user_inputs=["소재지", "임차점포", "업력", "매출감소"],
        locked_facts=locked,
        evidence=evidence,
    )
    validate_explanation(packet, locked_facts=locked, allowed_evidence=evidence)
    assert packet.evidence
    assert packet.policy_version == decision.policy_version


def test_explanation_guard_rejects_changed_calculation_and_prohibited_claim(
    engine: EligibilityEngine, index: PolicySearchIndex
) -> None:
    decision = engine.evaluate(
        "POL_SEOUL_FUND_2026",
        SessionEligibilityProfile(region="서울특별시"),
        as_of=date(2026, 8, 15),
        rule_ids=["FUND_ALL_01"],
        check_availability=False,
    )
    evidence = index.search("지원대상", policy_id=decision.policy_id, top_k=1)
    locked = LockedExplanationFacts(
        eligibility_status=decision.eligibility_status.value,
        availability_status=decision.availability_status.value,
        cashflow_change={"ending_cash_delta": 100},
        debt_interest_change={"debt_delta": 0},
    )
    packet = build_explanation_packet(decision, used_user_inputs=["소재지"], locked_facts=locked, evidence=evidence)
    changed = packet.model_copy(update={"cashflow_change": {"ending_cash_delta": 999}})
    with pytest.raises(ValueError, match="cash-flow"):
        validate_explanation(changed, locked_facts=locked, allowed_evidence=evidence)
    prohibited = packet.model_copy(update={"conclusion": "반드시 승인됩니다."})
    with pytest.raises(ValueError, match="Prohibited claim"):
        validate_explanation(prohibited, locked_facts=locked, allowed_evidence=evidence)


@pytest.mark.parametrize(
    "forbidden_field",
    ["approval_probability", "repayment_schedule", "policy_ranking", "generated_eligibility_rule"],
)
def test_explanation_schema_rejects_llm_created_financial_or_decision_fields(forbidden_field: str) -> None:
    payload = {
        "conclusion": "추가 확인이 필요합니다.",
        "eligibility_status": "추가 확인 필요",
        "availability_status": "접수 가능 여부 확인 필요",
        "used_user_inputs": [],
        "applied_conditions": [],
        "cashflow_change": {},
        "debt_interest_change": {},
        "unconfirmed_conditions": [],
        "evidence": [],
        "as_of": "2026-08-16",
        "policy_version": "v1",
        "locked_facts_sha256": "0" * 64,
        "final_check_notice": "공식 기관 확인 필요",
        forbidden_field: 0.5,
    }
    from src.rag.safe_explanation import SafeExplanation

    with pytest.raises(ValidationError):
        SafeExplanation.model_validate(payload)


def test_explanation_requires_retrieved_official_evidence(
    engine: EligibilityEngine, index: PolicySearchIndex
) -> None:
    decision = engine.evaluate(
        "POL_SEOUL_FUND_2026",
        SessionEligibilityProfile(region="서울특별시"),
        as_of=date(2026, 8, 15),
        rule_ids=["FUND_ALL_01"],
        check_availability=False,
    )
    evidence = index.search("지원대상", policy_id=decision.policy_id, top_k=1)
    locked = LockedExplanationFacts(
        eligibility_status=decision.eligibility_status.value,
        availability_status=decision.availability_status.value,
        cashflow_change={},
        debt_interest_change={},
    )
    packet = build_explanation_packet(decision, used_user_inputs=["소재지"], locked_facts=locked, evidence=[])
    with pytest.raises(ValueError, match="evidence"):
        validate_explanation(packet, locked_facts=locked, allowed_evidence=evidence)


def test_manifest_records_no_training_no_external_llm_and_no_profile_persistence() -> None:
    manifest = json.loads((PROJECT_ROOT / "reports/re_stage6/manifest.json").read_text(encoding="utf-8"))
    assert manifest["checks"]["model_training_performed"] is False
    assert manifest["checks"]["external_llm_called"] is False
    assert manifest["checks"]["raw_session_profile_persisted"] is False
