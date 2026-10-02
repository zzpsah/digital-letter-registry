import unittest

from letter_registry.rename_execution import (
    ApprovedRenameExecutor,
    RenamePlanItem,
    StoredRenameIdentity,
    rename_plan_digest,
)


RID = "11111111-1111-4111-8111-111111111111"


class FakeRepository:
    def __init__(self, filename="DOC10086.pdf"):
        self.filename = filename

    def get_rename_identity(self, record_id):
        return StoredRenameIdentity(
            record_id=record_id,
            original_filename=self.filename,
            storage_provider="gdrive",
            storage_object_reference="private-object-reference",
        )


class FakeTransport:
    def __init__(self):
        self.calls = []

    def rename(self, *, provider, object_reference, new_filename):
        self.calls.append((provider, object_reference, new_filename))


class RenameExecutionTests(unittest.TestCase):
    def setUp(self):
        self.item = RenamePlanItem(
            record_id=RID,
            original_filename="DOC10086.pdf",
            proposed_filename=(
                "scholarship-guidelines__education-department__"
                "2026-10-01__REF-001.pdf"
            ),
        )

    def test_digest_is_stable(self):
        self.assertEqual(
            rename_plan_digest([self.item]),
            rename_plan_digest([self.item]),
        )

    def test_confirmation_is_required(self):
        transport = FakeTransport()
        executor = ApprovedRenameExecutor(FakeRepository(), transport)

        with self.assertRaisesRegex(ValueError, "confirmation"):
            executor.execute(
                [self.item],
                approved_digest=rename_plan_digest([self.item]),
                confirmed=False,
            )

        self.assertEqual(transport.calls, [])

    def test_digest_must_match_exact_plan(self):
        transport = FakeTransport()
        executor = ApprovedRenameExecutor(FakeRepository(), transport)

        with self.assertRaisesRegex(ValueError, "digest"):
            executor.execute(
                [self.item],
                approved_digest="0" * 64,
                confirmed=True,
            )

        self.assertEqual(transport.calls, [])

    def test_stale_filename_stops_before_any_mutation(self):
        transport = FakeTransport()
        executor = ApprovedRenameExecutor(
            FakeRepository(filename="already-changed.pdf"),
            transport,
        )

        with self.assertRaisesRegex(ValueError, "stale"):
            executor.execute(
                [self.item],
                approved_digest=rename_plan_digest([self.item]),
                confirmed=True,
            )

        self.assertEqual(transport.calls, [])

    def test_approved_exact_plan_executes_once(self):
        transport = FakeTransport()
        executor = ApprovedRenameExecutor(FakeRepository(), transport)

        count = executor.execute(
            [self.item],
            approved_digest=rename_plan_digest([self.item]),
            confirmed=True,
        )

        self.assertEqual(count, 1)
        self.assertEqual(transport.calls[0][0], "gdrive")
        self.assertEqual(
            transport.calls[0][2],
            self.item.proposed_filename,
        )


if __name__ == "__main__":
    unittest.main()
