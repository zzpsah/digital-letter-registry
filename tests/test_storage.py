from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from letter_registry.orchestration import ingest_original
from letter_registry.persistence import InMemoryLetterRepository
from letter_registry.storage import (
    GoogleDriveOriginalStorage,
    InMemoryOriginalStorage,
)


OWNER_ID = "11111111-1111-4111-8111-111111111111"
LETTER_ID = "22222222-2222-4222-8222-222222222222"


class FakeDriveTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, Path]] = []

    def upload_file(
        self,
        *,
        folder_reference: str,
        filename: str,
        path: Path,
    ) -> str:
        self.calls.append((folder_reference, filename, path))
        return "opaque-drive-object-reference"


class StorageTests(unittest.TestCase):
    def test_in_memory_storage_keeps_synthetic_original(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.pdf"
            path.write_bytes(b"synthetic-content")
            storage = InMemoryOriginalStorage()

            stored = storage.store_original(path)

            self.assertEqual(stored.provider, "memory")
            self.assertEqual(storage.objects[stored.object_reference], b"synthetic-content")

    def test_drive_adapter_uses_runtime_folder_reference(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.pdf"
            path.write_bytes(b"synthetic-content")
            transport = FakeDriveTransport()
            storage = GoogleDriveOriginalStorage(
                transport=transport,
                originals_folder_reference="runtime-private-folder-reference",
            )

            stored = storage.store_original(path)

            self.assertEqual(stored.provider, "gdrive")
            self.assertEqual(stored.object_reference, "opaque-drive-object-reference")
            self.assertEqual(
                transport.calls[0][0],
                "runtime-private-folder-reference",
            )

    def test_end_to_end_synthetic_storage_and_repository_slice(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "DOC10086.pdf"
            path.write_bytes(b"synthetic-letter")
            storage = InMemoryOriginalStorage()
            repository = InMemoryLetterRepository()

            record = ingest_original(
                path,
                storage=storage,
                repository=repository,
                owner_id=OWNER_ID,
                received_at=datetime(2026, 10, 2, tzinfo=timezone.utc),
                record_id=LETTER_ID,
            )

            self.assertEqual(record.record_id, LETTER_ID)
            self.assertEqual(len(storage.objects), 1)
            self.assertEqual(len(repository.letters), 1)
            self.assertEqual(len(repository.processing), 1)

    def test_drive_adapter_contains_no_private_folder_default(self) -> None:
        transport = FakeDriveTransport()

        with self.assertRaises(ValueError):
            GoogleDriveOriginalStorage(
                transport=transport,
                originals_folder_reference="",
            )


if __name__ == "__main__":
    unittest.main()
