"""UTF-8 CSV adapters for the detailed RE Stage 3 input contract."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from pydantic import ValidationError

from .errors import CashflowInputError
from .schemas import CashEvent, DetailedCashflowInput, LoanInput


EVENT_COLUMNS = (
    "event_id",
    "event_date",
    "event_type",
    "amount",
    "expense_type",
    "description",
    "source",
)
LOAN_COLUMNS = (
    "loan_id",
    "principal",
    "annual_interest_rate_percent",
    "repayment_method",
    "payment_day",
    "maturity_date",
    "grace_months",
)


def _read_rows(path: Path, expected: tuple[str, ...]) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if tuple(reader.fieldnames or ()) != expected:
                raise CashflowInputError(
                    "CSV_HEADER_MISMATCH",
                    str(path),
                    f"필수 헤더 순서: {','.join(expected)}",
                )
            return list(reader)
    except UnicodeDecodeError as exc:
        raise CashflowInputError(
            "CSV_ENCODING_ERROR", str(path), "CSV는 UTF-8 또는 UTF-8-SIG여야 합니다."
        ) from exc


def _parse_int(value: str, field: str) -> int:
    if value.strip() == "":
        raise CashflowInputError("MISSING_REQUIRED_VALUE", field, "필수 값이 비어 있습니다.")
    try:
        parsed = int(value)
    except ValueError as exc:
        raise CashflowInputError(
            "INVALID_WON_AMOUNT", field, "원 단위 정수를 입력해야 합니다."
        ) from exc
    return parsed


def _validation_error(field: str, exc: ValidationError) -> CashflowInputError:
    first = exc.errors()[0]
    location = ".".join(str(part) for part in first["loc"])
    return CashflowInputError(
        "INVALID_INPUT", f"{field}.{location}", str(first["msg"])
    )


def load_detailed_csv(
    events_path: Path,
    loans_path: Path,
    *,
    reference_date: date,
    opening_cash: int,
    safe_cash_threshold: int,
) -> DetailedCashflowInput:
    event_rows = _read_rows(events_path, EVENT_COLUMNS)
    loan_rows = _read_rows(loans_path, LOAN_COLUMNS)
    events: list[CashEvent] = []
    loans: list[LoanInput] = []
    for index, row in enumerate(event_rows, start=2):
        payload = dict(row)
        payload["amount"] = _parse_int(row["amount"], f"events.row{index}.amount")
        payload["expense_type"] = row["expense_type"] or None
        try:
            events.append(CashEvent.model_validate(payload))
        except ValidationError as exc:
            raise _validation_error(f"events.row{index}", exc) from exc
    for index, row in enumerate(loan_rows, start=2):
        payload = dict(row)
        for column in ("principal", "payment_day", "grace_months"):
            payload[column] = _parse_int(row[column], f"loans.row{index}.{column}")
        try:
            payload["annual_interest_rate_percent"] = float(
                row["annual_interest_rate_percent"]
            )
        except ValueError as exc:
            raise CashflowInputError(
                "INVALID_PERCENTAGE",
                f"loans.row{index}.annual_interest_rate_percent",
                "연이율은 백분율 숫자여야 합니다.",
            ) from exc
        try:
            loans.append(LoanInput.model_validate(payload))
        except ValidationError as exc:
            raise _validation_error(f"loans.row{index}", exc) from exc
    try:
        return DetailedCashflowInput(
            reference_date=reference_date,
            opening_cash=opening_cash,
            safe_cash_threshold=safe_cash_threshold,
            events=events,
            loans=loans,
        )
    except ValidationError as exc:
        raise _validation_error("input", exc) from exc
