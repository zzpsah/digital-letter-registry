from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from letter_registry.intake import IntakePolicy, IntakeService
from letter_registry.jobs import InMemoryProcessingQueue
from letter_registry.persistence import InMemoryLetterRepository
from letter_registry.storage import InMemoryOriginalStorage


OWNER_ID = "11111111-1111-4111-8111-111111111111"


class IntakeTests(unittest.TestCase):
    def test_synthetic_pdf_is_archived_and_queued(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic-letter.pdf"
            path.write_bytes(b"%PDF-synthetic")

            storage = InMemoryOriginalStorage()
            repository = InMemoryLetterRepository()
            queue = InMemoryProcessingQueue()
            service = IntakeService(
                storage=storage,
                repository=repository,
                queue=queue,
            )

            result = service.ingest(path, owner_id=OWNER_ID)

        self.assertEqual(len(storage.objects), 1)
        self.assertEqual(len(repository.letters), 1)
        self.assertEqual(len(repository.processing), 1)
        self.assertEqual(len(queue.jobs), 1)
        self.assertEqual(queue.jobs[0].letter_id, result.record.record_id)

    def test_duplicate_is_rejected_before_second_storage_write(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic-letter.pdf"
            path.write_bytes(b"%PDF-same-content")

            storage = InMemoryOriginalStorage()
            repository = InMemoryLetterRepository()
            queue = InMemoryProcessingQueue()
            service = IntakeService(
                storage=storage,
                repository=repository,
                queue=queue,
            )

            service.ingest(path, owner_id=OWNER_ID)
            with self.assertRaisesRegex(ValueError, "already exists"):
                service.ingest(path, owner_id=OWNER_ID)

            self.assertEqual(len(storage.objects), 1)
            self.assertEqual(len(queue.jobs), 1)

    def test_real_looking_filename_is_blocked_by_default(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "official-letter.pdf"
            path.write_bytes(b"%PDF-real-looking")

            with self.assertRaisesRegex(ValueError, "real document intake is disabled"):
                IntakePolicy().validate(path)

    def test_explicit_non_synthetic_policy_allows_normal_filename(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "official-letter.pdf"
            path.write_bytes(b"%PDF-content")

            IntakePolicy(synthetic_only=False).validate(path)

    def test_unsupported_extension_is_rejected(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.exe"
            path.write_bytes(b"x")
            with self.assertRaisesRegex(ValueError, "unsupported"):
                IntakePolicy().validate(path)

    def test_size_limit_is_enforced(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.pdf"
            path.write_bytes(b"x" * 11)
            with self.assertRaisesRegex(ValueError, "size limit"):
                IntakePolicy(max_bytes=10).validate(path)


if __name__ == "__main__":
    unittest.main()
