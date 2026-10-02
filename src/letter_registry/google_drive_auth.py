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
    refresh_token = os.environ.get(
        "GOOGLE_DRIVE_REFRESH_TOKEN", ""
    ).strip()
    if refresh_token:
        return GoogleRefreshTokenProvider.from_environment()

    static = os.environ.get("GOOGLE_DRIVE_ACCESS_TOKEN", "").strip()
    if static:
        return StaticAccessTokenProvider(static)

    raise ValueError(
        "Configure Google Drive OAuth refresh credentials or a runtime access token"
    )
