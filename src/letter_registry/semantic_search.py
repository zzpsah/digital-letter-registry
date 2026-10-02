"""Chunk embedding persistence and semantic search."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from .embeddings import EmbeddingProvider, TextChunk, chunk_text


def vector_literal(values: tuple[float, ...]) -> str:
    if not values:
        raise ValueError("embedding vector cannot be empty")
    return "[" + ",".join(format(value, ".9g") for value in values) + "]"


class ChunkTransport(Protocol):
    def upsert(
        self,
        table: str,
        row: dict[str, object],
        *,
        on_conflict: str,
    ) -> dict[str, object]:
        ...

    def rpc(
        self,
        function: str,
        params: dict[str, object],
    ) -> list[dict[str, object]]:
        ...


@dataclass(slots=True)
class SupabaseEmbeddingRepository:
    transport: ChunkTransport
    provider: EmbeddingProvider

    def embed_document_chunks(
        self,
        *,
        owner_id: str,
        letter_id: str,
        extracted_text: str,
        max_characters: int = 2400,
        overlap_characters: int = 240,
    ) -> int:
        UUID(owner_id)
        UUID(letter_id)

        chunks = chunk_text(
            extracted_text,
            max_characters=max_characters,
            overlap_characters=overlap_characters,
        )
        for chunk in chunks:
            result = self.provider.embed_document(chunk.content)
            self.transport.upsert(
                "letter_chunks",
                {
                    "owner_id": owner_id,
                    "letter_id": letter_id,
                    "chunk_index": chunk.index,
                    "content": chunk.content,
                    "embedding": vector_literal(result.values),
                    "embedding_version": result.version,
                },
                on_conflict="letter_id,chunk_index,embedding_version",
            )
        return len(chunks)

    def semantic_search(
        self,
        query: str,
        *,
        limit: int = 25,
    ) -> list[dict[str, object]]:
        normalized = " ".join(query.split()).strip()
        if not normalized:
            return []
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")

        result = self.provider.embed_query(normalized)
        return self.transport.rpc(
            "search_letter_chunks_semantic",
            {
                "query_embedding": vector_literal(result.values),
                "query_embedding_version": result.version,
                "result_limit": limit,
            },
        )
