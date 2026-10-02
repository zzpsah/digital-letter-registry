import unittest

from letter_registry.original_access import OriginalFile, SupabaseOriginalAccessService


class FakeDatabase:
    def select(self, table, *, filters=None, columns="*"):
        return [{
            "original_filename": "synthetic.pdf",
            "storage_provider": "gdrive",
            "storage_object_id": "private-object-reference",
        }]


class FakeStorage:
    def __init__(self):
        self.calls = []

    def download(self, *, provider, object_reference, filename):
        self.calls.append((provider, object_reference, filename))
        return OriginalFile(
            filename=filename,
            content_type="application/pdf",
            content=b"%PDF-synthetic",
        )


class OriginalAccessTests(unittest.TestCase):
    def test_private_reference_stays_between_server_components(self):
        storage = FakeStorage()
        service = SupabaseOriginalAccessService(storage)

        original = service.fetch(
            record_id="22222222-2222-4222-8222-222222222222",
            database=FakeDatabase(),
        )

        self.assertIsNotNone(original)
        self.assertEqual(original.filename, "synthetic.pdf")
        self.assertEqual(original.content_type, "application/pdf")
        self.assertEqual(
            storage.calls[0],
            ("gdrive", "private-object-reference", "synthetic.pdf"),
        )
        self.assertFalse(hasattr(original, "storage_object_id"))

    def test_missing_letter_returns_none(self):
        class EmptyDatabase:
            def select(self, table, *, filters=None, columns="*"):
                return []

        service = SupabaseOriginalAccessService(FakeStorage())
        self.assertIsNone(
            service.fetch(
                record_id="22222222-2222-4222-8222-222222222222",
                database=EmptyDatabase(),
            )
        )


if __name__ == "__main__":
    unittest.main()
