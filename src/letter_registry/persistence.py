"""Persistence ports and public-safe Supabase row mapping.

The domain stays provider-independent. Supabase-specific constraints such as
UUID identifiers are enforced only at this boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol
from uuid import UUID

from .models import DocumentRecord


def _validated_uuid(value: str, *, field_name: str) -> str:
    try:
        return str(UUID(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"{field_name} must be a valid UUID") from exc


def build_supabase_letter_row(
    record: DocumentRecord,
    *,
    owner_id: str,
    storage_provider: str = "gdrive",
) -> dict[str, object]:
    """Map immutable source identity to the public.letters schema."""

    if not storage_provider.strip():
        raise ValueError("storage_provider is required")

    return {
        "id": _validated_uuid(record.record_id, field_name="record_id"),
        "owner_id": _validated_uuid(owner_id, field_name="owner_id"),
        "original_filename": record.original_filename,
        "original_sha256": record.original_sha256.lower(),
        "storage_provider": storage_provider,
        "storage_object_id": record.original_storage_reference,
        "issue_date": record.issue_date.isoformat() if record.issue_date else None,
        "received_at": record.received_at.isoformat(),
        "uploaded_at": record.uploaded_at.isoformat(),
        "status": record.status.value,
    }


def build_supabase_processing_row(
    record: DocumentRecord,
    *,
    owner_id: str,
) -> dict[str, object]:
    """Map current processing-version state to public.letter_processing."""

    processing = record.processing
    return {
        "letter_id": _validated_uuid(record.record_id, field_name="record_id"),
        "owner_id": _validated_uuid(owner_id, field_name="owner_id"),
        "ocr_version": processing.extraction,
        "context_version": processing.context,
        "dictionary_version": processing.dictionary,
        "filename_rule_version": processing.filename_rule,
        "category_schema_version": processing.category_schema,
        "embedding_version": processing.embedding,
        "status_rule_version": processing.status_rule,
    }


class LetterRepository(Protocol):
    """Minimal persistence port used by ingestion before OCR/AI exists."""

    def save_source(self, record: DocumentRecord, *, owner_id: str) -> None:
        ...

    def save_processing_state(self, record: DocumentRecord, *, owner_id: str) -> None:
        ...


@dataclass(slots=True)
class InMemoryLetterRepository:
    """Synthetic repository for tests and vertical-slice development."""

    letters: dict[str, dict[str, object]] = field(default_factory=dict)
    processing: dict[str, dict[str, object]] = field(default_factory=dict)

    def save_source(self, record: DocumentRecord, *, owner_id: str) -> None:
        row = build_supabase_letter_row(record, owner_id=owner_id)
        sha = str(row["original_sha256"])

        duplicate = next(
            (
                existing
                for existing in self.letters.values()
                if existing["owner_id"] == row["owner_id"]
                and existing["original_sha256"] == sha
                and existing["id"] != row["id"]
            ),
            None,
        )
        if duplicate is not None:
            raise ValueError("duplicate source content for owner")

        self.letters[str(row["id"])] = row

    def save_processing_state(self, record: DocumentRecord, *, owner_id: str) -> None:
        row = build_supabase_processing_row(record, owner_id=owner_id)
        letter_id = str(row["letter_id"])
        if letter_id not in self.letters:
            raise ValueError("source record must be saved before processing state")
        self.processing[letter_id] = row
