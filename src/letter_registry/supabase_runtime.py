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
    def from_worker_environment(cls) -> "SupabasePostgrestTransport":
        """Build a worker transport from a dedicated non-human Auth account.

        A directly supplied SUPABASE_ACCESS_TOKEN remains supported for
        one-shot/manual integration tests. Normal background workers should use
        SUPABASE_WORKER_EMAIL + SUPABASE_WORKER_PASSWORD so each run obtains a
        fresh short-lived user session and continues to respect RLS.
        """

        access_token = os.environ.get("SUPABASE_ACCESS_TOKEN", "").strip()
        if access_token:
            return cls.from_environment()

        worker_email = os.environ.get("SUPABASE_WORKER_EMAIL", "").strip()
        worker_password = os.environ.get("SUPABASE_WORKER_PASSWORD", "")
        if not worker_email or not worker_password:
            raise ValueError(
                "missing worker auth: set SUPABASE_ACCESS_TOKEN or "
                "SUPABASE_WORKER_EMAIL and SUPABASE_WORKER_PASSWORD"
            )

        from .auth import SupabasePasswordlessAuth

        session = SupabasePasswordlessAuth.from_environment().sign_in_with_password(
            email=worker_email,
            password=worker_password,
        )
        return cls(
            base_url=os.environ.get("SUPABASE_URL", "").strip(),
            publishable_key=os.environ.get(
                "SUPABASE_PUBLISHABLE_KEY", ""
            ).strip(),
            access_token=session.access_token,
        )

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

    def update(
        self,
        table: str,
        row: dict[str, object],
        *,
        filters: dict[str, str],
    ) -> dict[str, object]:
        if not filters:
            raise ValueError("update filters are required")
        params = [(key, f"eq.{value}") for key, value in filters.items()]
        result = self._request(
            method="PATCH",
            path=f"{table}?{parse.urlencode(params)}",
            row=row,
            prefer="return=representation",
        )
        if isinstance(result, list):
            return result[0] if result else {}
        if isinstance(result, dict):
            return result
        raise SupabaseRuntimeError("unexpected update response shape")

    def delete(
        self,
        table: str,
        *,
        filters: dict[str, str],
    ) -> list[dict[str, object]]:
        if not filters:
            raise ValueError("delete filters are required")
        params = [(key, f"eq.{value}") for key, value in filters.items()]
        result = self._request(
            method="DELETE",
            path=f"{table}?{parse.urlencode(params)}",
            prefer="return=representation",
        )
        if isinstance(result, list):
            return [item for item in result if isinstance(item, dict)]
        if isinstance(result, dict) and not result:
            return []
        raise SupabaseRuntimeError("unexpected delete response shape")

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


_ARCHIVE_SCOPED_TABLES = frozenset({
    "letters",
    "letter_processing",
    "letter_relationships",
    "letter_chunks",
    "processing_jobs",
    "processing_profiles",
    "letter_sources",
    "document_categories",
    "account_access_requests",
})

_ARCHIVE_SCOPED_RPCS = frozenset()


_ARCHIVE_CONFLICT_REWRITES = {
    ("letters", "owner_id,original_sha256"): "archive_id,original_sha256",
    (
        "letter_sources",
        "owner_id,source_channel,external_message_id",
    ): "archive_id,source_channel,external_message_id",
    ("processing_profiles", "owner_id"): "archive_id",
}


@dataclass(slots=True)
class ArchiveScopedSupabaseTransport:
    """Scope all archive-domain table operations to one configured archive."""

    transport: SupabasePostgrestTransport
    archive_id: str

    def __post_init__(self) -> None:
        from uuid import UUID

        self.archive_id = str(UUID(self.archive_id))

    def _row(self, table: str, row: dict[str, object]) -> dict[str, object]:
        prepared = dict(row)
        if table in _ARCHIVE_SCOPED_TABLES:
            existing = prepared.get("archive_id")
            if existing is not None and str(existing) != self.archive_id:
                raise ValueError("cross-archive write rejected")
            prepared["archive_id"] = self.archive_id
        return prepared

    def _filters(
        self,
        table: str,
        filters: dict[str, str] | None,
    ) -> dict[str, str] | None:
        if table not in _ARCHIVE_SCOPED_TABLES:
            return dict(filters) if filters is not None else None
        prepared = dict(filters or {})
        existing = prepared.get("archive_id")
        if existing is not None and str(existing) != self.archive_id:
            raise ValueError("cross-archive read rejected")
        prepared["archive_id"] = self.archive_id
        return prepared

    @staticmethod
    def _conflict(table: str, on_conflict: str | None) -> str | None:
        if on_conflict is None:
            return None
        return _ARCHIVE_CONFLICT_REWRITES.get(
            (table, on_conflict),
            on_conflict,
        )

    def insert(
        self,
        table: str,
        row: dict[str, object],
        *,
        on_conflict: str | None = None,
    ) -> dict[str, object]:
        return self.transport.insert(
            table,
            self._row(table, row),
            on_conflict=self._conflict(table, on_conflict),
        )

    def upsert(
        self,
        table: str,
        row: dict[str, object],
        *,
        on_conflict: str,
    ) -> dict[str, object]:
        return self.transport.upsert(
            table,
            self._row(table, row),
            on_conflict=self._conflict(table, on_conflict) or on_conflict,
        )

    def update(
        self,
        table: str,
        row: dict[str, object],
        *,
        filters: dict[str, str],
    ) -> dict[str, object]:
        return self.transport.update(
            table,
            self._row(table, row),
            filters=self._filters(table, filters) or {},
        )

    def delete(
        self,
        table: str,
        *,
        filters: dict[str, str],
    ) -> list[dict[str, object]]:
        return self.transport.delete(
            table,
            filters=self._filters(table, filters) or {},
        )

    def select(
        self,
        table: str,
        *,
        filters: dict[str, str] | None = None,
        columns: str = "*",
    ) -> list[dict[str, object]]:
        return self.transport.select(
            table,
            filters=self._filters(table, filters),
            columns=columns,
        )

    def rpc(
        self,
        function: str,
        params: dict[str, object],
    ) -> list[dict[str, object]]:
        scoped = dict(params)
        if function in _ARCHIVE_SCOPED_RPCS:
            scoped.setdefault("target_archive_id", self.archive_id)
        return self.transport.rpc(function, scoped)
