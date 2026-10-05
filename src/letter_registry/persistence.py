"""Persistence ports and public-safe Supabase row mapping.

The domain stays provider-independent. Supabase-specific constraints such as
UUID identifiers are enforced only at this boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Protocol
from uuid import UUID

from .extraction import ExtractionResult
from .structured_analysis import ContextAnalysisResult
from .models import DocumentRecord
from .naming import FILENAME_RULE_VERSION, build_smart_filename


def _validated_deadline_at(value: object) -> str | None:
    """Return only absolute ISO date/datetime values suitable for timestamptz."""
    raw = str(value or "").strip()
    if not raw:
        return None
    candidate = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        datetime.fromisoformat(candidate)
        return raw
    except ValueError:
        return None


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

    def storage_reference_exists(
        self,
        *,
        owner_id: str,
        object_reference: str,
    ) -> bool:
        ...

    def source_exists_by_hash(self, *, owner_id: str, sha256: str) -> bool:
        ...

    def save_source(self, record: DocumentRecord, *, owner_id: str) -> None:
        ...

    def save_processing_state(self, record: DocumentRecord, *, owner_id: str) -> None:
        ...


@dataclass(slots=True)
class InMemoryLetterRepository:
    """Synthetic repository for tests and vertical-slice development."""

    letters: dict[str, dict[str, object]] = field(default_factory=dict)
    processing: dict[str, dict[str, object]] = field(default_factory=dict)

    def storage_reference_exists(
        self,
        *,
        owner_id: str,
        object_reference: str,
    ) -> bool:
        owner = _validated_uuid(owner_id, field_name="owner_id")
        return any(
            row["owner_id"] == owner
            and row["storage_object_id"] == object_reference
            for row in self.letters.values()
        )

    def source_exists_by_hash(self, *, owner_id: str, sha256: str) -> bool:
        owner = _validated_uuid(owner_id, field_name="owner_id")
        normalized_sha = sha256.lower()
        return any(
            row["owner_id"] == owner
            and row["original_sha256"] == normalized_sha
            for row in self.letters.values()
        )

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


def build_supabase_extraction_patch(
    record: DocumentRecord,
    *,
    owner_id: str,
    result: ExtractionResult,
) -> dict[str, object]:
    """Build the processing-row patch for extracted text/version."""

    return {
        "letter_id": _validated_uuid(record.record_id, field_name="record_id"),
        "owner_id": _validated_uuid(owner_id, field_name="owner_id"),
        "extracted_text": result.text,
        "ocr_version": result.version,
    }


def build_supabase_context_processing_patch(
    record: DocumentRecord,
    *,
    owner_id: str,
    result: ContextAnalysisResult,
) -> dict[str, object]:
    """Build letter_processing patch for structured context + concepts."""

    return {
        "letter_id": _validated_uuid(record.record_id, field_name="record_id"),
        "owner_id": _validated_uuid(owner_id, field_name="owner_id"),
        "structured_context": result.context.to_json_dict(),
        "concepts": list(result.context.concepts),
        "context_version": result.version,
        "filename_rule_version": (
            FILENAME_RULE_VERSION
            if result.context.title and result.context.authority
            else record.processing.filename_rule
        ),
    }


def build_supabase_letter_context_patch(
    record: DocumentRecord,
    *,
    owner_id: str,
    result: ContextAnalysisResult,
) -> dict[str, object]:
    """Build searchable public.letters metadata patch from structured context."""

    context = result.context
    row: dict[str, object] = {
        "id": _validated_uuid(record.record_id, field_name="record_id"),
        "owner_id": _validated_uuid(owner_id, field_name="owner_id"),
    }

    optional_values = {
        "title": context.title,
        "authority": context.authority,
        "category": context.category,
        "subcategory": context.subcategory,
        "summary": context.summary,
        "reference_number": context.reference_number,
        "action_required": context.action_required,
    }
    for key, value in optional_values.items():
        if value is not None and str(value).strip():
            row[key] = value

    parsed_issue_date: date | None = None
    if context.issue_date:
        try:
            parsed_issue_date = date.fromisoformat(context.issue_date)
            row["issue_date"] = parsed_issue_date.isoformat()
        except ValueError:
            parsed_issue_date = None

    if context.title and context.authority:
        row["smart_filename"] = build_smart_filename(
            short_title=context.title,
            issuer=context.authority,
            issue_date=parsed_issue_date,
            reference_number=context.reference_number,
            original_filename=record.original_filename,
        )

    deadline_at = _validated_deadline_at(context.deadline)
    if deadline_at:
        row["deadline_at"] = deadline_at

    return row
