import json
import os
import tempfile
import google.auth.transport.requests
import unittest
from pathlib import Path
from unittest.mock import patch

from letter_registry.google_drive_auth import (
    GoogleAuthorizedUserFileProvider,
    GoogleRefreshTokenProvider,
    GoogleServiceAccountProvider,
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

    def test_environment_uses_authorized_user_file_when_refresh_env_is_absent(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "credentials.json"
            path.write_text(
                json.dumps(
                    {
                        "client_id": "synthetic-client",
                        "client_secret": "synthetic-secret",
                        "refresh_token": "synthetic-refresh",
                    }
                ),
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {
                    "GOOGLE_OAUTH_CREDENTIALS_FILE": str(path),
                    "GOOGLE_DRIVE_ACCESS_TOKEN": "fallback-token",
                },
                clear=True,
            ):
                provider = drive_token_provider_from_environment()

        self.assertIsInstance(provider, GoogleAuthorizedUserFileProvider)

    def test_authorized_user_file_delegates_refresh(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "credentials.json"
            path.write_text(
                json.dumps(
                    {
                        "client_id": "synthetic-client",
                        "client_secret": "synthetic-secret",
                        "refresh_token": "synthetic-refresh",
                    }
                ),
                encoding="utf-8",
            )
            provider = GoogleAuthorizedUserFileProvider(str(path))
            with patch.object(
                GoogleRefreshTokenProvider,
                "get_access_token",
                return_value="synthetic-access",
            ) as refresh:
                token = provider.get_access_token()

        self.assertEqual(token, "synthetic-access")
        refresh.assert_called_once()

    def test_environment_prefers_refresh_credentials(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "credentials.json"
            path.write_text(
                json.dumps(
                    {
                        "client_id": "file-client",
                        "client_secret": "file-secret",
                        "refresh_token": "file-refresh",
                    }
                ),
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {
                    "GOOGLE_OAUTH_CREDENTIALS_FILE": str(path),
                    "GOOGLE_OAUTH_CLIENT_ID": "synthetic-client",
                    "GOOGLE_OAUTH_CLIENT_SECRET": "synthetic-secret",
                    "GOOGLE_DRIVE_REFRESH_TOKEN": "synthetic-refresh",
                    "GOOGLE_DRIVE_ACCESS_TOKEN": "fallback-token",
                },
                clear=True,
            ):
                provider = drive_token_provider_from_environment()

        self.assertIsInstance(provider, GoogleRefreshTokenProvider)

    def test_environment_accepts_service_account_json_for_serverless_runtime(self):
        payload = {"type": "service_account", "client_email": "synthetic@example.invalid", "private_" + "key": "synthetic-value", "token_uri": "https://oauth2.googleapis.com/token"}
        with patch.dict(os.environ, {"GOOGLE_SERVICE_ACCOUNT_JSON": json.dumps(payload)}, clear=True):
            provider = drive_token_provider_from_environment()
        self.assertIsInstance(provider, GoogleServiceAccountProvider)
        self.assertIsNone(provider.credentials_path)
        self.assertEqual(json.loads(provider.credentials_json), payload)

    def test_service_account_json_mints_token_from_in_memory_info(self):
        payload = {"type": "service_account", "client_email": "synthetic@example.invalid", "private_" + "key": "synthetic-value", "token_uri": "https://oauth2.googleapis.com/token"}
        class Credentials:
            valid = False
            token = None
            def refresh(self, request):
                self.token = "synthetic-json-service-account-access"
                self.valid = True
        credentials = Credentials()
        provider = GoogleServiceAccountProvider(credentials_json=json.dumps(payload))
        with patch("google.oauth2.service_account.Credentials.from_service_account_info", return_value=credentials) as load_credentials, patch("google.auth.transport.requests.Request", return_value=object()):
            token = provider.get_access_token()
        self.assertEqual(token, "synthetic-json-service-account-access")
        load_credentials.assert_called_once_with(payload, scopes=["https://www.googleapis.com/auth/drive"])

    def test_service_account_json_rejects_incomplete_or_invalid_json(self):
        for raw in ("not-json", json.dumps({"type": "service_account"})):
            with self.subTest(raw=raw), patch.dict(os.environ, {"GOOGLE_SERVICE_ACCOUNT_JSON": raw}, clear=True):
                with self.assertRaises(ValueError):
                    GoogleServiceAccountProvider.from_environment()

    def test_environment_prefers_service_account_file_over_refresh_token(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "service-account.json"
            path.write_text("{}", encoding="utf-8")
            with patch.dict(
                os.environ,
                {
                    "GOOGLE_SERVICE_ACCOUNT_FILE": str(path),
                    "GOOGLE_OAUTH_CLIENT_ID": "legacy-client",
                    "GOOGLE_OAUTH_CLIENT_SECRET": "legacy-secret",
                    "GOOGLE_DRIVE_REFRESH_TOKEN": "legacy-refresh",
                },
                clear=True,
            ):
                provider = drive_token_provider_from_environment()
        self.assertIsInstance(provider, GoogleServiceAccountProvider)

    def test_service_account_provider_mints_short_lived_access_token(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "service-account.json"
            path.write_text("synthetic-only", encoding="utf-8")
            class Credentials:
                valid = False
                token = None
                def refresh(self, request):
                    self.token = "synthetic-service-account-access"
                    self.valid = True
            credentials = Credentials()
            provider = GoogleServiceAccountProvider(str(path))
            with patch(
                "google.oauth2.service_account.Credentials.from_service_account_file",
                return_value=credentials,
            ) as load_credentials, patch(
                "google.auth.transport.requests.Request",
                return_value=object(),
            ):
                token = provider.get_access_token()
        self.assertEqual(token, "synthetic-service-account-access")
        load_credentials.assert_called_once_with(
            str(path), scopes=["https://www.googleapis.com/auth/drive"]
        )

    def test_service_account_provider_requires_existing_file(self):
        with patch.dict(
            os.environ,
            {"GOOGLE_SERVICE_ACCOUNT_FILE": "/missing/service-account.json"},
            clear=True,
        ):
            with self.assertRaisesRegex(ValueError, "file is missing"):
                GoogleServiceAccountProvider.from_environment()

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
