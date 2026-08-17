"""Build the frozen RE9 persona oracle and local QA evidence."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from contextlib import contextmanager
from datetime import date
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from app.main import app
from scripts.build_re_stage7_examples import build_hero
from src.integration.re_stage8 import (
    SampleCompareRequest,
    _dynamic_policy_alternatives,
    _load_sample,
)
from src.policy.discovery import DiscoveryEligibilityEngine, staged_questions
from src.policy.eligibility import SessionEligibilityProfile
from src.policy.re_stage8_2_events import DynamicPolicyScenario
from src.rag.hybrid_search import HybridPolicySearchIndex
import src.rag.openai_embeddings as embedding_module


PERSONA_PATH = PROJECT_ROOT / "data/samples/re_stage9/personas.json"
RETRIEVAL_PATH = PROJECT_ROOT / "data/samples/re_stage9/retrieval_cases.json"
REPORT_DIR = PROJECT_ROOT / "reports/re_stage9"
AS_OF = date(2026, 8, 17)
PROHIBITED_POSITIVE_CLAIMS = (
    "AI가 미래를 예측하고 최적 정책을 추천합니다",
    "개인 점포 폐업확률을 예측합니다",
    "대출 승인 가능성을 예측합니다",
    "정책 수혜로 매출이 회복됩니다",
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


@contextmanager
def embedding_mode(force_retry_failure: bool):
    previous_key = os.environ.get("OPENAI_API_KEY")
    original_urlopen = embedding_module.urlopen
    attempts = {"count": 0}
    embedding_module._SINGLE_TEXT_CACHE.clear()
    if force_retry_failure:
        os.environ["OPENAI_API_KEY"] = "re9-test-nonsecret"

        def fail_urlopen(*_args, **_kwargs):
            attempts["count"] += 1
            raise HTTPError(
                embedding_module.EMBEDDINGS_URL,
                500,
                "RE9 simulated outage",
                {},
                BytesIO(),
            )

        embedding_module.urlopen = fail_urlopen
    else:
        os.environ["OPENAI_API_KEY"] = ""
    try:
        yield attempts
    finally:
        embedding_module.urlopen = original_urlopen
        embedding_module._SINGLE_TEXT_CACHE.clear()
        if previous_key is None:
            os.environ.pop("OPENAI_API_KEY", None)
        else:
            os.environ["OPENAI_API_KEY"] = previous_key


def alternative_summary(payload: dict, alternative_id: str) -> dict:
    item = next(
        row
        for row in payload["intervention_results"]
        if row["alternative_id"] == alternative_id
    )
    metrics = item.get("metrics") or {}
    return {
        "alternative_id": alternative_id,
        "candidate_state": item["candidate_state"],
        "ranking_eligible": item["ranking_eligible"],
        "week13_ending_cash": metrics.get("week13_ending_cash"),
        "month6_ending_cash": metrics.get("month6_ending_cash"),
        "week13_minimum_cash": metrics.get("week13_minimum_cash"),
        "net_new_borrowing": metrics.get("net_new_borrowing"),
        "refinanced_principal": metrics.get("refinanced_principal"),
        "maximum_monthly_debt_service": metrics.get(
            "maximum_monthly_debt_service"
        ),
        "total_interest_through_maturity": metrics.get(
            "total_interest_through_maturity"
        ),
        "confirmation_item_count": metrics.get("confirmation_item_count"),
    }


def dynamic_workflow(persona: dict) -> dict:
    spec = persona["dynamic_workflow"]
    search = HybridPolicySearchIndex().search(
        spec["query"], mode="bm25", top_k=5, max_chunks_per_policy=1
    )
    retrieved_ids = [item.chunk.policy_id for item in search.results]
    partial_profile = SessionEligibilityProfile.model_validate(
        spec["partial_profile"]
    )
    questions = staged_questions([spec["policy_id"]], partial_profile)
    complete_profile = SessionEligibilityProfile.model_validate(
        spec["complete_profile"]
    )
    decision = DiscoveryEligibilityEngine().evaluate(
        spec["policy_id"], complete_profile, district="", as_of=AS_OF
    )
    scenario = DynamicPolicyScenario(
        policy_id=spec["policy_id"],
        approved_support_amount=spec["approved_support_amount"],
        payment_date=date.fromisoformat(spec["payment_date"]),
    )
    request = SampleCompareRequest(
        sample_id=persona["comparison_request"]["sample_id"],
        policy_scenarios=[scenario],
        eligibility_profile=complete_profile,
    )
    alternatives = _dynamic_policy_alternatives(
        request,
        {"candidates": [decision]},
        reference_date=_load_sample(request.sample_id).reference_date,
    )
    result, _ = build_hero(
        _load_sample(request.sample_id), additional_alternatives=alternatives
    )
    alternative_id = f"dynamic_{spec['policy_id'].lower()}"
    dynamic = next(
        item for item in result.alternatives if item.alternative_id == alternative_id
    )
    assert dynamic.metrics is not None
    return {
        "retrieval_mode": search.retrieval_mode,
        "retrieved_policy_ids": retrieved_ids,
        "target_policy_retrieved": spec["policy_id"] in retrieved_ids,
        "staged_question_fields": [item["field"] for item in questions],
        "completed_eligibility_status": decision["eligibility_status"],
        "completed_candidate_state": decision["candidate_state"],
        "dynamic_alternative_id": alternative_id,
        "dynamic_support_amount": dynamic.metrics.support_or_cost_reduction,
        "dynamic_week13_minimum_cash": dynamic.metrics.week13_minimum_cash,
        "dynamic_ranking_eligible": dynamic.ranking_eligible,
        "ranking_trace": {
            ranking.goal.value: ranking.ordered_alternative_ids
            for ranking in result.rankings
        },
        "passed": (
            spec["policy_id"] in retrieved_ids
            and bool(questions)
            and decision["candidate_state"] == "지금 비교 가능"
            and dynamic.metrics.support_or_cost_reduction
            == spec["approved_support_amount"]
            and any(
                alternative_id in ranking.ordered_alternative_ids
                for ranking in result.rankings
            )
        ),
    }


def run_persona(client: TestClient, persona: dict) -> dict:
    with embedding_mode(bool(persona.get("force_embedding_retry_failure"))) as attempts:
        response = client.post(
            "/api/v1/alternatives/compare",
            json=persona["comparison_request"],
        )
    if response.status_code != 200:
        raise RuntimeError(
            f"{persona['persona_id']} comparison failed: {response.status_code} {response.text}"
        )
    payload = response.json()
    no_action = alternative_summary(payload, "no_action")
    focus_id = persona.get("focus_alternative_id") or payload["comparison_result"][
        "top_alternative_id"
    ]
    focus = alternative_summary(payload, focus_id)
    weekly_last = next(
        item
        for item in payload["intervention_results"]
        if item["alternative_id"] == "no_action"
    )["weekly_13"][-1]["closing_cash"]
    output = {
        "persona_id": persona["persona_id"],
        "name": persona["name"],
        "input_sha256": sha256_bytes(
            json.dumps(
                persona, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ),
        "screen_step_count": 4,
        "sample_notice": payload["sample"]["notice"],
        "external_scenario_source": payload["external_scenario"]["source"],
        "retrieval_mode": payload["policy_discovery"]["retrieval_mode"],
        "embedding_attempts": attempts["count"],
        "candidate_count": len(payload["policy_discovery"]["candidates"]),
        "staged_question_count": len(payload["policy_discovery"]["staged_questions"]),
        "selected_goal": payload["comparison_result"]["selected_goal"],
        "top_alternative_id": payload["comparison_result"]["top_alternative_id"],
        "ranking_trace": payload["comparison_result"]["ordered_alternative_ids"],
        "no_action": no_action,
        "focus_alternative": focus,
        "graph_metric_match": weekly_last == no_action["week13_ending_cash"],
        "raw_internal_identifier_exposed": any(
            token in response.text for token in ('"chunk_id"', '"rule_id"', '"search_score"')
        ),
    }
    if persona.get("eligibility_probe"):
        eligibility = client.post(
            "/api/v1/policies/eligibility", json=persona["eligibility_probe"]
        )
        if eligibility.status_code != 200:
            raise RuntimeError(f"{persona['persona_id']} eligibility probe failed")
        output["eligibility_probe"] = eligibility.json()["eligibility_results"][0]
    if persona.get("dynamic_workflow"):
        output["dynamic_workflow"] = dynamic_workflow(persona)
    if persona.get("invalid_request"):
        marker = "re9-sensitive-marker"
        bad = dict(persona["invalid_request"])
        bad["area_code"] = marker
        invalid = client.post("/api/v1/alternatives/compare", json=bad)
        output["invalid_input"] = {
            "status_code": invalid.status_code,
            "safe_error_shape": (
                invalid.status_code == 422
                and marker not in invalid.text
                and invalid.json().get("error") == "invalid_input"
            ),
        }
    checks = [
        output["screen_step_count"] == 4,
        "가상 사업장" in output["sample_notice"],
        output["graph_metric_match"],
        not output["raw_internal_identifier_exposed"],
    ]
    if persona["persona_id"] == "P02":
        refinance = alternative_summary(payload, "refinance")
        output["partial_refinance"] = refinance
        checks.extend(
            [
                refinance["refinanced_principal"] == 50_000_000,
                refinance["net_new_borrowing"] == 0,
            ]
        )
    if persona["persona_id"] == "P04":
        checks.append(focus["week13_minimum_cash"] < 0)
    if persona.get("eligibility_probe"):
        probe = output["eligibility_probe"]
        checks.append(probe["candidate_state"] == "제외")
    if persona.get("dynamic_workflow"):
        checks.append(output["dynamic_workflow"]["passed"])
    if persona.get("force_embedding_retry_failure"):
        checks.extend(
            [
                attempts["count"] == 2,
                output["retrieval_mode"] == "bm25_fallback",
                output["invalid_input"]["safe_error_shape"],
                "직접 입력 Fallback" in output["external_scenario_source"],
            ]
        )
    output["passed"] = all(checks)
    return output


def retrieval_evaluation() -> list[dict]:
    cases = json.loads(RETRIEVAL_PATH.read_text(encoding="utf-8"))
    index = HybridPolicySearchIndex()
    rows = []
    for case in cases:
        outcome = index.search(
            case["query"], mode="bm25", top_k=5, max_chunks_per_policy=1
        )
        ranked = [item.chunk.policy_id for item in outcome.results]
        rank = ranked.index(case["policy_id"]) + 1 if case["policy_id"] in ranked else None
        rows.append(
            {
                **case,
                "retrieval_mode": outcome.retrieval_mode,
                "rank": rank,
                "hit_at_5": rank is not None,
                "retrieved_policy_ids": ranked,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def main() -> None:
    personas = json.loads(PERSONA_PATH.read_text(encoding="utf-8"))
    if len(personas) != 8:
        raise ValueError("RE9 persona contract must contain exactly 8 personas")
    client = TestClient(app)
    results = [run_persona(client, persona) for persona in personas]
    retrieval = retrieval_evaluation()
    html = client.get("/").text
    prohibited_hits = [claim for claim in PROHIBITED_POSITIVE_CLAIMS if claim in html]
    persona_pass_count = sum(item["passed"] for item in results)
    retrieval_pass_count = sum(item["hit_at_5"] for item in retrieval)
    oracle = {
        "contract_version": "re9-v1",
        "as_of_date": AS_OF.isoformat(),
        "persona_input_sha256": sha256_file(PERSONA_PATH),
        "retrieval_input_sha256": sha256_file(RETRIEVAL_PATH),
        "persona_count": len(results),
        "persona_pass_count": persona_pass_count,
        "retrieval_case_count": len(retrieval),
        "retrieval_pass_count": retrieval_pass_count,
        "prohibited_positive_claim_hits": prohibited_hits,
        "screenshot_image_analysis_performed": False,
        "personas": results,
        "retrieval_results": retrieval,
        "gate_passed_local": (
            persona_pass_count == 8
            and retrieval_pass_count == 20
            and not prohibited_hits
        ),
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    oracle_path = REPORT_DIR / "persona_oracle.json"
    write_json(oracle_path, oracle)
    write_csv(
        REPORT_DIR / "persona_summary.csv",
        results,
        [
            "persona_id",
            "name",
            "input_sha256",
            "selected_goal",
            "top_alternative_id",
            "retrieval_mode",
            "embedding_attempts",
            "candidate_count",
            "staged_question_count",
            "graph_metric_match",
            "passed",
        ],
    )
    write_csv(
        REPORT_DIR / "retrieval_20_cases.csv",
        retrieval,
        ["case_id", "policy_id", "query", "retrieval_mode", "rank", "hit_at_5"],
    )
    lines = [
        "# RE Stage 9 로컬 자동 QA",
        "",
        f"- 계약: `re9-v1` / 기준일: {AS_OF.isoformat()}",
        f"- 가상 페르소나: `{persona_pass_count}/8`",
        f"- 대표 10개 정책 공식근거 검색: `{retrieval_pass_count}/20` Hit@5",
        f"- 금지된 긍정 주장: `{len(prohibited_hits)}건`",
        "- 스크린샷 이미지 분석: 사용자 요청에 따라 미실시",
        "- 외부 URL·운영계정·실제 Usage tier·운영 API 키: 사용자 배포 결정 전 미검증",
        "",
        "## 페르소나 결과",
        "",
        "| ID | 상황 | 목표 | 1순위 | 검색 | 통과 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in results:
        lines.append(
            f"| {item['persona_id']} | {item['name']} | {item['selected_goal']} | "
            f"{item['top_alternative_id']} | {item['retrieval_mode']} | "
            f"{'통과' if item['passed'] else '실패'} |"
        )
    lines.extend(
        [
            "",
            "## 해석 경계",
            "",
            "이 결과는 고정 가상 사업장의 기능·수치 일치 검증이다. 실제 사용성, 만족도, 정책 승인 가능성 또는 정책의 현실 효과를 입증하지 않는다.",
        ]
    )
    (REPORT_DIR / "verification.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    output_paths = [
        oracle_path,
        REPORT_DIR / "persona_summary.csv",
        REPORT_DIR / "retrieval_20_cases.csv",
        REPORT_DIR / "verification.md",
        REPORT_DIR / "functional_spec.md",
        REPORT_DIR / "functional_spec_pdf_qa.json",
        REPORT_DIR / "deployment_runbook.md",
        REPORT_DIR / "final_qa_report.md",
        REPORT_DIR / "presentation_evidence.md",
        REPORT_DIR / "기획서_제출본.md",
        PROJECT_ROOT / "output/pdf/RE9_기능명세서.pdf",
        PROJECT_ROOT / "프로젝트 계획서.md",
        PROJECT_ROOT / "MVP 단계별 구현 체크리스트.md",
        PROJECT_ROOT / "README.md",
    ]
    missing_outputs = [
        path.relative_to(PROJECT_ROOT).as_posix()
        for path in output_paths
        if not path.is_file()
    ]
    if missing_outputs:
        raise FileNotFoundError(f"Missing RE9 output files: {missing_outputs}")
    write_json(
        REPORT_DIR / "manifest.json",
        {
            "contract_version": "re9-v1",
            "status": "local_qa_complete_external_deployment_pending"
            if oracle["gate_passed_local"]
            else "local_qa_failed",
            "gate_passed_local": oracle["gate_passed_local"],
            "gate_passed_re9": False,
            "external_blockers": [
                "deployment platform and account approval",
                "public URL and submission-period availability",
                "deployment account Usage tier and production API key",
                "live mobile and desktop DOM QA",
                "demo-day current policy status and official-link recheck",
            ],
            "local_limits": [
                "Docker CLI is not installed, so the container image was not built locally",
                "No automation browser was connected, so local browser DOM QA was not rerun",
                "Screenshot image analysis was excluded by user request",
            ],
            "outputs": [
                {
                    "path": path.relative_to(PROJECT_ROOT).as_posix(),
                    "sha256": sha256_file(path),
                }
                for path in output_paths
            ],
        },
    )
    if not oracle["gate_passed_local"]:
        raise SystemExit(
            f"RE9 local QA failed: personas={persona_pass_count}/8, retrieval={retrieval_pass_count}/20"
        )
    print(
        f"RE9 local QA passed: personas={persona_pass_count}/8, retrieval={retrieval_pass_count}/20"
    )


if __name__ == "__main__":
    main()
