import json
import os
import unittest
from unittest.mock import patch

from letter_registry.session import SupabaseSessionError, SupabaseUserSession


class SupabaseUserSessionTests(unittest.TestCase):
    def test_user_id_is_verified_through_auth_endpoint(self):
        seen = {}

        def executor(req):
            seen["url"] = req.full_url
            seen["authorization"] = req.headers["Authorization"]
            return 200, json.dumps({
                "id": "11111111-1111-4111-8111-111111111111"
            })

        session = SupabaseUserSession(
            base_url="https://example.supabase.co",
            publishable_key="synthetic-key",
            access_token="synthetic-token",
            http_executor=executor,
        )

        self.assertEqual(
            session.user_id(),
            "11111111-1111-4111-8111-111111111111",
        )
        self.assertTrue(seen["url"].endswith("/auth/v1/user"))
        self.assertEqual(
            seen["authorization"],
            "Bearer synthetic-token",
        )

    def test_invalid_user_response_fails_closed(self):
        session = SupabaseUserSession(
            base_url="https://example.supabase.co",
            publishable_key="synthetic-key",
            access_token="synthetic-token",
            http_executor=lambda req: (200, '{"id":"not-a-uuid"}'),
        )
        with self.assertRaises(SupabaseSessionError):
            session.user_id()

    def test_environment_requires_runtime_configuration(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                SupabaseUserSession.from_environment(
                    access_token="synthetic-token"
                )


if __name__ == "__main__":
    unittest.main()
