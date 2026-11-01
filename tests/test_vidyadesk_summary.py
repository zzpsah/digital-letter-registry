from datetime import datetime, timezone
from pathlib import Path
import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from letter_registry.access import ArchiveMembership, ArchiveRole
from letter_registry.api import ApiDependencies, create_app
from letter_registry.auth import SupabaseAuthSession
from letter_registry.vidyadesk_summary import build_summary


class FakeTransport:
    def __init__(self, *, archive_name="UMV Tetahali"):
        self.archive_name = archive_name
        self.calls = []

    def select(self, table, *, filters=None, columns="*"):
        self.calls.append((table, dict(filters or {}), columns))
        if table == "archives":
            return [{
                "id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                "name": self.archive_name,
                "status": "active",
            }]
        raise AssertionError(table)

    def rpc(self, function, params):
        self.calls.append(("rpc", function, dict(params)))
        return [{
            "public_document_count": 2,
            "latest_public_document_at": "2026-10-31T10:30:00+00:00",
        }]


class VidyaDeskSummaryTests(unittest.TestCase):
    def test_summary_returns_only_public_document_count_and_timestamp(self):
        payload = build_summary(
            public_document_count=2,
            latest_public_document_at="2026-10-31T10:30:00+00:00",
            archive_name="UMV Tetahali",
            expected_archive_name="UMV Tetahali",
            school_key="umv-tetahali",
            now=datetime(2026, 11, 1, 5, 30, tzinfo=timezone.utc),
        )
        self.assertEqual(payload["sourceSystem"], "digital-letter-registry")
        self.assertEqual(payload["scope"]["schoolKey"], "umv-tetahali")
        self.assertEqual(payload["retrievedAt"], "2026-11-01T05:30:00Z")
        self.assertEqual(payload["data"], {
            "publicDocumentCount": 2,
            "latestPublicDocumentAt": "2026-10-31T10:30:00Z",
        })
        self.assertNotIn("letter_id", str(payload))
        self.assertNotIn("filename", str(payload))

    def test_summary_fails_closed_for_unconfirmed_school_or_archive(self):
        with self.assertRaises(ValueError):
            build_summary(
                public_document_count=0,
                latest_public_document_at=None,
                archive_name="UMV Tetahali",
                expected_archive_name="Another archive",
                school_key="umv-tetahali",
            )
        with self.assertRaises(ValueError):
            build_summary(
                public_document_count=0,
                latest_public_document_at=None,
                archive_name="UMV Tetahali",
                expected_archive_name="UMV Tetahali",
                school_key="another-school",
            )

    def test_summary_supports_zero_public_documents(self):
        payload = build_summary(
            public_document_count=0,
            latest_public_document_at=None,
            archive_name="UMV Tetahali",
            expected_archive_name="UMV Tetahali",
            school_key="umv-tetahali",
        )
        self.assertEqual(payload["data"]["publicDocumentCount"], 0)
        self.assertIsNone(payload["data"]["latestPublicDocumentAt"])

    def test_sql_rpc_is_authenticated_viewer_only_and_aggregate_only(self):
        migration = Path("supabase/migrations/20261101080000_add_vidyadesk_public_summary_rpc.sql").read_text().lower()
        self.assertIn("security definer", migration)
        self.assertIn("member_role is distinct from 'viewer'", migration)
        self.assertIn("a.status = 'active'", migration)
        self.assertIn("l.visibility = 'public'", migration)
        self.assertIn("l.is_archived = false", migration)
        self.assertIn("revoke all on function public.vidyadesk_public_archive_summary(uuid) from anon", migration)
        self.assertIn("grant execute on function public.vidyadesk_public_archive_summary(uuid) to authenticated", migration)
        self.assertNotIn("service_role", migration)
        self.assertNotIn("select l.*", migration)

    def test_summary_rejects_negative_counts(self):
        with self.assertRaises(ValueError):
            build_summary(
                public_document_count=-1,
                latest_public_document_at=None,
                archive_name="UMV Tetahali",
                expected_archive_name="UMV Tetahali",
                school_key="umv-tetahali",
            )


class VidyaDeskSummaryRouteTests(unittest.TestCase):
    ARCHIVE_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    TOKEN = "dedicated-dlr-integration-test-token"

    def setUp(self):
        self.client = TestClient(create_app(ApiDependencies()))
        self.env = {
            "DLR_VIDYADESK_READ_TOKEN": self.TOKEN,
            "DLR_VIDYADESK_SCHOOL_KEY": "umv-tetahali",
            "DLR_VIDYADESK_ARCHIVE_NAME": "UMV Tetahali",
            "DLR_VIDYADESK_SERVICE_EMAIL": "vidyadesk-viewer@example.test",
            "DLR_VIDYADESK_SERVICE_PASSWORD": "test-only-password",
        }

    def test_route_is_disabled_without_server_configuration(self):
        with patch.dict(os.environ, {}, clear=True):
            response = self.client.get(
                "/api/v1/integrations/vidyadesk/summary",
                headers={"Authorization": "Bearer " + self.TOKEN},
            )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "integration_not_configured")

    def test_wrong_machine_token_is_rejected_before_supabase_auth(self):
        with patch.dict(os.environ, self.env, clear=False), patch(
            "letter_registry.api.SupabasePasswordlessAuth.from_environment"
        ) as auth_factory:
            response = self.client.get(
                "/api/v1/integrations/vidyadesk/summary",
                headers={"Authorization": "Bearer wrong"},
            )
        self.assertEqual(response.status_code, 401)
        auth_factory.assert_not_called()

    def test_scope_override_is_rejected(self):
        with patch.dict(os.environ, self.env, clear=False):
            response = self.client.get(
                "/api/v1/integrations/vidyadesk/summary?archive_id=another",
                headers={"Authorization": "Bearer " + self.TOKEN},
            )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "scope_override_not_allowed")

    def test_route_uses_dedicated_viewer_and_returns_aggregate_only(self):
        transport = FakeTransport()
        membership = ArchiveMembership(
            archive_id=self.ARCHIVE_ID,
            user_id="bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            role=ArchiveRole.VIEWER,
        )
        session = SupabaseAuthSession(
            access_token="synthetic-viewer-access-token",
            refresh_token="synthetic-viewer-refresh-token",
            expires_in=3600,
        )
        with patch.dict(os.environ, self.env, clear=False), patch(
            "letter_registry.api.SupabasePasswordlessAuth.from_environment"
        ) as auth_factory, patch(
            "letter_registry.api._archive_id", return_value=self.ARCHIVE_ID
        ), patch(
            "letter_registry.api._archive_membership", return_value=membership
        ) as membership_check, patch(
            "letter_registry.api._raw_transport", return_value=transport
        ):
            auth_factory.return_value.sign_in_with_password.return_value = session
            response = self.client.get(
                "/api/v1/integrations/vidyadesk/summary",
                headers={"Authorization": "Bearer " + self.TOKEN},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["data"]["publicDocumentCount"], 2)
        self.assertEqual(
            payload["data"]["latestPublicDocumentAt"],
            "2026-10-31T10:30:00Z",
        )
        self.assertNotIn("private-id-should-not-escape", response.text)
        self.assertNotIn("another-private-id", response.text)
        membership_check.assert_called_once_with(
            "synthetic-viewer-access-token",
            roles={ArchiveRole.VIEWER},
        )
        rpc_call = next(call for call in transport.calls if call[0] == "rpc")
        self.assertEqual(rpc_call[1], "vidyadesk_public_archive_summary")
        self.assertEqual(rpc_call[2], {"target_archive_id": self.ARCHIVE_ID})
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_archive_name_mismatch_fails_closed(self):
        transport = FakeTransport(archive_name="Different archive")
        membership = ArchiveMembership(
            archive_id=self.ARCHIVE_ID,
            user_id="bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            role=ArchiveRole.VIEWER,
        )
        session = SupabaseAuthSession(
            access_token="synthetic-viewer-access-token",
            refresh_token="synthetic-viewer-refresh-token",
            expires_in=3600,
        )
        with patch.dict(os.environ, self.env, clear=False), patch(
            "letter_registry.api.SupabasePasswordlessAuth.from_environment"
        ) as auth_factory, patch(
            "letter_registry.api._archive_id", return_value=self.ARCHIVE_ID
        ), patch(
            "letter_registry.api._archive_membership", return_value=membership
        ), patch(
            "letter_registry.api._raw_transport", return_value=transport
        ):
            auth_factory.return_value.sign_in_with_password.return_value = session
            response = self.client.get(
                "/api/v1/integrations/vidyadesk/summary",
                headers={"Authorization": "Bearer " + self.TOKEN},
            )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "provider_unavailable")
        self.assertFalse(any(call[0] == "rpc" for call in transport.calls))

    def test_non_viewer_identity_cannot_use_integration(self):
        with patch.dict(os.environ, self.env, clear=False), patch(
            "letter_registry.api.SupabasePasswordlessAuth.from_environment"
        ) as auth_factory, patch(
            "letter_registry.api._archive_id", return_value=self.ARCHIVE_ID
        ), patch(
            "letter_registry.api._archive_membership",
            side_effect=HTTPException(status_code=403, detail="not a viewer"),
        ), patch("letter_registry.api._raw_transport") as raw_transport:
            auth_factory.return_value.sign_in_with_password.return_value = SupabaseAuthSession(
                access_token="synthetic-access-token",
                refresh_token="synthetic-refresh-token",
                expires_in=3600,
            )
            response = self.client.get(
                "/api/v1/integrations/vidyadesk/summary",
                headers={"Authorization": "Bearer " + self.TOKEN},
            )
        self.assertEqual(response.status_code, 403)
        raw_transport.assert_not_called()


if __name__ == "__main__":
    unittest.main()
