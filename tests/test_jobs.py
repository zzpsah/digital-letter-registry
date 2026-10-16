import unittest

from letter_registry.jobs import SupabaseProcessingQueue


class FakeTransport:
    def __init__(self, *, duplicate=False, missing_letter=False):
        self.calls = []
        self.duplicate = duplicate
        self.missing_letter = missing_letter

    def insert(self, table, row, *, on_conflict=None):
        self.calls.append(("insert", table, row, on_conflict))
        if self.duplicate:
            return {}
        return {
            "id": "33333333-3333-4333-8333-333333333333",
            "created_at": "2026-10-02T08:00:00+00:00",
        }

    def select(self, table, *, filters=None, columns="*"):
        self.calls.append(("select", table, filters, columns))
        if table == "letters":
            if self.missing_letter:
                return []
            return [{"archive_id": "44444444-4444-4444-8444-444444444444"}]
        return [{
            "id": "33333333-3333-4333-8333-333333333333",
            "created_at": "2026-10-02T08:00:00+00:00",
        }]


class SupabaseProcessingQueueTests(unittest.TestCase):
    def test_enqueue_persists_pending_job(self):
        transport = FakeTransport()
        queue = SupabaseProcessingQueue(transport)

        job = queue.enqueue(
            letter_id="22222222-2222-4222-8222-222222222222",
            owner_id="11111111-1111-4111-8111-111111111111",
        )

        self.assertEqual(job.job_id, "33333333-3333-4333-8333-333333333333")
        _, table, row, conflict = transport.calls[1]
        self.assertEqual(table, "processing_jobs")
        self.assertEqual(row["archive_id"], "44444444-4444-4444-8444-444444444444")
        self.assertEqual(row["status"], "pending")
        self.assertEqual(conflict, "letter_id,reason")

    def test_duplicate_enqueue_reuses_existing_job(self):
        transport = FakeTransport(duplicate=True)
        queue = SupabaseProcessingQueue(transport)

        job = queue.enqueue(
            letter_id="22222222-2222-4222-8222-222222222222",
            owner_id="11111111-1111-4111-8111-111111111111",
        )

        self.assertEqual(job.job_id, "33333333-3333-4333-8333-333333333333")
        self.assertEqual(transport.calls[2][0], "select")
        self.assertEqual(transport.calls[2][1], "processing_jobs")

    def test_enqueue_rejects_invisible_letter_without_insert(self):
        transport = FakeTransport(missing_letter=True)
        queue = SupabaseProcessingQueue(transport)
        with self.assertRaisesRegex(RuntimeError, "target letter is not visible"):
            queue.enqueue(
                letter_id="22222222-2222-4222-8222-222222222222",
                owner_id="11111111-1111-4111-8111-111111111111",
            )
        self.assertFalse(any(call[0] == "insert" for call in transport.calls))


if __name__ == "__main__":
    unittest.main()
