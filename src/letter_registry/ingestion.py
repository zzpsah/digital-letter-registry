"""Provider-independent ingestion preparation.

This stage prepares immutable source identity from a local/synthetic file and a
private storage reference. It performs no Drive upload, OCR, AI call, or network
request.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .fingerprints import sha256_file
from .models import DocumentRecord, ProcessingVersions
from .persistence import LetterRepository


def prepare_source_record(
    path: str | Path,
    *,
    storage_reference: str,
    received_at: datetime | None = None,
    record_id: str | None = None,
    processing: ProcessingVersions | None = None,
) -> DocumentRecord:
    """Build immutable source identity after private storage has supplied a reference."""

    source_path = Path(path)
    if not source_path.is_file():
        raise ValueError("source path must be an existing file")
    if not storage_reference.strip():
        raise ValueError("storage_reference is required")

    received = received_at or datetime.now(timezone.utc)
    if received.tzinfo is None:
        raise ValueError("received_at must be timezone-aware")

    return DocumentRecord(
        record_id=record_id or str(uuid4()),
        original_filename=source_path.name,
        original_sha256=sha256_file(source_path),
        original_storage_reference=storage_reference,
        received_at=received,
        processing=processing or ProcessingVersions(),
    )


def persist_prepared_source(
    repository: LetterRepository,
    record: DocumentRecord,
    *,
    owner_id: str,
) -> None:
    """Persist source identity then initialize its processing-version row."""

    repository.save_source(record, owner_id=owner_id)
    repository.save_processing_state(record, owner_id=owner_id)
