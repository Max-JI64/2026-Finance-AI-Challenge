"""SQLite-backed local policy evidence store for RE8.

Only official/reviewed policy chunks are stored. User questions and eligibility
profiles are intentionally never written to this database.
"""

from __future__ import annotations

import json
import math
import sqlite3
from collections import Counter
from datetime import date
from pathlib import Path

from src.rag.policy_index import INDEX_PATH, PolicyChunk, SearchResult, tokenize
from src.settings import PROJECT_ROOT


DATABASE_PATH = PROJECT_ROOT / "rag/index/policy_re8.sqlite3"
ENGINE_VERSION = "re8-sqlite-bm25-v1"


def build_local_policy_db(
    source_path: Path = INDEX_PATH,
    database_path: Path = DATABASE_PATH,
) -> dict[str, int | str]:
    """Rebuild the deterministic local evidence database from the frozen index."""

    chunks: list[PolicyChunk] = []
    with source_path.open("r", encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                chunks.append(PolicyChunk.model_validate(json.loads(line)))
    if not chunks:
        raise ValueError("RE6 policy index is empty")

    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    try:
        connection.executescript(
            """
            PRAGMA journal_mode=DELETE;
            DROP TABLE IF EXISTS policy_chunks;
            DROP TABLE IF EXISTS metadata;
            CREATE TABLE metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
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
                text TEXT NOT NULL
            );
            CREATE INDEX idx_policy_filter
                ON policy_chunks(policy_id, policy_version, effective_from, effective_to);
            """
        )
        connection.executemany(
            """
            INSERT INTO policy_chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    item.chunk_id,
                    item.policy_id,
                    item.policy_version,
                    item.source_type,
                    item.source_path,
                    item.source_url,
                    item.page_or_section,
                    item.effective_from.isoformat() if item.effective_from else None,
                    item.effective_to.isoformat() if item.effective_to else None,
                    item.retrieved_at.isoformat(),
                    item.content_hash,
                    item.text,
                )
                for item in chunks
            ],
        )
        connection.executemany(
            "INSERT INTO metadata(key, value) VALUES (?, ?)",
            [("engine_version", ENGINE_VERSION), ("chunk_count", str(len(chunks)))],
        )
        connection.commit()
    finally:
        connection.close()
    return {
        "engine_version": ENGINE_VERSION,
        "chunk_count": len(chunks),
        "policy_count": len({item.policy_id for item in chunks}),
    }


class SQLitePolicySearchIndex:
    """Read-only, deterministic BM25 retrieval over a local SQLite chunk store."""

    def __init__(self, path: Path = DATABASE_PATH) -> None:
        if not path.is_file():
            raise FileNotFoundError(f"local policy database not found: {path}")
        self.path = path

    def _load_candidates(
        self,
        *,
        policy_id: str,
        policy_version: str | None,
        as_of: date | None,
    ) -> list[PolicyChunk]:
        query = "SELECT * FROM policy_chunks WHERE policy_id = ?"
        params: list[str] = [policy_id]
        if policy_version is not None:
            query += " AND policy_version = ?"
            params.append(policy_version)
        if as_of is not None:
            query += " AND (effective_from IS NULL OR effective_from <= ?)"
            query += " AND (effective_to IS NULL OR effective_to >= ?)"
            params.extend([as_of.isoformat(), as_of.isoformat()])
        query += " ORDER BY chunk_id"
        connection = sqlite3.connect(f"file:{self.path.as_posix()}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            rows = connection.execute(query, params).fetchall()
        finally:
            connection.close()
        return [PolicyChunk.model_validate(dict(row)) for row in rows]

    def search(
        self,
        query: str,
        *,
        policy_id: str,
        policy_version: str | None = None,
        as_of: date | None = None,
        top_k: int = 5,
    ) -> list[SearchResult]:
        if not policy_id:
            raise ValueError("policy_id filter is required")
        if top_k < 1 or top_k > 20:
            raise ValueError("top_k must be between 1 and 20")
        query_tokens = Counter(tokenize(query))
        if not query_tokens:
            return []
        chunks = self._load_candidates(
            policy_id=policy_id, policy_version=policy_version, as_of=as_of
        )
        if not chunks:
            return []
        tokenized = [tokenize(item.text + " " + item.page_or_section) for item in chunks]
        frequency: Counter[str] = Counter()
        for tokens in tokenized:
            frequency.update(set(tokens))
        average_length = sum(len(tokens) for tokens in tokenized) / len(tokenized)
        scored: list[SearchResult] = []
        for chunk, tokens in zip(chunks, tokenized, strict=True):
            counts = Counter(tokens)
            score = 0.0
            for token, weight in query_tokens.items():
                term_frequency = counts[token]
                if not term_frequency:
                    continue
                document_frequency = frequency[token]
                inverse = math.log(
                    1 + (len(chunks) - document_frequency + 0.5) / (document_frequency + 0.5)
                )
                denominator = term_frequency + 1.2 * (
                    0.25 + 0.75 * max(1, len(tokens)) / average_length
                )
                score += weight * inverse * (term_frequency * 2.2 / denominator)
            if score > 0:
                scored.append(SearchResult(chunk=chunk, score=score))
        scored.sort(key=lambda item: (-item.score, item.chunk.chunk_id))
        return scored[:top_k]
