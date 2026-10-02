import unittest

from letter_registry.access import ArchiveRole
from letter_registry.account_admin import SupabaseArchiveAccountAdmin


ARCHIVE_ID = "11111111-1111-4111-8111-111111111111"
USER_ID = "22222222-2222-4222-8222-222222222222"
INVITE_ID = "33333333-3333-4333-8333-333333333333"
INVITE_CODE = "44444444-4444-4444-8444-444444444444"


class FakeTransport:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def rpc(self, function, params):
        self.calls.append((function, params))
        return self.responses.get(function, [])


class AccountAdminTests(unittest.TestCase):
    def test_list_access_parses_member_and_invite(self):
        transport = FakeTransport(
            {
                "dlr_list_archive_access": [
                    {
                        "kind": "member",
                        "record_id": USER_ID,
                        "user_id": USER_ID,
                        "email": "ADMIN@example.com",
                        "role": "admin",
                        "status": "active",
                        "invite_code": None,
                        "created_at": "2026-10-02T00:00:00Z",
                    },
                    {
                        "kind": "invite",
                        "record_id": INVITE_ID,
                        "user_id": None,
                        "email": "new@example.com",
                        "role": "viewer",
                        "status": "pending",
                        "invite_code": INVITE_CODE,
                        "created_at": "2026-10-02T00:00:00Z",
                    },
                ]
            }
        )
        service = SupabaseArchiveAccountAdmin(transport, ARCHIVE_ID)
        items = service.list_access()

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].role, ArchiveRole.ADMIN)
        self.assertEqual(items[0].email, "admin@example.com")
        self.assertEqual(items[1].invite_code, INVITE_CODE)

    def test_invite_uses_normalized_email_and_role(self):
        transport = FakeTransport(
            {
                "dlr_invite_archive_member": [
                    {
                        "invite_id": INVITE_ID,
                        "email": "new@example.com",
                        "role": "editor",
                        "status": "pending",
                        "invite_code": INVITE_CODE,
                        "user_id": None,
                    }
                ]
            }
        )
        service = SupabaseArchiveAccountAdmin(transport, ARCHIVE_ID)
        result = service.invite(
            email=" NEW@example.com ",
            role=ArchiveRole.EDITOR,
        )

        self.assertEqual(result.email, "new@example.com")
        self.assertEqual(result.role, ArchiveRole.EDITOR)
        function, params = transport.calls[0]
        self.assertEqual(function, "dlr_invite_archive_member")
        self.assertEqual(params["target_role"], "editor")

    def test_update_member_validates_status(self):
        service = SupabaseArchiveAccountAdmin(FakeTransport({}), ARCHIVE_ID)
        with self.assertRaises(ValueError):
            service.update_member(
                user_id=USER_ID,
                role=ArchiveRole.VIEWER,
                status="deleted",
            )

    def test_update_member_parses_response(self):
        transport = FakeTransport(
            {
                "dlr_update_archive_member": [
                    {
                        "user_id": USER_ID,
                        "email": "user@example.com",
                        "role": "viewer",
                        "status": "disabled",
                    }
                ]
            }
        )
        service = SupabaseArchiveAccountAdmin(transport, ARCHIVE_ID)
        result = service.update_member(
            user_id=USER_ID,
            role=ArchiveRole.VIEWER,
            status="disabled",
        )
        self.assertEqual(result.status, "disabled")
        self.assertEqual(result.role, ArchiveRole.VIEWER)

    def test_revoke_invite_reads_table_response(self):
        transport = FakeTransport(
            {"dlr_revoke_archive_invite": [{"revoked": True}]}
        )
        service = SupabaseArchiveAccountAdmin(transport, ARCHIVE_ID)
        self.assertTrue(service.revoke_invite(INVITE_ID))


if __name__ == "__main__":
    unittest.main()
