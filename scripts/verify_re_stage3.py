"""Build deterministic RE Stage 3 verification artifacts from synthetic data."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.cashflow.csv_io import load_detailed_csv
from src.cashflow.engine import run_detailed_cashflow, run_simple_cashflow
from src.cashflow.loans import build_loan_schedule
from src.cashflow.schemas import (
    DetailedCashflowInput,
    LoanInput,
    RepaymentMethod,
    SimpleCashflowInput,
)


SAMPLES = ROOT / "data" / "samples" / "re_stage3"
TEMPLATES = ROOT / "data" / "templates" / "re_stage3"
REPORTS = ROOT / "reports" / "re_stage3"


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    sample_path = SAMPLES / "01_declining_low_debt.json"
    sample_payload = json.loads(sample_path.read_text(encoding="utf-8"))
    simple = SimpleCashflowInput.model_validate(sample_payload)
    first = run_simple_cashflow(simple)
    second = run_simple_cashflow(simple)

    checks: list[dict[str, object]] = []

    def check(name: str, expected: object, actual: object) -> None:
        checks.append(
            {
                "check": name,
                "expected": expected,
                "actual": actual,
                "passed": expected == actual,
            }
        )

    month = first.monthly_6[0]
    check("recent_revenue_half_up_average", 6_000_000, simple.resolved_monthly_revenue())
    check("month1_operating_inflow", 6_000_000, month.operating_inflow)
    check("month1_fixed_cost", 3_000_000, month.fixed_cost)
    check("month1_variable_cost", 1_200_000, month.variable_cost)
    check("month1_tax_utility", 300_000, month.tax_utility)
    check("month1_combined_debt_payment", 500_000, month.debt_service_combined)
    check("month1_ending_cash", 11_000_000, month.closing_cash)
    check("month6_ending_cash", 16_000_000, first.monthly_summary.ending_cash)
    check("week13_ending_cash", 13_000_000, first.weekly_summary.ending_cash)
    check(
        "all_13_week_closing_cash",
        [
            15_000_000,
            15_000_000,
            13_500_000,
            11_000_000,
            16_000_000,
            16_000_000,
            15_700_000,
            12_500_000,
            11_000_000,
            17_000_000,
            16_700_000,
            15_500_000,
            13_000_000,
        ],
        [period.closing_cash for period in first.weekly_13],
    )
    check(
        "all_6_month_closing_cash",
        [11_000_000, 12_000_000, 13_000_000, 14_000_000, 15_000_000, 16_000_000],
        [period.closing_cash for period in first.monthly_6],
    )
    check(
        "week_month_overlap",
        first.monthly_6[2].closing_cash,
        first.weekly_13[-1].closing_cash,
    )
    check("deterministic_result", True, first.to_dict() == second.to_dict())

    method_summaries: dict[str, dict[str, object]] = {}
    for method in RepaymentMethod:
        loan = LoanInput(
            loan_id=f"verify-{method.value}",
            principal=1_200_000,
            annual_interest_rate_percent=12,
            repayment_method=method,
            payment_day=1,
            maturity_date=date(2027, 8, 1),
            grace_months=0,
        )
        schedule = build_loan_schedule(loan, date(2026, 9, 1))
        method_summaries[method.value] = {
            "payment_count": len(schedule),
            "principal_total": sum(item.principal for item in schedule),
            "interest_total": sum(item.interest for item in schedule),
            "closing_principal": schedule[-1].closing_principal,
        }
        check(f"{method.value}_payment_count", 12, len(schedule))
        check(
            f"{method.value}_principal_total",
            1_200_000,
            sum(item.principal for item in schedule),
        )
        check(f"{method.value}_closing_principal", 0, schedule[-1].closing_principal)

    detailed = load_detailed_csv(
        TEMPLATES / "cashflow_events.csv",
        TEMPLATES / "loans.csv",
        reference_date=date(2026, 9, 1),
        opening_cash=10_000_000,
        safe_cash_threshold=2_000_000,
    )
    detailed_result = run_detailed_cashflow(detailed)
    check("detailed_csv_event_rows", 14, len(detailed.events))
    check("detailed_csv_loan_rows", 1, len(detailed.loans))
    check(
        "detailed_debt_split",
        True,
        detailed_result.debt_summary["principal_interest_split_available"],
    )

    warning_payload = json.loads(
        (SAMPLES / "05_unit_warning.json").read_text(encoding="utf-8")
    )
    warning_result = run_simple_cashflow(
        SimpleCashflowInput.model_validate(warning_payload)
    )
    check(
        "unit_warning_detected",
        True,
        any(
            item["code"] == "POSSIBLE_TEN_THOUSAND_WON_UNIT"
            for item in warning_result.warnings
        ),
    )

    if not all(item["passed"] for item in checks):
        failed = [item["check"] for item in checks if not item["passed"]]
        raise RuntimeError(f"RE Stage 3 verification failed: {failed}")

    write_json(
        REPORTS / "input_schema.json",
        {
            "simple": SimpleCashflowInput.model_json_schema(),
            "detailed": DetailedCashflowInput.model_json_schema(),
        },
    )
    write_json(REPORTS / "simple_sample_result.json", first.to_dict())
    write_json(REPORTS / "detailed_sample_result.json", detailed_result.to_dict())
    write_json(REPORTS / "loan_method_summary.json", method_summaries)
    with (REPORTS / "manual_check.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as stream:
        writer = csv.DictWriter(
            stream, fieldnames=("check", "expected", "actual", "passed")
        )
        writer.writeheader()
        writer.writerows(checks)

    tracked = [
        ROOT / "src" / "cashflow" / "schemas.py",
        ROOT / "src" / "cashflow" / "loans.py",
        ROOT / "src" / "cashflow" / "engine.py",
        ROOT / "src" / "cashflow" / "csv_io.py",
        sample_path,
        TEMPLATES / "cashflow_events.csv",
        TEMPLATES / "loans.csv",
        REPORTS / "input_schema.json",
        REPORTS / "simple_sample_result.json",
        REPORTS / "detailed_sample_result.json",
        REPORTS / "loan_method_summary.json",
        REPORTS / "manual_check.csv",
    ]
    manifest = {
        "stage": "RE Stage 3",
        "status": "completed",
        "engine_version": "re3-v1",
        "verification_date": "2026-08-16",
        "external_data_used": False,
        "policy_ml_rag_used": False,
        "check_count": len(checks),
        "passed_count": sum(bool(item["passed"]) for item in checks),
        "deterministic": True,
        "weekly_periods": len(first.weekly_13),
        "monthly_periods": len(first.monthly_6),
        "files": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in tracked
        ],
    }
    write_json(REPORTS / "manifest.json", manifest)
    print(
        f"RE_STAGE3=PASSED checks={manifest['passed_count']}/{manifest['check_count']}"
    )


if __name__ == "__main__":
    main()
