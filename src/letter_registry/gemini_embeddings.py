"""Gemini embedding provider for semantic retrieval."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Callable
from urllib import error, request

from .embeddings import EmbeddingResult


class GeminiEmbeddingError(RuntimeError):
    pass


HttpExecutor = Callable[[request.Request], tuple[int, str]]


def _default_http_executor(req: request.Request) -> tuple[int, str]:
    try:
        with request.urlopen(req, timeout=60) as response:  # noqa: S310
            return response.status, response.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise GeminiEmbeddingError(
            f"Gemini embedding request failed with HTTP {exc.code}: {body}"
        ) from exc
    except error.URLError as exc:
        raise GeminiEmbeddingError(
            f"Gemini embedding request failed: {exc.reason}"
        ) from exc


@dataclass(slots=True)
class GeminiEmbeddingProvider:
    api_key: str
    model: str = "gemini-embedding-2"
    dimensions: int = 768
    http_executor: HttpExecutor = _default_http_executor

    @property
    def version(self) -> str:
        return f"gemini:{self.model}:{self.dimensions}:v1"

    @classmethod
    def from_environment(cls) -> "GeminiEmbeddingProvider":
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required at runtime")

        model = os.environ.get("EMBEDDING_MODEL", "gemini-embedding-2").strip()
        dimensions = int(os.environ.get("EMBEDDING_DIMENSIONS", "768"))
        if dimensions < 128 or dimensions > 3072:
            raise ValueError("EMBEDDING_DIMENSIONS must be between 128 and 3072")

        return cls(
            api_key=api_key,
            model=model,
            dimensions=dimensions,
        )

    def embed_document(self, text: str) -> EmbeddingResult:
        if not text.strip():
            raise ValueError("embedding text cannot be empty")
        instructed = (
            "Represent this official education/government document passage for retrieval. "
            "Preserve semantic meaning across Hindi, English, and Hinglish.\n\n"
            f"{text}"
        )
        return self._embed(instructed)

    def embed_query(self, text: str) -> EmbeddingResult:
        if not text.strip():
            raise ValueError("embedding text cannot be empty")
        instructed = (
            "Represent this user search query for retrieving relevant official "
            "education/government letters.\n\n"
            f"{text}"
        )
        return self._embed(instructed)

    def _embed(self, text: str) -> EmbeddingResult:
        if not text.strip():
            raise ValueError("embedding text cannot be empty")

        payload = {
            "content": {
                "parts": [{"text": text}],
            },
            "output_dimensionality": self.dimensions,
        }

        req = request.Request(
            (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{self.model}:embedContent"
            ),
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            },
            method="POST",
        )
        status, raw = self.http_executor(req)
        if status < 200 or status >= 300:
            raise GeminiEmbeddingError(
                f"unexpected Gemini embedding HTTP status: {status}"
            )

        try:
            data = json.loads(raw)
            values = tuple(float(x) for x in data["embedding"]["values"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise GeminiEmbeddingError(
                "Gemini returned an invalid embedding response"
            ) from exc

        if len(values) != self.dimensions:
            raise GeminiEmbeddingError(
                f"expected {self.dimensions} embedding dimensions, got {len(values)}"
            )

        return EmbeddingResult(
            values=values,
            version=self.version,
        )
