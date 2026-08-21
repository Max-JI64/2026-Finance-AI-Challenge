"""BM25 + OpenAI vector retrieval over the RE8.2 local policy database."""

from __future__ import annotations

import math
import sqlite3
import struct
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from src.rag.openai_embeddings import DEFAULT_EMBEDDING_MODEL, OpenAIEmbeddingClient, OpenAIEmbeddingError
from src.rag.policy_index import PolicyChunk, tokenize
from src.settings import PROJECT_ROOT


DATABASE_PATH = PROJECT_ROOT / "rag/index/policy_re8.sqlite3"
RRF_K = 60


@dataclass(frozen=True)
class HybridSearchResult:
    chunk: PolicyChunk
    combined_score: float
    bm25_score: float | None
    vector_score: float | None
    bm25_rank: int | None
    vector_rank: int | None


@dataclass(frozen=True)
class HybridSearchOutcome:
    results: tuple[HybridSearchResult, ...]
    retrieval_mode: str
    embedding_model: str | None
    fallback_reason: str | None = None


def _decode_vector(blob: bytes, dimensions: int) -> tuple[float, ...]:
    return struct.unpack(f"<{dimensions}f", blob)


def _normalized(vector: tuple[float, ...]) -> tuple[float, ...]:
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return tuple(value / norm for value in vector)


class HybridPolicySearchIndex:
    def __init__(self, path: Path = DATABASE_PATH) -> None:
        if not path.is_file():
            raise FileNotFoundError(path)
        self.path = path

    def policy_catalog(self) -> list[dict[str, str]]:
        connection = sqlite3.connect(f"file:{self.path.as_posix()}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            rows = connection.execute(
                "SELECT policy_id, policy_version, policy_name, official_url, "
                "search_district, industry_scope, application_start, application_end, "
                "availability_as_of, effective_from, effective_to, rule_engine, event_status "
                "FROM policy_sources ORDER BY policy_name, policy_id"
            ).fetchall()
        finally:
            connection.close()
        return [dict(row) for row in rows]

    def _load_chunks(
        self,
        *,
        policy_id: str | None,
        policy_version: str | None,
        as_of: date | None,
        district: str | None,
    ) -> list[PolicyChunk]:
        query = "SELECT c.* FROM policy_chunks c JOIN policy_sources s USING(policy_id) WHERE 1=1"
        params: list[str] = []
        if policy_id:
            query += " AND c.policy_id = ?"
            params.append(policy_id)
        if policy_version:
            query += " AND c.policy_version = ?"
            params.append(policy_version)
        if as_of:
            query += " AND (c.effective_from IS NULL OR c.effective_from <= ?)"
            query += " AND (c.effective_to IS NULL OR c.effective_to >= ?)"
            params.extend([as_of.isoformat(), as_of.isoformat()])
        if district:
            query += " AND (s.search_district = '*' OR s.search_district = ?)"
            params.append(district)
        query += " ORDER BY c.chunk_id"
        connection = sqlite3.connect(f"file:{self.path.as_posix()}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            rows = connection.execute(query, params).fetchall()
        finally:
            connection.close()
        return [PolicyChunk.model_validate(dict(row)) for row in rows]

    def _load_vectors(self, chunk_ids: list[str], model: str) -> dict[str, tuple[float, ...]]:
        if not chunk_ids:
            return {}
        connection = sqlite3.connect(f"file:{self.path.as_posix()}?mode=ro", uri=True)
        try:
            placeholders = ",".join("?" for _ in chunk_ids)
            rows = connection.execute(
                f"SELECT chunk_id, dimensions, vector FROM policy_embeddings "
                f"WHERE model = ? AND chunk_id IN ({placeholders})",
                [model, *chunk_ids],
            ).fetchall()
        finally:
            connection.close()
        return {
            str(chunk_id): _decode_vector(blob, int(dimensions))
            for chunk_id, dimensions, blob in rows
        }

    @staticmethod
    def _bm25(query: str, chunks: list[PolicyChunk]) -> dict[str, float]:
        query_tokens = Counter(tokenize(query))
        if not query_tokens or not chunks:
            return {}
        tokenized = [tokenize(item.text + " " + item.page_or_section) for item in chunks]
        document_frequency: Counter[str] = Counter()
        for tokens in tokenized:
            document_frequency.update(set(tokens))
        average_length = sum(len(tokens) for tokens in tokenized) / len(tokenized)
        scores: dict[str, float] = {}
        for chunk, tokens in zip(chunks, tokenized, strict=True):
            counts = Counter(tokens)
            score = 0.0
            for token, weight in query_tokens.items():
                frequency = counts[token]
                if not frequency:
                    continue
                df = document_frequency[token]
                inverse = math.log(1 + (len(chunks) - df + 0.5) / (df + 0.5))
                denominator = frequency + 1.2 * (
                    0.25 + 0.75 * max(1, len(tokens)) / average_length
                )
                score += weight * inverse * (frequency * 2.2 / denominator)
            if score > 0:
                scores[chunk.chunk_id] = score
        return scores

    def search(
        self,
        query: str,
        *,
        policy_id: str | None = None,
        policy_ids: set[str] | None = None,
        policy_version: str | None = None,
        as_of: date | None = None,
        district: str | None = None,
        top_k: int = 5,
        model: str = DEFAULT_EMBEDDING_MODEL,
        mode: str = "hybrid",
        max_chunks_per_policy: int = 1,
    ) -> HybridSearchOutcome:
        if mode not in {"bm25", "vector", "hybrid"}:
            raise ValueError("mode는 bm25, vector, hybrid 중 하나여야 합니다.")
        if top_k < 1 or top_k > 50:
            raise ValueError("top_k는 1 이상 50 이하여야 합니다.")
        chunks = self._load_chunks(
            policy_id=policy_id,
            policy_version=policy_version,
            as_of=as_of,
            district=district,
        )
        if policy_ids is not None:
            chunks = [chunk for chunk in chunks if chunk.policy_id in policy_ids]
        chunk_by_id = {item.chunk_id: item for item in chunks}
        bm25_scores = self._bm25(query, chunks) if mode in {"bm25", "hybrid"} else {}
        bm25_order = sorted(bm25_scores, key=lambda key: (-bm25_scores[key], key))
        bm25_rank = {chunk_id: index for index, chunk_id in enumerate(bm25_order, start=1)}

        vector_scores: dict[str, float] = {}
        vector_rank: dict[str, int] = {}
        fallback_reason: str | None = None
        effective_mode = mode
        if mode in {"vector", "hybrid"}:
            try:
                response = OpenAIEmbeddingClient(model=model).embed([query])
                query_vector = _normalized(response.vectors[0])
                vectors = self._load_vectors(list(chunk_by_id), model)
                if len(vectors) != len(chunk_by_id):
                    raise OpenAIEmbeddingError("DB의 Embedding 행이 완전하지 않습니다.")
                vector_scores = {
                    chunk_id: sum(left * right for left, right in zip(query_vector, vector, strict=True))
                    for chunk_id, vector in vectors.items()
                }
                vector_order = sorted(vector_scores, key=lambda key: (-vector_scores[key], key))
                vector_rank = {chunk_id: index for index, chunk_id in enumerate(vector_order, start=1)}
            except (OpenAIEmbeddingError, OSError, ValueError) as exc:
                if mode == "vector":
                    return HybridSearchOutcome((), "unavailable", model, type(exc).__name__)
                effective_mode = "bm25_fallback"
                fallback_reason = type(exc).__name__

        combined: list[HybridSearchResult] = []
        for chunk_id in set(bm25_rank) | set(vector_rank):
            score = 0.0
            if chunk_id in bm25_rank:
                score += 1.0 / (RRF_K + bm25_rank[chunk_id])
            if chunk_id in vector_rank:
                score += 1.0 / (RRF_K + vector_rank[chunk_id])
            combined.append(
                HybridSearchResult(
                    chunk=chunk_by_id[chunk_id],
                    combined_score=score,
                    bm25_score=bm25_scores.get(chunk_id),
                    vector_score=vector_scores.get(chunk_id),
                    bm25_rank=bm25_rank.get(chunk_id),
                    vector_rank=vector_rank.get(chunk_id),
                )
            )
        if effective_mode == "bm25_fallback" or mode == "bm25":
            combined.sort(key=lambda item: (-(item.bm25_score or 0.0), item.chunk.chunk_id))
        elif mode == "vector":
            combined.sort(key=lambda item: (-(item.vector_score or -1.0), item.chunk.chunk_id))
        else:
            combined.sort(key=lambda item: (-item.combined_score, item.chunk.chunk_id))

        selected: list[HybridSearchResult] = []
        per_policy: Counter[str] = Counter()
        for item in combined:
            if per_policy[item.chunk.policy_id] >= max_chunks_per_policy:
                continue
            selected.append(item)
            per_policy[item.chunk.policy_id] += 1
            if len(selected) >= top_k:
                break
        return HybridSearchOutcome(
            tuple(selected), effective_mode, model if vector_rank else None, fallback_reason
        )
