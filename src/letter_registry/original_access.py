"""Server-side access to immutable originals without leaking storage references."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class OriginalFile:
    filename: str
    content_type: str
    content: bytes


class DatabaseTransport(Protocol):
    def select(
        self,
        table: str,
        *,
        filters: dict[str, str] | None = None,
        columns: str = "*",
    ) -> list[dict[str, object]]:
        ...


class PrivateOriginalTransport(Protocol):
    """Runtime private-storage reader.

    Implementations may use Google Drive, object storage, or another private
    backend. They receive opaque server-side references only.
    """

    def download(
        self,
        *,
        provider: str,
        object_reference: str,
        filename: str,
    ) -> OriginalFile:
        ...


@dataclass(slots=True)
class SupabaseOriginalAccessService:
    storage: PrivateOriginalTransport

    def fetch(
        self,
        *,
        record_id: str,
        database: DatabaseTransport,
    ) -> OriginalFile | None:
        rows = database.select(
            "letters",
            filters={"id": record_id},
            columns="original_filename,storage_provider,storage_object_id",
        )
        if not rows:
            return None

        row = rows[0]
        filename = str(row["original_filename"])
        provider = str(row["storage_provider"])
        object_reference = str(row["storage_object_id"])

        return self.storage.download(
            provider=provider,
            object_reference=object_reference,
            filename=filename,
        )
