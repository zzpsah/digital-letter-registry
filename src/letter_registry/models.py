"""Stable source-record and derived-processing contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import StrEnum


class DocumentStatus(StrEnum):
    CURRENT = "current"
    EXPIRED = "expired"
    HISTORICAL = "historical"
    SUPERSEDED = "superseded"
    UNKNOWN = "unknown"


class DocumentRelationship(StrEnum):
    DUPLICATE_OF = "duplicate_of"
    EXTENDS = "extends"
    SUPERSEDES = "supersedes"
    CORRECTS = "corrects"
    RELATED_TO = "related_to"


@dataclass(frozen=True, slots=True)
class ProcessingVersions:
    """Versions prove which replaceable processors produced derived fields."""

    extraction: str = "unprocessed"
    context: str = "unprocessed"
    dictionary: str = "unprocessed"
    filename_rule: str = "unprocessed"
    category_schema: str = "unprocessed"
    embedding: str = "unprocessed"
    status_rule: str = "unprocessed"


@dataclass(frozen=True, slots=True)
class DocumentRecord:
    """The immutable source identity for one privately stored original."""

    record_id: str
    original_filename: str
    original_sha256: str
    original_storage_reference: str
    received_at: datetime
    uploaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    issue_date: date | None = None
    status: DocumentStatus = DocumentStatus.UNKNOWN
    processing: ProcessingVersions = field(default_factory=ProcessingVersions)

    def __post_init__(self) -> None:
        if not self.record_id.strip():
            raise ValueError("record_id is required")
        if not self.original_filename.strip():
            raise ValueError("original_filename is required")
        if len(self.original_sha256) != 64 or any(
            char not in "0123456789abcdef" for char in self.original_sha256.lower()
        ):
            raise ValueError("original_sha256 must be a SHA-256 hex digest")
        if not self.original_storage_reference.strip():
            raise ValueError("original_storage_reference is required")
        if self.received_at.tzinfo is None or self.uploaded_at.tzinfo is None:
            raise ValueError("received_at and uploaded_at must be timezone-aware")
