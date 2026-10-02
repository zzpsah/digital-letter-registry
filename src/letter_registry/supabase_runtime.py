"""Runtime Supabase PostgREST transport.

Secrets and user sessions come from environment/runtime only. Nothing here
contains project-specific identifiers or credentials.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Callable
from urllib import error, parse, request


class SupabaseRuntimeError(RuntimeError):
    """Raised when a runtime Supabase request fails."""


HttpExecutor = Callable[[request.Request], tuple[int, str]]


def _default_http_executor(req: request.Request) -> tuple[int, str]:
    try:
        with request.urlopen(req, timeout=30) as response:  # noqa: S310
            return response.status, response.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SupabaseRuntimeError(
            f"Supabase request failed with HTTP {exc.code}: {body}"
        ) from exc
    except error.URLError as exc:
        raise SupabaseRuntimeError(f"Supabase request failed: {exc.reason}") from exc


@dataclass(slots=True)
class SupabasePostgrestTransport:
    """Authenticated PostgREST transport using a user access token."""

    base_url: str
    publishable_key: str
    access_token: str
    http_executor: HttpExecutor = _default_http_executor

    @classmethod
    def from_environment(cls) -> "SupabasePostgrestTransport":
        values = {
            "base_url": os.environ.get("SUPABASE_URL", "").strip(),
            "publishable_key": os.environ.get("SUPABASE_PUBLISHABLE_KEY", "").strip(),
            "access_token": os.environ.get("SUPABASE_ACCESS_TOKEN", "").strip(),
        }
        missing = [key for key, value in values.items() if not value]
        if missing:
            names = ", ".join(
                {
                    "base_url": "SUPABASE_URL",
                    "publishable_key": "SUPABASE_PUBLISHABLE_KEY",
                    "access_token": "SUPABASE_ACCESS_TOKEN",
                }[key]
                for key in missing
            )
            raise ValueError(f"missing required runtime environment: {names}")
        return cls(**values)

    def _request(
        self,
        *,
        method: str,
        path: str,
        row: dict[str, object] | None = None,
        prefer: str | None = None,
    ) -> object:
        url = f"{self.base_url.rstrip('/')}/rest/v1/{path.lstrip('/')}"
        headers = {
            "apikey": self.publishable_key,
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer

        body = None if row is None else json.dumps(row).encode("utf-8")
        req = request.Request(url, data=body, headers=headers, method=method)
        status, text = self.http_executor(req)
        if status < 200 or status >= 300:
            raise SupabaseRuntimeError(f"unexpected Supabase HTTP status: {status}")
        if not text.strip():
            return {}
        return json.loads(text)

    def insert(
        self,
        table: str,
        row: dict[str, object],
        *,
        on_conflict: str | None = None,
    ) -> dict[str, object]:
        query = ""
        prefer = "return=representation"
        if on_conflict:
            query = "?" + parse.urlencode({"on_conflict": on_conflict})
            prefer += ",resolution=ignore-duplicates"
        result = self._request(
            method="POST",
            path=f"{table}{query}",
            row=row,
            prefer=prefer,
        )
        if isinstance(result, list):
            return result[0] if result else {}
        if isinstance(result, dict):
            return result
        raise SupabaseRuntimeError("unexpected insert response shape")

    def upsert(
        self,
        table: str,
        row: dict[str, object],
        *,
        on_conflict: str,
    ) -> dict[str, object]:
        query = "?" + parse.urlencode({"on_conflict": on_conflict})
        result = self._request(
            method="POST",
            path=f"{table}{query}",
            row=row,
            prefer="return=representation,resolution=merge-duplicates",
        )
        if isinstance(result, list):
            return result[0] if result else {}
        if isinstance(result, dict):
            return result
        raise SupabaseRuntimeError("unexpected upsert response shape")

    def rpc(
        self,
        function: str,
        params: dict[str, object],
    ) -> list[dict[str, object]]:
        result = self._request(
            method="POST",
            path=f"rpc/{function}",
            row=params,
        )
        if isinstance(result, list):
            return [item for item in result if isinstance(item, dict)]
        raise SupabaseRuntimeError("unexpected RPC response shape")

    def select(
        self,
        table: str,
        *,
        filters: dict[str, str] | None = None,
        columns: str = "*",
    ) -> list[dict[str, object]]:
        params: list[tuple[str, str]] = [("select", columns)]
        for key, value in (filters or {}).items():
            params.append((key, f"eq.{value}"))
        result = self._request(
            method="GET",
            path=f"{table}?{parse.urlencode(params)}",
        )
        if isinstance(result, list):
            return [item for item in result if isinstance(item, dict)]
        raise SupabaseRuntimeError("unexpected select response shape")
