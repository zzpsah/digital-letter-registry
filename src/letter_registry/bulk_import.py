"""Preview-first historical bulk import.

Scanning and preview are read-only. Execution requires an exact preview digest
plus explicit confirmation and delegates each accepted file to IntakeService,
which preserves all existing storage, duplicate, and queue safety rules.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol

from .fingerprints import sha256_file


_ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


class DuplicateLookup(Protocol):
    def source_exists_by_hash(self, *, owner_id: str, sha256: str) -> bool:
        ...


class BulkIntake(Protocol):
    def ingest(self, path: str | Path, *, owner_id: str):
        ...


@dataclass(frozen=True, slots=True)
class BulkImportItem:
    relative_path: str
    filename: str
    sha256: str | None
    size_bytes: int
    status: str
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class BulkImportPreview:
    root: str
    items: tuple[BulkImportItem, ...]
    digest: str

    @property
    def new_count(self) -> int:
        return sum(1 for item in self.items if item.status == "new")

    @property
    def duplicate_count(self) -> int:
        return sum(1 for item in self.items if item.status == "duplicate")

    @property
    def skipped_count(self) -> int:
        return sum(1 for item in self.items if item.status == "skipped")


@dataclass(frozen=True, slots=True)
class BulkImportExecutionResult:
    imported: int
    skipped: int
    failed: int
    failures: tuple[str, ...]


def _preview_digest(root: Path, items: Iterable[BulkImportItem]) -> str:
    payload = {
        "root_name": root.name,
        "items": [
            {
                "relative_path": item.relative_path,
                "filename": item.filename,
                "sha256": item.sha256,
                "size_bytes": item.size_bytes,
                "status": item.status,
                "reason": item.reason,
            }
            for item in items
        ],
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def preview_historical_import(
    root: str | Path,
    *,
    owner_id: str,
    repository: DuplicateLookup,
    recursive: bool = True,
) -> BulkImportPreview:
    source_root = Path(root)
    if not source_root.is_dir():
        raise ValueError("bulk import root must be an existing directory")

    iterator = source_root.rglob("*") if recursive else source_root.glob("*")
    items: list[BulkImportItem] = []

    for path in sorted(
        (p for p in iterator if p.is_file()),
        key=lambda p: p.relative_to(source_root).as_posix().casefold(),
    ):
        relative = path.relative_to(source_root).as_posix()
        extension = path.suffix.lower()
        size = path.stat().st_size

        if extension not in _ALLOWED_EXTENSIONS:
            items.append(
                BulkImportItem(
                    relative_path=relative,
                    filename=path.name,
                    sha256=None,
                    size_bytes=size,
                    status="skipped",
                    reason="unsupported_file_type",
                )
            )
            continue

        if size < 1:
            items.append(
                BulkImportItem(
                    relative_path=relative,
                    filename=path.name,
                    sha256=None,
                    size_bytes=size,
                    status="skipped",
                    reason="empty_file",
                )
            )
            continue

        digest = sha256_file(path)
        duplicate = repository.source_exists_by_hash(
            owner_id=owner_id,
            sha256=digest,
        )
        items.append(
            BulkImportItem(
                relative_path=relative,
                filename=path.name,
                sha256=digest,
                size_bytes=size,
                status="duplicate" if duplicate else "new",
                reason="already_archived" if duplicate else None,
            )
        )

    frozen = tuple(items)
    return BulkImportPreview(
        root=str(source_root),
        items=frozen,
        digest=_preview_digest(source_root, frozen),
    )


def execute_historical_import(
    preview: BulkImportPreview,
    *,
    approved_digest: str,
    confirmed: bool,
    owner_id: str,
    intake: BulkIntake,
) -> BulkImportExecutionResult:
    if not confirmed:
        raise PermissionError("bulk import requires explicit confirmation")
    if approved_digest != preview.digest:
        raise ValueError("approved bulk-import digest does not match preview")

    root = Path(preview.root)
    imported = 0
    skipped = 0
    failures: list[str] = []

    for item in preview.items:
        if item.status != "new":
            skipped += 1
            continue

        path = root / item.relative_path
        if not path.is_file():
            failures.append(f"{item.relative_path}: source file no longer exists")
            continue

        current_sha = sha256_file(path)
        if current_sha != item.sha256:
            failures.append(
                f"{item.relative_path}: source changed after preview"
            )
            continue

        try:
            intake.ingest(path, owner_id=owner_id)
            imported += 1
        except Exception as exc:
            failures.append(
                f"{item.relative_path}: {str(exc)[:500] or exc.__class__.__name__}"
            )

    return BulkImportExecutionResult(
        imported=imported,
        skipped=skipped,
        failed=len(failures),
        failures=tuple(failures),
    )
