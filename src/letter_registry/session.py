"""Supabase authenticated-session identity lookup."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Callable
from urllib import error, request
from uuid import UUID


class SupabaseSessionError(RuntimeError):
    pass


HttpExecutor = Callable[[request.Request], tuple[int, str]]


def _default_http_executor(req: request.Request) -> tuple[int, str]:
    try:
        with request.urlopen(req, timeout=30) as response:  # noqa: S310
            return response.status, response.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SupabaseSessionError(
            f"Supabase session lookup failed with HTTP {exc.code}: {body}"
        ) from exc
    except error.URLError as exc:
        raise SupabaseSessionError(
            f"Supabase session lookup failed: {exc.reason}"
        ) from exc


@dataclass(slots=True)
class SupabaseUserSession:
    base_url: str
    publishable_key: str
    access_token: str
    http_executor: HttpExecutor = _default_http_executor

    @classmethod
    def from_environment(
        cls,
        *,
        access_token: str,
    ) -> "SupabaseUserSession":
        base_url = os.environ.get("SUPABASE_URL", "").strip()
        publishable_key = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "").strip()
        if not base_url:
            raise ValueError("SUPABASE_URL is required at runtime")
        if not publishable_key:
            raise ValueError("SUPABASE_PUBLISHABLE_KEY is required at runtime")
        if not access_token.strip():
            raise ValueError("access_token is required")
        return cls(
            base_url=base_url,
            publishable_key=publishable_key,
            access_token=access_token,
        )

    def user_id(self) -> str:
        req = request.Request(
            f"{self.base_url.rstrip('/')}/auth/v1/user",
            headers={
                "apikey": self.publishable_key,
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json",
            },
            method="GET",
        )
        status, raw = self.http_executor(req)
        if status < 200 or status >= 300:
            raise SupabaseSessionError(
                f"unexpected Supabase session HTTP status: {status}"
            )
        try:
            data = json.loads(raw)
            return str(UUID(str(data["id"])))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise SupabaseSessionError(
                "Supabase returned an invalid authenticated-user response"
            ) from exc
