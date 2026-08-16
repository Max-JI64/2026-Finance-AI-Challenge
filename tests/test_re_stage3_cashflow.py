from __future__ import annotations

import json
from datetime import date

import pytest
from pydantic import ValidationError

from src.cashflow.csv_io import load_detailed_csv
from src.cashflow.engine import run_detailed_cashflow, run_simple_cashflow
from src.cashflow.errors import CashflowInputError
from src.cashflow.loans import build_loan_schedule
from src.cashflow.schemas import (
    CashEvent,
    DetailedCashflowInput,
    LoanInput,
    OtherFixedCost,
    RepaymentMethod,
    SimpleCashflowInput,
)


def simple_input(**overrides: object) -> SimpleCashflowInput:
    payload: dict[str, object] = {
        "reference_date": "2026-09-01",
        "opening_cash": 10_000_000,
        "safe_cash_threshold": 2_000_000,
        "monthly_revenue": 6_000_000,
        "revenue_receipt_day": 5,
        "monthly_rent": 1_000_000,
        "rent_payment_day": 1,
        "monthly_labor_cost": 2_000_000,
        "labor_payment_day": 25,
        "monthly_variable_cost": None,
        "variable_cost_rate_percent": 20,
        "variable_cost_payment_day": 20,
        "other_fixed_costs": [
            {
                "name": "공과금",
                "amount": 300_000,
                "payment_day": 15,
                "expense_type": "utility",
            }
        ],
        "total_loan_balance": 12_000_000,
        "monthly_debt_payment": 500_000,
        "debt_payment_day": 28,
    }
    payload.update(overrides)
    return SimpleCashflowInput.model_validate(payload)


def test_simple_hand_calculation_matches_weekly_and_monthly_results() -> None:
    result = run_simple_cashflow(simple_input())

    assert len(result.weekly_13) == 13
    assert len(result.monthly_6) == 6
    assert result.monthly_6[0].operating_inflow == 6_000_000
    assert result.monthly_6[0].fixed_cost == 3_000_000
    assert result.monthly_6[0].variable_cost == 1_200_000
    assert result.monthly_6[0].tax_utility == 300_000
    assert result.monthly_6[0].debt_service_combined == 500_000
    assert result.monthly_6[0].closing_cash == 11_000_000
    assert result.monthly_summary.ending_cash == 16_000_000
    assert result.weekly_summary.ending_cash == 13_000_000
    assert result.weekly_13[-1].closing_cash == result.monthly_6[2].closing_cash
    assert result.weekly_summary.first_cash_depletion_date is None
    assert result.debt_summary["principal_interest_split_available"] is False


def test_recent_revenue_average_uses_half_up_won_rounding() -> None:
    data = simple_input(monthly_revenue=None, recent_monthly_revenues=[0, 1])
    assert data.resolved_monthly_revenue() == 1


def test_computed_cash_can_be_negative_and_is_not_clipped() -> None:
    data = simple_input(
        opening_cash=100_000,
        safe_cash_threshold=50_000,
        monthly_revenue=0,
        monthly_rent=200_000,
        monthly_labor_cost=0,
        variable_cost_rate_percent=None,
        monthly_variable_cost=0,
        other_fixed_costs=[],
        total_loan_balance=0,
        monthly_debt_payment=0,
    )
    result = run_simple_cashflow(data)

    assert result.weekly_13[0].closing_cash == -100_000
    assert result.weekly_summary.minimum_cash < 0
    assert result.weekly_summary.first_cash_depletion_date == date(2026, 9, 1)


@pytest.mark.parametrize(
    "method",
    [
        RepaymentMethod.EQUAL_PRINCIPAL,
        RepaymentMethod.EQUAL_PAYMENT,
        RepaymentMethod.BULLET,
    ],
)
def test_all_loan_methods_clear_principal_and_round_to_won(
    method: RepaymentMethod,
) -> None:
    loan = LoanInput(
        loan_id=f"loan-{method.value}",
        principal=1_200_000,
        annual_interest_rate_percent=12,
        repayment_method=method,
        payment_day=1,
        maturity_date=date(2027, 8, 1),
        grace_months=0,
    )
    schedule = build_loan_schedule(loan, date(2026, 9, 1))

    assert len(schedule) == 12
    assert schedule[0].interest == 12_000
    assert schedule[-1].closing_principal == 0
    assert sum(payment.principal for payment in schedule) == 1_200_000
    assert all(isinstance(payment.total_payment, int) for payment in schedule)
    if method is RepaymentMethod.EQUAL_PRINCIPAL:
        assert schedule[0].principal == 100_000
        assert schedule[-1].interest == 1_000
        assert sum(payment.interest for payment in schedule) == 78_000
    if method is RepaymentMethod.BULLET:
        assert all(payment.principal == 0 for payment in schedule[:-1])
        assert schedule[-1].principal == 1_200_000


def test_grace_period_boundary_is_interest_only_then_amortizes() -> None:
    loan = LoanInput(
        loan_id="grace-loan",
        principal=1_000_000,
        annual_interest_rate_percent=12,
        repayment_method=RepaymentMethod.EQUAL_PRINCIPAL,
        payment_day=15,
        maturity_date=date(2027, 2, 15),
        grace_months=2,
    )
    schedule = build_loan_schedule(loan, date(2026, 9, 1))

    assert schedule[0].principal == schedule[1].principal == 0
    assert schedule[1].closing_principal == 1_000_000
    assert schedule[2].principal == 250_000
    assert schedule[-1].closing_principal == 0


def test_detailed_events_and_loans_produce_split_debt_cashflow() -> None:
    data = DetailedCashflowInput(
        reference_date=date(2026, 9, 1),
        opening_cash=2_000_000,
        safe_cash_threshold=1_000_000,
        events=[
            CashEvent(
                event_id="sales-1",
                event_date=date(2026, 9, 5),
                event_type="operating_inflow",
                amount=3_000_000,
            ),
            CashEvent(
                event_id="rent-1",
                event_date=date(2026, 9, 1),
                event_type="fixed_cost",
                amount=1_000_000,
                expense_type="rent",
            ),
        ],
        loans=[
            LoanInput(
                loan_id="L1",
                principal=600_000,
                annual_interest_rate_percent=12,
                repayment_method="equal_principal",
                payment_day=10,
                maturity_date=date(2027, 2, 10),
            )
        ],
    )
    result = run_detailed_cashflow(data)

    assert result.monthly_6[0].debt_principal == 100_000
    assert result.monthly_6[0].debt_interest == 6_000
    assert result.monthly_6[0].closing_cash == 3_894_000
    assert result.debt_summary["remaining_principal_at_6_months"] == 0
    assert result.debt_summary["principal_interest_split_available"] is True
    assert len(result.loan_schedules) == 6


def test_input_validation_rejects_negative_string_nan_duplicate_and_overlap() -> None:
    with pytest.raises(ValidationError):
        simple_input(opening_cash=-1)
    with pytest.raises(ValidationError):
        simple_input(monthly_rent="1000000")
    with pytest.raises(ValidationError):
        simple_input(variable_cost_rate_percent=float("nan"))
    with pytest.raises(ValidationError):
        simple_input(monthly_variable_cost=1, variable_cost_rate_percent=20)
    with pytest.raises(ValidationError):
        simple_input(total_loan_balance=0, monthly_debt_payment=1)
    with pytest.raises(ValidationError):
        SimpleCashflowInput.model_validate(
            simple_input().model_dump(exclude={"safe_cash_threshold"})
        )


def test_detailed_input_detects_duplicate_cost_and_sensitive_extra_fields() -> None:
    duplicate = {
        "event_date": "2026-09-01",
        "event_type": "fixed_cost",
        "amount": 100_000,
        "expense_type": "rent",
        "description": "임대료",
    }
    with pytest.raises(ValidationError, match="probable duplicate cost"):
        DetailedCashflowInput.model_validate(
            {
                "reference_date": "2026-09-01",
                "opening_cash": 1_000_000,
                "safe_cash_threshold": 100_000,
                "events": [
                    {"event_id": "a", **duplicate},
                    {"event_id": "b", **duplicate},
                ],
            }
        )
    payload = simple_input().model_dump(mode="json")
    payload["account_number"] = "not-allowed"
    with pytest.raises(ValidationError):
        SimpleCashflowInput.model_validate(payload)
    schema_text = json.dumps(SimpleCashflowInput.model_json_schema(), ensure_ascii=False)
    for forbidden in ("주민등록번호", "account_number", "credit_score", "business_number"):
        assert forbidden not in schema_text


def test_detailed_csv_loader_accepts_utf8_template_and_returns_field_errors(tmp_path) -> None:
    events = tmp_path / "events.csv"
    loans = tmp_path / "loans.csv"
    events.write_text(
        "event_id,event_date,event_type,amount,expense_type,description,source\n"
        "sale1,2026-09-05,operating_inflow,3000000,,매출입금,user\n",
        encoding="utf-8-sig",
    )
    loans.write_text(
        "loan_id,principal,annual_interest_rate_percent,repayment_method,payment_day,maturity_date,grace_months\n"
        "L1,600000,12,equal_principal,10,2027-02-10,0\n",
        encoding="utf-8-sig",
    )
    loaded = load_detailed_csv(
        events,
        loans,
        reference_date=date(2026, 9, 1),
        opening_cash=2_000_000,
        safe_cash_threshold=1_000_000,
    )
    assert loaded.events[0].amount == 3_000_000
    assert loaded.loans[0].principal == 600_000

    events.write_text(
        "event_id,event_date,event_type,amount,expense_type,description,source\n"
        "bad,2026-09-05,operating_inflow,삼백만원,,매출입금,user\n",
        encoding="utf-8-sig",
    )
    with pytest.raises(CashflowInputError) as caught:
        load_detailed_csv(
            events,
            loans,
            reference_date=date(2026, 9, 1),
            opening_cash=2_000_000,
            safe_cash_threshold=1_000_000,
        )
    assert caught.value.code == "INVALID_WON_AMOUNT"
    assert caught.value.field == "events.row2.amount"


def test_same_input_is_deterministic_and_has_no_policy_ml_or_rag_output() -> None:
    data = simple_input()
    first = run_simple_cashflow(data).to_dict()
    second = run_simple_cashflow(data).to_dict()

    assert first == second
    serialized = json.dumps(first, ensure_ascii=False)
    for forbidden in ("policy_id", "model_score", "rag_answer", "approval_probability"):
        assert forbidden not in serialized
