"""Minimal Supabase passwordless-auth client for the private web app."""

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
        raise SupabaseAuthError(f"Supabase Auth failed: {exc.reason}") from exc


@dataclass(slots=True)
class SupabasePasswordlessAuth:
    base_url: str
    publishable_key: str
    http_executor: HttpExecutor = _default_http_executor

    @classmethod
    def from_environment(cls) -> "SupabasePasswordlessAuth":
        base_url = os.environ.get("SUPABASE_URL", "").strip()
        publishable_key = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "").strip()
        if not base_url:
            raise ValueError("SUPABASE_URL is required at runtime")
        if not publishable_key:
            raise ValueError("SUPABASE_PUBLISHABLE_KEY is required at runtime")
        return cls(base_url=base_url, publishable_key=publishable_key)

    def send_magic_link(self, *, email: str, redirect_to: str) -> None:
        normalized = email.strip().lower()
        if not normalized or "@" not in normalized or len(normalized) > 320:
            raise ValueError("valid email is required")
        if not redirect_to.startswith(("https://", "http://localhost", "http://127.0.0.1")):
            raise ValueError("redirect_to must be an HTTPS URL or local development URL")

        query = parse.urlencode({"redirect_to": redirect_to})
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
            raise SupabaseAuthError(f"unexpected Supabase Auth HTTP status: {status}")
