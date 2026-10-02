from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from letter_registry.bulk_import import (
    execute_historical_import,
    preview_historical_import,
)


OWNER_ID = "11111111-1111-4111-8111-111111111111"


class FakeRepository:
    def __init__(self, duplicates=None):
        self.duplicates = set(duplicates or [])

    def source_exists_by_hash(self, *, owner_id, sha256):
        return sha256 in self.duplicates


class FakeIntake:
    def __init__(self):
        self.calls = []

    def ingest(self, path, *, owner_id):
        self.calls.append((Path(path).name, owner_id))


class BulkImportTests(unittest.TestCase):
    def test_preview_is_read_only_and_classifies_supported_files(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            pdf = root / "synthetic-a.pdf"
            pdf.write_bytes(b"%PDF-a")
            (root / "notes.txt").write_text("skip", encoding="utf-8")
            (root / "empty.jpg").write_bytes(b"")

            preview = preview_historical_import(
                root,
                owner_id=OWNER_ID,
                repository=FakeRepository(),
            )

        statuses = {item.filename: item.status for item in preview.items}
        self.assertEqual(statuses["synthetic-a.pdf"], "new")
        self.assertEqual(statuses["notes.txt"], "skipped")
        self.assertEqual(statuses["empty.jpg"], "skipped")
        self.assertEqual(preview.new_count, 1)
        self.assertEqual(preview.skipped_count, 2)
        self.assertEqual(len(preview.digest), 64)

    def test_duplicate_is_previewed_without_intake(self):
        from letter_registry.fingerprints import sha256_file

        with TemporaryDirectory() as directory:
            root = Path(directory)
            pdf = root / "synthetic-a.pdf"
            pdf.write_bytes(b"%PDF-a")
            digest = sha256_file(pdf)
            intake = FakeIntake()

            preview = preview_historical_import(
                root,
                owner_id=OWNER_ID,
                repository=FakeRepository({digest}),
            )

            result = execute_historical_import(
                preview,
                approved_digest=preview.digest,
                confirmed=True,
                owner_id=OWNER_ID,
                intake=intake,
            )

        self.assertEqual(preview.duplicate_count, 1)
        self.assertEqual(result.imported, 0)
        self.assertEqual(result.skipped, 1)
        self.assertEqual(intake.calls, [])

    def test_execution_requires_exact_digest_and_confirmation(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "synthetic-a.pdf").write_bytes(b"%PDF-a")
            preview = preview_historical_import(
                root,
                owner_id=OWNER_ID,
                repository=FakeRepository(),
            )
            intake = FakeIntake()

            with self.assertRaises(PermissionError):
                execute_historical_import(
                    preview,
                    approved_digest=preview.digest,
                    confirmed=False,
                    owner_id=OWNER_ID,
                    intake=intake,
                )
            with self.assertRaises(ValueError):
                execute_historical_import(
                    preview,
                    approved_digest="0" * 64,
                    confirmed=True,
                    owner_id=OWNER_ID,
                    intake=intake,
                )

        self.assertEqual(intake.calls, [])

    def test_changed_file_is_not_imported_after_preview(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            pdf = root / "synthetic-a.pdf"
            pdf.write_bytes(b"%PDF-a")
            preview = preview_historical_import(
                root,
                owner_id=OWNER_ID,
                repository=FakeRepository(),
            )
            pdf.write_bytes(b"%PDF-changed")
            intake = FakeIntake()

            result = execute_historical_import(
                preview,
                approved_digest=preview.digest,
                confirmed=True,
                owner_id=OWNER_ID,
                intake=intake,
            )

        self.assertEqual(result.imported, 0)
        self.assertEqual(result.failed, 1)
        self.assertIn("changed after preview", result.failures[0])
        self.assertEqual(intake.calls, [])

    def test_approved_unchanged_new_file_delegates_to_intake(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "synthetic-a.pdf").write_bytes(b"%PDF-a")
            preview = preview_historical_import(
                root,
                owner_id=OWNER_ID,
                repository=FakeRepository(),
            )
            intake = FakeIntake()

            result = execute_historical_import(
                preview,
                approved_digest=preview.digest,
                confirmed=True,
                owner_id=OWNER_ID,
                intake=intake,
            )

        self.assertEqual(result.imported, 1)
        self.assertEqual(result.failed, 0)
        self.assertEqual(intake.calls[0][0], "synthetic-a.pdf")


if __name__ == "__main__":
    unittest.main()
