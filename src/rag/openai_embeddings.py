"""Minimal OpenAI Embeddings client for RE8.2.

The client reads the project-local ``.env`` without logging credentials and
never persists user query text. It deliberately uses the standard library so
the service does not need a framework or an additional SDK dependency.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.settings import PROJECT_ROOT


EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-large"
SUPPORTED_EMBEDDING_MODELS = {
    "text-embedding-3-small",
    "text-embedding-3-large",
}
_LOCAL_ENV_LOADED = False
_SINGLE_TEXT_CACHE: dict[tuple[str, str], EmbeddingResponse] = {}


def load_local_openai_env(path: Path = PROJECT_ROOT / ".env") -> None:
    """Load only the OpenAI variables that are absent from the environment."""

    global _LOCAL_ENV_LOADED
    if _LOCAL_ENV_LOADED:
        return
    _LOCAL_ENV_LOADED = True
    if not path.is_file():
        return
    allowed = {"OPENAI_API_KEY", "OPENAI_EMBEDDING_MODEL"}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key not in allowed or key in os.environ:
            continue
        os.environ[key] = value.strip().strip('"').strip("'")


load_local_openai_env()


@dataclass(frozen=True)
class EmbeddingResponse:
    model: str
    vectors: tuple[tuple[float, ...], ...]
    prompt_tokens: int | None


class OpenAIEmbeddingError(RuntimeError):
    """Raised when an Embeddings request cannot be completed safely."""


class OpenAIEmbeddingClient:
    def __init__(
        self,
        *,
        model: str | None = None,
        api_key: str | None = None,
        timeout_seconds: int = 5,
        max_attempts: int = 2,
    ) -> None:
        load_local_openai_env()
        selected_model = model or os.getenv(
            "OPENAI_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL
        )
        if selected_model not in SUPPORTED_EMBEDDING_MODELS:
            raise ValueError(f"지원하지 않는 Embedding 모델입니다: {selected_model}")
        self.model = selected_model
        self.api_key = (api_key or os.getenv("OPENAI_API_KEY", "")).strip()
        self.timeout_seconds = timeout_seconds
        if max_attempts not in {1, 2}:
            raise ValueError("Embedding 요청은 사용자 동작당 최대 2회까지 허용됩니다.")
        self.max_attempts = max_attempts

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def embed(self, texts: list[str]) -> EmbeddingResponse:
        if not self.api_key:
            raise OpenAIEmbeddingError("OPENAI_API_KEY가 설정되지 않았습니다.")
        cleaned = [text.strip() for text in texts]
        if not cleaned or any(not text for text in cleaned):
            raise ValueError("Embedding 입력은 비어 있을 수 없습니다.")
        cache_key = (self.model, cleaned[0]) if len(cleaned) == 1 else None
        if cache_key is not None and cache_key in _SINGLE_TEXT_CACHE:
            return _SINGLE_TEXT_CACHE[cache_key]
        payload = json.dumps(
            {"model": self.model, "input": cleaned},
            ensure_ascii=False,
        ).encode("utf-8")
        request = Request(
            EMBEDDINGS_URL,
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        body: dict[str, object] | None = None
        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    body = json.loads(response.read().decode("utf-8"))
                break
            except HTTPError as exc:
                last_error = exc
                retryable = exc.code == 429 or exc.code >= 500
                if not retryable or attempt == self.max_attempts:
                    raise OpenAIEmbeddingError(
                        f"OpenAI Embeddings HTTP {exc.code}; attempts={attempt}"
                    ) from exc
            except (URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt == self.max_attempts:
                    raise OpenAIEmbeddingError(
                        f"OpenAI Embeddings 호출에 실패했습니다; attempts={attempt}"
                    ) from exc
        if body is None:
            raise OpenAIEmbeddingError("OpenAI Embeddings 응답이 없습니다.") from last_error

        ordered = sorted(body.get("data", []), key=lambda item: int(item["index"]))
        if len(ordered) != len(cleaned):
            raise OpenAIEmbeddingError("Embedding 응답 개수가 요청과 다릅니다.")
        vectors = tuple(
            tuple(float(value) for value in item["embedding"])
            for item in ordered
        )
        if not vectors or any(not vector for vector in vectors):
            raise OpenAIEmbeddingError("비어 있는 Embedding 응답입니다.")
        dimensions = len(vectors[0])
        if any(len(vector) != dimensions for vector in vectors):
            raise OpenAIEmbeddingError("Embedding 차원이 일관되지 않습니다.")
        usage = body.get("usage") or {}
        result = EmbeddingResponse(
            model=str(body.get("model") or self.model),
            vectors=vectors,
            prompt_tokens=(
                int(usage["prompt_tokens"])
                if usage.get("prompt_tokens") is not None
                else None
            ),
        )
        if cache_key is not None:
            _SINGLE_TEXT_CACHE[cache_key] = result
        return result
