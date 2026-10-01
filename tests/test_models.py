from datetime import datetime, timezone

import unittest

from letter_registry.models import DocumentRecord, DocumentStatus


class DocumentRecordTests(unittest.TestCase):
    def test_record_requires_stable_source_identity(self) -> None:
        record = DocumentRecord(
            record_id="ltr_01",
            original_filename="DOC10086.pdf",
            original_sha256="a" * 64,
            original_storage_reference="drive:file-private-reference",
            received_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(record.status, DocumentStatus.UNKNOWN)
        self.assertEqual(record.processing.embedding, "unprocessed")

    def test_record_rejects_invalid_hash(self) -> None:
        with self.assertRaises(ValueError):
            DocumentRecord(
                record_id="ltr_01",
                original_filename="scan.pdf",
                original_sha256="not-a-hash",
                original_storage_reference="private:reference",
                received_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
            )
