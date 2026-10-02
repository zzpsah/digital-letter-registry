from datetime import datetime, timezone
import unittest

from letter_registry.extraction import ExtractionResult
from letter_registry.models import DocumentRecord
from letter_registry.persistence import build_supabase_extraction_patch


class ExtractionPersistenceTests(unittest.TestCase):
    def test_extraction_patch_contains_text_and_version(self) -> None:
        record = DocumentRecord(
            record_id="22222222-2222-4222-8222-222222222222",
            original_filename="synthetic.pdf",
            original_sha256="a" * 64,
            original_storage_reference="synthetic-reference",
            received_at=datetime(2026, 10, 2, tzinfo=timezone.utc),
        )
        result = ExtractionResult(
            text="शिक्षा विभाग synthetic text",
            method="ocr",
            version="ocr-hi-en-v1",
            needs_ocr=False,
        )

        row = build_supabase_extraction_patch(
            record,
            owner_id="11111111-1111-4111-8111-111111111111",
            result=result,
        )

        self.assertEqual(row["extracted_text"], "शिक्षा विभाग synthetic text")
        self.assertEqual(row["ocr_version"], "ocr-hi-en-v1")
        self.assertEqual(row["letter_id"], record.record_id)


if __name__ == "__main__":
    unittest.main()
