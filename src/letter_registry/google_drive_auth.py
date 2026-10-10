"""Runtime-only Google Drive OAuth access-token providers.

Secrets stay in environment/runtime secret storage. Refreshed access tokens are
kept in process memory only and are never persisted by this module.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Callable, Protocol
from urllib import error, parse, request


class GoogleOAuthError(RuntimeError):
    pass


class DriveAccessTokenProvider(Protocol):
    def get_access_token(self) -> str:
        ...


@dataclass(slots=True)
class GoogleAuthorizedUserFileProvider:
    credentials_path: str
    _delegate: "GoogleRefreshTokenProvider | None" = field(default=None, init=False)

    @classmethod
    def from_environment(cls) -> "GoogleAuthorizedUserFileProvider":
        path = os.environ.get("GOOGLE_OAUTH_CREDENTIALS_FILE", "").strip()
        if not path:
            raise ValueError("Google authorized-user credentials file is required")
        return cls(credentials_path=path)

    def _provider(self) -> "GoogleRefreshTokenProvider":
        if self._delegate is not None:
            return self._delegate
        try:
            with open(self.credentials_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("Google authorized-user credentials file is invalid") from exc

        values = {
            "client_id": str(data.get("client_id") or "").strip(),
            "client_secret": str(data.get("client_secret") or "").strip(),
            "refresh_token": str(data.get("refresh_token") or "").strip(),
        }
        if not all(values.values()):
            raise ValueError("Google authorized-user credentials file is incomplete")
        self._delegate = GoogleRefreshTokenProvider(**values)
        return self._delegate

    def get_access_token(self) -> str:
        return self._provider().get_access_token()


TextHttpExecutor = Callable[[request.Request], tuple[int, str]]


def _default_http_executor(req: request.Request) -> tuple[int, str]:
    try:
        with request.urlopen(req, timeout=30) as response:  # noqa: S310
            return response.status, response.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise GoogleOAuthError(
            f"Google OAuth refresh failed with HTTP {exc.code}: {body}"
        ) from exc
    except error.URLError as exc:
        raise GoogleOAuthError(
            f"Google OAuth refresh failed: {exc.reason}"
        ) from exc


@dataclass(slots=True)
class StaticAccessTokenProvider:
    access_token: str

    def get_access_token(self) -> str:
        token = self.access_token.strip()
        if not token:
            raise ValueError("Google Drive access token is required")
        return token



@dataclass(slots=True)
class GoogleServiceAccountProvider:
    """Mint short-lived Drive access tokens from a service-account key file.

    The private key remains in a root/user-readable runtime file; access tokens
    are cached only in memory. Uploads require a folder accessible to the service
    account (normally a Google Workspace Shared Drive).
    """

    credentials_path: str | None = None
    credentials_json: str | None = None
    _credentials: object | None = field(default=None, init=False)
    _request_factory: object | None = field(default=None, init=False)

    @classmethod
    def from_environment(cls) -> "GoogleServiceAccountProvider":
        path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "").strip()
        if path:
            if not os.path.isfile(path):
                raise ValueError("Google service-account credentials file is missing")
            return cls(credentials_path=path)
        raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
        if raw:
            try:
                info = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError("Google service-account JSON is invalid") from exc
            required = ("type", "client_email", "private_" + "key", "token_uri")
            if not isinstance(info, dict) or info.get("type") != "service_account" or not all(str(info.get(key) or "").strip() for key in required):
                raise ValueError("Google service-account JSON is incomplete")
            return cls(credentials_json=raw)
        raise ValueError("Google service-account credentials file or JSON is required")

    def get_access_token(self) -> str:
        if self._credentials is None:
            try:
                from google.oauth2 import service_account
                from google.auth.transport.requests import Request
            except ImportError as exc:
                raise RuntimeError("google-auth is required for service-account Drive auth") from exc
            try:
                scopes = ["https://www.googleapis.com/auth/drive"]
                if self.credentials_json is not None:
                    self._credentials = service_account.Credentials.from_service_account_info(json.loads(self.credentials_json), scopes=scopes)
                elif self.credentials_path:
                    self._credentials = service_account.Credentials.from_service_account_file(self.credentials_path, scopes=scopes)
                else:
                    raise ValueError("Google service-account credentials are missing")
            except (OSError, ValueError, KeyError) as exc:
                raise ValueError("Google service-account credentials file is invalid") from exc
            self._request_factory = Request
        credentials = self._credentials
        if not getattr(credentials, "valid", False):
            try:
                credentials.refresh(self._request_factory())
            except Exception as exc:
                # Never include credential material or provider response bodies.
                raise GoogleOAuthError("Google service-account token refresh failed") from exc
        token = str(getattr(credentials, "token", "") or "").strip()
        if not token:
            raise GoogleOAuthError("Google service-account returned an empty access token")
        return token

@dataclass(slots=True)
class GoogleRefreshTokenProvider:
    client_id: str
    client_secret: str
    refresh_token: str
    http_executor: TextHttpExecutor = _default_http_executor
    refresh_margin_seconds: int = 60
    _cached_token: str | None = field(default=None, init=False)
    _expires_at: float = field(default=0.0, init=False)

    @classmethod
    def from_environment(cls) -> "GoogleRefreshTokenProvider":
        values = {
            "client_id": os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").strip(),
            "client_secret": os.environ.get(
                "GOOGLE_OAUTH_CLIENT_SECRET", ""
            ).strip(),
            "refresh_token": os.environ.get(
                "GOOGLE_DRIVE_REFRESH_TOKEN", ""
            ).strip(),
        }
        missing = [key for key, value in values.items() if not value]
        if missing:
            raise ValueError(
                "Google OAuth refresh configuration is incomplete"
            )
        return cls(**values)

    def get_access_token(self) -> str:
        now = time.monotonic()
        if (
            self._cached_token
            and now < self._expires_at - self.refresh_margin_seconds
        ):
            return self._cached_token

        payload = parse.urlencode(
            {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            }
        ).encode("utf-8")
        req = request.Request(
            "https://oauth2.googleapis.com/token",
            data=payload,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )
        status, raw = self.http_executor(req)
        if status < 200 or status >= 300:
            raise GoogleOAuthError(
                f"unexpected Google OAuth HTTP status: {status}"
            )

        try:
            data = json.loads(raw)
            token = str(data["access_token"]).strip()
            expires_in = int(data.get("expires_in", 3600))
        except (
            KeyError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            raise GoogleOAuthError(
                "Google OAuth returned an invalid refresh response"
            ) from exc

        if not token:
            raise GoogleOAuthError(
                "Google OAuth returned an empty access token"
            )
        if expires_in <= 0:
            raise GoogleOAuthError(
                "Google OAuth returned an invalid token lifetime"
            )

        self._cached_token = token
        self._expires_at = time.monotonic() + expires_in
        return token


def drive_token_provider_from_environment() -> DriveAccessTokenProvider:
    service_account_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "").strip()
    service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if service_account_file or service_account_json:
        return GoogleServiceAccountProvider.from_environment()

    refresh_token = os.environ.get(
        "GOOGLE_DRIVE_REFRESH_TOKEN", ""
    ).strip()
    if refresh_token:
        return GoogleRefreshTokenProvider.from_environment()

    credentials_file = os.environ.get(
        "GOOGLE_OAUTH_CREDENTIALS_FILE", ""
    ).strip()
    if credentials_file:
        return GoogleAuthorizedUserFileProvider.from_environment()

    static = os.environ.get("GOOGLE_DRIVE_ACCESS_TOKEN", "").strip()
    if static:
        return StaticAccessTokenProvider(static)

    raise ValueError(
        "Configure Google Drive OAuth refresh credentials or a runtime access token"
    )
