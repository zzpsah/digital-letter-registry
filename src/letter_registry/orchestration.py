"""Ingestion orchestration across private storage and persistence."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .ingestion import prepare_source_record, persist_prepared_source
from .models import DocumentRecord, ProcessingVersions
from .persistence import LetterRepository
from .storage import OriginalStorage


def ingest_original(
    path: str | Path,
    *,
    storage: OriginalStorage,
    repository: LetterRepository,
    owner_id: str,
    received_at: datetime | None = None,
    record_id: str | None = None,
    processing: ProcessingVersions | None = None,
) -> DocumentRecord:
    """Store the immutable original, then persist its source identity."""

    stored = storage.store_original(path)
    record = prepare_source_record(
        path,
        storage_reference=stored.object_reference,
        received_at=received_at,
        record_id=record_id,
        processing=processing,
    )

    persist_prepared_source(repository, record, owner_id=owner_id)
    return record
