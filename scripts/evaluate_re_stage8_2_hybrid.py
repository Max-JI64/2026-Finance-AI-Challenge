"""Evaluate BM25, vector, and Hybrid retrieval on one frozen Korean oracle."""

from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from datetime import date
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.rag.hybrid_search import HybridPolicySearchIndex
from src.rag.openai_embeddings import OpenAIEmbeddingError
from src.policy.discovery import DiscoveryEligibilityEngine
from src.policy.eligibility import SessionEligibilityProfile


CASES_PATH = ROOT / "data/samples/re_stage8_2/hybrid_evaluation_cases.json"
REPORT_DIR = ROOT / "reports/re_stage8_2"
JSON_PATH = REPORT_DIR / "hybrid_retrieval_evaluation.json"
MD_PATH = REPORT_DIR / "hybrid_retrieval_evaluation.md"
VARIANTS = (
    ("bm25", "bm25", "text-embedding-3-small"),
    ("vector-small", "vector", "text-embedding-3-small"),
    ("hybrid-small", "hybrid", "text-embedding-3-small"),
    ("vector-large", "vector", "text-embedding-3-large"),
    ("hybrid-large", "hybrid", "text-embedding-3-large"),
)
SELECTED_VARIANT = "hybrid-large"
THRESHOLDS = {
    "candidate_recall_at_5": 0.95,
    "hit_rate_at_5": 0.95,
    "mean_reciprocal_rank": 0.80,
}


def _evaluate_safety_cases(
    cases: list[dict[str, object]], index: HybridPolicySearchIndex
) -> dict[str, object]:
    engine = DiscoveryEligibilityEngine()
    rows: list[dict[str, object]] = []
    for case in cases:
        task = str(case["task"])
        passed = False
        actual: dict[str, object]
        if task == "eligibility":
            decision = engine.evaluate(
                str(case["policy_id"]),
                SessionEligibilityProfile.model_validate(case.get("profile") or {}),
                district=str(case.get("district") or ""),
                as_of=date(2026, 8, 17),
            )
            actual = {
                "candidate_state": decision["candidate_state"],
                "eligibility_status": decision["eligibility_status"],
                "availability_status": decision["availability_status"],
            }
            passed = all(
                actual[key.removeprefix("expected_")] == value
                for key, value in case.items()
                if key.startswith("expected_")
            )
        elif task == "version_filter":
            outcome = index.search(
                str(case["query"]),
                policy_id=str(case["policy_id"]),
                policy_version=str(case["policy_version"]),
                as_of=date(2026, 8, 17),
                mode="bm25",
                top_k=5,
            )
            actual = {"result_count": len(outcome.results)}
            passed = actual["result_count"] == case["expected_result_count"]
        elif task == "fallback":
            with patch(
                "src.rag.hybrid_search.OpenAIEmbeddingClient.embed",
                side_effect=OpenAIEmbeddingError("frozen safety case"),
            ):
                outcome = index.search(
                    str(case["query"]),
                    as_of=date(2026, 8, 17),
                    mode="hybrid",
                    model="text-embedding-3-large",
                    top_k=5,
                )
            actual = {"retrieval_mode": outcome.retrieval_mode}
            passed = actual["retrieval_mode"] == case["expected_retrieval_mode"]
        else:
            raise ValueError(f"지원하지 않는 safety task: {task}")
        rows.append({"case_id": case["case_id"], "task": task, "passed": passed, "actual": actual})
    return {
        "cases": len(rows),
        "passed": sum(bool(item["passed"]) for item in rows),
        "pass_rate": sum(bool(item["passed"]) for item in rows) / len(rows),
        "rows": rows,
    }


def evaluate() -> dict[str, object]:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    retrieval_cases = [case for case in cases if case.get("task", "retrieval") == "retrieval"]
    safety_cases = [case for case in cases if case.get("task") != "retrieval" and case.get("task")]
    index = HybridPolicySearchIndex()
    variants: dict[str, object] = {}
    for label, mode, model in VARIANTS:
        rows = []
        reciprocal_ranks: list[float] = []
        recalls: list[float] = []
        type_hits: dict[str, list[bool]] = defaultdict(list)
        started = time.perf_counter()
        for case in retrieval_cases:
            query_started = time.perf_counter()
            outcome = index.search(
                case["query"],
                as_of=date(2026, 8, 17),
                district=case.get("district"),
                top_k=5,
                mode=mode,
                model=model,
                max_chunks_per_policy=1,
            )
            returned = [item.chunk.policy_id for item in outcome.results]
            expected = set(case["expected_policy_ids"])
            found = expected.intersection(returned)
            hit_ranks = [rank for rank, policy_id in enumerate(returned, start=1) if policy_id in expected]
            first_rank = min(hit_ranks) if hit_ranks else None
            recall = len(found) / len(expected)
            hit = bool(found)
            reciprocal_ranks.append(0.0 if first_rank is None else 1.0 / first_rank)
            recalls.append(recall)
            type_hits[case["type"]].append(hit)
            rows.append(
                {
                    "case_id": case["case_id"],
                    "type": case["type"],
                    "query": case["query"],
                    "expected_policy_ids": case["expected_policy_ids"],
                    "returned_policy_ids": returned,
                    "first_relevant_rank": first_rank,
                    "recall_at_5": recall,
                    "latency_ms": round((time.perf_counter() - query_started) * 1000, 1),
                    "retrieval_mode": outcome.retrieval_mode,
                }
            )
        variants[label] = {
            "mode": mode,
            "model": None if mode == "bm25" else model,
            "cases": len(rows),
            "candidate_recall_at_5": sum(recalls) / len(recalls),
            "hit_rate_at_5": sum(bool(item["first_relevant_rank"]) for item in rows) / len(rows),
            "mean_reciprocal_rank": sum(reciprocal_ranks) / len(reciprocal_ranks),
            "total_latency_ms": round((time.perf_counter() - started) * 1000, 1),
            "hit_rate_by_type": {
                key: sum(values) / len(values) for key, values in sorted(type_hits.items())
            },
            "rows": rows,
        }
    safety = _evaluate_safety_cases(safety_cases, index)
    selected_metrics = variants[SELECTED_VARIANT]
    new_policy_rows = [
        row for row in selected_metrics["rows"]
        if str(row["case_id"]).startswith("new-")
    ]
    new_policy_hit_rate = sum(bool(row["first_relevant_rank"]) for row in new_policy_rows) / len(new_policy_rows)
    quality_gate = (
        all(selected_metrics[key] >= threshold for key, threshold in THRESHOLDS.items())
        and new_policy_hit_rate == 1.0
        and safety["pass_rate"] == 1.0
    )
    result = {
        "as_of_date": "2026-08-17",
        "oracle_cases": len(cases),
        "retrieval_cases": len(retrieval_cases),
        "safety_cases": len(safety_cases),
        "variants": variants,
        "selected_variant": SELECTED_VARIANT,
        "selection_approved_by_user": True,
        "thresholds": THRESHOLDS,
        "new_policy_hit_rate_at_5": new_policy_hit_rate,
        "safety_evaluation": safety,
        "quality_gate_passed": quality_gate,
        "query_persistence": False,
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# RE8.2 BM25·Vector·Hybrid 검색 평가",
        "",
        f"- 고정 한국어 정답계약: {len(cases)}건(검색 {len(retrieval_cases)}건 + 안전성 {len(safety_cases)}건)",
        "- 동일 질문을 BM25 단독, Vector 단독, Hybrid에 적용",
        "- 사용자 승인 선택: text-embedding-3-large 3072차원 + Hybrid",
        "",
        "| 방식 | Candidate Recall@5 | Hit@5 | MRR | 총 지연(ms) |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for label, _, _ in VARIANTS:
        item = variants[label]
        lines.append(
            f"| {label} | {item['candidate_recall_at_5']:.3f} | {item['hit_rate_at_5']:.3f} | {item['mean_reciprocal_rank']:.3f} | {item['total_latency_ms']:.1f} |"
        )
    lines.extend([
        "",
        f"신규 4개 정책 Hit@5: {new_policy_hit_rate:.3f}",
        f"안전성: {safety['passed']}/{safety['cases']} 통과",
        f"최종 품질 Gate: {'통과' if quality_gate else '실패'}",
    ])
    MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    summary = evaluate()
    print(
        json.dumps(
            {
                key: {
                    field: value
                    for field, value in item.items()
                    if field in {"candidate_recall_at_5", "hit_rate_at_5", "mean_reciprocal_rank", "total_latency_ms"}
                }
                for key, item in summary["variants"].items()
            }
            | {
                "selected_variant": summary["selected_variant"],
                "new_policy_hit_rate_at_5": summary["new_policy_hit_rate_at_5"],
                "safety_pass_rate": summary["safety_evaluation"]["pass_rate"],
                "quality_gate_passed": summary["quality_gate_passed"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
