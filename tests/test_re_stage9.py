import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = PROJECT_ROOT / "reports/re_stage9"


def test_re9_frozen_persona_oracle_passes_all_eight() -> None:
    oracle = json.loads((REPORT_DIR / "persona_oracle.json").read_text(encoding="utf-8"))
    assert oracle["persona_count"] == 8
    assert oracle["persona_pass_count"] == 8
    assert oracle["gate_passed_local"] is True
    assert oracle["screenshot_image_analysis_performed"] is False
    assert not oracle["prohibited_positive_claim_hits"]
    assert oracle["persona_input_sha256"] == hashlib.sha256(
        (PROJECT_ROOT / "data/samples/re_stage9/personas.json").read_bytes()
    ).hexdigest()


def test_re9_retrieval_contract_has_two_cases_per_representative_policy() -> None:
    oracle = json.loads((REPORT_DIR / "persona_oracle.json").read_text(encoding="utf-8"))
    counts = {}
    for item in oracle["retrieval_results"]:
        counts[item["policy_id"]] = counts.get(item["policy_id"], 0) + 1
        assert item["hit_at_5"] is True
    assert len(counts) == 10
    assert set(counts.values()) == {2}
    assert oracle["retrieval_pass_count"] == 20


def test_re9_partial_refinance_and_fallback_trace_are_frozen() -> None:
    oracle = json.loads((REPORT_DIR / "persona_oracle.json").read_text(encoding="utf-8"))
    by_id = {item["persona_id"]: item for item in oracle["personas"]}
    assert by_id["P02"]["partial_refinance"]["refinanced_principal"] == 50_000_000
    assert by_id["P02"]["partial_refinance"]["net_new_borrowing"] == 0
    assert by_id["P05"]["dynamic_workflow"]["passed"] is True
    assert by_id["P08"]["embedding_attempts"] == 2
    assert by_id["P08"]["retrieval_mode"] == "bm25_fallback"
    assert by_id["P08"]["invalid_input"]["safe_error_shape"] is True


def test_re9_manifest_hashes_and_external_gate_remain_honest() -> None:
    manifest = json.loads((REPORT_DIR / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["gate_passed_local"] is True
    assert manifest["gate_passed_re9"] is False
    assert manifest["external_blockers"]
    for item in manifest["outputs"]:
        path = PROJECT_ROOT / item["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]


def test_deployment_contract_has_healthcheck_nonroot_and_no_secret() -> None:
    dockerfile = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")
    runtime = (PROJECT_ROOT / "requirements-runtime.txt").read_text(encoding="utf-8")
    env_example = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")
    assert "HEALTHCHECK" in dockerfile
    assert "USER appuser" in dockerfile
    assert "uvicorn app.main:app --host 0.0.0.0" in dockerfile
    assert "pytest" not in runtime
    assert "OPENAI_API_KEY=" in env_example
    assert "sk-" not in env_example


def test_health_and_public_page_do_not_expose_internal_ids() -> None:
    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    html = client.get("/").text
    assert "rule_id" not in html.lower()
    assert "chunk_id" not in html.lower()
    assert "search_score" not in html.lower()
