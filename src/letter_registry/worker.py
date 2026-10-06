"""One-job derived-processing worker orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Protocol

from .extraction import ExtractionResult, VersionedTextExtractor
from .jobs import ProcessingJob
from .models import DocumentRecord
from .original_access import SupabaseOriginalAccessService
from .processing_pipeline import ProcessingOutcome, process_archived_document
from .autonomous_learning import AutonomousCorrectionMemory
from .relationship_inference import RelationshipCandidate, infer_relationship_suggestions
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


class RelationshipSuggestionRepository(Protocol):
    def save_suggestion(self, suggestion, *, owner_id: str) -> None:
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
    embeddings: EmbeddingRepository | None
    fallback_context_provider: DocumentContextProvider | None = None
    correction_memory: AutonomousCorrectionMemory | None = None
    relationship_repository: RelationshipSuggestionRepository | None = None
    allow_real_documents: bool = False

    def _progress(self, job: ProcessingJob, stage: str, percent: int, detail: str) -> None:
        try:
            self.database.update(
                "processing_jobs",
                {"progress_stage": stage, "progress_percent": percent, "progress_detail": detail},
                filters={"id": job.job_id},
            )
        except Exception:
            pass

    def run_once(self) -> WorkerRunResult:
        job = self.queue.claim_next()
        if job is None:
            return WorkerRunResult(status="idle")

        try:
            self._progress(job, "starting", 5, "Worker started")
            record = self.source_loader.load(job.letter_id)
            if record is None:
                raise RuntimeError("archived source record was not found")

            document_owner_id = job.owner_id
            select_rows = getattr(self.database, "select", None)
            if callable(select_rows):
                try:
                    owner_rows = select_rows(
                        "letters",
                        filters={"id": record.record_id},
                        columns="owner_id",
                    )
                    if owner_rows and owner_rows[0].get("owner_id"):
                        document_owner_id = str(owner_rows[0]["owner_id"])
                except Exception:
                    document_owner_id = job.owner_id

            if not self.allow_real_documents:
                name = record.original_filename.casefold()
                if "synthetic" not in name and "test" not in name:
                    raise RuntimeError(
                        "real document processing is disabled by runtime safety policy"
                    )

            self._progress(job, "source_ready", 12, "Loading original document")
            original = self.original_access.fetch(
                record_id=record.record_id,
                database=self.database,
            )
            if original is None:
                raise RuntimeError("private original could not be resolved")

            safe_name = Path(original.filename).name
            if not safe_name:
                raise RuntimeError("private original has no valid filename")

            extraction_override = None
            if job.reason.startswith(("manual_retry:", "manual_reprocess:", "quality-upgrade:")):
                try:
                    processing_rows = self.database.select(
                        "letter_processing",
                        filters={"letter_id": record.record_id},
                        columns="extracted_text,ocr_version",
                    )
                    if processing_rows:
                        existing_text = str(processing_rows[0].get("extracted_text") or "").strip()
                        existing_version = str(processing_rows[0].get("ocr_version") or "").strip()
                        if existing_text:
                            extraction_override = ExtractionResult(
                                text=existing_text,
                                method="reused_existing_extraction",
                                version=existing_version or record.processing.extraction,
                                needs_ocr=False,
                            )
                except Exception:
                    extraction_override = None

            intake_context = ""
            try:
                source_rows = self.database.select(
                    "letter_sources",
                    filters={"letter_id": record.record_id},
                    columns="metadata,received_at",
                )
                for source_row in source_rows:
                    metadata = source_row.get("metadata")
                    if isinstance(metadata, dict):
                        text = str(metadata.get("query_text") or "").strip()
                        if text:
                            intake_context = text
                            break
            except Exception:
                intake_context = ""

            with TemporaryDirectory() as directory:
                path = Path(directory) / safe_name
                path.write_bytes(original.content)

                outcome: ProcessingOutcome = process_archived_document(
                    path,
                    record=record,
                    owner_id=document_owner_id,
                    extractor=self.extractor,
                    context_provider=self.context_provider,
                    repository=self.repository,
                    fallback_context_provider=self.fallback_context_provider,
                    intake_context=intake_context,
                    correction_memory=self.correction_memory,
                    extraction_override=extraction_override,
                    progress_callback=lambda stage, percent, detail: self._progress(job, stage, percent, detail),
                )

                chunks = 0
                if self.embeddings is not None:
                    self._progress(job, "indexing", 88, "Updating search index")
                    chunks = self.embeddings.embed_document_chunks(
                        owner_id=document_owner_id,
                        letter_id=job.letter_id,
                        extracted_text=outcome.extraction.text,
                    )

            if self.relationship_repository is not None:
                self._progress(job, "relationships", 94, "Checking related documents")
                candidate_rows = self.database.select(
                    "letters",
                    filters={"owner_id": document_owner_id},
                    columns=(
                        "id,reference_number,authority,category,title,summary,issue_date"
                    ),
                )
                candidates = [
                    RelationshipCandidate(
                        record_id=str(row["id"]),
                        reference_number=(
                            str(row["reference_number"])
                            if row.get("reference_number") is not None
                            else None
                        ),
                        authority=(
                            str(row["authority"])
                            if row.get("authority") is not None
                            else None
                        ),
                        category=(
                            str(row["category"])
                            if row.get("category") is not None
                            else None
                        ),
                        title=(
                            str(row["title"])
                            if row.get("title") is not None
                            else None
                        ),
                        summary=(
                            str(row["summary"])
                            if row.get("summary") is not None
                            else None
                        ),
                        issue_date=(
                            str(row["issue_date"])
                            if row.get("issue_date") is not None
                            else None
                        ),
                    )
                    for row in candidate_rows
                ]
                suggestions = infer_relationship_suggestions(
                    source_letter_id=record.record_id,
                    source_reference_number=outcome.context.context.reference_number,
                    source_authority=outcome.context.context.authority,
                    source_category=outcome.context.context.category,
                    source_text=outcome.extraction.text,
                    source_title=outcome.context.context.title,
                    source_summary=outcome.context.context.summary,
                    source_issue_date=outcome.context.context.issue_date,
                    candidates=candidates,
                )
                for suggestion in suggestions:
                    self.relationship_repository.save_suggestion(
                        suggestion,
                        owner_id=document_owner_id,
                    )

            if self.embeddings is not None:
                version = str(getattr(self.embeddings.provider, "version"))
                self.repository.save_embedding_version(
                    record,
                    owner_id=document_owner_id,
                    embedding_version=version,
                )
            self._progress(job, "complete", 100, "Reprocess complete")
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
