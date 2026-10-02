import json
import os
import unittest
from unittest.mock import patch

from letter_registry.auth import SupabasePasswordlessAuth


class SupabasePasswordlessAuthTests(unittest.TestCase):
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
            redirect_to="https://archive.example.com/auth/callback",
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

    def test_environment_requires_url_and_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                SupabasePasswordlessAuth.from_environment()


if __name__ == "__main__":
    unittest.main()
