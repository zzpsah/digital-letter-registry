"""Native DLR authentication primitives; no hosted identity provider required.

The repository is deliberately injected so password/JWT/session policy can be
unit-tested independently from the Oracle PostgreSQL connection layer.
"""
from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

import bcrypt
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError


class NativeAuthError(RuntimeError):
    """Authentication failure that must not disclose account existence."""


@dataclass(frozen=True, slots=True)
class NativeAuthSession:
    access_token: str
    refresh_token: str
    expires_in: int


class NativeAuthRepository(Protocol):
    def user_by_email(self, email: str) -> dict[str, Any] | None: ...
    def user_by_id(self, user_id: str) -> dict[str, Any] | None: ...
    def create_session(self, user_id: str, token_hash: str, expires_at: datetime,
                       user_agent: str | None, ip_address: str | None) -> str: ...
    def active_session_by_refresh_hash(self, token_hash: str) -> dict[str, Any] | None: ...
    def active_session_by_id(self, session_id: str) -> dict[str, Any] | None: ...
    def rotate_session(self, session_id: str, old_hash: str, new_hash: str,
                       expires_at: datetime) -> bool: ...
    def revoke_session(self, session_id: str) -> None: ...
    def update_password(self, user_id: str, password_hash: str, scheme: str) -> None: ...
    def record_login(self, user_id: str) -> None: ...


class NativeAuthService:
    ISSUER = "digital-letter-registry"
    AUDIENCE = "dlr-app"
    ACCESS_TTL_SECONDS = 15 * 60
    REFRESH_TTL = timedelta(days=30)
    _password_hasher = PasswordHasher()

    @classmethod
    def from_environment(cls) -> "NativeAuthService":
        import os
        from pathlib import Path
        from .postgres_runtime import PostgresAuthRepository

        secret_file = os.environ.get(
            "DLR_AUTH_JWT_SECRET_FILE",
            "/home/prashant/.config/dlr/native-runtime/jwt-secret",
        )
        secret = Path(secret_file).read_text(encoding="utf-8").strip()
        return cls(PostgresAuthRepository(), secret)

    def __init__(self, repository: NativeAuthRepository, jwt_secret: str,
                 *, access_ttl_seconds: int = ACCESS_TTL_SECONDS,
                 refresh_ttl: timedelta = REFRESH_TTL) -> None:
        if len(jwt_secret.encode("utf-8")) < 32:
            raise ValueError("native JWT secret must contain at least 32 bytes")
        if access_ttl_seconds < 60 or access_ttl_seconds > 3600:
            raise ValueError("access token lifetime must be between 60 and 3600 seconds")
        self.repository = repository
        self.jwt_secret = jwt_secret
        self.access_ttl_seconds = access_ttl_seconds
        self.refresh_ttl = refresh_ttl

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    def _verify_password(cls, password: str, password_hash: str,
                         scheme: str) -> bool:
        try:
            if scheme == "bcrypt" or password_hash.startswith(("$2a$", "$2b$", "$2y$")):
                return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("ascii"))
            if scheme == "argon2" or password_hash.startswith("$argon2"):
                return cls._password_hasher.verify(password_hash, password)
        except (ValueError, InvalidHashError, VerificationError, VerifyMismatchError):
            return False
        return False

    @classmethod
    def _hash_password(cls, password: str) -> tuple[str, str]:
        if len(password) < 8 or len(password) > 256:
            raise ValueError("password must contain between 8 and 256 characters")
        return cls._password_hasher.hash(password), "argon2"

    def _access_token(self, user_id: str, session_id: str) -> str:
        now = datetime.now(timezone.utc)
        claims = {
            "iss": self.ISSUER,
            "aud": self.AUDIENCE,
            "sub": user_id,
            "sid": session_id,
            "iat": now,
            "nbf": now,
            "exp": now + timedelta(seconds=self.access_ttl_seconds),
        }
        return jwt.encode(claims, self.jwt_secret, algorithm="HS256")

    def _new_session(self, user_id: str, *, user_agent: str | None,
                     ip_address: str | None) -> NativeAuthSession:
        refresh_token = secrets.token_urlsafe(48)
        expires_at = datetime.now(timezone.utc) + self.refresh_ttl
        session_id = self.repository.create_session(
            user_id, self._token_hash(refresh_token), expires_at,
            user_agent, ip_address,
        )
        return NativeAuthSession(
            access_token=self._access_token(user_id, session_id),
            refresh_token=refresh_token,
            expires_in=self.access_ttl_seconds,
        )

    def sign_in(self, email: str, password: str, *, user_agent: str | None = None,
                ip_address: str | None = None) -> NativeAuthSession:
        normalized = email.strip().lower()
        user = self.repository.user_by_email(normalized)
        if not user or bool(user.get("is_disabled")):
            raise NativeAuthError("Email or password is invalid")
        password_hash = str(user.get("password_hash") or "")
        scheme = str(user.get("password_scheme") or "bcrypt")
        if not password_hash or not self._verify_password(password, password_hash, scheme):
            raise NativeAuthError("Email or password is invalid")
        if not user.get("email_verified_at"):
            raise NativeAuthError("Email address must be verified before sign-in")
        # Upgrade a legacy GoTrue bcrypt hash to Argon2 after successful login.
        if scheme == "bcrypt" or password_hash.startswith(("$2a$", "$2b$", "$2y$")):
            upgraded_hash, upgraded_scheme = self._hash_password(password)
            self.repository.update_password(str(user["id"]), upgraded_hash, upgraded_scheme)
        self.repository.record_login(str(user["id"]))
        return self._new_session(str(user["id"]), user_agent=user_agent,
                                 ip_address=ip_address)

    def verify_access_token(self, access_token: str) -> dict[str, Any]:
        try:
            claims = jwt.decode(
                access_token, self.jwt_secret, algorithms=["HS256"],
                issuer=self.ISSUER, audience=self.AUDIENCE,
                options={"require": ["sub", "sid", "exp", "iat"]},
            )
        except jwt.InvalidTokenError as exc:
            raise NativeAuthError("Invalid or expired session") from exc
        session = self.repository.active_session_by_id(str(claims["sid"]))
        if not session or str(session.get("user_id")) != str(claims["sub"]):
            raise NativeAuthError("Invalid or expired session")
        user = self.repository.user_by_id(str(claims["sub"]))
        if not user or bool(user.get("is_disabled")):
            raise NativeAuthError("Invalid or expired session")
        return user

    def refresh(self, refresh_token: str) -> NativeAuthSession:
        old_hash = self._token_hash(refresh_token)
        current = self.repository.active_session_by_refresh_hash(old_hash)
        if not current:
            raise NativeAuthError("Invalid or expired refresh session")
        user_id = str(current["user_id"])
        user = self.repository.user_by_id(user_id)
        if not user or bool(user.get("is_disabled")):
            self.repository.revoke_session(str(current["id"]))
            raise NativeAuthError("Invalid or expired refresh session")
        new_token = secrets.token_urlsafe(48)
        expires_at = datetime.now(timezone.utc) + self.refresh_ttl
        if not self.repository.rotate_session(
            str(current["id"]), old_hash, self._token_hash(new_token), expires_at
        ):
            raise NativeAuthError("Refresh session was already used")
        return NativeAuthSession(
            access_token=self._access_token(user_id, str(current["id"])),
            refresh_token=new_token,
            expires_in=self.access_ttl_seconds,
        )

    def sign_out(self, access_token: str) -> None:
        user = self.verify_access_token(access_token)
        claims = jwt.decode(
            access_token, self.jwt_secret, algorithms=["HS256"],
            issuer=self.ISSUER, audience=self.AUDIENCE,
        )
        if str(user["id"]) == str(claims["sub"]):
            self.repository.revoke_session(str(claims["sid"]))

    def sign_out_refresh(self, refresh_token: str) -> None:
        current = self.repository.active_session_by_refresh_hash(self._token_hash(refresh_token))
        if current:
            self.repository.revoke_session(str(current["id"]))

    def complete_approved_account(self, email: str, password: str, approval_token: str) -> str:
        password_hash, scheme = self._hash_password(password)
        complete = getattr(self.repository, "complete_approved_account", None)
        if complete is None:
            raise NativeAuthError("native account activation is unavailable")
        return str(complete(email.strip().lower(), password_hash, approval_token, scheme))

    def register_with_invite(self, email: str, password: str, invite_code: str) -> NativeAuthSession:
        password_hash, scheme = self._hash_password(password)
        register = getattr(self.repository, "register_with_invite", None)
        if register is None:
            raise NativeAuthError("native invitation registration is unavailable")
        user_id, _role = register(email.strip().lower(), password_hash, invite_code, scheme)
        return self._new_session(str(user_id), user_agent=None, ip_address=None)

    def sign_in_google(self, email: str, google_subject: str, *,
                       user_agent: str | None = None,
                       ip_address: str | None = None) -> NativeAuthSession:
        link_identity = getattr(self.repository, "link_google_user", None)
        if link_identity is None:
            raise NativeAuthError("native Google identity linking is unavailable")
        try:
            user_id = link_identity(email.strip().lower(), google_subject)
        except ValueError as exc:
            raise NativeAuthError(str(exc)) from exc
        return self._new_session(str(user_id), user_agent=user_agent, ip_address=ip_address)

    def confirm_user(self, user_id: str) -> None:
        confirm = getattr(self.repository, "confirm_user", None)
        if confirm is None:
            raise NativeAuthError("native account confirmation is unavailable")
        confirm(user_id)

    def admin_user_account_action(self, access_token: str, archive_id: str,
                                  target_user_id: str, action: str,
                                  password: str | None = None) -> None:
        user = self.verify_access_token(access_token)
        password_hash = scheme = None
        if action == "reset_password":
            if password is None:
                raise ValueError("password is required")
            password_hash, scheme = self._hash_password(password)
        operation = getattr(self.repository, "admin_user_account_action", None)
        if operation is None:
            raise NativeAuthError("native account administration is unavailable")
        operation(str(user["id"]), archive_id, target_user_id, action,
                  password_hash, scheme or "argon2")

    def change_password(self, user_id: str, new_password: str) -> None:
        password_hash, scheme = self._hash_password(new_password)
        self.repository.update_password(user_id, password_hash, scheme)
