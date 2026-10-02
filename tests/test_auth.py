import json
import os
import unittest
from unittest.mock import patch

from letter_registry.auth import (
    SupabaseAuthError,
    SupabaseAuthSession,
    SupabasePasswordlessAuth,
)


class SupabasePasswordlessAuthTests(unittest.TestCase):
    def test_google_authorize_url_uses_supabase_social_endpoint(self):
        auth = SupabasePasswordlessAuth(
            base_url="https://example.supabase.co",
            publishable_key="synthetic-key",
            http_executor=lambda req: (200, "{}"),
        )
        url = auth.social_authorize_url(
            provider="google",
            redirect_to="https://archive.example.com/auth/confirm",
        )
        self.assertTrue(url.startswith(
            "https://example.supabase.co/auth/v1/authorize?"
        ))
        self.assertIn("provider=google", url)
        self.assertIn("redirect_to=", url)

    def test_google_authorize_url_rejects_unsafe_redirect(self):
        auth = SupabasePasswordlessAuth(
            base_url="https://example.supabase.co",
            publishable_key="synthetic-key",
            http_executor=lambda req: (200, "{}"),
        )
        with self.assertRaises(ValueError):
            auth.social_authorize_url(
                provider="google",
                redirect_to="ftp://unsafe.example.com",
            )

    def test_google_provider_enabled_reads_auth_settings(self):
        auth = SupabasePasswordlessAuth(
            base_url="https://example.supabase.co",
            publishable_key="synthetic-key",
            http_executor=lambda req: (
                200,
                json.dumps({"external": {"google": True}}),
            ),
        )
        self.assertTrue(auth.provider_enabled("google"))

    def test_magic_link_disables_new_user_creation(self):
        seen = {}

        def executor(req):
            seen["url"] = req.full_url
            seen["body"] = json.loads(req.data.decode("utf-8"))
            return 200, "{}"

        auth = SupabasePasswordlessAuth(
            base_url="https://example.supabase.co",
            publishable_key="synthetic-key",
            http_executor=executor,
        )
        auth.send_magic_link(
            email="USER@example.com",
            redirect_to="https://archive.example.com/auth/confirm",
        )

        self.assertIn("redirect_to=", seen["url"])
        self.assertEqual(seen["body"]["email"], "user@example.com")
        self.assertFalse(seen["body"]["create_user"])

    def test_magic_link_rejects_unsafe_redirect(self):
        auth = SupabasePasswordlessAuth(
            base_url="https://example.supabase.co",
            publishable_key="synthetic-key",
            http_executor=lambda req: (200, "{}"),
        )
        with self.assertRaises(ValueError):
            auth.send_magic_link(
                email="user@example.com",
                redirect_to="ftp://unsafe.example.com",
            )

    def test_token_hash_verification_returns_session(self):
        seen = {}

        def executor(req):
            seen["url"] = req.full_url
            seen["body"] = json.loads(req.data.decode("utf-8"))
            return 200, json.dumps({
                "access_token": "synthetic-access",
                "refresh_token": "synthetic-refresh",
                "expires_in": 3600,
            })

        auth = SupabasePasswordlessAuth(
            base_url="https://example.supabase.co",
            publishable_key="synthetic-key",
            http_executor=executor,
        )
        session = auth.verify_token_hash(
            token_hash="synthetic-token-hash",
            verification_type="email",
        )

        self.assertEqual(session.access_token, "synthetic-access")
        self.assertEqual(session.refresh_token, "synthetic-refresh")
        self.assertEqual(session.expires_in, 3600)
        self.assertTrue(seen["url"].endswith("/auth/v1/verify"))
        self.assertEqual(
            seen["body"],
            {
                "token_hash": "synthetic-token-hash",
                "type": "email",
            },
        )

    def test_refresh_session_rotates_session_tokens(self):
        seen = {}

        def executor(req):
            seen["url"] = req.full_url
            seen["body"] = json.loads(req.data.decode("utf-8"))
            return 200, json.dumps({
                "access_token": "new-access",
                "refresh_token": "new-refresh",
                "expires_in": 7200,
            })

        auth = SupabasePasswordlessAuth(
            base_url="https://example.supabase.co",
            publishable_key="synthetic-key",
            http_executor=executor,
        )
        session = auth.refresh_session(refresh_token="old-refresh")

        self.assertEqual(session.access_token, "new-access")
        self.assertEqual(session.refresh_token, "new-refresh")
        self.assertIn("grant_type=refresh_token", seen["url"])
        self.assertEqual(
            seen["body"],
            {"refresh_token": "old-refresh"},
        )

    def test_invalid_session_response_fails_closed(self):
        auth = SupabasePasswordlessAuth(
            base_url="https://example.supabase.co",
            publishable_key="synthetic-key",
            http_executor=lambda req: (200, "{}"),
        )
        with self.assertRaises(SupabaseAuthError):
            auth.verify_token_hash(
                token_hash="synthetic",
                verification_type="email",
            )

    def test_session_requires_both_tokens(self):
        with self.assertRaises(ValueError):
            SupabaseAuthSession(
                access_token="",
                refresh_token="refresh",
                expires_in=3600,
            )

    def test_environment_requires_url_and_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                SupabasePasswordlessAuth.from_environment()


if __name__ == "__main__":
    unittest.main()
