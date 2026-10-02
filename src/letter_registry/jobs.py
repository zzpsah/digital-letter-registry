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
    def enqueue(self, *, letter_id: str, owner_id: str) -> ProcessingJob:
        ...


@dataclass(slots=True)
class InMemoryProcessingQueue:
    """Synthetic queue used by tests/development only."""

    jobs: list[ProcessingJob] = field(default_factory=list)

    def enqueue(self, *, letter_id: str, owner_id: str) -> ProcessingJob:
        UUID(letter_id)
        UUID(owner_id)
        job = ProcessingJob(
            job_id=str(uuid4()),
            letter_id=letter_id,
            owner_id=owner_id,
            created_at=datetime.now(timezone.utc),
        )
        self.jobs.append(job)
        return job



class JobTransport(Protocol):
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

    def enqueue(self, *, letter_id: str, owner_id: str) -> ProcessingJob:
        UUID(letter_id)
        UUID(owner_id)
        row = self.transport.insert(
            "processing_jobs",
            {
                "owner_id": owner_id,
                "letter_id": letter_id,
                "reason": "initial_processing",
                "status": "pending",
            },
            on_conflict="letter_id,reason",
        )

        job_id = str(row.get("id") or uuid4())
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
        )
