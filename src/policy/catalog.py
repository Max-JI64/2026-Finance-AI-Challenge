"""Read the reviewed RE2 policy catalog without filling unknown official terms."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from pathlib import Path

from src.settings import PROJECT_ROOT


FINANCIAL_METADATA = (
    PROJECT_ROOT / "data" / "processed_re" / "policy" / "re_stage2" / "financial_metadata.csv"
)
POLICY_METADATA = (
    PROJECT_ROOT / "data" / "processed_re" / "policy" / "re_stage2" / "policy_metadata.csv"
)


class SupportKind(StrEnum):
    DIRECT_LOAN = "direct_loan"
    INTEREST_SUBSIDIZED_LOAN = "interest_subsidized_loan"
    REFINANCE = "refinance"
    GRANT = "grant"
    REIMBURSEMENT_GRANT = "reimbursement_grant"
    VOUCHER = "voucher"
    GUARANTEE = "guarantee"
    CREDIT_LINE = "credit_line"
    INSPECTION_SUPPORT = "inspection_support"


class CalculationStatus(StrEnum):
    READY_WITH_USER_SCENARIO = "ready_with_user_scenario"
    BLOCKED_MISSING_OFFICIAL_TERMS = "blocked_missing_official_terms"
    REQUIRES_SUBPRODUCT_SELECTION = "requires_subproduct_selection"


@dataclass(frozen=True)
class SubsidyPhase:
    months: int
    percentage_points: float


@dataclass(frozen=True)
class PolicyEventProfile:
    policy_id: str
    policy_version: str
    event_id: str
    event_name: str
    support_form: str
    support_kind: SupportKind
    calculation_status: CalculationStatus
    maximum_amount: int | None
    official_interest_rate_percent: float | None
    reference_rate_spread_percent: float | None
    subsidy_phases: tuple[SubsidyPhase, ...]
    effective_from: date | None
    effective_to: date | None
    linked_event_id: str | None
    deduplication_key: str
    raw: dict[str, str]

    @property
    def missing_or_unquantifiable(self) -> tuple[str, ...]:
        values: list[str] = []
        for field in (
            "minimum_amount",
            "maximum_amount",
            "support_rate",
            "interest_rate_rule",
            "interest_subsidy_rule",
            "guarantee_fee_rule",
            "grace_period",
            "repayment_period",
            "repayment_method",
            "matching_fund_rate",
            "payment_method",
            "reimbursement_delay_rule",
        ):
            if self.raw.get(field) == "미확인":
                values.append(field)
        if self.raw.get("unquantifiable_conditions") not in {"", "해당 없음", "미확인"}:
            values.append("unquantifiable_conditions")
        return tuple(values)


def _parse_date(value: str) -> date | None:
    if not value or value in {"미확인", "자금소진시", "예산소진시", "모집마감시"}:
        return None
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})", value)
    if not match:
        return None
    return date(*(int(part) for part in match.groups()))


def _parse_amount(value: str) -> int | None:
    return int(value) if value.isdigit() else None


def _support_kind(row: dict[str, str]) -> SupportKind:
    event_id = row["event_id"]
    form = row["support_form"]
    if event_id == "SEMAS_REFINANCE":
        return SupportKind.REFINANCE
    if event_id == "ZERO_MARKET_GRANT" or form == "사후정산 보조금":
        return SupportKind.REIMBURSEMENT_GRANT
    if form == "보조금":
        return SupportKind.GRANT
    if form == "카드 바우처":
        return SupportKind.VOUCHER
    if form == "보증·이차보전 연계":
        return SupportKind.GUARANTEE
    if form == "은행협력자금":
        return SupportKind.INTEREST_SUBSIDIZED_LOAN
    if form in {"직접융자", "직접대출"}:
        return SupportKind.DIRECT_LOAN
    if form == "한도대출":
        return SupportKind.CREDIT_LINE
    if form == "검사비 지원":
        return SupportKind.INSPECTION_SUPPORT
    raise ValueError(f"Unsupported official support form: {form}")


def _calculation_status(event_id: str) -> CalculationStatus:
    if event_id == "SEOUL_FACILITY":
        return CalculationStatus.REQUIRES_SUBPRODUCT_SELECTION
    if event_id in {"SEOUL_SAFE_ACCOUNT", "SAFETY_TEST"}:
        return CalculationStatus.BLOCKED_MISSING_OFFICIAL_TERMS
    return CalculationStatus.READY_WITH_USER_SCENARIO


def _interest_terms(row: dict[str, str]) -> tuple[float | None, float | None]:
    rule = row["interest_rate_rule"]
    exact = re.fullmatch(r"연\s*(\d+(?:\.\d+)?)%\s*(?:고정)?", rule)
    if exact:
        return float(exact.group(1)), None
    spread = re.search(r"기준금리\s*\+(\d+(?:\.\d+)?)%p", rule)
    if spread:
        return None, float(spread.group(1))
    return None, None


def _subsidy_phases(event_id: str, rule: str) -> tuple[SubsidyPhase, ...]:
    if rule in {"해당 없음", "미확인", ""}:
        return ()
    if event_id == "SEOUL_MIDEAST":
        return (SubsidyPhase(24, 2.5), SubsidyPhase(36, 1.8))
    rate = re.search(r"(?:최대\s*)?(\d+(?:\.\d+)?)%p", rule)
    years = re.search(r"(\d+)년\s*이내", rule)
    if rate and years:
        return (SubsidyPhase(int(years.group(1)) * 12, float(rate.group(1))),)
    raise ValueError(f"Unparsed official interest subsidy rule: {event_id} {rule}")


def _links(policy_id: str, event_id: str) -> tuple[str | None, str]:
    if event_id == "RESTART_GUARANTEE":
        return "SEOUL_RESTART_FUND", "LINKED_RESTART_POLICY_LOAN"
    if event_id == "SEOUL_RESTART_FUND":
        return "RESTART_GUARANTEE", "LINKED_RESTART_POLICY_LOAN"
    return None, f"{policy_id}:{event_id}"


class PolicyCatalog:
    def __init__(
        self,
        financial_path: Path = FINANCIAL_METADATA,
        policy_path: Path = POLICY_METADATA,
    ) -> None:
        with policy_path.open("r", encoding="utf-8-sig", newline="") as stream:
            policy_rows = list(csv.DictReader(stream))
        with financial_path.open("r", encoding="utf-8-sig", newline="") as stream:
            financial_rows = list(csv.DictReader(stream))
        policy_by_id = {row["policy_id"]: row for row in policy_rows}
        profiles: list[PolicyEventProfile] = []
        for row in financial_rows:
            policy = policy_by_id[row["policy_id"]]
            official_rate, spread = _interest_terms(row)
            linked, dedup = _links(row["policy_id"], row["event_id"])
            profiles.append(
                PolicyEventProfile(
                    policy_id=row["policy_id"],
                    policy_version=policy["policy_version"],
                    event_id=row["event_id"],
                    event_name=row["event_name"],
                    support_form=row["support_form"],
                    support_kind=_support_kind(row),
                    calculation_status=_calculation_status(row["event_id"]),
                    maximum_amount=_parse_amount(row["maximum_amount"]),
                    official_interest_rate_percent=official_rate,
                    reference_rate_spread_percent=spread,
                    subsidy_phases=_subsidy_phases(
                        row["event_id"], row["interest_subsidy_rule"]
                    ),
                    effective_from=_parse_date(policy["effective_from"]),
                    effective_to=_parse_date(policy["effective_to"]),
                    linked_event_id=linked,
                    deduplication_key=dedup,
                    raw=row,
                )
            )
        self._profiles = tuple(profiles)
        self._by_key = {(item.policy_id, item.event_id): item for item in profiles}
        if len(self._profiles) != 30 or len(self._by_key) != 30:
            raise ValueError("RE4 catalog must contain 30 unique reviewed financial events")

    @property
    def profiles(self) -> tuple[PolicyEventProfile, ...]:
        return self._profiles

    def get(self, policy_id: str, event_id: str) -> PolicyEventProfile:
        try:
            return self._by_key[(policy_id, event_id)]
        except KeyError as exc:
            raise KeyError(f"Unknown approved policy event: {policy_id}/{event_id}") from exc
