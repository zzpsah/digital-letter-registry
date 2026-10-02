from datetime import datetime, timezone
import unittest

from letter_registry.source_loader import SupabaseSourceLoader


class FakeTransport:
    def select(self, table, *, filters=None, columns="*"):
        if table == "letters":
            return [{
                "id": "22222222-2222-4222-8222-222222222222",
                "original_filename": "synthetic.pdf",
                "original_sha256": "a" * 64,
                "storage_object_id": "private-reference",
                "received_at": "2026-10-02T08:00:00+00:00",
                "uploaded_at": "2026-10-02T08:01:00+00:00",
                "issue_date": "2026-10-01",
                "status": "current",
            }]
        return [{
            "ocr_version": "native-pdf-v1",
            "context_version": "context-v1",
            "dictionary_version": "gov-hi-v1",
            "filename_rule_version": "official-v1",
            "category_schema_version": "schema-v1",
            "embedding_version": "embedding-v1",
            "status_rule_version": "status-v1",
        }]


class SourceLoaderTests(unittest.TestCase):
    def test_load_reconstructs_private_domain_record(self):
        record = SupabaseSourceLoader(FakeTransport()).load(
            "22222222-2222-4222-8222-222222222222"
        )

        self.assertIsNotNone(record)
        self.assertEqual(record.original_filename, "synthetic.pdf")
        self.assertEqual(record.original_storage_reference, "private-reference")
        self.assertEqual(record.processing.embedding, "embedding-v1")
        self.assertEqual(record.issue_date.isoformat(), "2026-10-01")

    def test_missing_record_returns_none(self):
        class Empty:
            def select(self, table, *, filters=None, columns="*"):
                return []

        self.assertIsNone(
            SupabaseSourceLoader(Empty()).load(
                "22222222-2222-4222-8222-222222222222"
            )
        )


if __name__ == "__main__":
    unittest.main()
