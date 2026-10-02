from datetime import datetime, timezone
import unittest
from uuid import UUID

from letter_registry.models import DocumentRecord, ProcessingVersions
from letter_registry.persistence import (
    InMemoryLetterRepository,
    build_supabase_letter_row,
    build_supabase_processing_row,
)


OWNER_ID = "11111111-1111-4111-8111-111111111111"
LETTER_ID = "22222222-2222-4222-8222-222222222222"


def synthetic_record(*, sha: str = "a" * 64) -> DocumentRecord:
    return DocumentRecord(
        record_id=LETTER_ID,
        original_filename="synthetic-letter.pdf",
        original_sha256=sha,
        original_storage_reference="synthetic-private-object-reference",
        received_at=datetime(2026, 10, 2, tzinfo=timezone.utc),
        processing=ProcessingVersions(
            extraction="text-v1",
            context="unprocessed",
            dictionary="gov-hi-v1",
            filename_rule="official-v1",
            category_schema="unprocessed",
            embedding="unprocessed",
            status_rule="unprocessed",
        ),
    )


class SupabaseMappingTests(unittest.TestCase):
    def test_letter_row_matches_core_schema_without_secret_values(self) -> None:
        row = build_supabase_letter_row(synthetic_record(), owner_id=OWNER_ID)

        self.assertEqual(row["id"], str(UUID(LETTER_ID)))
        self.assertEqual(row["owner_id"], str(UUID(OWNER_ID)))
        self.assertEqual(row["storage_provider"], "gdrive")
        self.assertEqual(
            row["storage_object_id"],
            "synthetic-private-object-reference",
        )
        self.assertNotIn("supabase_url", row)
        self.assertNotIn("api_key", row)

    def test_processing_versions_map_to_database_columns(self) -> None:
        row = build_supabase_processing_row(synthetic_record(), owner_id=OWNER_ID)

        self.assertEqual(row["ocr_version"], "text-v1")
        self.assertEqual(row["dictionary_version"], "gov-hi-v1")
        self.assertEqual(row["filename_rule_version"], "official-v1")

    def test_supabase_boundary_requires_uuid_record_id(self) -> None:
        record = DocumentRecord(
            record_id="ltr-not-a-uuid",
            original_filename="synthetic.pdf",
            original_sha256="b" * 64,
            original_storage_reference="synthetic-reference",
            received_at=datetime(2026, 10, 2, tzinfo=timezone.utc),
        )

        with self.assertRaises(ValueError):
            build_supabase_letter_row(record, owner_id=OWNER_ID)

    def test_in_memory_repository_rejects_duplicate_owner_hash(self) -> None:
        repository = InMemoryLetterRepository()
        first = synthetic_record()
        second = DocumentRecord(
            record_id="33333333-3333-4333-8333-333333333333",
            original_filename="same-content-different-name.pdf",
            original_sha256=first.original_sha256,
            original_storage_reference="synthetic-reference-2",
            received_at=datetime(2026, 10, 2, tzinfo=timezone.utc),
        )

        repository.save_source(first, owner_id=OWNER_ID)

        with self.assertRaisesRegex(ValueError, "duplicate source content"):
            repository.save_source(second, owner_id=OWNER_ID)

    def test_processing_requires_existing_source(self) -> None:
        repository = InMemoryLetterRepository()

        with self.assertRaisesRegex(ValueError, "source record"):
            repository.save_processing_state(synthetic_record(), owner_id=OWNER_ID)

    def test_synthetic_source_and_processing_vertical_slice(self) -> None:
        repository = InMemoryLetterRepository()
        record = synthetic_record()

        repository.save_source(record, owner_id=OWNER_ID)
        repository.save_processing_state(record, owner_id=OWNER_ID)

        self.assertIn(LETTER_ID, repository.letters)
        self.assertIn(LETTER_ID, repository.processing)


if __name__ == "__main__":
    unittest.main()
