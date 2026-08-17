"""Deterministic RE Stage 7 policy-alternative decision support."""

from .engine import compare_alternatives, minimum_loan_for_safe_cash, suggest_safe_cash
from .routing import CombinationRegistry, route_candidate
from .schemas import (
    AlternativeKind,
    AlternativeSpec,
    CandidateContext,
    CandidateState,
    CombinationRule,
    CombinationStatus,
    DecisionResult,
    MarketScenario,
    UserGoal,
)

__all__ = [
    "AlternativeKind",
    "AlternativeSpec",
    "CandidateContext",
    "CandidateState",
    "CombinationRegistry",
    "CombinationRule",
    "CombinationStatus",
    "DecisionResult",
    "MarketScenario",
    "UserGoal",
    "compare_alternatives",
    "minimum_loan_for_safe_cash",
    "route_candidate",
    "suggest_safe_cash",
]
