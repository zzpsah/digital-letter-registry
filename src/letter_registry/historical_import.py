"""Historical bulk-import preview.

This layer inventories candidate files and predicts duplicate/new outcomes.
It performs no storage upload, database insert, rename, OCR, or AI call.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol

from .fingerprints import sha256_file


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
