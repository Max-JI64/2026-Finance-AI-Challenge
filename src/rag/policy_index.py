"""Deterministic official-policy retrieval for RE6 without model training."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from src.settings import PROJECT_ROOT


INDEX_PATH = PROJECT_ROOT / "data/processed_re/policy/re_stage6/policy_index.jsonl"


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def tokenize(text: str) -> list[str]:
    normalized = re.sub(r"[^0-9A-Za-z가-힣]+", " ", text.lower())
    words = [word for word in normalized.split() if len(word) > 1]
    compact = "".join(words)
    bigrams = [compact[index : index + 2] for index in range(max(0, len(compact) - 1))]
    return words + bigrams


class PolicyChunk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_id: str
    policy_version: str
    chunk_id: str
    source_type: str
    source_path: str
    source_url: str
    page_or_section: str
    effective_from: date | None = None
    effective_to: date | None = None
    retrieved_at: date
    content_hash: str
    text: str


class SearchResult(BaseModel):
    chunk: PolicyChunk
    score: float = Field(ge=0)


class PolicySearchIndex:
    def __init__(self, path: Path = INDEX_PATH) -> None:
        with path.open("r", encoding="utf-8") as stream:
            self.chunks = tuple(PolicyChunk.model_validate(json.loads(line)) for line in stream if line.strip())
        if not self.chunks:
            raise ValueError("RE6 policy index is empty")
        self._tokens = [tokenize(chunk.text + " " + chunk.page_or_section) for chunk in self.chunks]
        self._document_frequency: Counter[str] = Counter()
        for tokens in self._tokens:
            self._document_frequency.update(set(tokens))
        self._average_length = sum(len(tokens) for tokens in self._tokens) / len(self._tokens)

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
        total = len(self.chunks)
        scored: list[SearchResult] = []
        for chunk, tokens in zip(self.chunks, self._tokens, strict=True):
            if chunk.policy_id != policy_id:
                continue
            if policy_version is not None and chunk.policy_version != policy_version:
                continue
            if as_of is not None:
                if chunk.effective_from is not None and chunk.effective_from > as_of:
                    continue
                if chunk.effective_to is not None and chunk.effective_to < as_of:
                    continue
            frequencies = Counter(tokens)
            length = max(1, len(tokens))
            score = 0.0
            for token, query_weight in query_tokens.items():
                frequency = frequencies[token]
                if frequency == 0:
                    continue
                df = self._document_frequency[token]
                idf = math.log(1 + (total - df + 0.5) / (df + 0.5))
                denominator = frequency + 1.2 * (1 - 0.75 + 0.75 * length / self._average_length)
                score += query_weight * idf * (frequency * 2.2 / denominator)
            if score > 0:
                scored.append(SearchResult(chunk=chunk, score=score))
        scored.sort(key=lambda item: (-item.score, item.chunk.chunk_id))
        return scored[:top_k]

