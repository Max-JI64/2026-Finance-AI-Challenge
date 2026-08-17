"""Generate deterministic RE8 OpenAPI and version manifest artifacts."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app
from src.integration.re_stage8 import VERSIONS
from src.rag.local_db import DATABASE_PATH


REPORT_DIR = PROJECT_ROOT / "reports/re_stage8"
TRACKED = [
    "app/main.py",
    "app/static/index.html",
    "app/static/styles.css",
    "app/static/app.js",
    "app/static/templates/거래내역_입력양식.csv",
    "app/static/templates/대출_입력양식.csv",
    "src/integration/re_stage8.py",
    "src/cashflow/quick_mode.py",
    "src/models/re_stage5_scenario_service.py",
    "src/rag/local_db.py",
    "src/rag/luna_client.py",
    "scripts/build_re_stage8_service_data.py",
    "config/re_stage8.yaml",
    "data/processed_re/re_stage8/commercial_area_points.json",
    "data/processed_re/re_stage8/market_features_2025q4.parquet",
    "data/processed_re/re_stage8/service_data_manifest.json",
    "rag/index/policy_re8.sqlite3",
    "tests/test_re_stage8.py",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    openapi_path = REPORT_DIR / "openapi.json"
    openapi_path.write_text(
        json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        chunk_count = connection.execute("SELECT COUNT(*) FROM policy_chunks").fetchone()[0]
        policy_count = connection.execute("SELECT COUNT(DISTINCT policy_id) FROM policy_chunks").fetchone()[0]
    finally:
        connection.close()
    manifest = {
        "stage": "RE Stage 8.1",
        "status": "complete",
        "gate": "passed",
        "as_of_date": "2026-08-17",
        "versions": VERSIONS,
        "local_rag": {
            "database": str(DATABASE_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "chunk_count": chunk_count,
            "policy_count": policy_count,
            "stores_user_queries": False,
            "stores_session_profiles": False,
        },
        "artifacts": {
            relative: {
                "sha256": sha256(PROJECT_ROOT / relative),
                "bytes": (PROJECT_ROOT / relative).stat().st_size,
            }
            for relative in TRACKED
        },
        "openapi": {
            "path": "reports/re_stage8/openapi.json",
            "sha256": sha256(openapi_path),
            "path_count": len(app.openapi()["paths"]),
        },
        "legacy_re8_screen_samples": {
            "status": "not_re8.1_evidence",
            "items": {
                path.name: {
                    "sha256": sha256(path),
                    "bytes": path.stat().st_size,
                }
                for path in sorted((REPORT_DIR / "screens").glob("*.png"))
            },
        },
    }
    (REPORT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"paths": manifest["openapi"]["path_count"], "chunks": chunk_count}))


if __name__ == "__main__":
    main()
