"""Stable, field-addressable errors for cash-flow input."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class InputIssue:
    code: str
    field: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "field": self.field, "message": self.message}


class CashflowInputError(ValueError):
    """Raised when an input cannot be calculated without inventing a value."""

    def __init__(self, code: str, field: str, message: str) -> None:
        self.code = code
        self.field = field
        self.message = message
        super().__init__(f"{code} [{field}]: {message}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "error",
            "error_code": self.code,
            "field": self.field,
            "message": self.message,
        }
