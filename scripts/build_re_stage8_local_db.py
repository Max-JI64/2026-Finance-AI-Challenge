"""Build the RE8 local SQLite policy evidence database."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.local_db import build_local_policy_db


if __name__ == "__main__":
    print(json.dumps(build_local_policy_db(), ensure_ascii=False, sort_keys=True))
