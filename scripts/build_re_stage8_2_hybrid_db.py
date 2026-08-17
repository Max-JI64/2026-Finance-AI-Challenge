"""Build the RE8.2 Markdown-first local Hybrid policy database.

User-reviewed Markdown is the only searchable policy body. Saved HTML is used
only to recover official URLs and is never chunked or embedded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sqlite3
import struct
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.rag.openai_embeddings import OpenAIEmbeddingClient


DATABASE_PATH = ROOT / "rag/index/policy_re8.sqlite3"
POLICY_METADATA_PATH = ROOT / "data/processed_re/policy/re_stage8_2/policy_metadata.csv"
SELECTED_ROOT = ROOT / "data/raw_re/policy/selected"
FUND_ROOT = ROOT / "data/raw_re/policy/seoul_fund/2026/2026년도 서울특별시 중소기업육성자금 융자지원 변경계획 공고"
AS_OF = date(2026, 8, 17)
ENGINE_VERSION = "re8.2-sqlite-hybrid-v1"
DEFAULT_MODELS = ("text-embedding-3-small", "text-embedding-3-large")


OFFICIAL_URLS = {
    "POL_SEOUL_FUND_2026": "https://www.seoul.go.kr/news/news_notice.do?nttNo=457365",
    "POL_SEOUL_CRISIS_TRACK2_2026H2": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000123842",
    "POL_SEOUL_CLOSURE_2026": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000119017",
    "POL_SEOUL_DIGITAL_MIDLIFE_2026H2": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000123844",
    "POL_SEOUL_ZERO_MARKET_2026_2": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000123336",
    "POL_SEOUL_SAFETY_TEST_2026H2": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000124676",
    "POL_SEOUL_RESTART_2026": "https://news.seoul.go.kr/economy/archives/573571",
    "POL_SEMAS_REFINANCE_2026": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000124909",
    "POL_SEMAS_RECHALLENGE_2026": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000124909",
    "POL_SEMAS_STABILITY_VOUCHER_2026": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000117908",
    "POL_SEMAS_EMPLOYMENT_INSURANCE_2026": "https://news.seoul.go.kr/economy/archives/568900",
    "POL_SEOUL_FAMILY_FRIENDLY_EMPLOYER_2026": "https://pointseoul.or.kr/",
    "POL_SEOUL_IEUM_SAVINGS_2026": "https://news.seoul.go.kr/economy/archives/572616",
    "POL_SEOUL_YELLOW_UMBRELLA_2026": "https://news.seoul.go.kr/economy/archives/568855",
    "POL_SEOUL_HOSPITAL_LIVING_EXPENSE_2026": "https://news.seoul.go.kr/economy/archives/508129",
    "POL_SEOUL_PRIVATE_CHILDCARE_2026": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000122913",
    "POL_JUNGGU_CUSTOM_SUPPORT_2026": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000121649",
}

POLICY_NAMES = {
    "POL_SEOUL_FUND_2026": "서울특별시 중소기업육성자금",
    "POL_SEOUL_CRISIS_TRACK2_2026H2": "위기 소상공인 조기발굴 및 선제지원",
    "POL_SEOUL_CLOSURE_2026": "새 길 여는 폐업지원",
    "POL_SEOUL_DIGITAL_MIDLIFE_2026H2": "중장년 소상공인 디지털 전환지원",
    "POL_SEOUL_ZERO_MARKET_2026_2": "서울제로마켓 활성화 지원",
    "POL_SEOUL_SAFETY_TEST_2026H2": "서울시 소상공인 안전검사 지원",
    "POL_SEOUL_RESTART_2026": "서울형 다시서기 프로젝트",
    "POL_SEMAS_REFINANCE_2026": "소상공인 정책자금 대환대출",
    "POL_SEMAS_RECHALLENGE_2026": "소상공인 재도전특별자금",
    "POL_SEMAS_STABILITY_VOUCHER_2026": "소상공인 경영안정 바우처",
    "POL_SEMAS_EMPLOYMENT_INSURANCE_2026": "소상공인 고용보험료 지원",
    "POL_SEOUL_FAMILY_FRIENDLY_EMPLOYER_2026": "서울시 육아휴직·출산휴가 기업지원금",
    "POL_SEOUL_IEUM_SAVINGS_2026": "서울형 이음공제",
    "POL_SEOUL_YELLOW_UMBRELLA_2026": "서울시 노란우산공제 희망장려금",
    "POL_SEOUL_HOSPITAL_LIVING_EXPENSE_2026": "서울형 입원 생활비 지원",
    "POL_SEOUL_PRIVATE_CHILDCARE_2026": "서울 소상공인 민간 아이돌봄서비스 지원",
    "POL_JUNGGU_CUSTOM_SUPPORT_2026": "중구 편편한 소상공인 맞춤형 지원",
}

POLICY_VERSIONS = {
    "POL_SEOUL_FUND_2026": "2026-05-04-change",
    "POL_SEOUL_CRISIS_TRACK2_2026H2": "2026-06-30",
    "POL_SEOUL_CLOSURE_2026": "2026-02",
    "POL_SEOUL_DIGITAL_MIDLIFE_2026H2": "2026-06-30",
    "POL_SEOUL_ZERO_MARKET_2026_2": "2026-06-17-2nd",
    "POL_SEOUL_SAFETY_TEST_2026H2": "2026-07-23",
    "POL_SEOUL_RESTART_2026": "2026-07-16",
    "POL_SEMAS_REFINANCE_2026": "2026-07-29-change4",
    "POL_SEMAS_RECHALLENGE_2026": "2026-07-29-change4",
    "POL_SEMAS_STABILITY_VOUCHER_2026": "2026-01-28",
    "POL_SEMAS_EMPLOYMENT_INSURANCE_2026": "2025-12-29",
    "POL_SEOUL_FAMILY_FRIENDLY_EMPLOYER_2026": "2026-03-11",
    "POL_SEOUL_IEUM_SAVINGS_2026": "2026-05-22",
    "POL_SEOUL_YELLOW_UMBRELLA_2026": "2026-08-12",
    "POL_SEOUL_HOSPITAL_LIVING_EXPENSE_2026": "2026-07-24",
    "POL_SEOUL_PRIVATE_CHILDCARE_2026": "2026-05-26-3rd",
    "POL_JUNGGU_CUSTOM_SUPPORT_2026": "2026-04-30",
}

# This folder currently contains a duplicate of the Yellow Umbrella Markdown,
# not the industrial-accident-insurance notice named by the folder. Keep the
# user's file untouched and quarantine it from retrieval until corrected.
QUARANTINED_POLICY_IDS = {"POL_SEOUL_INDUSTRIAL_ACCIDENT_INSURANCE_2026"}


@dataclass(frozen=True)
class SourceSpec:
    policy_id: str
    markdown_path: Path
    html_path: Path | None = None


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def discover_sources() -> list[SourceSpec]:
    rows: list[SourceSpec] = []
    for snapshot in ("2026-08-15", "2026-08-17"):
        root = SELECTED_ROOT / snapshot
        if not root.is_dir():
            continue
        for folder in sorted(path for path in root.iterdir() if path.is_dir()):
            if folder.name in QUARANTINED_POLICY_IDS:
                continue
            markdowns = sorted(folder.glob("*.md"))
            if len(markdowns) != 1:
                raise RuntimeError(f"정책 폴더에는 Markdown이 정확히 하나여야 합니다: {folder}")
            html = folder / "official_page.html"
            if folder.name == "POL_SEMAS_POLICY_LOANS_2026_CHANGE4":
                for alias in ("POL_SEMAS_REFINANCE_2026", "POL_SEMAS_RECHALLENGE_2026"):
                    rows.append(SourceSpec(alias, markdowns[0], html if html.is_file() else None))
            else:
                rows.append(SourceSpec(folder.name, markdowns[0], html if html.is_file() else None))
    fund_markdown = FUND_ROOT / "2026년_중소기업육성자금_융자지원_변경계획_공고.md"
    if not fund_markdown.is_file():
        raise FileNotFoundError(fund_markdown)
    rows.append(SourceSpec("POL_SEOUL_FUND_2026", fund_markdown))
    policy_ids = [item.policy_id for item in rows]
    duplicates = sorted({item for item in policy_ids if policy_ids.count(item) > 1})
    if duplicates:
        raise RuntimeError(f"중복 정책 ID: {duplicates}")
    missing = sorted(set(POLICY_NAMES).difference(policy_ids))
    if missing:
        raise RuntimeError(f"정책 Markdown 누락: {missing}")
    return sorted(rows, key=lambda item: item.policy_id)


def load_policy_metadata() -> dict[str, dict[str, str]]:
    import csv

    with POLICY_METADATA_PATH.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 17 or len({row["policy_id"] for row in rows}) != 17:
        raise RuntimeError("RE8.2 policy metadata must contain 17 unique policies")
    return {row["policy_id"]: row for row in rows}


def extract_html_url(path: Path | None, fallback: str) -> str:
    if path is None:
        return fallback
    text = path.read_text(encoding="utf-8", errors="ignore")
    canonical = re.search(
        r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)',
        text,
        flags=re.IGNORECASE,
    )
    if canonical and canonical.group(1).startswith("http"):
        return canonical.group(1).replace("http://", "https://", 1)
    announcement = re.search(r"pblancId=(PBLN_[0-9]+)", text)
    if announcement:
        return (
            "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId="
            + announcement.group(1)
        )
    return fallback


def split_long_section(section: str, limit: int = 2400) -> Iterable[str]:
    if len(section) <= limit:
        yield section
        return
    lines = section.splitlines()
    heading = lines[0] if lines and lines[0].startswith("#") else ""
    body = "\n".join(lines[1:] if heading else lines)
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", body) if part.strip()]
    current = heading
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip()
        if current and len(candidate) > limit:
            yield current.strip()
            current = f"{heading}\n\n{paragraph}".strip() if heading else paragraph
        else:
            current = candidate
    if current.strip() and current.strip() != heading:
        yield current.strip()


def chunk_markdown(path: Path) -> list[tuple[str, str]]:
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").strip()
    if not text:
        raise RuntimeError(f"빈 Markdown: {path}")
    sections = [part.strip() for part in re.split(r"(?=^#{1,4}\s+)", text, flags=re.MULTILINE) if part.strip()]
    chunks: list[tuple[str, str]] = []
    for section in sections:
        for part in split_long_section(section):
            heading = next((line.lstrip("# ").strip() for line in part.splitlines() if line.startswith("#")), path.stem)
            chunks.append((heading[:180], part))
    return chunks


def normalized_blob(vector: tuple[float, ...]) -> bytes:
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return struct.pack(f"<{len(vector)}f", *(value / norm for value in vector))


def load_reusable_embeddings() -> dict[tuple[str, str], tuple[int, bytes]]:
    """Load vectors by model and canonical chunk hash before atomic replacement."""

    if not DATABASE_PATH.is_file():
        return {}
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if not {"policy_chunks", "policy_embeddings"}.issubset(tables):
            return {}
        rows = connection.execute(
            "SELECT e.model, c.content_hash, e.dimensions, e.vector "
            "FROM policy_embeddings e JOIN policy_chunks c USING(chunk_id)"
        ).fetchall()
    finally:
        connection.close()
    return {
        (str(model), str(content_hash)): (int(dimensions), bytes(vector))
        for model, content_hash, dimensions, vector in rows
    }


def build_database(
    models: tuple[str, ...], batch_size: int = 32, *, reuse_existing: bool = True
) -> dict[str, object]:
    sources = discover_sources()
    policy_metadata = load_policy_metadata()
    reusable = load_reusable_embeddings() if reuse_existing else {}
    source_rows: list[tuple[object, ...]] = []
    chunk_rows: list[tuple[object, ...]] = []
    for source in sources:
        policy_id = source.policy_id
        official_url = extract_html_url(source.html_path, OFFICIAL_URLS[policy_id])
        metadata = policy_metadata[policy_id]
        source_rows.append(
            (
                policy_id,
                POLICY_VERSIONS[policy_id],
                POLICY_NAMES[policy_id],
                relative(source.markdown_path),
                sha256_file(source.markdown_path),
                relative(source.html_path) if source.html_path else None,
                sha256_file(source.html_path) if source.html_path else None,
                official_url,
                AS_OF.isoformat(),
                "markdown_body_html_link_only",
                metadata["search_district"],
                metadata["industry_scope"],
                metadata["application_start"] or None,
                metadata["application_end"] or None,
                metadata["availability_as_of"],
                metadata["effective_from"] or None,
                metadata["effective_to"] or None,
                metadata["rule_engine"],
                metadata["event_status"],
            )
        )
        for sequence, (section, text) in enumerate(chunk_markdown(source.markdown_path), start=1):
            chunk_id = f"{policy_id}::md::{sequence:03d}"
            chunk_rows.append(
                (
                    chunk_id,
                    policy_id,
                    POLICY_VERSIONS[policy_id],
                    "official_user_reviewed_markdown",
                    relative(source.markdown_path),
                    official_url,
                    section,
                    metadata["effective_from"] or None,
                    metadata["effective_to"] or None,
                    AS_OF.isoformat(),
                    sha256_bytes(text.encode("utf-8")),
                    text,
                )
            )

    temp_path = DATABASE_PATH.with_suffix(".sqlite3.tmp")
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    if temp_path.exists():
        temp_path.unlink()
    connection = sqlite3.connect(temp_path)
    try:
        connection.executescript(
            """
            PRAGMA journal_mode=DELETE;
            CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE policy_sources (
                policy_id TEXT PRIMARY KEY,
                policy_version TEXT NOT NULL,
                policy_name TEXT NOT NULL,
                markdown_path TEXT NOT NULL,
                markdown_sha256 TEXT NOT NULL,
                html_path TEXT,
                html_sha256 TEXT,
                official_url TEXT NOT NULL,
                reviewed_at TEXT NOT NULL,
                ingestion_mode TEXT NOT NULL,
                search_district TEXT NOT NULL,
                industry_scope TEXT NOT NULL,
                application_start TEXT,
                application_end TEXT,
                availability_as_of TEXT NOT NULL,
                effective_from TEXT,
                effective_to TEXT,
                rule_engine TEXT NOT NULL,
                event_status TEXT NOT NULL
            );
            CREATE TABLE policy_chunks (
                chunk_id TEXT PRIMARY KEY,
                policy_id TEXT NOT NULL,
                policy_version TEXT NOT NULL,
                source_type TEXT NOT NULL,
                source_path TEXT NOT NULL,
                source_url TEXT NOT NULL,
                page_or_section TEXT NOT NULL,
                effective_from TEXT,
                effective_to TEXT,
                retrieved_at TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                text TEXT NOT NULL,
                FOREIGN KEY(policy_id) REFERENCES policy_sources(policy_id)
            );
            CREATE TABLE policy_embeddings (
                chunk_id TEXT NOT NULL,
                model TEXT NOT NULL,
                dimensions INTEGER NOT NULL,
                vector BLOB NOT NULL,
                PRIMARY KEY(chunk_id, model),
                FOREIGN KEY(chunk_id) REFERENCES policy_chunks(chunk_id)
            );
            CREATE INDEX idx_policy_chunks_filter ON policy_chunks(policy_id, policy_version);
            CREATE INDEX idx_policy_embeddings_model ON policy_embeddings(model, chunk_id);
            """
        )
        connection.executemany("INSERT INTO policy_sources VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", source_rows)
        connection.executemany("INSERT INTO policy_chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", chunk_rows)
        embedding_rows: list[tuple[object, ...]] = []
        texts = [str(row[-1]) for row in chunk_rows]
        chunk_ids = [str(row[0]) for row in chunk_rows]
        usage_by_model: dict[str, int] = {}
        dimensions_by_model: dict[str, int] = {}
        reused_by_model: dict[str, int] = {}
        generated_by_model: dict[str, int] = {}
        for model in models:
            client = OpenAIEmbeddingClient(model=model, timeout_seconds=60)
            model_usage = 0
            pending: list[tuple[str, str, str]] = []
            reused_count = 0
            for chunk_id, text, row in zip(chunk_ids, texts, chunk_rows, strict=True):
                content_hash = str(row[-2])
                cached = reusable.get((model, content_hash))
                if cached is None:
                    pending.append((chunk_id, text, content_hash))
                    continue
                dimensions, vector = cached
                dimensions_by_model[model] = dimensions
                embedding_rows.append((chunk_id, model, dimensions, vector))
                reused_count += 1
            for start in range(0, len(pending), batch_size):
                batch = pending[start : start + batch_size]
                response = client.embed([item[1] for item in batch])
                model_usage += response.prompt_tokens or 0
                for (chunk_id, _text, _content_hash), vector in zip(
                    batch, response.vectors, strict=True
                ):
                    dimensions_by_model[model] = len(vector)
                    embedding_rows.append(
                        (chunk_id, model, len(vector), normalized_blob(vector))
                    )
            usage_by_model[model] = model_usage
            reused_by_model[model] = reused_count
            generated_by_model[model] = len(pending)
        connection.executemany("INSERT INTO policy_embeddings VALUES (?, ?, ?, ?)", embedding_rows)
        metadata = {
            "engine_version": ENGINE_VERSION,
            "as_of_date": AS_OF.isoformat(),
            "policy_count": str(len(source_rows)),
            "chunk_count": str(len(chunk_rows)),
            "embedding_models": json.dumps(models, ensure_ascii=False),
            "embedding_dimensions": json.dumps(dimensions_by_model, sort_keys=True),
            "embedding_prompt_tokens": json.dumps(usage_by_model, sort_keys=True),
            "embedding_reused_rows": json.dumps(reused_by_model, sort_keys=True),
            "embedding_generated_rows": json.dumps(generated_by_model, sort_keys=True),
            "canonical_body": "user_reviewed_markdown",
            "html_body_indexed": "false",
            "user_query_persisted": "false",
        }
        connection.executemany("INSERT INTO metadata VALUES (?, ?)", metadata.items())
        connection.commit()
    finally:
        connection.close()
    temp_path.replace(DATABASE_PATH)
    return {
        "engine_version": ENGINE_VERSION,
        "database": relative(DATABASE_PATH),
        "policy_count": len(source_rows),
        "chunk_count": len(chunk_rows),
        "embedding_models": list(models),
        "embedding_reused_rows": reused_by_model,
        "embedding_generated_rows": generated_by_model,
        "html_body_indexed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", default=",".join(DEFAULT_MODELS))
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--no-reuse", action="store_true")
    args = parser.parse_args()
    models = tuple(item.strip() for item in args.models.split(",") if item.strip())
    print(
        json.dumps(
            build_database(models, args.batch_size, reuse_existing=not args.no_reuse),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
