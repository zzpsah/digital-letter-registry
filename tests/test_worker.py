from datetime import datetime, timezone
from pathlib import Path
import unittest

from letter_registry.context_hints import ContextHints
from letter_registry.extraction import VersionedTextExtractor
from letter_registry.jobs import ProcessingJob
from letter_registry.models import DocumentRecord
from letter_registry.original_access import OriginalFile
from letter_registry.structured_analysis import StructuredDocumentContext
from letter_registry.worker import DocumentProcessingWorker


OWNER_ID = "11111111-1111-4111-8111-111111111111"
LETTER_ID = "22222222-2222-4222-8222-222222222222"
JOB_ID = "33333333-3333-4333-8333-333333333333"


class FakeQueue:
    def __init__(self, job):
        self.job = job
        self.completed = []
        self.failed = []

    def claim_next(self):
        job, self.job = self.job, None
        return job

    def complete(self, job):
        self.completed.append(job.job_id)

    def fail(self, job, *, error_message):
        self.failed.append((job.job_id, error_message))


class FakeSourceLoader:
    def __init__(self, record):
        self.record = record

    def load(self, record_id):
        return self.record


class FakeDatabase:
    pass


class FakeOriginalAccess:
    def fetch(self, *, record_id, database):
        return OriginalFile(
            filename="synthetic.pdf",
            content_type="application/pdf",
            content=b"%PDF-synthetic",
        )


class FakePdfBackend:
    def extract_text(self, path: Path) -> str:
        return (
            "बिहार विद्यालय परीक्षा समिति इंटरमीडिएट परीक्षा प्रपत्र की "
            "अंतिम तिथि में अवधि विस्तार किया गया है। आवश्यक कार्रवाई सुनिश्चित करें। "
            "This synthetic official letter contains enough native text for processing."
        )


class FakeContextProvider:
    version = "fake-context-v1"

    def analyze(self, *, extracted_text: str, hints: ContextHints):
        return StructuredDocumentContext(
            title="Synthetic Exam Extension",
            authority="BSEB",
            category="exam",
            summary="Synthetic summary",
            concepts=("exam_form",),
        )


class FakeRepository:
    def __init__(self):
        self.extraction = None
        self.context = None
        self.embedding_version = None

    def save_extraction_result(self, record, *, owner_id, result):
        self.extraction = result

    def save_context_result(self, record, *, owner_id, result):
        self.context = result

    def save_embedding_version(
        self, record, *, owner_id, embedding_version
    ):
        self.embedding_version = embedding_version


class FakeEmbeddingProvider:
    version = "fake-embedding-v1"


class FakeEmbeddings:
    def __init__(self):
        self.provider = FakeEmbeddingProvider()

    def embed_document_chunks(
        self,
        *,
        owner_id,
        letter_id,
        extracted_text,
        max_characters=2400,
        overlap_characters=240,
    ):
        return 2


def record():
    return DocumentRecord(
        record_id=LETTER_ID,
        original_filename="synthetic.pdf",
        original_sha256="a" * 64,
        original_storage_reference="private-reference",
        received_at=datetime(2026, 10, 2, tzinfo=timezone.utc),
    )


def job():
    return ProcessingJob(
        job_id=JOB_ID,
        letter_id=LETTER_ID,
        owner_id=OWNER_ID,
        created_at=datetime(2026, 10, 2, tzinfo=timezone.utc),
    )


class WorkerTests(unittest.TestCase):
    def test_successful_job_runs_full_derived_pipeline(self):
        queue = FakeQueue(job())
        repository = FakeRepository()
        worker = DocumentProcessingWorker(
            queue=queue,
            source_loader=FakeSourceLoader(record()),
            database=FakeDatabase(),
            original_access=FakeOriginalAccess(),
            repository=repository,
            extractor=VersionedTextExtractor(FakePdfBackend()),
            context_provider=FakeContextProvider(),
            embeddings=FakeEmbeddings(),
        )

        result = worker.run_once()

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.chunks, 2)
        self.assertEqual(queue.completed, [JOB_ID])
        self.assertEqual(queue.failed, [])
        self.assertIsNotNone(repository.extraction)
        self.assertIsNotNone(repository.context)
        self.assertEqual(
            repository.embedding_version,
            "fake-embedding-v1",
        )

    def test_worker_saves_reviewable_relationship_suggestion(self):
        class RelationshipDatabase:
            def select(self, table, *, filters=None, columns="*"):
                if table == "letters":
                    return [{
                        "id": "55555555-5555-4555-8555-555555555555",
                        "reference_number": "BSEB/123/2026",
                        "authority": "BSEB",
                        "category": "exam",
                        "title": "Prior Notice",
                        "summary": "Prior synthetic notice",
                    }]
                return []

        class RelationshipRepo:
            def __init__(self):
                self.saved = []

            def save_suggestion(self, suggestion, *, owner_id):
                self.saved.append((suggestion, owner_id))

        class ExtensionContextProvider:
            version = "fake-context-v1"

            def analyze(self, *, extracted_text, hints):
                return StructuredDocumentContext(
                    title="Synthetic Extension",
                    authority="BSEB",
                    category="exam",
                    reference_number="BSEB/456/2026",
                    summary="Extension",
                )

        class ExtensionPdfBackend:
            def extract_text(self, path):
                return (
                    "BSEB/123/2026 के संदर्भ में परीक्षा प्रपत्र की "
                    "अंतिम तिथि हेतु तिथि विस्तार किया जाता है। "
                    "Synthetic text with enough content for native extraction."
                )

        relations = RelationshipRepo()
        queue = FakeQueue(job())
        worker = DocumentProcessingWorker(
            queue=queue,
            source_loader=FakeSourceLoader(record()),
            database=RelationshipDatabase(),
            original_access=FakeOriginalAccess(),
            repository=FakeRepository(),
            extractor=VersionedTextExtractor(ExtensionPdfBackend()),
            context_provider=ExtensionContextProvider(),
            embeddings=FakeEmbeddings(),
            relationship_repository=relations,
        )

        result = worker.run_once()

        self.assertEqual(result.status, "completed")
        self.assertEqual(len(relations.saved), 1)
        self.assertEqual(
            relations.saved[0][0].relationship_type.value,
            "extends",
        )

    def test_missing_source_marks_job_failed(self):
        queue = FakeQueue(job())
        worker = DocumentProcessingWorker(
            queue=queue,
            source_loader=FakeSourceLoader(None),
            database=FakeDatabase(),
            original_access=FakeOriginalAccess(),
            repository=FakeRepository(),
            extractor=VersionedTextExtractor(FakePdfBackend()),
            context_provider=FakeContextProvider(),
            embeddings=FakeEmbeddings(),
        )

        result = worker.run_once()

        self.assertEqual(result.status, "failed")
        self.assertEqual(queue.completed, [])
        self.assertEqual(queue.failed[0][0], JOB_ID)
        self.assertIn("not found", queue.failed[0][1])

    def test_real_looking_record_is_blocked_by_default(self):
        real_record = DocumentRecord(
            record_id=LETTER_ID,
            original_filename="official-letter.pdf",
            original_sha256="b" * 64,
            original_storage_reference="private-reference",
            received_at=datetime(2026, 10, 2, tzinfo=timezone.utc),
        )
        queue = FakeQueue(job())
        worker = DocumentProcessingWorker(
            queue=queue,
            source_loader=FakeSourceLoader(real_record),
            database=FakeDatabase(),
            original_access=FakeOriginalAccess(),
            repository=FakeRepository(),
            extractor=VersionedTextExtractor(FakePdfBackend()),
            context_provider=FakeContextProvider(),
            embeddings=FakeEmbeddings(),
        )

        result = worker.run_once()

        self.assertEqual(result.status, "failed")
        self.assertIn("real document processing is disabled", result.error)
        self.assertEqual(queue.completed, [])

    def test_manual_retry_uses_fallback_when_primary_context_fails(self):
        class FailingContextProvider:
            version = "failing-context-v1"

            def analyze(self, *, extracted_text: str, hints: ContextHints):
                raise RuntimeError("primary context unavailable")

        retry_job = ProcessingJob(
            job_id=JOB_ID,
            letter_id=LETTER_ID,
            owner_id=OWNER_ID,
            created_at=datetime(2026, 10, 2, tzinfo=timezone.utc),
            reason="manual_retry:20261006T073609Z",
        )
        queue = FakeQueue(retry_job)
        worker = DocumentProcessingWorker(
            queue=queue,
            source_loader=FakeSourceLoader(record()),
            database=FakeDatabase(),
            original_access=FakeOriginalAccess(),
            repository=FakeRepository(),
            extractor=VersionedTextExtractor(FakePdfBackend()),
            context_provider=FailingContextProvider(),
            fallback_context_provider=FakeContextProvider(),
            embeddings=None,
        )

        result = worker.run_once()

        self.assertEqual(result.status, "completed")
        self.assertEqual(queue.completed, [JOB_ID])
        self.assertEqual(queue.failed, [])

    def test_manual_reprocess_reuses_existing_extracted_text(self):
        class ReuseDatabase:
            def select(self, table, *, filters=None, columns="*"):
                if table == "letter_processing":
                    return [{
                        "extracted_text": (
                            "बिहार विद्यालय परीक्षा समिति के निर्देश के अनुसार "
                            "यह पहले से निकाला गया पर्याप्त पाठ है। "
                            "Existing extracted text should be reused during manual reprocess."
                        ),
                        "ocr_version": "ocr-pdf-hi-en-v1",
                    }]
                return []

        class ExplodingPdfBackend:
            def extract_text(self, path):
                raise AssertionError("OCR/native extraction must not run for manual reprocess")

        retry_job = ProcessingJob(
            job_id=JOB_ID,
            letter_id=LETTER_ID,
            owner_id=OWNER_ID,
            created_at=datetime(2026, 10, 2, tzinfo=timezone.utc),
            reason="manual_reprocess:20261006T151605Z",
        )
        queue = FakeQueue(retry_job)
        repository = FakeRepository()
        worker = DocumentProcessingWorker(
            queue=queue,
            source_loader=FakeSourceLoader(record()),
            database=ReuseDatabase(),
            original_access=FakeOriginalAccess(),
            repository=repository,
            extractor=VersionedTextExtractor(ExplodingPdfBackend()),
            context_provider=FakeContextProvider(),
            embeddings=None,
        )

        result = worker.run_once()

        self.assertEqual(result.status, "completed")
        self.assertEqual(queue.completed, [JOB_ID])
        self.assertIsNone(repository.extraction)
        self.assertIsNotNone(repository.context)

    def test_worker_completes_without_embeddings(self):
        queue = FakeQueue(job())
        repository = FakeRepository()
        worker = DocumentProcessingWorker(
            queue=queue,
            source_loader=FakeSourceLoader(record()),
            database=FakeDatabase(),
            original_access=FakeOriginalAccess(),
            repository=repository,
            extractor=VersionedTextExtractor(FakePdfBackend()),
            context_provider=FakeContextProvider(),
            embeddings=None,
        )

        result = worker.run_once()

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.chunks, 0)
        self.assertEqual(queue.completed, [JOB_ID])
        self.assertEqual(queue.failed, [])
        self.assertIsNone(repository.embedding_version)

    def test_no_pending_job_is_idle(self):
        worker = DocumentProcessingWorker(
            queue=FakeQueue(None),
            source_loader=FakeSourceLoader(record()),
            database=FakeDatabase(),
            original_access=FakeOriginalAccess(),
            repository=FakeRepository(),
            extractor=VersionedTextExtractor(FakePdfBackend()),
            context_provider=FakeContextProvider(),
            embeddings=FakeEmbeddings(),
        )

        result = worker.run_once()

        self.assertEqual(result.status, "idle")


if __name__ == "__main__":
    unittest.main()
