"""Portable loading helpers for the completed RE5 LightGBM artifacts."""

from __future__ import annotations

import __main__
from pathlib import Path
from typing import Any

import joblib


def load_re_stage5_artifact(path: str | Path) -> dict[str, Any]:
    """Load an RE5 artifact, including the legacy ``__main__`` class reference.

    The one-time holdout runner was invoked with ``python -m`` and therefore
    serialized ``FittedSparsePreprocessor`` under ``__main__``.  The original
    artifact stays byte-for-byte unchanged; this compatibility shim supplies
    the same class while unpickling it from a different process.
    """

    from src.models.run_re_stage5_holdout import FittedSparsePreprocessor

    missing = object()
    previous = getattr(__main__, "FittedSparsePreprocessor", missing)
    setattr(__main__, "FittedSparsePreprocessor", FittedSparsePreprocessor)
    try:
        artifact = joblib.load(Path(path))
    finally:
        if previous is missing:
            delattr(__main__, "FittedSparsePreprocessor")
        else:
            setattr(__main__, "FittedSparsePreprocessor", previous)

    if not isinstance(artifact, dict):
        raise TypeError("RE5 artifact payload must be a dictionary.")
    return artifact
