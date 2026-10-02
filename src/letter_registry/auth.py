"""Server-safe Supabase authentication helpers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Callable
from urllib import error, parse, request


class SupabaseAuthError(RuntimeError):
    pass


HttpExecutor = Callable[[request.Request], tuple[int, str]]


def _default_http_executor(req: request.Request) -> tuple[int, str]:
    try:
        with request.urlopen(req, timeout=30) as response:  # noqa: S310
            return response.status, response.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SupabaseAuthError(
            f"Supabase Auth failed with HTTP {exc.code}: {body}"
        ) from exc
    except error.URLError as exc:
        raise SupabaseAuthError(
            f"Supabase Auth failed: {exc.reason}"
        ) from exc


@dataclass(frozen=True, slots=True)
class SupabaseAuthSession:
    access_token: str
    refresh_token: str
    expires_in: int

    def __post_init__(self) -> None:
        if not self.access_token.strip():
            raise ValueError("access_token is required")
        if not self.refresh_token.strip():
            raise ValueError("refresh_token is required")
        if self.expires_in <= 0:
            raise ValueError("expires_in must be positive")


@dataclass(slots=True)
class SupabasePasswordlessAuth:
    base_url: str
    publishable_key: str
    http_executor: HttpExecutor = _default_http_executor

    @classmethod
    def from_environment(cls) -> "SupabasePasswordlessAuth":
        base_url = os.environ.get("SUPABASE_URL", "").strip()
        publishable_key = os.environ.get(
            "SUPABASE_PUBLISHABLE_KEY", ""
        ).strip()
        if not base_url:
            raise ValueError("SUPABASE_URL is required at runtime")
        if not publishable_key:
            raise ValueError(
                "SUPABASE_PUBLISHABLE_KEY is required at runtime"
            )
        return cls(
            base_url=base_url,
            publishable_key=publishable_key,
        )

    @staticmethod
    def _validate_redirect_to(redirect_to: str) -> str:
        target = redirect_to.strip()
        if not target.startswith(
            ("https://", "http://localhost", "http://127.0.0.1")
        ):
            raise ValueError(
                "redirect_to must be an HTTPS URL or local development URL"
            )
        return target

    def social_authorize_url(
        self,
        *,
        provider: str,
        redirect_to: str,
    ) -> str:
        normalized_provider = provider.strip().lower()
        if normalized_provider != "google":
            raise ValueError("unsupported social auth provider")
        target = self._validate_redirect_to(redirect_to)
        query = parse.urlencode(
            {
                "provider": normalized_provider,
                "redirect_to": target,
            }
        )
        return f"{self.base_url.rstrip('/')}/auth/v1/authorize?{query}"

    def provider_enabled(self, provider: str) -> bool:
        normalized_provider = provider.strip().lower()
        if normalized_provider != "google":
            raise ValueError("unsupported social auth provider")
        req = request.Request(
            f"{self.base_url.rstrip('/')}/auth/v1/settings",
            headers={"apikey": self.publishable_key},
            method="GET",
        )
        status, raw = self.http_executor(req)
        if status < 200 or status >= 300:
            raise SupabaseAuthError(
                f"unexpected Supabase settings HTTP status: {status}"
            )
        try:
            data = json.loads(raw)
            return bool((data.get("external") or {}).get(normalized_provider))
        except (TypeError, json.JSONDecodeError) as exc:
            raise SupabaseAuthError(
                "Supabase Auth returned invalid provider settings"
            ) from exc

    def send_magic_link(
        self,
        *,
        email: str,
        redirect_to: str,
    ) -> None:
        normalized = email.strip().lower()
        if (
            not normalized
            or "@" not in normalized
            or len(normalized) > 320
        ):
            raise ValueError("valid email is required")
        target = self._validate_redirect_to(redirect_to)

        query = parse.urlencode({"redirect_to": target})
        req = request.Request(
            f"{self.base_url.rstrip('/')}/auth/v1/otp?{query}",
            data=json.dumps(
                {
                    "email": normalized,
                    "create_user": False,
                }
            ).encode("utf-8"),
            headers={
                "apikey": self.publishable_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        status, _ = self.http_executor(req)
        if status < 200 or status >= 300:
            raise SupabaseAuthError(
                f"unexpected Supabase Auth HTTP status: {status}"
            )

    def sign_in_with_password(
        self,
        *,
        email: str,
        password: str,
    ) -> SupabaseAuthSession:
        normalized = email.strip().lower()
        if (
            not normalized
            or "@" not in normalized
            or len(normalized) > 320
        ):
            raise ValueError("valid email is required")
        if len(password) < 6 or len(password) > 256:
            raise ValueError("password must be between 6 and 256 characters")

        req = request.Request(
            (
                f"{self.base_url.rstrip('/')}/auth/v1/token"
                "?grant_type=password"
            ),
            data=json.dumps(
                {
                    "email": normalized,
                    "password": password,
                }
            ).encode("utf-8"),
            headers={
                "apikey": self.publishable_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        status, raw = self.http_executor(req)
        if status < 200 or status >= 300:
            raise SupabaseAuthError(
                f"unexpected Supabase password auth HTTP status: {status}"
            )
        return self._session_from_response(raw)

    def verify_token_hash(
        self,
        *,
        token_hash: str,
        verification_type: str = "email",
    ) -> SupabaseAuthSession:
        token = token_hash.strip()
        if not token:
            raise ValueError("token_hash is required")
        if verification_type != "email":
            raise ValueError("only email token verification is supported")

        req = request.Request(
            f"{self.base_url.rstrip('/')}/auth/v1/verify",
            data=json.dumps(
                {
                    "token_hash": token,
                    "type": verification_type,
                }
            ).encode("utf-8"),
            headers={
                "apikey": self.publishable_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        status, raw = self.http_executor(req)
        if status < 200 or status >= 300:
            raise SupabaseAuthError(
                f"unexpected Supabase verify HTTP status: {status}"
            )
        return self._session_from_response(raw)

    def refresh_session(
        self,
        *,
        refresh_token: str,
    ) -> SupabaseAuthSession:
        token = refresh_token.strip()
        if not token:
            raise ValueError("refresh_token is required")

        req = request.Request(
            (
                f"{self.base_url.rstrip('/')}/auth/v1/token"
                "?grant_type=refresh_token"
            ),
            data=json.dumps(
                {"refresh_token": token}
            ).encode("utf-8"),
            headers={
                "apikey": self.publishable_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        status, raw = self.http_executor(req)
        if status < 200 or status >= 300:
            raise SupabaseAuthError(
                f"unexpected Supabase refresh HTTP status: {status}"
            )
        return self._session_from_response(raw)

    @staticmethod
    def _session_from_response(raw: str) -> SupabaseAuthSession:
        try:
            data = json.loads(raw)
            return SupabaseAuthSession(
                access_token=str(data["access_token"]),
                refresh_token=str(data["refresh_token"]),
                expires_in=int(data.get("expires_in", 3600)),
            )
        except (
            KeyError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            raise SupabaseAuthError(
                "Supabase Auth returned an invalid session response"
            ) from exc
