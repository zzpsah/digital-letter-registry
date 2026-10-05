"""Authenticated letter-detail access without leaking storage references."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class DetailTransport(Protocol):
    def select(
        self,
        table: str,
        *,
        filters: dict[str, str] | None = None,
        columns: str = "*",
    ) -> list[dict[str, object]]:
        ...


@dataclass(frozen=True, slots=True)
class LetterDetail:
    record_id: str
    smart_filename: str | None
    title: str | None
    summary: str | None
    reference_number: str | None
    authority: str | None
    category: str | None
    subcategory: str | None
    issue_date: str | None
    status: str
    action_required: str | None
    deadline_at: str | None
    concepts: tuple[str, ...]
    structured_context: dict[str, object]


@dataclass(slots=True)
class SupabaseLetterDetailRepository:
    transport: DetailTransport

    def get(self, record_id: str) -> LetterDetail | None:
        letter_rows = self.transport.select(
            "letters",
            filters={"id": record_id},
            columns=(
                "id,smart_filename,title,summary,reference_number,authority,canonical_authority_id,"
                "category,subcategory,issue_date,status,action_required,deadline_at"
            ),
        )
        if not letter_rows:
            return None

        processing_rows = self.transport.select(
            "letter_processing",
            filters={"letter_id": record_id},
            columns="concepts,structured_context",
        )

        letter = letter_rows[0]
        display_authority = letter.get("authority")
        canonical_authority_id = str(letter.get("canonical_authority_id") or "").strip()
        if canonical_authority_id:
            authority_rows = self.transport.select(
                "authorities",
                filters={"id": canonical_authority_id},
                columns="short_name,name_en",
            )
            if authority_rows:
                display_authority = (
                    authority_rows[0].get("short_name")
                    or authority_rows[0].get("name_en")
                    or display_authority
                )
        processing = processing_rows[0] if processing_rows else {}
        return LetterDetail(
            record_id=str(letter["id"]),
            smart_filename=letter.get("smart_filename"),
            title=letter.get("title"),
            summary=letter.get("summary"),
            reference_number=letter.get("reference_number"),
            authority=display_authority,
            category=letter.get("category"),
            subcategory=letter.get("subcategory"),
            issue_date=(
                str(letter["issue_date"]) if letter.get("issue_date") else None
            ),
            status=str(letter.get("status") or "unknown"),
            action_required=letter.get("action_required"),
            deadline_at=(
                str(letter["deadline_at"]) if letter.get("deadline_at") else None
            ),
            concepts=tuple(str(x) for x in (processing.get("concepts") or [])),
            structured_context=(
                processing.get("structured_context")
                if isinstance(processing.get("structured_context"), dict)
                else {}
            ),
        )
