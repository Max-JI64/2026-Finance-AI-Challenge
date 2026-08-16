"""Build and verify deterministic RE6 eligibility and official-policy index artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.policy.eligibility import EligibilityEngine, SessionEligibilityProfile, profile_from_reviewed_example
from src.rag.policy_index import PolicyChunk, PolicySearchIndex, content_hash
from src.rag.safe_explanation import SafeExplanation


CONFIG_PATH = ROOT / "config/re_stage6.yaml"
OUTPUT_DIR = ROOT / "data/processed_re/policy/re_stage6"
REPORT_DIR = ROOT / "reports/re_stage6"
INDEX_PATH = OUTPUT_DIR / "policy_index.jsonl"
EXAMPLE_RESULTS_PATH = OUTPUT_DIR / "eligibility_example_results.json"
MANIFEST_PATH = REPORT_DIR / "manifest.json"
VERIFICATION_PATH = REPORT_DIR / "verification.md"
EVALUATION_CASES_PATH = ROOT / "data/samples/re_stage6/rag_evaluation_cases.json"
RAG_EVALUATION_PATH = REPORT_DIR / "rag_evaluation.json"
RAG_EVALUATION_MD_PATH = REPORT_DIR / "rag_evaluation.md"
PROFILE_SCHEMA_PATH = OUTPUT_DIR / "session_eligibility_profile.schema.json"
EXPLANATION_SCHEMA_PATH = OUTPUT_DIR / "safe_explanation.schema.json"


def now_kst() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="minutes")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_date(value: str) -> date | None:
    if not value or value in {"미확인", "자금소진시", "예산소진시", "모집마감시"}:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_index(config: dict[str, object]) -> list[PolicyChunk]:
    source = config["source_contract"]
    metadata_rows = read_csv(ROOT / source["policy_metadata"])
    source_rows = read_csv(ROOT / source["source_manifest"])
    policy_by_id = {row["policy_id"]: row for row in metadata_rows}
    source_by_path = {row["source_path"]: row for row in source_rows}
    chunks: list[PolicyChunk] = []
    seen_chunk_ids: set[str] = set()
    with (ROOT / source["policy_chunks"]).open("r", encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            raw = json.loads(line)
            policy = policy_by_id[raw["policy_id"]]
            source_row = source_by_path.get(raw["source_path"])
            source_url = source_row["source_url"] if source_row else policy["official_notice_url"]
            source_type = (
                f"official_{source_row['source_role']}_{source_row['file_type']}"
                if source_row
                else "official_reviewed_extract"
            )
            chunk_id = raw["chunk_id"]
            if chunk_id in seen_chunk_ids:
                suffix = hashlib.sha256(raw["source_path"].encode("utf-8")).hexdigest()[:8]
                chunk_id = f"{chunk_id}::source::{suffix}"
            if chunk_id in seen_chunk_ids:
                raise RuntimeError(f"Duplicate enriched chunk_id: {chunk_id}")
            seen_chunk_ids.add(chunk_id)
            chunks.append(
                PolicyChunk(
                    policy_id=raw["policy_id"],
                    policy_version=policy["policy_version"],
                    chunk_id=chunk_id,
                    source_type=source_type,
                    source_path=raw["source_path"],
                    source_url=source_url,
                    page_or_section=raw["locator"],
                    effective_from=parse_date(policy["effective_from"]),
                    effective_to=parse_date(policy["effective_to"]),
                    retrieved_at=date.fromisoformat(policy["retrieved_at"]),
                    content_hash=content_hash(raw["text"]),
                    text=raw["text"],
                )
            )
    if len(chunks) != int(source["chunk_count"]):
        raise RuntimeError(f"Expected {source['chunk_count']} source chunks, got {len(chunks)}")
    for policy in metadata_rows:
        metadata_text = "\n".join(
            [
                f"정책명: {policy['policy_name']}",
                f"기관: {policy['provider']}",
                f"지원유형: {policy['policy_type']}",
                f"지원대상 지역: {policy['region_scope']}",
                f"지원대상 업종: {policy['industry_scope']}",
                f"업력조건: {policy['business_age_rule']}",
                f"매출조건: {policy['revenue_rule']}",
                f"상시근로자조건: {policy['employee_rule']}",
                f"신용·연체조건: {policy['credit_or_delinquency_rule']}",
                f"신청기간: {policy['application_start']} ~ {policy['application_end']}",
                f"접수상태 기준일 정보: {policy['application_status_as_of']}",
                f"공식공고: {policy['official_notice_url']}",
                f"신청페이지: {policy['application_url']}",
                f"문의처: {policy['inquiry']}",
            ]
        )
        metadata_chunk_id = f"{policy['policy_id']}::metadata::001"
        if metadata_chunk_id in seen_chunk_ids:
            raise RuntimeError(f"Duplicate metadata chunk_id: {metadata_chunk_id}")
        seen_chunk_ids.add(metadata_chunk_id)
        chunks.append(
            PolicyChunk(
                policy_id=policy["policy_id"],
                policy_version=policy["policy_version"],
                chunk_id=metadata_chunk_id,
                source_type="official_reviewed_metadata",
                source_path=policy["source_path"],
                source_url=policy["official_notice_url"],
                page_or_section="RE2 검수 정책 Metadata",
                effective_from=parse_date(policy["effective_from"]),
                effective_to=parse_date(policy["effective_to"]),
                retrieved_at=date.fromisoformat(policy["retrieved_at"]),
                content_hash=content_hash(metadata_text),
                text=metadata_text,
            )
        )
    expected_total = int(source["chunk_count"]) + int(source["derived_policy_metadata_chunk_count"])
    if len(chunks) != expected_total:
        raise RuntimeError(f"Expected {expected_total} indexed chunks, got {len(chunks)}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with INDEX_PATH.open("w", encoding="utf-8", newline="\n") as stream:
        for chunk in chunks:
            stream.write(json.dumps(chunk.model_dump(mode="json"), ensure_ascii=False) + "\n")
    return chunks


def evaluate_examples(config: dict[str, object]) -> list[dict[str, object]]:
    examples = read_csv(ROOT / config["source_contract"]["eligibility_examples"])
    engine = EligibilityEngine()
    results: list[dict[str, object]] = []
    for example in examples:
        rule_ids = example["expected_rule_ids"].split(";")
        decision = engine.evaluate(
            example["policy_id"],
            profile_from_reviewed_example(example["decisive_inputs"]),
            as_of=date(2026, 8, 15),
            rule_ids=rule_ids,
            check_availability=False,
        )
        passed = decision.eligibility_status.value == example["expected_status"]
        results.append(
            {
                "example_id": example["example_id"],
                "policy_id": example["policy_id"],
                "expected_status": example["expected_status"],
                "actual_status": decision.eligibility_status.value,
                "passed": passed,
                "evaluated_rule_ids": rule_ids,
            }
        )
    if not all(item["passed"] for item in results):
        failed = [item for item in results if not item["passed"]]
        raise RuntimeError(f"Reviewed eligibility examples failed: {failed}")
    write_json(EXAMPLE_RESULTS_PATH, results)
    return results


def retrieval_smoke_tests(index: PolicySearchIndex) -> list[dict[str, object]]:
    cases = [
        ("POL_SEOUL_FUND_2026", "지원대상 융자 제한업종", ("지원대상", "제한업종")),
        ("POL_SEOUL_CRISIS_TRACK2_2026H2", "지원대상 매출 감소 임차 점포", ("매출", "임대차")),
        ("POL_SEMAS_REFINANCE_2026", "대환대출 금리와 지원대상", ("대환", "금리")),
        ("POL_SEMAS_STABILITY_VOUCHER_2026", "바우처 사용처와 신청대상", ("바우처", "매출")),
    ]
    rows: list[dict[str, object]] = []
    for policy_id, query, expected_any in cases:
        results = index.search(query, policy_id=policy_id, as_of=date(2026, 8, 15), top_k=5)
        combined = " ".join(item.chunk.text for item in results)
        hit = bool(results) and any(token in combined for token in expected_any)
        rows.append(
            {
                "policy_id": policy_id,
                "query": query,
                "top_chunk_ids": [item.chunk.chunk_id for item in results],
                "hit": hit,
            }
        )
    if not all(item["hit"] for item in rows):
        raise RuntimeError(f"Retrieval smoke test failed: {rows}")
    return rows


def retrieval_evaluation(index: PolicySearchIndex) -> dict[str, object]:
    cases = json.loads(EVALUATION_CASES_PATH.read_text(encoding="utf-8"))
    rows: list[dict[str, object]] = []
    reciprocal_ranks: list[float] = []
    for case in cases:
        results = index.search(
            case["query"],
            policy_id=case["policy_id"],
            as_of=date(2026, 8, 15),
            top_k=3,
        )
        returned = [item.chunk.chunk_id for item in results]
        expected = set(case["expected_chunk_ids"])
        hit_ranks = [
            index + 1
            for index, chunk_id in enumerate(returned)
            if any(
                chunk_id == expected_id or chunk_id.startswith(expected_id + "::source::")
                for expected_id in expected
            )
        ]
        rank = min(hit_ranks) if hit_ranks else None
        reciprocal_ranks.append(0.0 if rank is None else 1.0 / rank)
        rows.append(
            {
                "case_id": case["case_id"],
                "policy_id": case["policy_id"],
                "query": case["query"],
                "expected_chunk_ids": case["expected_chunk_ids"],
                "returned_chunk_ids": returned,
                "first_relevant_rank": rank,
                "hit_at_3": rank is not None,
            }
        )
    result = {
        "cases": len(rows),
        "hit_at_3": sum(item["hit_at_3"] for item in rows),
        "hit_rate_at_3": sum(item["hit_at_3"] for item in rows) / len(rows),
        "mean_reciprocal_rank": sum(reciprocal_ranks) / len(reciprocal_ranks),
        "rows": rows,
    }
    if result["hit_at_3"] != len(rows):
        raise RuntimeError(f"RAG evaluation failed: {result}")
    write_json(RAG_EVALUATION_PATH, result)
    lines = [
        "# RE6 공식근거 검색 평가",
        "",
        f"- Hit@3: {result['hit_at_3']}/{result['cases']} ({result['hit_rate_at_3']:.1%})",
        f"- MRR: {result['mean_reciprocal_rank']:.4f}",
        "- 평가 범위: 검수된 공식 원문·공식 페이지·정책 Metadata만 사용",
        "- 검색 실패 시 처리: 근거 없음으로 반환하고 조건을 생성하지 않음",
        "",
        "| Case | 정책 | 질문 | 최초 정답 순위 | Hit@3 |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['case_id']} | `{row['policy_id']}` | {row['query']} | {row['first_relevant_rank']} | {'통과' if row['hit_at_3'] else '실패'} |"
        )
    RAG_EVALUATION_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def main() -> None:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    chunks = build_index(config)
    example_results = evaluate_examples(config)
    write_json(PROFILE_SCHEMA_PATH, SessionEligibilityProfile.model_json_schema())
    write_json(EXPLANATION_SCHEMA_PATH, SafeExplanation.model_json_schema())
    index = PolicySearchIndex(INDEX_PATH)
    retrieval_results = retrieval_smoke_tests(index)
    rag_evaluation = retrieval_evaluation(index)
    sources = config["source_contract"]
    source_hashes = {
        key: sha256_file(ROOT / sources[key])
        for key in (
            "eligibility_rules",
            "eligibility_examples",
            "policy_metadata",
            "policy_versions",
            "source_manifest",
            "policy_chunks",
        )
    }
    manifest = {
        "generated_at_kst": now_kst(),
        "stage": "RE Stage 6",
        "status": "complete_verified",
        "engine_version": config["project"]["engine_version"],
        "source_hashes": source_hashes,
        "counts": {
            "policies": len({chunk.policy_id for chunk in chunks}),
            "eligibility_rules": len(EligibilityEngine().rules),
            "reviewed_examples": len(example_results),
            "official_chunks": len(chunks),
            "retrieval_smoke_cases": len(retrieval_results),
            "rag_evaluation_cases": rag_evaluation["cases"],
        },
        "checks": {
            "reviewed_examples_passed": sum(item["passed"] for item in example_results),
            "retrieval_smoke_passed": sum(item["hit"] for item in retrieval_results),
            "rag_hit_rate_at_3": rag_evaluation["hit_rate_at_3"],
            "rag_mean_reciprocal_rank": rag_evaluation["mean_reciprocal_rank"],
            "official_source_only": all(chunk.source_type.startswith("official_") for chunk in chunks),
            "chunk_metadata_complete": all(
                chunk.policy_id
                and chunk.policy_version
                and chunk.source_url
                and chunk.page_or_section
                and chunk.content_hash
                for chunk in chunks
            ),
            "model_training_performed": False,
            "external_llm_called": False,
            "raw_session_profile_persisted": False,
        },
        "retrieval_results": retrieval_results,
        "outputs": {
            str(INDEX_PATH.relative_to(ROOT)): {
                "bytes": INDEX_PATH.stat().st_size,
                "sha256": sha256_file(INDEX_PATH),
            },
            str(EXAMPLE_RESULTS_PATH.relative_to(ROOT)): {
                "bytes": EXAMPLE_RESULTS_PATH.stat().st_size,
                "sha256": sha256_file(EXAMPLE_RESULTS_PATH),
            },
            str(RAG_EVALUATION_PATH.relative_to(ROOT)): {
                "bytes": RAG_EVALUATION_PATH.stat().st_size,
                "sha256": sha256_file(RAG_EVALUATION_PATH),
            },
            str(RAG_EVALUATION_MD_PATH.relative_to(ROOT)): {
                "bytes": RAG_EVALUATION_MD_PATH.stat().st_size,
                "sha256": sha256_file(RAG_EVALUATION_MD_PATH),
            },
            str(PROFILE_SCHEMA_PATH.relative_to(ROOT)): {
                "bytes": PROFILE_SCHEMA_PATH.stat().st_size,
                "sha256": sha256_file(PROFILE_SCHEMA_PATH),
            },
            str(EXPLANATION_SCHEMA_PATH.relative_to(ROOT)): {
                "bytes": EXPLANATION_SCHEMA_PATH.stat().st_size,
                "sha256": sha256_file(EXPLANATION_SCHEMA_PATH),
            },
        },
    }
    write_json(MANIFEST_PATH, manifest)
    VERIFICATION_PATH.write_text(
        "\n".join(
            [
                "# RE Stage 6 준비·핵심 검증",
                "",
                "- 검수 정책: 10개",
                "- 공식 자격 Rule: 56개",
                f"- 수작업 정답사례: {sum(item['passed'] for item in example_results)}/20 통과",
                f"- 공식 정책 Chunk: {len(chunks)}개",
                f"- 검색 Smoke Case: {sum(item['hit'] for item in retrieval_results)}/4 통과",
                f"- 검색 평가 Hit@3: {rag_evaluation['hit_at_3']}/{rag_evaluation['cases']}",
                f"- 검색 평가 MRR: {rag_evaluation['mean_reciprocal_rank']:.4f}",
                "- 검색 방식: 결정론적 BM25, 모델 학습 없음",
                "- 외부 LLM 호출: 없음",
                "- 세션 자격 프로필 저장: 없음",
                "",
                "자격판정은 공개 Rule과 세션 입력의 일치 여부만 반환하며 승인 가능성을 뜻하지 않는다. 검색 결과는 공식 원문 Chunk와 버전·기준일·URL을 함께 반환한다.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest["counts"] | manifest["checks"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
