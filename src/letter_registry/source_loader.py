"""Load archived source identity for derived-processing workers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol

from .models import DocumentRecord, DocumentStatus, ProcessingVersions


class SourceTransport(Protocol):
    def select(
        self,
        table: str,
        *,
        filters: dict[str, str] | None = None,
        columns: str = "*",
    ) -> list[dict[str, object]]:
        ...


def _dt(value: object) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


@dataclass(slots=True)
class SupabaseSourceLoader:
    transport: SourceTransport

    def load(self, record_id: str) -> DocumentRecord | None:
        rows = self.transport.select(
            "letters",
            filters={"id": record_id},
            columns=(
                "id,original_filename,original_sha256,storage_object_id,"
                "received_at,uploaded_at,issue_date,status"
            ),
        )
        if not rows:
            return None

        processing_rows = self.transport.select(
            "letter_processing",
            filters={"letter_id": record_id},
            columns=(
                "ocr_version,context_version,dictionary_version,"
                "filename_rule_version,category_schema_version,"
                "embedding_version,status_rule_version"
            ),
        )
        p = processing_rows[0] if processing_rows else {}
        row = rows[0]

        issue_date = (
            date.fromisoformat(str(row["issue_date"]))
            if row.get("issue_date")
            else None
        )
        return DocumentRecord(
            record_id=str(row["id"]),
            original_filename=str(row["original_filename"]),
            original_sha256=str(row["original_sha256"]),
            original_storage_reference=str(row["storage_object_id"]),
            received_at=_dt(row["received_at"]),
            uploaded_at=_dt(row["uploaded_at"]),
            issue_date=issue_date,
            status=DocumentStatus(str(row.get("status") or "unknown")),
            processing=ProcessingVersions(
                extraction=str(p.get("ocr_version") or "unprocessed"),
                context=str(p.get("context_version") or "unprocessed"),
                dictionary=str(p.get("dictionary_version") or "unprocessed"),
                filename_rule=str(p.get("filename_rule_version") or "unprocessed"),
                category_schema=str(p.get("category_schema_version") or "unprocessed"),
                embedding=str(p.get("embedding_version") or "unprocessed"),
                status_rule=str(p.get("status_rule_version") or "unprocessed"),
            ),
        )
