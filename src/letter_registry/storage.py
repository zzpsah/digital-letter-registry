"""Private original-storage ports.

Provider-specific credentials and folder identifiers are runtime configuration.
This module performs no network access by itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True, slots=True)
class StoredOriginal:
    provider: str
    object_reference: str


class OriginalStorage(Protocol):
    """Store an immutable original and return an opaque private reference."""

    def store_original(self, path: str | Path) -> StoredOriginal:
        ...


@dataclass(slots=True)
class InMemoryOriginalStorage:
    """Synthetic storage for tests; stores bytes only in process memory."""

    provider: str = "memory"
    objects: dict[str, bytes] = field(default_factory=dict)

    def store_original(self, path: str | Path) -> StoredOriginal:
        source = Path(path)
        if not source.is_file():
            raise ValueError("source path must be an existing file")

        key = f"synthetic:{len(self.objects) + 1}"
        self.objects[key] = source.read_bytes()
        return StoredOriginal(provider=self.provider, object_reference=key)


class GoogleDriveTransport(Protocol):
    """Runtime-supplied Google Drive transport."""

    def upload_file(
        self,
        *,
        folder_reference: str,
        filename: str,
        path: Path,
    ) -> str:
        """Upload and return the private Drive file/object identifier."""
        ...


@dataclass(slots=True)
class GoogleDriveOriginalStorage:
    """Google Drive adapter with no hard-coded folder ID or credentials."""

    transport: GoogleDriveTransport
    originals_folder_reference: str
    provider: str = "gdrive"

    def __post_init__(self) -> None:
        if not self.originals_folder_reference.strip():
            raise ValueError("originals_folder_reference is required")

    def store_original(self, path: str | Path) -> StoredOriginal:
        source = Path(path)
        if not source.is_file():
            raise ValueError("source path must be an existing file")

        object_reference = self.transport.upload_file(
            folder_reference=self.originals_folder_reference,
            filename=source.name,
            path=source,
        )
        if not object_reference.strip():
            raise ValueError("Drive transport returned an empty object reference")

        return StoredOriginal(
            provider=self.provider,
            object_reference=object_reference,
        )
