import unittest
from datetime import datetime, timezone
from uuid import uuid4

from letter_registry.jobs import InMemoryProcessingQueue
from letter_registry.self_healing import SelfHealingReprocessor


class FakeTransport:
    def __init__(self, processing):
        self.processing = processing
        self.jobs = []

    def select(self, table, *, filters=None, columns="*"):
        rows = self.processing if table == "letter_processing" else self.jobs
        result = []
        for row in rows:
            if filters and any(str(row.get(k)) != str(v) for k, v in filters.items()):
                continue
            result.append(dict(row))
        return result

    def record_job(self, job):
        self.jobs.append({
            "id": job.job_id,
            "letter_id": job.letter_id,
            "reason": job.reason,
            "status": "pending",
        })


class RecordingQueue(InMemoryProcessingQueue):
    def __init__(self, transport):
        super().__init__()
        self.transport = transport

    def enqueue(self, **kwargs):
        job = super().enqueue(**kwargs)
        if not any(row["id"] == job.job_id for row in self.transport.jobs):
            self.transport.record_job(job)
        return job


class SelfHealingTests(unittest.TestCase):
    def row(self, *, context_version="hermes:current-default:text-v1", needs=True):
        return {
            "letter_id": str(uuid4()),
            "owner_id": str(uuid4()),
            "context_version": context_version,
            "dictionary_version": "gov-education-hi-en-auto-v2",
            "structured_context": {
                "needs_reprocessing": needs,
                "quality_version": "document-quality-v1",
            },
        }

    def test_lower_tier_low_quality_gets_daily_recovery_job(self):
        transport = FakeTransport([self.row()])
        queue = RecordingQueue(transport)
        result = SelfHealingReprocessor(transport, queue).scan(
            target_context_version="supabase-gemini:gemini-3.6-flash:document-v1",
            target_dictionary_version="gov-education-hi-en-auto-v2",
            now=datetime(2026, 10, 5, tzinfo=timezone.utc),
        )
        self.assertEqual(result.enqueued, 1)
        self.assertTrue(queue.jobs[0].reason.endswith(":20261005"))

    def test_same_preferred_version_does_not_loop(self):
        target = "supabase-gemini:gemini-3.6-flash:document-v1"
        transport = FakeTransport([self.row(context_version=target)])
        queue = RecordingQueue(transport)
        result = SelfHealingReprocessor(transport, queue).scan(
            target_context_version=target,
            target_dictionary_version="gov-education-hi-en-auto-v2",
        )
        self.assertEqual(result.enqueued, 0)
        self.assertEqual(result.skipped_same_target, 1)

    def test_daily_batch_cap_prevents_quota_stampede(self):
        transport = FakeTransport([self.row() for _ in range(8)])
        queue = RecordingQueue(transport)
        result = SelfHealingReprocessor(transport, queue).scan(
            target_context_version="supabase-gemini:gemini-3.6-flash:document-v1",
            target_dictionary_version="gov-education-hi-en-auto-v2",
            max_enqueues=3,
            now=datetime(2026, 10, 5, tzinfo=timezone.utc),
        )
        self.assertEqual(result.enqueued, 3)
        self.assertEqual(len(queue.jobs), 3)

    def test_same_day_same_target_is_idempotent(self):
        transport = FakeTransport([self.row()])
        queue = RecordingQueue(transport)
        scanner = SelfHealingReprocessor(transport, queue)
        kwargs = dict(
            target_context_version="supabase-gemini:gemini-3.6-flash:document-v1",
            target_dictionary_version="gov-education-hi-en-auto-v2",
            now=datetime(2026, 10, 5, tzinfo=timezone.utc),
        )
        self.assertEqual(scanner.scan(**kwargs).enqueued, 1)
        self.assertEqual(scanner.scan(**kwargs).enqueued, 0)


if __name__ == "__main__":
    unittest.main()
