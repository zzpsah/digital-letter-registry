from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from datetime import datetime, timezone

from letter_registry.google_drive_catalog import HistoricalDriveItem
from letter_registry.historical_import import (
    HistoricalDriveImportService,
    preview_historical_import,
)
from letter_registry.jobs import InMemoryProcessingQueue
from letter_registry.original_access import OriginalFile
from letter_registry.persistence import InMemoryLetterRepository


OWNER_ID = "11111111-1111-4111-8111-111111111111"


class FakeRepository:
    def __init__(self, existing=None):
        self.existing = set(existing or [])

    def source_exists_by_hash(self, *, owner_id, sha256):
        return sha256 in self.existing


class HistoricalImportPreviewTests(unittest.TestCase):
    def test_preview_counts_new_and_duplicate_files_without_mutation(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "letter-a.pdf"
            second = root / "letter-b.pdf"
            duplicate = root / "letter-copy.pdf"
            ignored = root / "notes.txt"

            first.write_bytes(b"first")
            second.write_bytes(b"second")
            duplicate.write_bytes(b"first")
            ignored.write_text("ignored")

            preview = preview_historical_import(
                [first, second, duplicate, ignored],
                owner_id=OWNER_ID,
                repository=FakeRepository(),
            )

        self.assertEqual(preview.total_files, 3)
        self.assertEqual(preview.new_files, 2)
        self.assertEqual(preview.duplicate_files, 1)
        self.assertEqual(len(preview.candidates), 3)

    def test_existing_archive_hash_is_marked_duplicate(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "historical.pdf"
            path.write_bytes(b"existing")
            import hashlib
            digest = hashlib.sha256(b"existing").hexdigest()

            preview = preview_historical_import(
                [path],
                owner_id=OWNER_ID,
                repository=FakeRepository(existing={digest}),
            )

        self.assertTrue(preview.candidates[0].duplicate)
        self.assertEqual(preview.new_files, 0)

    def test_missing_and_unsupported_paths_are_ignored(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            unsupported = root / "synthetic.exe"
            unsupported.write_bytes(b"x")

            preview = preview_historical_import(
                [root / "missing.pdf", unsupported],
                owner_id=OWNER_ID,
                repository=FakeRepository(),
            )

        self.assertEqual(preview.total_files, 0)


if __name__ == "__main__":
    unittest.main()



class FakeHistoricalReader:
    def download(self, *, provider, object_reference, filename):
        return OriginalFile(
            filename=filename,
            content_type="application/pdf",
            content=b"%PDF-synthetic-history",
        )


def drive_item(
    name="synthetic-history.pdf",
    object_reference="synthetic-drive-history-1",
):
    return HistoricalDriveItem(
        object_reference=object_reference,
        filename=name,
        mime_type="application/pdf",
        size_bytes=123,
        modified_at=datetime(
            2026, 1, 2, tzinfo=timezone.utc
        ),
    )


class HistoricalDriveImportTests(unittest.TestCase):
    def service(self):
        return HistoricalDriveImportService(
            repository=InMemoryLetterRepository(),
            queue=InMemoryProcessingQueue(),
            reader=FakeHistoricalReader(),
        )

    def test_preview_does_not_mutate_and_marks_synthetic_eligible(self):
        service = self.service()
        rows = service.preview(
            [drive_item()],
            owner_id=OWNER_ID,
        )

        self.assertEqual(rows[0].status, "eligible")
        self.assertEqual(service.repository.letters, {})
        self.assertEqual(service.queue.jobs, [])

    def test_real_historical_file_is_blocked_by_default(self):
        rows = self.service().preview(
            [drive_item(name="official-2024.pdf")],
            owner_id=OWNER_ID,
        )
        self.assertEqual(
            rows[0].status,
            "real_document_blocked",
        )

    def test_adoption_requires_confirmation(self):
        with self.assertRaisesRegex(
            ValueError,
            "explicit confirmation",
        ):
            self.service().adopt(
                drive_item(),
                owner_id=OWNER_ID,
                confirmed=False,
            )

    def test_confirmed_adoption_reuses_drive_object_and_queues(self):
        service = self.service()
        result = service.adopt(
            drive_item(),
            owner_id=OWNER_ID,
            confirmed=True,
        )

        self.assertEqual(
            result.record.original_storage_reference,
            "synthetic-drive-history-1",
        )
        self.assertEqual(len(service.repository.letters), 1)
        self.assertEqual(len(service.queue.jobs), 1)
        self.assertEqual(
            service.queue.jobs[0].reason,
            "historical_import",
        )

    def test_existing_drive_object_is_skipped(self):
        service = self.service()
        source = drive_item()
        service.adopt(
            source,
            owner_id=OWNER_ID,
            confirmed=True,
        )
        rows = service.preview(
            [source],
            owner_id=OWNER_ID,
        )
        self.assertEqual(
            rows[0].status,
            "already_archived",
        )

    def test_same_content_under_new_object_is_rejected(self):
        service = self.service()
        service.adopt(
            drive_item(),
            owner_id=OWNER_ID,
            confirmed=True,
        )
        with self.assertRaisesRegex(
            ValueError,
            "content is already archived",
        ):
            service.adopt(
                drive_item(
                    object_reference="synthetic-drive-history-2"
                ),
                owner_id=OWNER_ID,
                confirmed=True,
            )
