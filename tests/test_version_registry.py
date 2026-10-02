import unittest

from letter_registry.version_registry import (
    ProcessingTargetVersions,
    SupabaseProcessingVersionRegistry,
    reprocessing_reason,
    schedule_reprocessing_preview,
)


OWNER_ID = "11111111-1111-4111-8111-111111111111"


class FakeTransport:
    def __init__(self):
        self.upserts = []
        self.rpc_calls = []
        self.profile_rows = [{
            "extraction_version": "native-pdf-v2",
            "context_version": "gemini:context-v2",
            "dictionary_version": "gov-hi-v2",
            "filename_rule_version": "official-v2",
            "category_schema_version": "categories-v2",
            "embedding_version": "gemini:embedding-v2",
            "status_rule_version": "relationships-v2",
        }]

    def upsert(self, table, row, *, on_conflict):
        self.upserts.append((table, row, on_conflict))
        return row

    def select(self, table, *, filters=None, columns="*"):
        return self.profile_rows

    def rpc(self, function, params):
        self.rpc_calls.append((function, params))
        return [{
            "letter_id": "22222222-2222-4222-8222-222222222222",
            "title": "Synthetic Letter",
            "smart_filename": "synthetic.pdf",
            "differences": ["context", "embedding"],
        }]


class VersionRegistryTests(unittest.TestCase):
    def test_profile_round_trip_mapping(self):
        transport = FakeTransport()
        registry = SupabaseProcessingVersionRegistry(transport)
        versions = ProcessingTargetVersions(
            extraction="native-pdf-v2",
            context="gemini:context-v2",
            dictionary="gov-hi-v2",
            filename_rule="official-v2",
            category_schema="categories-v2",
            embedding="gemini:embedding-v2",
            status_rule="relationships-v2",
        )

        registry.set_profile(owner_id=OWNER_ID, versions=versions)
        loaded = registry.get_profile(owner_id=OWNER_ID)

        self.assertEqual(loaded, versions)
        self.assertEqual(transport.upserts[0][0], "processing_profiles")
        self.assertEqual(transport.upserts[0][2], "archive_id")

    def test_enqueue_reprocessing_returns_inserted_count(self):
        transport = FakeTransport()
        transport.rpc = lambda function, params: [{"enqueued": 3}]
        registry = SupabaseProcessingVersionRegistry(transport)

        self.assertEqual(registry.enqueue_reprocessing(limit=50), 3)

    def test_preview_returns_differing_stages(self):
        registry = SupabaseProcessingVersionRegistry(FakeTransport())

        rows = registry.preview(limit=25)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].differences, ("context", "embedding"))

    def test_blank_target_version_is_rejected(self):
        with self.assertRaises(ValueError):
            ProcessingTargetVersions(
                extraction="",
                context="v1",
                dictionary="v1",
                filename_rule="v1",
                category_schema="v1",
                embedding="v1",
                status_rule="v1",
            )

    def test_preview_limit_is_bounded(self):
        registry = SupabaseProcessingVersionRegistry(FakeTransport())
        with self.assertRaises(ValueError):
            registry.preview(limit=501)

    def test_scheduler_requires_explicit_approval(self):
        versions = ProcessingTargetVersions(
            extraction="native-pdf-v2",
            context="gemini:context-v2",
            dictionary="gov-hi-v2",
            filename_rule="official-v2",
            category_schema="categories-v2",
            embedding="gemini:embedding-v2",
            status_rule="relationships-v2",
        )
        preview = SupabaseProcessingVersionRegistry(
            FakeTransport()
        ).preview()

        class Queue:
            def __init__(self):
                self.calls = []

            def enqueue(self, *, letter_id, owner_id, reason="initial_processing"):
                self.calls.append((letter_id, owner_id, reason))

        queue = Queue()
        with self.assertRaises(PermissionError):
            schedule_reprocessing_preview(
                owner_id=OWNER_ID,
                versions=versions,
                preview=preview,
                queue=queue,
            )
        self.assertEqual(queue.calls, [])

    def test_approved_scheduler_uses_deterministic_profile_reason(self):
        versions = ProcessingTargetVersions(
            extraction="native-pdf-v2",
            context="gemini:context-v2",
            dictionary="gov-hi-v2",
            filename_rule="official-v2",
            category_schema="categories-v2",
            embedding="gemini:embedding-v2",
            status_rule="relationships-v2",
        )
        preview = SupabaseProcessingVersionRegistry(
            FakeTransport()
        ).preview()

        class Queue:
            def __init__(self):
                self.calls = []

            def enqueue(self, *, letter_id, owner_id, reason="initial_processing"):
                self.calls.append((letter_id, owner_id, reason))

        queue = Queue()
        result = schedule_reprocessing_preview(
            owner_id=OWNER_ID,
            versions=versions,
            preview=preview,
            queue=queue,
            approved=True,
        )

        self.assertEqual(result.reason, reprocessing_reason(versions))
        self.assertEqual(len(queue.calls), 1)
        self.assertEqual(queue.calls[0][2], result.reason)


if __name__ == "__main__":
    unittest.main()
