"""Hybrid text/fuzzy + semantic archive ranking."""

from __future__ import annotations

from dataclasses import dataclass

from .search import SearchResult, SupabaseSearchRepository
from .semantic_search import SupabaseEmbeddingRepository


@dataclass(frozen=True, slots=True)
class HybridSearchResult:
    result: SearchResult
    semantic_similarity: float
    hybrid_rank: float


@dataclass(slots=True)
class HybridSearchRepository:
    text_search: SupabaseSearchRepository
    semantic_search: SupabaseEmbeddingRepository
    text_weight: float = 0.55
    semantic_weight: float = 0.45

    def search(self, query: str, *, limit: int = 25) -> list[HybridSearchResult]:
        text_results = self.text_search.search(query, limit=min(100, limit * 3))
        semantic_rows = self.semantic_search.semantic_search(
            query,
            limit=min(100, limit * 3),
        )

        semantic_by_letter: dict[str, float] = {}
        for row in semantic_rows:
            letter_id = str(row["letter_id"])
            similarity = float(row.get("semantic_similarity") or 0.0)
            semantic_by_letter[letter_id] = max(
                semantic_by_letter.get(letter_id, 0.0),
                similarity,
            )

        merged: list[HybridSearchResult] = []
        for result in text_results:
            semantic = semantic_by_letter.get(result.record_id, 0.0)
            rank = (
                self.text_weight * result.combined_rank
                + self.semantic_weight * semantic
            )
            merged.append(
                HybridSearchResult(
                    result=result,
                    semantic_similarity=semantic,
                    hybrid_rank=rank,
                )
            )

        merged.sort(key=lambda item: item.hybrid_rank, reverse=True)
        return merged[:limit]
