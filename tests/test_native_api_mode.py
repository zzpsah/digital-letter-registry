from __future__ import annotations

from fastapi.testclient import TestClient

from letter_registry.api import app


def test_native_mode_uses_native_google_oauth_and_disables_supabase_proxy(monkeypatch):
    monkeypatch.setenv("DLR_NATIVE_POSTGRES_ENABLED", "true")
    monkeypatch.setenv("DLR_NATIVE_AUTH_ENABLED", "true")
    monkeypatch.setenv("DLR_DATABASE_PASSWORD_FILE", "/home/prashant/.config/dlr/native-runtime/database-password")
    monkeypatch.setenv("DLR_AUTH_JWT_SECRET_FILE", "/home/prashant/.config/dlr/native-runtime/jwt-secret")
    monkeypatch.setenv("DLR_GOOGLE_WEB_CLIENT_ID", "native-client-id")
    monkeypatch.setenv("DLR_GOOGLE_WEB_CLIENT_SECRET", "native-client-secret")
    monkeypatch.setenv("DLR_GOOGLE_WEB_REDIRECT_URI", "https://archive.example.org/auth/google/callback")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    monkeypatch.setenv("AUTH_APP_ORIGIN", "https://archive.example.org")

    with TestClient(app) as client:
        providers = client.get("/api/v1/auth/providers")
        assert providers.status_code == 200
        assert providers.json()["google"] is True

        start = client.get("/auth/google", follow_redirects=False)
        assert start.status_code == 302
        assert start.headers["location"].startswith("https://accounts.google.com/o/oauth2/v2/auth?")
        assert "dlr_google_state" in start.headers.get("set-cookie", "")
        assert "dlr_google_verifier" in start.headers.get("set-cookie", "")

        # The old Supabase compatibility API is not registered in native mode.
        old_proxy = client.get("/rest/v1/letters")
        assert old_proxy.status_code == 404
