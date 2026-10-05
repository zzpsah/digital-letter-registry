"""Supabase repository adapter with an injected transport.

The adapter contains no project URL, key, token, or network client. Runtime code
must provide a transport that is already authenticated for the intended user.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Protocol

from .extraction import ExtractionResult
from .structured_analysis import ContextAnalysisResult
from .models import DocumentRecord
from .rename_execution import StoredRenameIdentity
from .persistence import (
    build_supabase_letter_row,
    build_supabase_processing_row,
    build_supabase_extraction_patch,
    build_supabase_context_processing_patch,
    build_supabase_letter_context_patch,
)


class SupabaseTransport(Protocol):
    """Minimal authenticated PostgREST-like transport."""

    def select(
        self,
        table: str,
        *,
        filters: dict[str, str] | None = None,
        columns: str = "*",
    ) -> list[dict[str, object]]:
        ...

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

    def update(
        self,
        table: str,
        row: dict[str, object],
        *,
        filters: dict[str, str],
    ) -> dict[str, object]:
        ...


@dataclass(slots=True)
class SupabaseLetterRepository:
    """Persist source identity and processing state through an injected transport."""

    transport: SupabaseTransport
    storage_provider: str = "gdrive"

    def get_rename_identity(
        self,
        record_id: str,
    ) -> StoredRenameIdentity | None:
        rows = self.transport.select(
            "letters",
            filters={"id": record_id},
            columns=(
                "id,original_filename,storage_provider,storage_object_id"
            ),
        )
        if not rows:
            return None
        row = rows[0]
        return StoredRenameIdentity(
            record_id=str(row["id"]),
            original_filename=str(row["original_filename"]),
            storage_provider=str(row["storage_provider"]),
            storage_object_reference=str(row["storage_object_id"]),
        )

    def storage_reference_exists(
        self,
        *,
        owner_id: str,
        object_reference: str,
    ) -> bool:
        rows = self.transport.select(
            "letters",
            filters={
                "storage_provider": self.storage_provider,
                "storage_object_id": object_reference,
            },
            columns="id",
        )
        return bool(rows)

    def source_exists_by_hash(self, *, owner_id: str, sha256: str) -> bool:
        rows = self.transport.select(
            "letters",
            filters={
                "original_sha256": sha256.lower(),
            },
            columns="id",
        )
        return bool(rows)

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
        # Reprocessing must not erase previously verified metadata merely
        # because a fallback provider cannot recover one field from noisy OCR.
        select_existing = getattr(self.transport, "select", None)
        existing_rows = (
            select_existing(
                "letters",
                filters={"id": record.record_id},
                columns=(
                    "title,authority,category,subcategory,summary,reference_number,"
                    "issue_date,action_required"
                ),
            )
            if callable(select_existing)
            else []
        )
        processing_rows = (
            select_existing(
                "letter_processing",
                filters={"letter_id": record.record_id},
                columns="structured_context",
            )
            if callable(select_existing)
            else []
        )
        previous_structured = (
            processing_rows[0].get("structured_context")
            if processing_rows and isinstance(processing_rows[0].get("structured_context"), dict)
            else {}
        )
        previous_confidence = float(previous_structured.get("confidence") or 0.0)
        result_context = getattr(result, "context", None)
        incoming_confidence = float(getattr(result_context, "confidence", None) or 0.0)
        confidence_downgrade = bool(
            result_context is not None
            and previous_structured
            and previous_confidence >= 0.55
            and incoming_confidence + 0.08 < previous_confidence
        )

        if existing_rows:
            existing = existing_rows[0]
            context = result.context
            merged = {}
            for field_name in (
                "title",
                "authority",
                "category",
                "subcategory",
                "summary",
                "reference_number",
                "issue_date",
                "action_required",
            ):
                current = getattr(context, field_name)
                previous = existing.get(field_name)
                preserve_previous = (
                    not str(current or "").strip()
                    or (
                        confidence_downgrade
                        and str(previous or "").strip()
                    )
                )
                if preserve_previous and str(previous or "").strip():
                    merged[field_name] = str(previous)
            if confidence_downgrade:
                for field_name in (
                    "summary_hi",
                    "whatsapp_summary",
                    "action_required_hi",
                    "applies_to",
                    "key_points",
                    "clean_document_text",
                ):
                    previous = previous_structured.get(field_name)
                    if previous not in (None, "", [], ()):
                        merged[field_name] = (
                            tuple(str(x) for x in previous)
                            if field_name in {"applies_to", "key_points"} and isinstance(previous, list)
                            else previous
                        )
                if previous_confidence:
                    merged["confidence"] = previous_confidence
            if merged:
                result = replace(result, context=replace(context, **merged))

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
        self.transport.update(
            "letters",
            letter_row,
            filters={"id": record.record_id},
        )


    def save_embedding_version(
        self,
        record: DocumentRecord,
        *,
        owner_id: str,
        embedding_version: str,
    ) -> None:
        if not embedding_version.strip():
            raise ValueError("embedding_version is required")
        self.transport.upsert(
            "letter_processing",
            {
                "letter_id": record.record_id,
                "owner_id": owner_id,
                "embedding_version": embedding_version,
            },
            on_conflict="letter_id",
        )
