import unittest

from letter_registry.access import (
    ArchiveRole,
    SupabaseArchiveAccess,
)
from letter_registry.supabase_runtime import ArchiveScopedSupabaseTransport


ARCHIVE_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
OTHER_ARCHIVE_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
USER_ID = "11111111-1111-4111-8111-111111111111"


class FakeAccessTransport:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def select(self, table, *, filters=None, columns="*"):
        self.calls.append((table, filters, columns))
        return list(self.rows)


class ArchiveAccessTests(unittest.TestCase):
    def test_membership_returns_role(self):
        transport = FakeAccessTransport([
            {
                "archive_id": ARCHIVE_ID,
                "user_id": USER_ID,
                "role": "editor",
                "status": "active",
            }
        ])
        membership = SupabaseArchiveAccess(
            transport=transport,
            archive_id=ARCHIVE_ID,
        ).membership(USER_ID)
        self.assertIsNotNone(membership)
        self.assertEqual(membership.role, ArchiveRole.EDITOR)
        self.assertTrue(membership.can_write)
        self.assertFalse(membership.is_admin)

    def test_require_rejects_wrong_role(self):
        transport = FakeAccessTransport([
            {
                "archive_id": ARCHIVE_ID,
                "user_id": USER_ID,
                "role": "viewer",
                "status": "active",
            }
        ])
        access = SupabaseArchiveAccess(
            transport=transport,
            archive_id=ARCHIVE_ID,
        )
        with self.assertRaises(PermissionError):
            access.require(USER_ID, roles={ArchiveRole.ADMIN})


class FakeRawTransport:
    def __init__(self):
        self.calls = []

    def insert(self, table, row, *, on_conflict=None):
        self.calls.append(("insert", table, dict(row), on_conflict))
        return dict(row)

    def upsert(self, table, row, *, on_conflict):
        self.calls.append(("upsert", table, dict(row), on_conflict))
        return dict(row)

    def select(self, table, *, filters=None, columns="*"):
        self.calls.append(("select", table, dict(filters or {}), columns))
        return []

    def rpc(self, function, params):
        self.calls.append(("rpc", function, dict(params)))
        return []


class ArchiveScopedTransportTests(unittest.TestCase):
    def test_insert_injects_archive_and_rewrites_duplicate_scope(self):
        raw = FakeRawTransport()
        transport = ArchiveScopedSupabaseTransport(raw, ARCHIVE_ID)
        transport.insert(
            "letters",
            {"owner_id": USER_ID, "original_sha256": "a" * 64},
            on_conflict="owner_id,original_sha256",
        )
        _, _, row, conflict = raw.calls[0]
        self.assertEqual(row["archive_id"], ARCHIVE_ID)
        self.assertEqual(conflict, "archive_id,original_sha256")

    def test_select_injects_archive_filter(self):
        raw = FakeRawTransport()
        transport = ArchiveScopedSupabaseTransport(raw, ARCHIVE_ID)
        transport.select("letters", filters={"status": "current"})
        _, _, filters, _ = raw.calls[0]
        self.assertEqual(filters["archive_id"], ARCHIVE_ID)
        self.assertEqual(filters["status"], "current")

    def test_cross_archive_read_is_rejected(self):
        raw = FakeRawTransport()
        transport = ArchiveScopedSupabaseTransport(raw, ARCHIVE_ID)
        with self.assertRaises(ValueError):
            transport.select(
                "letters",
                filters={"archive_id": OTHER_ARCHIVE_ID},
            )

    def test_rpc_preserves_parameters_and_relies_on_rls(self):
        raw = FakeRawTransport()
        transport = ArchiveScopedSupabaseTransport(raw, ARCHIVE_ID)
        transport.rpc("search_letter_cards", {"search_query": "exam"})
        _, _, params = raw.calls[0]
        self.assertEqual(params, {"search_query": "exam"})


if __name__ == "__main__":
    unittest.main()
