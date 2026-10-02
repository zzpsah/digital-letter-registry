"""Durable-processing queue contracts.

The HTTP intake path only archives the immutable source and enqueues a job.
OCR/AI/embedding work belongs to a worker.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class ProcessingJob:
    job_id: str
    letter_id: str
    owner_id: str
    created_at: datetime
    reason: str = "initial_processing"


class ProcessingQueue(Protocol):
    def enqueue(
        self,
        *,
        letter_id: str,
        owner_id: str,
        reason: str = "initial_processing",
    ) -> ProcessingJob:
        ...


@dataclass(slots=True)
class InMemoryProcessingQueue:
    """Synthetic queue used by tests/development only."""

    jobs: list[ProcessingJob] = field(default_factory=list)

    def enqueue(
        self,
        *,
        letter_id: str,
        owner_id: str,
        reason: str = "initial_processing",
    ) -> ProcessingJob:
        UUID(letter_id)
        UUID(owner_id)
        if not reason.strip():
            raise ValueError("processing job reason is required")

        existing = next(
            (
                job
                for job in self.jobs
                if job.letter_id == letter_id and job.reason == reason
            ),
            None,
        )
        if existing is not None:
            return existing

        job = ProcessingJob(
            job_id=str(uuid4()),
            letter_id=letter_id,
            owner_id=owner_id,
            created_at=datetime.now(timezone.utc),
            reason=reason,
        )
        self.jobs.append(job)
        return job


class JobTransport(Protocol):
    def rpc(
        self,
        function: str,
        params: dict[str, object],
    ) -> list[dict[str, object]]:
        ...

    def select(
        self,
        table: str,
        *,
        filters: dict[str, str] | None = None,
        columns: str = "*",
    ) -> list[dict[str, object]]:
        ...

    def insert(
        self,
        table: str,
        row: dict[str, object],
        *,
        on_conflict: str | None = None,
    ) -> dict[str, object]:
        ...


@dataclass(slots=True)
class SupabaseProcessingQueue:
    """Durable queue persisted in public.processing_jobs."""

    transport: JobTransport

    def enqueue(
        self,
        *,
        letter_id: str,
        owner_id: str,
        reason: str = "initial_processing",
    ) -> ProcessingJob:
        UUID(letter_id)
        UUID(owner_id)
        if not reason.strip():
            raise ValueError("processing job reason is required")

        row = self.transport.insert(
            "processing_jobs",
            {
                "owner_id": owner_id,
                "letter_id": letter_id,
                "reason": reason,
                "status": "pending",
            },
            on_conflict="letter_id,reason",
        )

        if not row.get("id"):
            existing = self.transport.select(
                "processing_jobs",
                filters={
                    "letter_id": letter_id,
                    "reason": reason,
                },
                columns="id,created_at,reason",
            )
            if not existing:
                raise RuntimeError(
                    "processing job insert returned no row and no existing job was found"
                )
            row = existing[0]

        job_id = str(row["id"])
        created_raw = row.get("created_at")
        created_at = (
            datetime.fromisoformat(str(created_raw).replace("Z", "+00:00"))
            if created_raw
            else datetime.now(timezone.utc)
        )
        return ProcessingJob(
            job_id=job_id,
            letter_id=letter_id,
            owner_id=owner_id,
            created_at=created_at,
            reason=str(row.get("reason") or reason),
        )

    def claim_next(self) -> ProcessingJob | None:
        rows = self.transport.rpc("claim_processing_job", {})
        if not rows:
            return None

        row = rows[0]
        return ProcessingJob(
            job_id=str(row["id"]),
            letter_id=str(row["letter_id"]),
            owner_id=str(row["owner_id"]),
            created_at=datetime.fromisoformat(
                str(row["created_at"]).replace("Z", "+00:00")
            ),
            reason=str(row.get("reason") or "initial_processing"),
        )

    def complete(self, job: ProcessingJob) -> None:
        self.transport.rpc(
            "complete_processing_job",
            {"job_id": job.job_id},
        )

    def fail(self, job: ProcessingJob, *, error_message: str) -> None:
        self.transport.rpc(
            "fail_processing_job",
            {
                "job_id": job.job_id,
                "error_message": error_message[:2000],
            },
        )
