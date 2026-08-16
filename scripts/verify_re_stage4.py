"""Create and verify RE Stage 4 artifacts from reviewed local policy data."""

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

from src.cashflow.schemas import CashEvent, DetailedCashflowInput
from src.policy.apply import apply_policy_plan
from src.policy.catalog import CalculationStatus, PolicyCatalog
from src.policy.converters import (
    convert_grant,
    convert_guarantee,
    convert_loan,
    convert_refinance,
    convert_voucher,
)
from src.policy.schemas import (
    GrantScenario,
    GuaranteeScenario,
    LoanScenario,
    PolicyFinancialEvent,
    PolicyPlan,
    RefinanceScenario,
    VoucherScenario,
)


SAMPLES = ROOT / "data" / "samples" / "re_stage4"
PROCESSED = ROOT / "data" / "processed_re" / "policy" / "re_stage4"
REPORTS = ROOT / "reports" / "re_stage4"


def load_json(name: str) -> dict[str, Any]:
    return json.loads((SAMPLES / name).read_text(encoding="utf-8"))


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
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    catalog = PolicyCatalog()
    profiles_path = PROCESSED / "policy_event_profiles.csv"
    with profiles_path.open("w", encoding="utf-8-sig", newline="") as stream:
        fields = (
            "policy_id",
            "policy_version",
            "event_id",
            "event_name",
            "support_kind",
            "calculation_status",
            "maximum_amount",
            "official_interest_rate_percent",
            "reference_rate_spread_percent",
            "subsidy_phases",
            "linked_event_id",
            "deduplication_key",
            "unconfirmed_fields",
            "source_path",
            "source_locator",
        )
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for profile in catalog.profiles:
            writer.writerow(
                {
                    "policy_id": profile.policy_id,
                    "policy_version": profile.policy_version,
                    "event_id": profile.event_id,
                    "event_name": profile.event_name,
                    "support_kind": profile.support_kind.value,
                    "calculation_status": profile.calculation_status.value,
                    "maximum_amount": (
                        profile.maximum_amount
                        if profile.maximum_amount is not None
                        else "미확인"
                    ),
                    "official_interest_rate_percent": (
                        profile.official_interest_rate_percent
                        if profile.official_interest_rate_percent is not None
                        else "해당 없음 또는 사용자 입력"
                    ),
                    "reference_rate_spread_percent": (
                        profile.reference_rate_spread_percent
                        if profile.reference_rate_spread_percent is not None
                        else "해당 없음"
                    ),
                    "subsidy_phases": ";".join(
                        f"{phase.months}m:{phase.percentage_points}%p"
                        for phase in profile.subsidy_phases
                    )
                    or "해당 없음",
                    "linked_event_id": profile.linked_event_id or "해당 없음",
                    "deduplication_key": profile.deduplication_key,
                    "unconfirmed_fields": ";".join(profile.missing_or_unquantifiable)
                    or "없음",
                    "source_path": profile.raw["source_path"],
                    "source_locator": profile.raw["source_locator"],
                }
            )

    grant = convert_grant(
        GrantScenario.model_validate(load_json("01_reimbursement_grant.json")), catalog
    )
    voucher = convert_voucher(
        VoucherScenario.model_validate(load_json("02_voucher.json")), catalog
    )
    direct_loan = convert_loan(
        LoanScenario.model_validate(load_json("03_direct_loan.json")), catalog
    )
    subsidized_loan = convert_loan(
        LoanScenario.model_validate(load_json("04_interest_subsidized_loan.json")),
        catalog,
    )
    refinance = convert_refinance(
        RefinanceScenario.model_validate(load_json("05_refinance.json")), catalog
    )
    guarantee = convert_guarantee(
        GuaranteeScenario.model_validate(load_json("06_guarantee_info_only.json")),
        catalog,
    )
    plans = [grant, voucher, direct_loan, subsidized_loan, refinance, guarantee]

    grant_impact = apply_policy_plan(
        DetailedCashflowInput(
            reference_date=date(2026, 9, 1),
            opening_cash=2_000_000,
            safe_cash_threshold=1_000_000,
            events=[],
            loans=[],
        ),
        [grant],
    )
    voucher_impact = apply_policy_plan(
        DetailedCashflowInput(
            reference_date=date(2026, 9, 1),
            opening_cash=1_000_000,
            safe_cash_threshold=100_000,
            events=[
                CashEvent(
                    event_id="utility-base",
                    event_date=date(2026, 9, 10),
                    event_type="tax_utility",
                    amount=100_000,
                    expense_type="utility",
                ),
                CashEvent(
                    event_id="insurance-base",
                    event_date=date(2026, 10, 10),
                    event_type="tax_utility",
                    amount=200_000,
                    expense_type="social_insurance",
                ),
            ],
        ),
        [voucher],
    )

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

    ready = sum(
        item.calculation_status is CalculationStatus.READY_WITH_USER_SCENARIO
        for item in catalog.profiles
    )
    check("catalog_event_count", 30, len(catalog.profiles))
    check("catalog_policy_count", 10, len({item.policy_id for item in catalog.profiles}))
    check("ready_with_user_scenario", 27, ready)
    check("intentionally_blocked_or_unselected", 3, 30 - ready)
    check("grant_support", 3_000_000, grant.summary["support_amount"])
    check("grant_pre_financing", 4_000_000, grant.summary["pre_financing_required"])
    check("grant_user_contribution", 1_000_000, grant.summary["user_contribution"])
    check("grant_minimum_cash", -2_000_000, grant_impact.with_policy.weekly_summary.minimum_cash)
    check("voucher_cash_inflow", 0, voucher.summary["cash_inflow"])
    check("voucher_cost_reduction", 250_000, voucher.summary["cost_reduction"])
    check("voucher_6m_delta", 250_000, voucher_impact.delta["month6_ending_cash"])
    check("direct_loan_principal", 10_000_000, direct_loan.summary["new_debt_principal"])
    check("direct_loan_rate", 2.5, direct_loan.summary["gross_interest_rate_percent"])
    check("direct_loan_payments", 60, direct_loan.summary["payment_count"])
    check("direct_loan_maturity_balance", 0, direct_loan.summary["remaining_principal_at_maturity"])
    check("subsidized_gross_rate", 5.0, subsidized_loan.summary["gross_interest_rate_percent"])
    check(
        "subsidized_interest_reduction_positive",
        True,
        subsidized_loan.summary["total_interest_reduction"] > 0,
    )
    check(
        "subsidized_net_interest_lower",
        True,
        subsidized_loan.summary["total_net_interest"]
        < subsidized_loan.summary["total_gross_interest"],
    )
    check("refinance_old_payments", 12, refinance.summary["old_payment_count"])
    check("refinance_new_payments", 120, refinance.summary["new_payment_count"])
    check(
        "refinance_first_payment_lower",
        True,
        refinance.summary["first_payment_change"] < 0,
    )
    check(
        "refinance_total_interest_tradeoff",
        True,
        refinance.summary["total_interest_change"] > 0,
    )
    check("guarantee_without_loan_cash", 0, guarantee.summary["cash_inflow"])
    check(
        "guarantee_info_only",
        "information_only",
        guarantee.events[0].effect_kind.value,
    )
    serialized = json.dumps(
        [plan.model_dump(mode="json") for plan in plans], ensure_ascii=False
    )
    check("approval_probability_absent", False, "approval_probability" in serialized)
    repeated_grant_impact = apply_policy_plan(
        DetailedCashflowInput(
            reference_date=date(2026, 9, 1),
            opening_cash=2_000_000,
            safe_cash_threshold=1_000_000,
            events=[],
            loans=[],
        ),
        [grant],
    )
    check(
        "deterministic_grant_application",
        True,
        grant_impact.model_dump(mode="json")
        == repeated_grant_impact.model_dump(mode="json"),
    )
    if not all(item["passed"] for item in checks):
        failed = [item["check"] for item in checks if not item["passed"]]
        raise RuntimeError(f"RE Stage 4 verification failed: {failed}")

    write_json(
        REPORTS / "input_schema.json",
        {
            "grant": GrantScenario.model_json_schema(),
            "voucher": VoucherScenario.model_json_schema(),
            "loan": LoanScenario.model_json_schema(),
            "refinance": RefinanceScenario.model_json_schema(),
            "guarantee": GuaranteeScenario.model_json_schema(),
            "financial_event": PolicyFinancialEvent.model_json_schema(),
            "policy_plan": PolicyPlan.model_json_schema(),
        },
    )
    write_json(
        REPORTS / "representative_scenarios.json",
        {
            "plans": [plan.model_dump(mode="json") for plan in plans],
            "grant_impact_delta": grant_impact.delta,
            "voucher_impact_delta": voucher_impact.delta,
        },
    )
    with (REPORTS / "assumption_ledger.jsonl").open("w", encoding="utf-8") as stream:
        for plan in plans:
            for assumption in plan.assumptions:
                stream.write(
                    json.dumps(
                        {
                            "policy_id": plan.policy_id,
                            "event_id": plan.event_id,
                            **assumption.model_dump(mode="json"),
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
    with (REPORTS / "financial_event_schedule.jsonl").open(
        "w", encoding="utf-8"
    ) as stream:
        for plan in plans:
            for event in plan.events:
                stream.write(
                    json.dumps(event.model_dump(mode="json"), ensure_ascii=False) + "\n"
                )
    with (REPORTS / "manual_check.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as stream:
        writer = csv.DictWriter(
            stream, fieldnames=("check", "expected", "actual", "passed")
        )
        writer.writeheader()
        writer.writerows(checks)

    audit = {
        "status": "pass",
        "policy_count": 10,
        "financial_event_count": 30,
        "ready_with_user_scenario": ready,
        "blocked_missing_official_terms": sum(
            item.calculation_status
            is CalculationStatus.BLOCKED_MISSING_OFFICIAL_TERMS
            for item in catalog.profiles
        ),
        "requires_subproduct_selection": sum(
            item.calculation_status
            is CalculationStatus.REQUIRES_SUBPRODUCT_SELECTION
            for item in catalog.profiles
        ),
        "representative_plan_count": len(plans),
        "representative_financial_event_count": sum(len(plan.events) for plan in plans),
        "manual_check_count": len(checks),
        "manual_check_passed": sum(bool(item["passed"]) for item in checks),
        "external_data_used": False,
        "approval_probability_generated": False,
        "causal_effect_claim_generated": False,
    }
    write_json(REPORTS / "catalog_audit.json", audit)

    tracked = [
        ROOT / "src" / "policy" / "catalog.py",
        ROOT / "src" / "policy" / "schemas.py",
        ROOT / "src" / "policy" / "converters.py",
        ROOT / "src" / "policy" / "apply.py",
        ROOT / "config" / "re_stage4.yaml",
        profiles_path,
        REPORTS / "input_schema.json",
        REPORTS / "representative_scenarios.json",
        REPORTS / "assumption_ledger.jsonl",
        REPORTS / "financial_event_schedule.jsonl",
        REPORTS / "manual_check.csv",
        REPORTS / "catalog_audit.json",
    ]
    write_json(
        REPORTS / "manifest.json",
        {
            "stage": "RE Stage 4",
            "status": "completed",
            "engine_version": "re4-v1",
            "verification_date": "2026-08-16",
            "files": [
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
                for path in tracked
            ],
        },
    )
    print(f"RE_STAGE4=PASSED checks={len(checks)}/{len(checks)} events=30")


if __name__ == "__main__":
    main()
