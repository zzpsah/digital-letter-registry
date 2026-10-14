import base64
import hashlib
import hmac
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from starlette.requests import Request

from letter_registry.local_supabase import (
    _cors_headers,
    _service_role_token,
    register_local_supabase_routes,
)
from letter_registry.supabase_runtime import SupabasePostgrestTransport
from letter_registry.worker_session import WorkerSession, _state_paths


class LocalSupabaseBridgeTests(unittest.TestCase):
    def test_service_role_token_is_short_lived_and_signed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            secret = b"test-only-local-jwt-secret-value-32-bytes-minimum"
            secret_path = Path(temp_dir) / "jwt-secret"
            secret_path.write_bytes(secret)
            with patch.dict(os.environ, {"DLR_LOCAL_JWT_SECRET_FILE": str(secret_path)}):
                token = _service_role_token()
            header_part, claims_part, signature_part = token.split(".")
            unsigned = f"{header_part}.{claims_part}"
            expected = base64.urlsafe_b64encode(
                hmac.new(secret, unsigned.encode("ascii"), hashlib.sha256).digest()
            ).rstrip(b"=").decode("ascii")
            self.assertEqual(signature_part, expected)
            claims = json.loads(base64.urlsafe_b64decode(claims_part + "==="))
            self.assertEqual(claims["role"], "service_role")
            self.assertEqual(claims["iss"], "supabase")
            self.assertGreater(claims["exp"], int(time.time()))
            self.assertLessEqual(claims["exp"] - claims["iat"], 300)

    def test_cors_allows_only_known_application_origin(self):
        allowed_request = Request({
            "type": "http",
            "method": "GET",
            "path": "/rest/v1/letters",
            "headers": [(b"origin", b"https://eletters.vercel.app")],
        })
        blocked_request = Request({
            "type": "http",
            "method": "GET",
            "path": "/rest/v1/letters",
            "headers": [(b"origin", b"https://attacker.invalid")],
        })
        with patch.dict(os.environ, {"DLR_LOCAL_CORS_ORIGINS": ""}, clear=False):
            self.assertEqual(_cors_headers(allowed_request)["Access-Control-Allow-Origin"], "https://eletters.vercel.app")
            self.assertEqual(_cors_headers(blocked_request), {})

    def test_local_primary_uses_separate_worker_session_cache(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            old_cache = str(Path(temp_dir) / "hosted-session.json")
            with patch.dict(os.environ, {
                "DLR_LOCAL_SUPABASE_PROXY_ENABLED": "true",
                "DLR_WORKER_SESSION_FILE": old_cache,
            }, clear=False):
                path, lock = _state_paths(None)
            self.assertNotEqual(str(path), old_cache)
            self.assertEqual(path.name, "worker-session.json")
            self.assertEqual(lock.name, "worker-session.lock")

    def test_local_primary_ignores_hosted_worker_access_token(self):
        session = WorkerSession(
            access_token="local-issued-access-token",
            refresh_token="local-issued-refresh-token",
            expires_at=time.time() + 3600,
            source="password",
        )
        with patch.dict(os.environ, {
            "DLR_LOCAL_SUPABASE_PROXY_ENABLED": "true",
            "SUPABASE_ACCESS_TOKEN": "hosted-project-token-must-not-be-used",
            "SUPABASE_WORKER_EMAIL": "worker@example.invalid",
            "SUPABASE_WORKER_PASSWORD": "test-only-password",
            "SUPABASE_URL": "http://127.0.0.1:8877",
            "SUPABASE_PUBLISHABLE_KEY": "local-public-key",
        }, clear=False):
            with patch("letter_registry.worker_session.load_worker_session", return_value=session) as load:
                transport = SupabasePostgrestTransport.from_worker_environment()
        load.assert_called_once_with(email="worker@example.invalid", password="test-only-password")
        self.assertEqual(transport.access_token, "local-issued-access-token")
        self.assertEqual(transport.base_url, "http://127.0.0.1:8877")

    def test_routes_are_registered_only_when_enabled(self):
        disabled = FastAPI()
        with patch.dict(os.environ, {"DLR_LOCAL_SUPABASE_PROXY_ENABLED": "false"}, clear=False):
            register_local_supabase_routes(disabled)
        self.assertNotIn("/rest/v1/{path:path}", {route.path for route in disabled.routes})

        enabled = FastAPI()
        with patch.dict(os.environ, {"DLR_LOCAL_SUPABASE_PROXY_ENABLED": "true"}, clear=False):
            register_local_supabase_routes(enabled)
        paths = {route.path for route in enabled.routes}
        self.assertIn("/auth/v1/{path:path}", paths)
        self.assertIn("/rest/v1/{path:path}", paths)
        self.assertIn("/functions/v1/dlr-admin-user-account", paths)
        self.assertIn("/functions/v1/dlr-confirm-account", paths)
        self.assertIn("/functions/v1/dlr-complete-approved-account", paths)


if __name__ == "__main__":
    unittest.main()
