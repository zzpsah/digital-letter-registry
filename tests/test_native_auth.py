from __future__ import annotations

from datetime import datetime, timezone

import bcrypt
import pytest

from letter_registry.native_auth import NativeAuthError, NativeAuthService


class MemoryAuthRepository:
    def __init__(self, user):
        self.user = dict(user)
        self.sessions = {}

    def user_by_email(self, email):
        return self.user if self.user["email"] == email else None

    def user_by_id(self, user_id):
        return self.user if self.user["id"] == user_id else None

    def create_session(self, user_id, token_hash, expires_at, user_agent, ip_address):
        session_id = "session-1"
        self.sessions[session_id] = {"id": session_id, "user_id": user_id,
                                     "token_hash": token_hash, "expires_at": expires_at,
                                     "revoked_at": None}
        return session_id

    def active_session_by_refresh_hash(self, token_hash):
        return next((row for row in self.sessions.values()
                     if row["token_hash"] == token_hash and row["revoked_at"] is None
                     and row["expires_at"] > datetime.now(timezone.utc)), None)

    def active_session_by_id(self, session_id):
        row = self.sessions.get(session_id)
        if row and row["revoked_at"] is None and row["expires_at"] > datetime.now(timezone.utc):
            return row
        return None

    def rotate_session(self, session_id, old_hash, new_hash, expires_at):
        row = self.sessions.get(session_id)
        if not row or row["token_hash"] != old_hash or row["revoked_at"] is not None:
            return False
        row.update(token_hash=new_hash, expires_at=expires_at)
        return True

    def revoke_session(self, session_id):
        self.sessions[session_id]["revoked_at"] = datetime.now(timezone.utc)

    def update_password(self, user_id, password_hash, scheme):
        self.user.update(password_hash=password_hash, password_scheme=scheme)

    def record_login(self, user_id):
        self.user["last_login_at"] = datetime.now(timezone.utc)

    def link_google_user(self, email, google_subject):
        if self.user["email"] != email or not self.user["email_verified_at"] or self.user["is_disabled"]:
            raise ValueError("Google sign-in is not enabled for this account")
        if self.user.get("google_subject") not in (None, google_subject):
            raise ValueError("a different Google identity is already linked")
        self.user["google_subject"] = google_subject
        return self.user["id"]


def make_service():
    legacy_hash = bcrypt.hashpw(b"Correct-Horse-42", bcrypt.gensalt()).decode()
    repo = MemoryAuthRepository({
        "id": "user-1", "email": "teacher@example.org", "password_hash": legacy_hash,
        "password_scheme": "bcrypt", "email_verified_at": datetime.now(timezone.utc),
        "is_disabled": False,
    })
    return NativeAuthService(repo, "x" * 48), repo


def test_native_sign_in_upgrades_bcrypt_and_issues_verifiable_session():
    auth, repo = make_service()
    session = auth.sign_in("TEACHER@example.org", "Correct-Horse-42")
    assert session.expires_in == 900
    assert repo.user["password_scheme"] == "argon2"
    assert auth.verify_access_token(session.access_token)["id"] == "user-1"


def test_native_sign_in_rejects_wrong_password():
    auth, _ = make_service()
    with pytest.raises(NativeAuthError):
        auth.sign_in("teacher@example.org", "wrong-password")


def test_native_sign_in_rejects_unverified_email():
    auth, repo = make_service()
    repo.user["email_verified_at"] = None
    with pytest.raises(NativeAuthError, match="verified"):
        auth.sign_in("teacher@example.org", "Correct-Horse-42")


def test_refresh_rotates_token_and_invalidates_previous_refresh_token():
    auth, _ = make_service()
    first = auth.sign_in("teacher@example.org", "Correct-Horse-42")
    second = auth.refresh(first.refresh_token)
    assert second.refresh_token != first.refresh_token
    assert auth.verify_access_token(second.access_token)["id"] == "user-1"
    with pytest.raises(NativeAuthError):
        auth.refresh(first.refresh_token)


def test_sign_out_revokes_access_session():
    auth, _ = make_service()
    session = auth.sign_in("teacher@example.org", "Correct-Horse-42")
    auth.sign_out(session.access_token)
    with pytest.raises(NativeAuthError):
        auth.verify_access_token(session.access_token)


def test_access_token_rejects_tampering():
    auth, _ = make_service()
    session = auth.sign_in("teacher@example.org", "Correct-Horse-42")
    with pytest.raises(NativeAuthError):
        auth.verify_access_token(session.access_token + "x")


def test_sign_out_revokes_refresh_token_when_access_token_is_expired_or_missing():
    auth, _ = make_service()
    session = auth.sign_in("teacher@example.org", "Correct-Horse-42")
    auth.sign_out_refresh(session.refresh_token)
    with pytest.raises(NativeAuthError):
        auth.refresh(session.refresh_token)


def test_google_sign_in_links_verified_identity_and_creates_native_session():
    auth, repo = make_service()
    session = auth.sign_in_google("teacher@example.org", "google-sub-123")
    assert repo.user["google_subject"] == "google-sub-123"
    assert auth.verify_access_token(session.access_token)["id"] == "user-1"


def test_google_sign_in_rejects_unverified_or_unapproved_account():
    auth, repo = make_service()
    repo.user["email_verified_at"] = None
    with pytest.raises(NativeAuthError):
        auth.sign_in_google("teacher@example.org", "google-sub-123")
