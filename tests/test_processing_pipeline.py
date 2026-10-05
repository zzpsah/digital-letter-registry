from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from letter_registry.context_hints import ContextHints
from letter_registry.extraction import VersionedTextExtractor
from letter_registry.models import DocumentRecord
from letter_registry.processing_pipeline import (
    _issue_date_from_text,
    _merge_operational_context,
    _semantic_title,
    process_archived_document,
)
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


    def test_semantic_title_ignores_wrong_category_when_source_is_ict_order(self) -> None:
        title = _semantic_title(
            "UDISE Notice",
            extracted_text=(
                "ICT Lab और Smart Class के संचालन के लिए कम्प्यूटर विज्ञान के शिक्षक को Nodal बनाया जाता है। "
                "जहाँ कम्प्यूटर शिक्षक नहीं हैं वहाँ deputation होगा और Mark On Duty attendance दर्ज की जाएगी।"
            ),
            summary="",
            category="student-data",
            filename="Nodel for ICT Lab & Smart Class Memo No. 2337 Dated 28-08-2026.pdf",
        )
        self.assertEqual(title, "ICT Lab / Smart Class Nodal & Deputation Order")

    def test_issue_date_prefers_final_official_memo_date(self) -> None:
        text = (
            "पुराना संदर्भ ज्ञापांक 11/1981 पटना, दिनांक 13-06-1981\n"
            "आदेश का मुख्य पाठ\n"
            "ज्ञापांक : 09/विविध (शुल्क)-41/2021-720 पटना, दिनांक 21-12-2021"
        )
        self.assertEqual(_issue_date_from_text(text), "2021-12-21")

    def test_operational_enrichment_extracts_title_deadline_amount_and_pages(self) -> None:
        text = """[[PAGE 1]]
शिक्षा विभाग बिहार सरकार
[[PAGE 2]]
कक्षा 11 एवं 12 के छात्र registration के लिए निर्देश।
[[PAGE 3]]
Registration fee ₹515 प्रति छात्र।
[[PAGE 4]]
आवेदन की अंतिम तिथि 20-10-2026 है।
[[PAGE 5]]
विद्यालय आवश्यक अभिलेख सत्यापित करें।
[[PAGE 6]]
संशोधित निर्देश का अनुपालन करें।
"""
        context = StructuredDocumentContext(
            title="Official Education Document",
            authority="Education Department, Bihar",
            category="registration",
            summary="Registration instructions for Classes 11 and 12.",
            action_required="Schools must verify records and complete registration.",
            key_points=(
                "Registration applies to Classes 11 and 12.",
                "Registration fee is ₹515 per student.",
            ),
        )

        enriched = _merge_operational_context(
            context,
            extracted_text=text,
            filename="Letter-276.pdf",
        )

        self.assertEqual(enriched.title, "पंजीयन कार्यक्रम एवं अंतिम तिथि")
        self.assertEqual(enriched.deadline, "2026-10-20")
        self.assertIn("Classes 11, 12", enriched.applies_to)
        self.assertTrue(
            any(item.value == "₹515" and item.page == 3 for item in enriched.important_amounts)
        )
        self.assertTrue(
            any(item.page == 4 and item.label == "Deadline / last date" for item in enriched.page_references)
        )
        self.assertEqual(enriched.page_count, 6)


if __name__ == "__main__":
    unittest.main()
