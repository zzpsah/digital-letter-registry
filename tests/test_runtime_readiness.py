import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from letter_registry.runtime_readiness import check_runtime_readiness


class RuntimeReadinessTests(unittest.TestCase):
    def test_ready_configuration_reports_only_status_not_secret_values(self):
        env = {
            "SUPABASE_URL": "https://private-project.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "private-publishable-key",
            "AUTH_REDIRECT_URL": "https://archive.example.com/auth/confirm",
            "GOOGLE_OAUTH_CLIENT_ID": "private-client-id",
            "GOOGLE_OAUTH_CLIENT_SECRET": "private-client-secret",
            "GOOGLE_DRIVE_REFRESH_TOKEN": "private-refresh-token",
            "DRIVE_ORIGINALS_FOLDER_REFERENCE": "private-folder-id",
            "GEMINI_API_KEY": "private-gemini-key",
            "ENABLE_REAL_INTAKE": "false",
        }
        with patch.dict(os.environ, env, clear=True):
            with patch(
                "letter_registry.runtime_readiness.shutil.which",
                side_effect=lambda name: f"/usr/bin/{name}",
            ):
                class Result:
                    returncode = 0
                    stdout = "List of available languages" + chr(10) + "eng" + chr(10) + "hin" + chr(10)
                    stderr = ""

                with patch(
                    "letter_registry.runtime_readiness.subprocess.run",
                    return_value=Result(),
                ):
                    readiness = check_runtime_readiness()

        self.assertTrue(readiness.ready)
        serialized = str(readiness.as_dict())
        for secret in (
            "private-project",
            "private-publishable-key",
            "private-client-secret",
            "private-refresh-token",
            "private-folder-id",
            "private-gemini-key",
        ):
            self.assertNotIn(secret, serialized)

    def test_service_account_file_counts_as_configured(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "service-account.json"
            path.write_text("{}", encoding="utf-8")
            with patch.dict(
                os.environ,
                {
                    "SUPABASE_URL": "https://example.supabase.co",
                    "SUPABASE_PUBLISHABLE_KEY": "key",
                    "AUTH_REDIRECT_URL": "http://localhost:8000/auth/confirm",
                    "GOOGLE_SERVICE_ACCOUNT_FILE": str(path),
                    "DRIVE_ORIGINALS_FOLDER_REFERENCE": "folder",
                },
                clear=True,
            ):
                with patch("letter_registry.runtime_readiness.shutil.which", return_value=None):
                    readiness = check_runtime_readiness()
            checks = {item.name: item for item in readiness.checks}
            self.assertTrue(checks["drive_credentials"].ready)
            self.assertNotIn(str(path), str(readiness.as_dict()))

    def test_drive_credentials_file_counts_as_configured(self):
        with tempfile.TemporaryDirectory() as td:
            credentials = Path(td) / "authorized-user.json"
            credentials.write_text("{}", encoding="utf-8")
            env = {
                "GOOGLE_OAUTH_CREDENTIALS_FILE": str(credentials),
            }
            with patch.dict(os.environ, env, clear=True):
                with patch(
                    "letter_registry.runtime_readiness.shutil.which",
                    return_value=None,
                ):
                    readiness = check_runtime_readiness()

        checks = {item.name: item for item in readiness.checks}
        self.assertTrue(checks["drive_credentials"].ready)
        self.assertNotIn(str(credentials), str(readiness.as_dict()))

    def test_missing_gemini_uses_deterministic_fallback(self):
        env = {
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "key",
            "AUTH_REDIRECT_URL": "https://archive.example.com/auth/confirm",
            "GOOGLE_DRIVE_ACCESS_TOKEN": "token",
            "DRIVE_ORIGINALS_FOLDER_REFERENCE": "folder",
            "ENABLE_REAL_INTAKE": "false",
        }
        with patch.dict(os.environ, env, clear=True):
            with patch(
                "letter_registry.runtime_readiness.shutil.which",
                side_effect=lambda name: f"/usr/bin/{name}",
            ):
                class Result:
                    returncode = 0
                    stdout = "List of available languages\neng\nhin\n"
                    stderr = ""

                with patch(
                    "letter_registry.runtime_readiness.subprocess.run",
                    return_value=Result(),
                ):
                    readiness = check_runtime_readiness()

        checks = {item.name: item for item in readiness.checks}
        self.assertTrue(checks["gemini"].ready)
        self.assertIn("deterministic", checks["gemini"].detail)
        self.assertTrue(readiness.ready)

    def test_missing_ocr_languages_fail_readiness(self):
        env = {
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "key",
            "AUTH_REDIRECT_URL": "http://localhost:8000/auth/confirm",
            "GOOGLE_DRIVE_ACCESS_TOKEN": "token",
            "DRIVE_ORIGINALS_FOLDER_REFERENCE": "folder",
            "GEMINI_API_KEY": "gemini",
        }
        with patch.dict(os.environ, env, clear=True):
            with patch(
                "letter_registry.runtime_readiness.shutil.which",
                side_effect=lambda name: f"/usr/bin/{name}",
            ):
                class Result:
                    returncode = 0
                    stdout = "List of available languages\neng\n"
                    stderr = ""

                with patch(
                    "letter_registry.runtime_readiness.subprocess.run",
                    return_value=Result(),
                ):
                    readiness = check_runtime_readiness()

        checks = {item.name: item for item in readiness.checks}
        self.assertFalse(checks["ocr_languages_hin_eng"].ready)
        self.assertFalse(readiness.ready)

    def test_non_local_http_auth_redirect_is_rejected(self):
        env = {
            "AUTH_REDIRECT_URL": "http://archive.example.com/auth/confirm",
        }
        with patch.dict(os.environ, env, clear=True):
            with patch(
                "letter_registry.runtime_readiness.shutil.which",
                return_value=None,
            ):
                readiness = check_runtime_readiness()

        checks = {item.name: item for item in readiness.checks}
        self.assertFalse(checks["auth_callback"].ready)

    def test_real_intake_enabled_is_not_synthetic_safe(self):
        with patch.dict(
            os.environ,
            {"ENABLE_REAL_INTAKE": "true"},
            clear=True,
        ):
            with patch(
                "letter_registry.runtime_readiness.shutil.which",
                return_value=None,
            ):
                readiness = check_runtime_readiness()

        checks = {item.name: item for item in readiness.checks}
        self.assertFalse(checks["synthetic_safety"].ready)
        self.assertEqual(
            checks["synthetic_safety"].detail,
            "real intake is enabled",
        )


    def test_configured_ocr_overrides_are_used_without_exposing_paths(self):
        env = {
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "key",
            "AUTH_REDIRECT_URL": "http://localhost:8000/auth/confirm",
            "GOOGLE_DRIVE_ACCESS_TOKEN": "token",
            "DRIVE_ORIGINALS_FOLDER_REFERENCE": "folder",
            "GEMINI_API_KEY": "gemini",
            "TESSERACT_CMD": "/private/tools/tesseract",
            "OCRMYPDF_CMD": "/private/tools/ocrmypdf",
        }
        with patch.dict(os.environ, env, clear=True):
            with patch(
                "letter_registry.runtime_readiness.shutil.which",
                side_effect=lambda name: name if name.startswith("/private/tools/") else None,
            ):
                with patch(
                    "letter_registry.runtime_readiness._ocr_languages",
                    return_value={"eng", "hin"},
                ) as languages:
                    readiness = check_runtime_readiness()

        checks = {item.name: item for item in readiness.checks}
        self.assertTrue(checks["tesseract"].ready)
        self.assertTrue(checks["ocrmypdf"].ready)
        self.assertTrue(checks["ocr_languages_hin_eng"].ready)
        languages.assert_called_once_with("/private/tools/tesseract")
        self.assertNotIn("/private/tools/", str(readiness.as_dict()))

if __name__ == "__main__":
    unittest.main()
