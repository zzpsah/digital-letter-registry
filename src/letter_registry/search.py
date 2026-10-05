"""Provider-neutral archive search contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True, slots=True)
class SearchFilters:
    authority: str | None = None
    category: str | None = None
    status: str | None = None
    year: int | None = None
    file_type: str | None = None


@dataclass(frozen=True, slots=True)
class SearchResult:
    record_id: str
    smart_filename: str | None
    title: str | None
    summary: str | None
    reference_number: str | None
    authority: str | None
    category: str | None
    issue_date: date | None
    status: str
    action_required: str | None
    concepts: tuple[str, ...]
    context_snippet: str | None
    file_type: str | None
    text_rank: float
    fuzzy_rank: float
    combined_rank: float
    summary_hi: str | None = None
    action_required_hi: str | None = None


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

    def search(
        self,
        query: str = "",
        *,
        filters: SearchFilters | None = None,
        limit: int = 25,
    ) -> list[SearchResult]:
        normalized = " ".join(query.split()).strip()
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")

        filters = filters or SearchFilters()
        if filters.year is not None and (filters.year < 1900 or filters.year > 2100):
            raise ValueError("year must be between 1900 and 2100")

        rows = self.transport.rpc(
            "search_letter_cards",
            {
                "search_query": normalized or None,
                "authority_filter": filters.authority,
                "category_filter": filters.category,
                "status_filter": filters.status,
                "year_filter": filters.year,
                "file_type_filter": filters.file_type,
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
                    summary=row.get("summary"),
                    summary_hi=row.get("summary_hi"),
                    reference_number=row.get("reference_number"),
                    authority=row.get("authority"),
                    category=row.get("category"),
                    issue_date=issue_date,
                    status=str(row["status"]),
                    action_required=row.get("action_required"),
                    action_required_hi=row.get("action_required_hi"),
                    concepts=tuple(str(x) for x in (row.get("concepts") or [])),
                    context_snippet=row.get("context_snippet"),
                    file_type=row.get("file_type"),
                    text_rank=float(row.get("text_rank") or 0.0),
                    fuzzy_rank=float(row.get("fuzzy_rank") or 0.0),
                    combined_rank=float(row.get("combined_rank") or 0.0),
                )
            )
        return results
