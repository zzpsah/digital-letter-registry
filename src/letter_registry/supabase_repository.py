"""Supabase repository adapter with an injected transport.

The adapter contains no project URL, key, token, or network client. Runtime code
must provide a transport that is already authenticated for the intended user.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .extraction import ExtractionResult
from .structured_analysis import ContextAnalysisResult
from .models import DocumentRecord
from .persistence import (
    build_supabase_letter_row,
    build_supabase_processing_row,
    build_supabase_extraction_patch,
    build_supabase_context_processing_patch,
    build_supabase_letter_context_patch,
)


class SupabaseTransport(Protocol):
    """Minimal authenticated PostgREST-like transport."""

    def insert(
        self,
        table: str,
        row: dict[str, object],
        *,
        on_conflict: str | None = None,
    ) -> dict[str, object]:
        ...

    def upsert(
        self,
        table: str,
        row: dict[str, object],
        *,
        on_conflict: str,
    ) -> dict[str, object]:
        ...


@dataclass(slots=True)
class SupabaseLetterRepository:
    """Persist source identity and processing state through an injected transport."""

    transport: SupabaseTransport
    storage_provider: str = "gdrive"

    def save_source(self, record: DocumentRecord, *, owner_id: str) -> None:
        row = build_supabase_letter_row(
            record,
            owner_id=owner_id,
            storage_provider=self.storage_provider,
        )
        self.transport.insert(
            "letters",
            row,
            on_conflict="owner_id,original_sha256",
        )

    def save_processing_state(self, record: DocumentRecord, *, owner_id: str) -> None:
        row = build_supabase_processing_row(record, owner_id=owner_id)
        self.transport.upsert(
            "letter_processing",
            row,
            on_conflict="letter_id",
        )


    def save_extraction_result(
        self,
        record: DocumentRecord,
        *,
        owner_id: str,
        result: ExtractionResult,
    ) -> None:
        row = build_supabase_extraction_patch(
            record,
            owner_id=owner_id,
            result=result,
        )
        self.transport.upsert(
            "letter_processing",
            row,
            on_conflict="letter_id",
        )


    def save_context_result(
        self,
        record: DocumentRecord,
        *,
        owner_id: str,
        result: ContextAnalysisResult,
    ) -> None:
        processing_row = build_supabase_context_processing_patch(
            record,
            owner_id=owner_id,
            result=result,
        )
        letter_row = build_supabase_letter_context_patch(
            record,
            owner_id=owner_id,
            result=result,
        )

        self.transport.upsert(
            "letter_processing",
            processing_row,
            on_conflict="letter_id",
        )
        self.transport.upsert(
            "letters",
            letter_row,
            on_conflict="id",
        )
