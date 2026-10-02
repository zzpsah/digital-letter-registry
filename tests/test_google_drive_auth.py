import json
import os
import unittest
from unittest.mock import patch

from letter_registry.google_drive_auth import (
    GoogleRefreshTokenProvider,
    StaticAccessTokenProvider,
    drive_token_provider_from_environment,
)


class DriveAuthTests(unittest.TestCase):
    def test_static_provider_returns_runtime_token(self):
        provider = StaticAccessTokenProvider(" synthetic-token ")
        self.assertEqual(
            provider.get_access_token(),
            "synthetic-token",
        )

    def test_refresh_provider_exchanges_and_caches_token(self):
        calls = []

        def executor(req):
            calls.append(req.data.decode("utf-8"))
            return 200, json.dumps({
                "access_token": "refreshed-token",
                "expires_in": 3600,
                "token_type": "Bearer",
            })

        provider = GoogleRefreshTokenProvider(
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
        self.assertIn("grant_type=refresh_token", calls[0])

    def test_environment_prefers_refresh_credentials(self):
        with patch.dict(
            os.environ,
            {
                "GOOGLE_OAUTH_CLIENT_ID": "synthetic-client",
                "GOOGLE_OAUTH_CLIENT_SECRET": "synthetic-secret",
                "GOOGLE_DRIVE_REFRESH_TOKEN": "synthetic-refresh",
                "GOOGLE_DRIVE_ACCESS_TOKEN": "fallback-token",
            },
            clear=True,
        ):
            provider = drive_token_provider_from_environment()

        self.assertIsInstance(provider, GoogleRefreshTokenProvider)

    def test_environment_can_fallback_to_static_token(self):
        with patch.dict(
            os.environ,
            {"GOOGLE_DRIVE_ACCESS_TOKEN": "fallback-token"},
            clear=True,
        ):
            provider = drive_token_provider_from_environment()

        self.assertIsInstance(provider, StaticAccessTokenProvider)


if __name__ == "__main__":
    unittest.main()
