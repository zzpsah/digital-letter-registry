"""Provider-neutral archive search contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True, slots=True)
class SearchResult:
    record_id: str
    smart_filename: str | None
    title: str | None
    authority: str | None
    category: str | None
    issue_date: date | None
    status: str
    action_required: str | None
    concepts: tuple[str, ...]
    context_snippet: str | None
    text_rank: float
    fuzzy_rank: float
    combined_rank: float


class SearchTransport(Protocol):
    def rpc(
        self,
        function: str,
        params: dict[str, object],
    ) -> list[dict[str, object]]:
        ...


@dataclass(slots=True)
class SupabaseSearchRepository:
    transport: SearchTransport

    def search(self, query: str, *, limit: int = 25) -> list[SearchResult]:
        normalized = " ".join(query.split()).strip()
        if not normalized:
            return []
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")

        rows = self.transport.rpc(
            "search_letters",
            {
                "search_query": normalized,
                "result_limit": limit,
            },
        )

        results: list[SearchResult] = []
        for row in rows:
            issue_date = (
                date.fromisoformat(str(row["issue_date"]))
                if row.get("issue_date")
                else None
            )
            results.append(
                SearchResult(
                    record_id=str(row["id"]),
                    smart_filename=row.get("smart_filename"),
                    title=row.get("title"),
                    authority=row.get("authority"),
                    category=row.get("category"),
                    issue_date=issue_date,
                    status=str(row["status"]),
                    action_required=row.get("action_required"),
                    concepts=tuple(str(x) for x in (row.get("concepts") or [])),
                    context_snippet=row.get("context_snippet"),
                    text_rank=float(row.get("text_rank") or 0.0),
                    fuzzy_rank=float(row.get("fuzzy_rank") or 0.0),
                    combined_rank=float(row.get("combined_rank") or 0.0),
                )
            )
        return results
