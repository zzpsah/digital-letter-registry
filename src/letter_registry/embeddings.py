"""Provider-neutral embeddings and chunking contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class TextChunk:
    index: int
    content: str


@dataclass(frozen=True, slots=True)
class EmbeddingResult:
    values: tuple[float, ...]
    version: str


class EmbeddingProvider(Protocol):
    version: str
    dimensions: int

    def embed_document(self, text: str) -> EmbeddingResult:
        ...

    def embed_query(self, text: str) -> EmbeddingResult:
        ...


def chunk_text(
    text: str,
    *,
    max_characters: int = 2400,
    overlap_characters: int = 240,
) -> list[TextChunk]:
    normalized = " ".join(text.split()).strip()
    if not normalized:
        return []
    if max_characters < 200:
        raise ValueError("max_characters must be at least 200")
    if overlap_characters < 0 or overlap_characters >= max_characters:
        raise ValueError("overlap_characters must be between 0 and max_characters")

    chunks: list[TextChunk] = []
    start = 0
    index = 0
    while start < len(normalized):
        end = min(start + max_characters, len(normalized))
        if end < len(normalized):
            split = normalized.rfind(" ", start, end)
            if split > start + max_characters // 2:
                end = split

        content = normalized[start:end].strip()
        if content:
            chunks.append(TextChunk(index=index, content=content))
            index += 1

        if end >= len(normalized):
            break
        start = max(0, end - overlap_characters)

    return chunks
