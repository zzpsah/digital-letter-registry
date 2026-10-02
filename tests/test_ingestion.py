from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from letter_registry.ingestion import prepare_source_record, persist_prepared_source
from letter_registry.persistence import InMemoryLetterRepository


OWNER_ID = "11111111-1111-4111-8111-111111111111"


class IngestionPreparationTests(unittest.TestCase):
    def test_prepare_source_record_hashes_file_and_preserves_original_name(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "DOC10086.pdf"
            path.write_bytes(b"synthetic-letter-content")

            record = prepare_source_record(
                path,
                storage_reference="synthetic-private-reference",
                received_at=datetime(2026, 10, 2, tzinfo=timezone.utc),
                record_id="22222222-2222-4222-8222-222222222222",
            )

            self.assertEqual(record.original_filename, "DOC10086.pdf")
            self.assertEqual(len(record.original_sha256), 64)
            self.assertEqual(
                record.original_storage_reference,
                "synthetic-private-reference",
            )

    def test_prepare_source_record_rejects_naive_timestamp(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.pdf"
            path.write_bytes(b"synthetic")

            with self.assertRaisesRegex(ValueError, "timezone-aware"):
                prepare_source_record(
                    path,
                    storage_reference="synthetic-reference",
                    received_at=datetime(2026, 10, 2),
                )

    def test_vertical_slice_persists_source_and_processing_state(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.pdf"
            path.write_bytes(b"synthetic")
            repository = InMemoryLetterRepository()

            record = prepare_source_record(
                path,
                storage_reference="synthetic-private-reference",
                received_at=datetime(2026, 10, 2, tzinfo=timezone.utc),
                record_id="22222222-2222-4222-8222-222222222222",
            )
            persist_prepared_source(repository, record, owner_id=OWNER_ID)

            self.assertEqual(len(repository.letters), 1)
            self.assertEqual(len(repository.processing), 1)

    def test_no_drive_or_supabase_client_is_required(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.pdf"
            path.write_bytes(b"synthetic")

            record = prepare_source_record(
                path,
                storage_reference="opaque-private-reference",
                record_id="22222222-2222-4222-8222-222222222222",
            )

            self.assertNotIn("http", record.original_storage_reference)


if __name__ == "__main__":
    unittest.main()
