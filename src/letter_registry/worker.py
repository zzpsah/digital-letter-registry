"""One-job derived-processing worker orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Protocol

from .extraction import VersionedTextExtractor
from .jobs import ProcessingJob
from .models import DocumentRecord
from .original_access import SupabaseOriginalAccessService
from .processing_pipeline import ProcessingOutcome, process_archived_document
from .structured_analysis import DocumentContextProvider


class WorkerQueue(Protocol):
    def claim_next(self) -> ProcessingJob | None:
        ...

    def complete(self, job: ProcessingJob) -> None:
        ...

    def fail(self, job: ProcessingJob, *, error_message: str) -> None:
        ...


class SourceLoader(Protocol):
    def load(self, record_id: str) -> DocumentRecord | None:
        ...


class WorkerRepository(Protocol):
    def save_extraction_result(self, record, *, owner_id, result) -> None:
        ...

    def save_context_result(self, record, *, owner_id, result) -> None:
        ...

    def save_embedding_version(
        self,
        record: DocumentRecord,
        *,
        owner_id: str,
        embedding_version: str,
    ) -> None:
        ...


class EmbeddingRepository(Protocol):
    provider: object

    def embed_document_chunks(
        self,
        *,
        owner_id: str,
        letter_id: str,
        extracted_text: str,
        max_characters: int = 2400,
        overlap_characters: int = 240,
    ) -> int:
        ...


@dataclass(frozen=True, slots=True)
class WorkerRunResult:
    status: str
    job_id: str | None = None
    letter_id: str | None = None
    chunks: int = 0
    error: str | None = None


@dataclass(slots=True)
class DocumentProcessingWorker:
    queue: WorkerQueue
    source_loader: SourceLoader
    database: object
    original_access: SupabaseOriginalAccessService
    repository: WorkerRepository
    extractor: VersionedTextExtractor
    context_provider: DocumentContextProvider
    embeddings: EmbeddingRepository
    allow_real_documents: bool = False

    def run_once(self) -> WorkerRunResult:
        job = self.queue.claim_next()
        if job is None:
            return WorkerRunResult(status="idle")

        try:
            record = self.source_loader.load(job.letter_id)
            if record is None:
                raise RuntimeError("archived source record was not found")

            if not self.allow_real_documents:
                name = record.original_filename.casefold()
                if "synthetic" not in name and "test" not in name:
                    raise RuntimeError(
                        "real document processing is disabled by runtime safety policy"
                    )

            original = self.original_access.fetch(
                record_id=record.record_id,
                database=self.database,
            )
            if original is None:
                raise RuntimeError("private original could not be resolved")

            safe_name = Path(original.filename).name
            if not safe_name:
                raise RuntimeError("private original has no valid filename")

            with TemporaryDirectory() as directory:
                path = Path(directory) / safe_name
                path.write_bytes(original.content)

                outcome: ProcessingOutcome = process_archived_document(
                    path,
                    record=record,
                    owner_id=job.owner_id,
                    extractor=self.extractor,
                    context_provider=self.context_provider,
                    repository=self.repository,
                )

                chunks = self.embeddings.embed_document_chunks(
                    owner_id=job.owner_id,
                    letter_id=job.letter_id,
                    extracted_text=outcome.extraction.text,
                )

            version = str(getattr(self.embeddings.provider, "version"))
            self.repository.save_embedding_version(
                record,
                owner_id=job.owner_id,
                embedding_version=version,
            )
            self.queue.complete(job)
            return WorkerRunResult(
                status="completed",
                job_id=job.job_id,
                letter_id=job.letter_id,
                chunks=chunks,
            )
        except Exception as exc:
            message = str(exc)[:2000] or exc.__class__.__name__
            self.queue.fail(job, error_message=message)
            return WorkerRunResult(
                status="failed",
                job_id=job.job_id,
                letter_id=job.letter_id,
                error=message,
            )
