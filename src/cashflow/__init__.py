"""Deterministic personal cash-flow engine for RE Stage 3."""

from .engine import CashflowResult, run_detailed_cashflow, run_simple_cashflow
from .errors import CashflowInputError
from .loans import LoanPayment, build_loan_schedule
from .schemas import (
    CashEvent,
    DetailedCashflowInput,
    LoanInput,
    OtherFixedCost,
    RepaymentMethod,
    SimpleCashflowInput,
)

__all__ = [
    "CashEvent",
    "CashflowInputError",
    "CashflowResult",
    "DetailedCashflowInput",
    "LoanInput",
    "LoanPayment",
    "OtherFixedCost",
    "RepaymentMethod",
    "SimpleCashflowInput",
    "build_loan_schedule",
    "run_detailed_cashflow",
    "run_simple_cashflow",
]
