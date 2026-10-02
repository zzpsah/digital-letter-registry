"""Processing-version registry and reprocessing preview."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ProcessingTargetVersions:
    extraction: str
    context: str
    dictionary: str
    filename_rule: str
    category_schema: str
    embedding: str
    status_rule: str

    def __post_init__(self) -> None:
        for value in (
            self.extraction,
            self.context,
            self.dictionary,
            self.filename_rule,
            self.category_schema,
            self.embedding,
            self.status_rule,
        ):
            if not value.strip():
                raise ValueError("processing target versions cannot be blank")


@dataclass(frozen=True, slots=True)
class ReprocessingPreview:
    letter_id: str
    title: str | None
    smart_filename: str | None
    differences: tuple[str, ...]


class ReprocessingQueue(Protocol):
    def enqueue(
        self,
        *,
        letter_id: str,
        owner_id: str,
        reason: str = "initial_processing",
    ):
        ...


class VersionRegistryTransport(Protocol):
    def select(
        self,
        table: str,
        *,
        filters: dict[str, str] | None = None,
        columns: str = "*",
    ) -> list[dict[str, object]]:
        ...

    def upsert(
        self,
        table: str,
        row: dict[str, object],
        *,
        on_conflict: str,
    ) -> dict[str, object]:
        ...

    def rpc(
        self,
        function: str,
        params: dict[str, object],
    ) -> list[dict[str, object]]:
        ...


@dataclass(slots=True)
class SupabaseProcessingVersionRegistry:
    transport: VersionRegistryTransport

    def set_profile(
        self,
        *,
        owner_id: str,
        versions: ProcessingTargetVersions,
    ) -> None:
        UUID(owner_id)
        self.transport.upsert(
            "processing_profiles",
            {
                "owner_id": owner_id,
                "extraction_version": versions.extraction,
                "context_version": versions.context,
                "dictionary_version": versions.dictionary,
                "filename_rule_version": versions.filename_rule,
                "category_schema_version": versions.category_schema,
                "embedding_version": versions.embedding,
                "status_rule_version": versions.status_rule,
            },
            on_conflict="owner_id",
        )

    def get_profile(
        self,
        *,
        owner_id: str,
    ) -> ProcessingTargetVersions | None:
        UUID(owner_id)
        rows = self.transport.select(
            "processing_profiles",
            filters={"owner_id": owner_id},
            columns=(
                "extraction_version,context_version,dictionary_version,"
                "filename_rule_version,category_schema_version,"
                "embedding_version,status_rule_version"
            ),
        )
        if not rows:
            return None
        row = rows[0]
        return ProcessingTargetVersions(
            extraction=str(row["extraction_version"]),
            context=str(row["context_version"]),
            dictionary=str(row["dictionary_version"]),
            filename_rule=str(row["filename_rule_version"]),
            category_schema=str(row["category_schema_version"]),
            embedding=str(row["embedding_version"]),
            status_rule=str(row["status_rule_version"]),
        )

    def enqueue_reprocessing(self, *, limit: int = 500) -> int:
        if limit < 1 or limit > 500:
            raise ValueError("limit must be between 1 and 500")
        rows = self.transport.rpc(
            "enqueue_reprocessing_jobs",
            {"result_limit": limit},
        )
        if not rows:
            return 0
        return int(rows[0].get("enqueued") or 0)

    def preview(self, *, limit: int = 100) -> list[ReprocessingPreview]:
        if limit < 1 or limit > 500:
            raise ValueError("limit must be between 1 and 500")
        rows = self.transport.rpc(
            "preview_reprocessing",
            {"result_limit": limit},
        )
        return [
            ReprocessingPreview(
                letter_id=str(row["letter_id"]),
                title=row.get("title"),
                smart_filename=row.get("smart_filename"),
                differences=tuple(str(x) for x in (row.get("differences") or [])),
            )
            for row in rows
        ]



def reprocessing_reason(versions: ProcessingTargetVersions) -> str:
    payload = json.dumps(
        {
            "extraction": versions.extraction,
            "context": versions.context,
            "dictionary": versions.dictionary,
            "filename_rule": versions.filename_rule,
            "category_schema": versions.category_schema,
            "embedding": versions.embedding,
            "status_rule": versions.status_rule,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = sha256(payload).hexdigest()[:16]
    return f"reprocess:{digest}"


@dataclass(frozen=True, slots=True)
class ReprocessingScheduleResult:
    reason: str
    queued_letter_ids: tuple[str, ...]


def schedule_reprocessing_preview(
    *,
    owner_id: str,
    versions: ProcessingTargetVersions,
    preview: list[ReprocessingPreview],
    queue: ReprocessingQueue,
    approved: bool = False,
) -> ReprocessingScheduleResult:
    UUID(owner_id)
    if not approved:
        raise PermissionError(
            "reprocessing scheduling requires explicit approval"
        )

    reason = reprocessing_reason(versions)
    queued: list[str] = []
    for item in preview:
        UUID(item.letter_id)
        queue.enqueue(
            letter_id=item.letter_id,
            owner_id=owner_id,
            reason=reason,
        )
        queued.append(item.letter_id)

    return ReprocessingScheduleResult(
        reason=reason,
        queued_letter_ids=tuple(queued),
    )
