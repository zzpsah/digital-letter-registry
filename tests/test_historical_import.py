from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from letter_registry.historical_import import preview_historical_import


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
