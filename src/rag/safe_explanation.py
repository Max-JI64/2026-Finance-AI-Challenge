"""Fact-locked explanation packets and LLM-output safety validation for RE6."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.policy.eligibility import EligibilityDecision
from src.rag.policy_index import SearchResult


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class EvidenceCitation(StrictModel):
    chunk_id: str
    policy_id: str
    policy_version: str
    source_url: str
    page_or_section: str
    excerpt: str = Field(max_length=500)


class LockedExplanationFacts(StrictModel):
    eligibility_status: str
    availability_status: str
    cashflow_change: dict[str, int | float | str | None]
    debt_interest_change: dict[str, int | float | str | None]

    @property
    def digest(self) -> str:
        payload = json.dumps(self.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class SafeExplanation(StrictModel):
    conclusion: str
    eligibility_status: str
    availability_status: str
    used_user_inputs: list[str]
    applied_conditions: list[str]
    cashflow_change: dict[str, int | float | str | None]
    debt_interest_change: dict[str, int | float | str | None]
    unconfirmed_conditions: list[str]
    evidence: list[EvidenceCitation]
    as_of: date
    policy_version: str
    locked_facts_sha256: str
    final_check_notice: str


PROHIBITED_PHRASES = (
    "승인 확률",
    "승인 가능성은",
    "확실히 승인",
    "반드시 승인",
    "최적 정책",
    "무조건 유리",
    "정책 때문에 매출",
    "수혜 효과가 보장",
)


def citations_from_results(results: list[SearchResult]) -> list[EvidenceCitation]:
    return [
        EvidenceCitation(
            chunk_id=item.chunk.chunk_id,
            policy_id=item.chunk.policy_id,
            policy_version=item.chunk.policy_version,
            source_url=item.chunk.source_url,
            page_or_section=item.chunk.page_or_section,
            excerpt=item.chunk.text[:500],
        )
        for item in results
    ]


def build_explanation_packet(
    decision: EligibilityDecision,
    *,
    used_user_inputs: list[str],
    locked_facts: LockedExplanationFacts,
    evidence: list[SearchResult],
) -> SafeExplanation:
    conditions = [
        f"{item.rule_id}: {item.reason}"
        for item in decision.rule_results
        if item.result.value in {"pass", "fail"}
    ]
    unknown = [
        f"{item.rule_id}: {item.reason}"
        for item in decision.rule_results
        if item.result.value == "unknown"
    ]
    return SafeExplanation(
        conclusion=(
            f"입력 기준 결과는 '{decision.overall_status}'입니다. "
            "이는 공개 조건과 입력값의 일치 여부이며 승인 가능성을 뜻하지 않습니다."
        ),
        eligibility_status=locked_facts.eligibility_status,
        availability_status=locked_facts.availability_status,
        used_user_inputs=used_user_inputs,
        applied_conditions=conditions,
        cashflow_change=locked_facts.cashflow_change,
        debt_interest_change=locked_facts.debt_interest_change,
        unconfirmed_conditions=unknown,
        evidence=citations_from_results(evidence),
        as_of=decision.as_of,
        policy_version=decision.policy_version,
        locked_facts_sha256=locked_facts.digest,
        final_check_notice=decision.final_check_notice,
    )


def validate_explanation(
    candidate: SafeExplanation,
    *,
    locked_facts: LockedExplanationFacts,
    allowed_evidence: list[SearchResult],
) -> None:
    if candidate.locked_facts_sha256 != locked_facts.digest:
        raise ValueError("LLM output changed or detached from locked calculation facts")
    if candidate.eligibility_status != locked_facts.eligibility_status:
        raise ValueError("LLM output changed the eligibility result")
    if candidate.availability_status != locked_facts.availability_status:
        raise ValueError("LLM output changed the application availability result")
    if candidate.cashflow_change != locked_facts.cashflow_change:
        raise ValueError("LLM output changed cash-flow calculations")
    if candidate.debt_interest_change != locked_facts.debt_interest_change:
        raise ValueError("LLM output changed debt or interest calculations")
    allowed_ids = {item.chunk.chunk_id for item in allowed_evidence}
    if not candidate.evidence or any(item.chunk_id not in allowed_ids for item in candidate.evidence):
        raise ValueError("LLM output used evidence outside retrieved official chunks")
    serialized = json.dumps(candidate.model_dump(mode="json"), ensure_ascii=False)
    found = [phrase for phrase in PROHIBITED_PHRASES if phrase in serialized]
    if found:
        raise ValueError(f"Prohibited claim in explanation: {found}")
