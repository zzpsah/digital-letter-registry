"""Runtime-only Google OAuth access-token provider.

Supports either a directly supplied short-lived access token or refresh-token
credentials. Secrets are read from environment only and never persisted.
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


class AccessTokenProvider(Protocol):
    def get_access_token(self) -> str:
        ...


HttpExecutor = Callable[[request.Request], tuple[int, str]]


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
            raise ValueError("Google access token is empty")
        return token


@dataclass(slots=True)
class GoogleOAuthRefreshTokenProvider:
    client_id: str
    client_secret: str
    refresh_token: str
    http_executor: HttpExecutor = _default_http_executor
    refresh_skew_seconds: int = 60
    _cached_token: str | None = field(default=None, init=False, repr=False)
    _expires_at: float = field(default=0.0, init=False, repr=False)

    @classmethod
    def from_environment(cls) -> AccessTokenProvider:
        direct = os.environ.get("GOOGLE_DRIVE_ACCESS_TOKEN", "").strip()
        if direct:
            return StaticAccessTokenProvider(direct)

        client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").strip()
        client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
        refresh_token = os.environ.get("GOOGLE_OAUTH_REFRESH_TOKEN", "").strip()
        missing = [
            name
            for name, value in (
                ("GOOGLE_OAUTH_CLIENT_ID", client_id),
                ("GOOGLE_OAUTH_CLIENT_SECRET", client_secret),
                ("GOOGLE_OAUTH_REFRESH_TOKEN", refresh_token),
            )
            if not value
        ]
        if missing:
            raise ValueError(
                "missing Google OAuth runtime environment: "
                + ", ".join(missing)
            )
        return cls(
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
        )

    def get_access_token(self) -> str:
        now = time.time()
        if (
            self._cached_token
            and now < self._expires_at - self.refresh_skew_seconds
        ):
            return self._cached_token

        body = parse.urlencode(
            {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            }
        ).encode("utf-8")
        req = request.Request(
            "https://oauth2.googleapis.com/token",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
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
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise GoogleOAuthError(
                "Google OAuth returned an invalid refresh response"
            ) from exc

        if not token:
            raise GoogleOAuthError("Google OAuth returned an empty access token")

        self._cached_token = token
        self._expires_at = now + max(60, expires_in)
        return token
