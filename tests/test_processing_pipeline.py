from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from letter_registry.context_hints import ContextHints
from letter_registry.extraction import VersionedTextExtractor
from letter_registry.models import DocumentRecord
from letter_registry.processing_pipeline import process_archived_document
from letter_registry.structured_analysis import StructuredDocumentContext


OWNER_ID = "11111111-1111-4111-8111-111111111111"


class FakePdfBackend:
    def extract_text(self, path: Path) -> str:
        return (
            "बिहार विद्यालय परीक्षा समिति द्वारा इंटरमीडिएट परीक्षा प्रपत्र "
            "की अंतिम तिथि में अवधि विस्तार किया गया है। आवश्यक कार्रवाई करें।"
        )


class FakeContextProvider:
    version = "fake-context-v1"

    def analyze(self, *, extracted_text: str, hints: ContextHints):
        return StructuredDocumentContext(
            title="Inter Exam Form Extension",
            authority="BSEB",
            category="exam",
            summary="Synthetic summary",
            action_required="Complete form before deadline",
            concepts=("exam_form",),
        )


class FakeRepository:
    def __init__(self) -> None:
        self.extraction = None
        self.context = None

    def save_extraction_result(self, record, *, owner_id, result):
        self.extraction = result

    def save_context_result(self, record, *, owner_id, result):
        self.context = result


class ProcessingPipelineTests(unittest.TestCase):
    def test_pipeline_extracts_analyzes_and_persists(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.pdf"
            path.write_bytes(b"%PDF-synthetic")
            record = DocumentRecord(
                record_id="22222222-2222-4222-8222-222222222222",
                original_filename="synthetic.pdf",
                original_sha256="a" * 64,
                original_storage_reference="synthetic-reference",
                received_at=datetime(2026, 10, 2, tzinfo=timezone.utc),
            )
            repository = FakeRepository()

            outcome = process_archived_document(
                path,
                record=record,
                owner_id=OWNER_ID,
                extractor=VersionedTextExtractor(FakePdfBackend()),
                context_provider=FakeContextProvider(),
                repository=repository,
            )

        self.assertIsNotNone(repository.extraction)
        self.assertIsNotNone(repository.context)
        self.assertEqual(outcome.context.version, "fake-context-v1")
        self.assertIn("deadline", outcome.context.context.concepts)
        self.assertIn("deadline_extension", outcome.context.context.concepts)


if __name__ == "__main__":
    unittest.main()
