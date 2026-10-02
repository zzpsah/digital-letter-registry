"""Historical bulk-import preview.

This layer inventories candidate files and predicts duplicate/new outcomes.
It performs no storage upload, database insert, rename, OCR, or AI call.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePath
from typing import Iterable, Protocol
from uuid import uuid4

from .fingerprints import sha256_file
from .google_drive_catalog import HistoricalDriveItem
from .jobs import ProcessingJob, ProcessingQueue
from .models import DocumentRecord
from .original_access import OriginalFile
from .persistence import LetterRepository


_ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


@dataclass(frozen=True, slots=True)
class HistoricalImportCandidate:
    path: Path
    original_filename: str
    sha256: str
    size_bytes: int
    extension: str
    duplicate: bool


@dataclass(frozen=True, slots=True)
class HistoricalImportPreview:
    candidates: tuple[HistoricalImportCandidate, ...]
    total_files: int
    new_files: int
    duplicate_files: int
    total_bytes: int


class DuplicateLookup(Protocol):
    def source_exists_by_hash(self, *, owner_id: str, sha256: str) -> bool:
        ...


def preview_historical_import(
    paths: Iterable[str | Path],
    *,
    owner_id: str,
    repository: DuplicateLookup,
) -> HistoricalImportPreview:
    """Inspect local candidate files without mutating storage/database."""

    candidates: list[HistoricalImportCandidate] = []
    seen_hashes: set[str] = set()

    for raw in paths:
        path = Path(raw)
        if not path.is_file():
            continue

        extension = path.suffix.lower()
        if extension not in _ALLOWED_EXTENSIONS:
            continue

        digest = sha256_file(path)
        duplicate = (
            digest in seen_hashes
            or repository.source_exists_by_hash(
                owner_id=owner_id,
                sha256=digest,
            )
        )
        seen_hashes.add(digest)

        candidates.append(
            HistoricalImportCandidate(
                path=path,
                original_filename=path.name,
                sha256=digest,
                size_bytes=path.stat().st_size,
                extension=extension.lstrip("."),
                duplicate=duplicate,
            )
        )

    total_bytes = sum(item.size_bytes for item in candidates)
    duplicate_files = sum(1 for item in candidates if item.duplicate)
    return HistoricalImportPreview(
        candidates=tuple(candidates),
        total_files=len(candidates),
        new_files=len(candidates) - duplicate_files,
        duplicate_files=duplicate_files,
        total_bytes=total_bytes,
    )



class HistoricalDriveReader(Protocol):
    def download(
        self,
        *,
        provider: str,
        object_reference: str,
        filename: str,
    ) -> OriginalFile:
        ...


@dataclass(frozen=True, slots=True)
class HistoricalDrivePreviewItem:
    object_reference: str
    filename: str
    status: str
    reason: str
    size_bytes: int | None


@dataclass(frozen=True, slots=True)
class HistoricalDriveAdoptionResult:
    record: DocumentRecord
    job: ProcessingJob


@dataclass(slots=True)
class HistoricalDriveImportService:
    """Preview and explicitly adopt files that already live in private Drive."""

    repository: LetterRepository
    queue: ProcessingQueue
    reader: HistoricalDriveReader
    synthetic_only: bool = True
    max_bytes: int = 50 * 1024 * 1024

    def preview(
        self,
        items: list[HistoricalDriveItem],
        *,
        owner_id: str,
    ) -> list[HistoricalDrivePreviewItem]:
        rows: list[HistoricalDrivePreviewItem] = []
        for item in items:
            extension = PurePath(item.filename).suffix.lower()
            if extension not in _ALLOWED_EXTENSIONS:
                rows.append(
                    HistoricalDrivePreviewItem(
                        object_reference=item.object_reference,
                        filename=item.filename,
                        status="unsupported",
                        reason="unsupported file type",
                        size_bytes=item.size_bytes,
                    )
                )
                continue

            if item.size_bytes is not None and item.size_bytes > self.max_bytes:
                rows.append(
                    HistoricalDrivePreviewItem(
                        object_reference=item.object_reference,
                        filename=item.filename,
                        status="too_large",
                        reason="file exceeds historical import size limit",
                        size_bytes=item.size_bytes,
                    )
                )
                continue

            if self.repository.storage_reference_exists(
                owner_id=owner_id,
                object_reference=item.object_reference,
            ):
                rows.append(
                    HistoricalDrivePreviewItem(
                        object_reference=item.object_reference,
                        filename=item.filename,
                        status="already_archived",
                        reason="private storage object is already registered",
                        size_bytes=item.size_bytes,
                    )
                )
                continue

            lowered = item.filename.casefold()
            if (
                self.synthetic_only
                and "synthetic" not in lowered
                and "test" not in lowered
            ):
                rows.append(
                    HistoricalDrivePreviewItem(
                        object_reference=item.object_reference,
                        filename=item.filename,
                        status="real_document_blocked",
                        reason="real historical adoption is disabled",
                        size_bytes=item.size_bytes,
                    )
                )
                continue

            rows.append(
                HistoricalDrivePreviewItem(
                    object_reference=item.object_reference,
                    filename=item.filename,
                    status="eligible",
                    reason="ready for confirmed adoption",
                    size_bytes=item.size_bytes,
                )
            )
        return rows

    def adopt(
        self,
        item: HistoricalDriveItem,
        *,
        owner_id: str,
        confirmed: bool,
    ) -> HistoricalDriveAdoptionResult:
        if not confirmed:
            raise ValueError(
                "historical adoption requires explicit confirmation"
            )

        preview = self.preview([item], owner_id=owner_id)[0]
        if preview.status != "eligible":
            raise ValueError(
                f"historical item is not eligible: {preview.status}"
            )

        original = self.reader.download(
            provider="gdrive",
            object_reference=item.object_reference,
            filename=item.filename,
        )
        if not original.content:
            raise ValueError("downloaded historical file is empty")
        if len(original.content) > self.max_bytes:
            raise ValueError(
                "downloaded historical file exceeds size limit"
            )

        digest = hashlib.sha256(original.content).hexdigest()
        if self.repository.source_exists_by_hash(
            owner_id=owner_id,
            sha256=digest,
        ):
            raise ValueError(
                "historical source content is already archived"
            )

        received_at = item.modified_at or datetime.now(timezone.utc)
        if received_at.tzinfo is None:
            received_at = received_at.replace(tzinfo=timezone.utc)

        record = DocumentRecord(
            record_id=str(uuid4()),
            original_filename=item.filename,
            original_sha256=digest,
            original_storage_reference=item.object_reference,
            received_at=received_at,
        )
        self.repository.save_source(record, owner_id=owner_id)
        self.repository.save_processing_state(
            record,
            owner_id=owner_id,
        )
        job = self.queue.enqueue(
            letter_id=record.record_id,
            owner_id=owner_id,
            reason="historical_import",
        )
        return HistoricalDriveAdoptionResult(
            record=record,
            job=job,
        )
