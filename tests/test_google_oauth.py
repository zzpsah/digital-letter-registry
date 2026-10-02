import json
import os
import unittest
from unittest.mock import patch

from letter_registry.google_oauth import (
    GoogleOAuthRefreshTokenProvider,
    StaticAccessTokenProvider,
)


class GoogleOAuthTests(unittest.TestCase):
    def test_direct_access_token_takes_precedence(self):
        with patch.dict(
            os.environ,
            {"GOOGLE_DRIVE_ACCESS_TOKEN": "direct-token"},
            clear=True,
        ):
            provider = GoogleOAuthRefreshTokenProvider.from_environment()

        self.assertIsInstance(provider, StaticAccessTokenProvider)
        self.assertEqual(provider.get_access_token(), "direct-token")

    def test_refresh_token_flow_caches_access_token(self):
        calls = []

        def executor(req):
            calls.append(req)
            return 200, json.dumps(
                {
                    "access_token": "refreshed-token",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                }
            )

        provider = GoogleOAuthRefreshTokenProvider(
            client_id="synthetic-client",
            client_secret="synthetic-secret",
            refresh_token="synthetic-refresh",
            http_executor=executor,
        )

        first = provider.get_access_token()
        second = provider.get_access_token()

        self.assertEqual(first, "refreshed-token")
        self.assertEqual(second, "refreshed-token")
        self.assertEqual(len(calls), 1)

    def test_refresh_request_uses_refresh_token_grant(self):
        seen = {}

        def executor(req):
            seen["body"] = req.data.decode("utf-8")
            return 200, '{"access_token":"token","expires_in":3600}'

        provider = GoogleOAuthRefreshTokenProvider(
            client_id="client",
            client_secret="secret",
            refresh_token="refresh",
            http_executor=executor,
        )
        provider.get_access_token()

        self.assertIn("grant_type=refresh_token", seen["body"])
        self.assertIn("refresh_token=refresh", seen["body"])

    def test_environment_requires_refresh_credentials_when_no_direct_token(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                GoogleOAuthRefreshTokenProvider.from_environment()


if __name__ == "__main__":
    unittest.main()
