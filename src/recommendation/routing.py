"""RE6-to-RE7 candidate routing and conservative combination checks."""

from __future__ import annotations

from itertools import combinations

from src.policy.eligibility import AvailabilityStatus, EligibilityDecision, EligibilityStatus

from .schemas import (
    CandidateContext,
    CandidateState,
    CombinationRule,
    CombinationStatus,
)


def route_candidate(decision: EligibilityDecision) -> CandidateContext:
    """Map separate RE6 statuses to the three approved user-visible groups."""

    if (
        decision.eligibility_status is EligibilityStatus.INELIGIBLE
        or decision.availability_status is AvailabilityStatus.CLOSED
    ):
        state = CandidateState.EXCLUDED
    elif (
        decision.eligibility_status is EligibilityStatus.ELIGIBLE_CANDIDATE
        and decision.availability_status is AvailabilityStatus.AVAILABLE_AS_OF_DATE
    ):
        state = CandidateState.ACTIONABLE
    else:
        state = CandidateState.CONDITIONAL

    reasons: list[str] = [
        f"자격: {decision.eligibility_status.value}",
        f"접수: {decision.availability_status.value}",
    ]
    items = [result.official_condition for result in decision.rule_results if result.rule_id in decision.unknown_rule_ids]
    if decision.availability_status is AvailabilityStatus.NEEDS_CURRENT_CHECK:
        items.append("기준일 현재 접수 가능 여부")
    if state is CandidateState.EXCLUDED:
        items.extend(
            result.official_condition
            for result in decision.rule_results
            if result.rule_id in decision.failed_rule_ids
        )
    return CandidateContext(
        policy_id=decision.policy_id,
        policy_version=decision.policy_version,
        eligibility_status=decision.eligibility_status.value,
        availability_status=decision.availability_status.value,
        candidate_state=state,
        reason_summary=" / ".join(reasons),
        items_to_confirm=list(dict.fromkeys(items)),
        as_of=decision.as_of,
        official_notice_url=decision.official_notice_url,
        application_url=decision.application_url,
    )


class CombinationRegistry:
    """Only evidence-backed pairs are compatible; unknown pairs stay conditional."""

    def __init__(self, rules: list[CombinationRule] | None = None):
        self._rules: dict[tuple[str, str], CombinationRule] = {}
        for rule in rules or []:
            self._rules[tuple(sorted(rule.policy_ids))] = rule

    def evaluate(
        self,
        policy_ids: list[str],
        *,
        deduplication_keys: list[str],
        same_expense_support_keys: dict[str, list[str]] | None = None,
    ) -> tuple[CombinationStatus, list[str]]:
        unique_ids = sorted(set(policy_ids))
        if len(deduplication_keys) != len(set(deduplication_keys)):
            return CombinationStatus.PROHIBITED, ["같은 정책 금융효과가 중복되었습니다."]

        expense_map = same_expense_support_keys or {}
        for left, right in combinations(unique_ids, 2):
            overlap = set(expense_map.get(left, [])) & set(expense_map.get(right, []))
            if overlap:
                return (
                    CombinationStatus.PROHIBITED,
                    [f"{left}와 {right}가 같은 지출을 중복 보전합니다: {', '.join(sorted(overlap))}"],
                )

        statuses: list[CombinationStatus] = []
        reasons: list[str] = []
        for pair in combinations(unique_ids, 2):
            rule = self._rules.get(pair)
            if rule is None:
                statuses.append(CombinationStatus.NEEDS_CONFIRMATION)
                reasons.append(f"{pair[0]} + {pair[1]} 동시수혜 공식 근거 확인 필요")
            else:
                statuses.append(rule.status)
                reasons.append(rule.reason)
        if CombinationStatus.PROHIBITED in statuses:
            return CombinationStatus.PROHIBITED, reasons
        if CombinationStatus.NEEDS_CONFIRMATION in statuses:
            return CombinationStatus.NEEDS_CONFIRMATION, reasons
        return CombinationStatus.COMPATIBLE, reasons

