"""Direct PostgreSQL transport for the native Oracle DLR runtime.

This replaces the PostgREST wire protocol with parameterized SQL. Identifiers
are validated/quoted and every value is bound separately. Authorization is
performed by FastAPI's archive-membership layer, not by a client JWT role.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID
from typing import Any

from psycopg import connect
from psycopg.rows import dict_row
from psycopg.sql import SQL, Identifier
from psycopg.types.json import Jsonb


class PostgresRuntimeError(RuntimeError):
    """Raised when the native PostgreSQL runtime cannot complete an operation."""

def _raise_native_operation_error(exc: Exception, default_message: str) -> None:
    message = str(exc).splitlines()[0][:240] or default_message
    if getattr(exc, "sqlstate", None) == "P0001":
        lowered = message.lower()
        if "admin access required" in lowered:
            raise PermissionError(message) from exc
        if "user not found" in lowered:
            raise LookupError(message) from exc
        raise ValueError(message) from exc
    raise PostgresRuntimeError(default_message) from exc


_IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]*$")
_ARCHIVE_TABLES = frozenset({
    "letters", "letter_processing", "letter_relationships", "letter_chunks",
    "processing_jobs", "processing_profiles", "letter_sources",
    "document_categories", "account_access_requests", "admin_audit_log",
})

_ARCHIVE_CONFLICT_REWRITES = {
    ("letters", "owner_id,original_sha256"): "archive_id,original_sha256",
    ("letter_sources", "owner_id,source_channel,external_message_id"): "archive_id,source_channel,external_message_id",
    ("processing_profiles", "owner_id"): "archive_id",
}


def _identifier(value: str) -> Identifier:
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"invalid SQL identifier: {value!r}")
    return Identifier(value)


def _adapt(value: Any) -> Any:
    if isinstance(value, dict):
        return Jsonb(value)
    if isinstance(value, tuple):
        return [_adapt(item) for item in value]
    if isinstance(value, list):
        return [_adapt(item) for item in value]
    return value


def _database_dsn() -> str:
    direct = os.environ.get("DLR_DATABASE_URL", "").strip()
    if direct:
        return direct
    password = os.environ.get("DLR_DATABASE_PASSWORD", "")
    password_file = os.environ.get("DLR_DATABASE_PASSWORD_FILE", "").strip()
    if not password and password_file:
        password = Path(password_file).read_text(encoding="utf-8").strip()
    if not password:
        raise ValueError("DLR_DATABASE_URL or DLR_DATABASE_PASSWORD_FILE is required")
    from urllib.parse import quote
    host = os.environ.get("DLR_DATABASE_HOST", "127.0.0.1")
    port = os.environ.get("DLR_DATABASE_PORT", "5432")
    database = os.environ.get("DLR_DATABASE_NAME", "dlr_primary")
    user = os.environ.get("DLR_DATABASE_USER", "dlr_app")
    return (f"postgresql://{quote(user, safe='')}:{quote(password, safe='')}@"
            f"{host}:{port}/{quote(database, safe='')}?sslmode=disable")


@dataclass(slots=True)
class PostgresTransport:
    """Small repository adapter matching the former transport's domain API."""

    dsn: str | None = None
    user_id: str | None = None

    def _connect(self):
        try:
            conn = connect(self.dsn or _database_dsn(), row_factory=dict_row,
                           connect_timeout=8, application_name="dlr-fastapi")
            # Apply the same database roles and RLS policies used by the old
            # API gateway. Native API calls never need BYPASSRLS privileges.
            conn.execute("SET ROLE authenticated" if self.user_id else "SET ROLE anon")
            # Preserve auth.uid()-based database RPC behavior during the
            # transition, without sending a JWT to PostgREST or GoTrue.
            conn.execute(
                "SELECT set_config('request.jwt.claim.sub', %s, false)",
                (self.user_id or "",),
            )
            conn.execute(
                "SELECT set_config('request.jwt.claims', %s, false)",
                ('{"sub":"' + (self.user_id or "") + '","role":"authenticated"}',),
            )
            return conn
        except Exception as exc:
            raise PostgresRuntimeError("native PostgreSQL connection failed") from exc

    @staticmethod
    def _where(filters: dict[str, str] | None) -> tuple[SQL, list[Any]]:
        clauses: list[SQL] = []
        values: list[Any] = []
        for key, raw in (filters or {}).items():
            ident = _identifier(key)
            operator, separator, value = str(raw).partition(".")
            if not separator:
                operator, value = "eq", str(raw)
            if operator == "eq":
                clauses.append(SQL("{} = %s").format(ident)); values.append(value)
            elif operator == "neq":
                clauses.append(SQL("{} <> %s").format(ident)); values.append(value)
            elif operator in {"gt", "gte", "lt", "lte"}:
                symbol = {"gt": ">", "gte": ">=", "lt": "<", "lte": "<="}[operator]
                clauses.append(SQL("{} " + symbol + " %s").format(ident)); values.append(value)
            elif operator == "is" and value == "null":
                clauses.append(SQL("{} IS NULL").format(ident))
            elif operator == "not" and value.startswith("is.null"):
                clauses.append(SQL("{} IS NOT NULL").format(ident))
            else:
                raise ValueError(f"unsupported PostgreSQL filter operator: {operator}")
        if not clauses:
            return SQL(""), values
        return SQL(" WHERE ").join([SQL(""), SQL(" AND ").join(clauses)]), values

    def select(self, table: str, *, filters: dict[str, str] | None = None,
               columns: str = "*") -> list[dict[str, Any]]:
        table_id = _identifier(table)
        selected = SQL("*") if columns.strip() == "*" else SQL(", ").join(
            _identifier(item.strip()) for item in columns.split(",")
        )
        where, values = self._where(filters)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(SQL("SELECT {} FROM public.{}").format(selected, table_id) + where, values)
            return [dict(row) for row in cur.fetchall()]

    def insert(self, table: str, row: dict[str, Any], *,
               on_conflict: str | None = None) -> dict[str, Any]:
        table_id = _identifier(table)
        keys = list(row)
        if not keys:
            raise ValueError("insert row cannot be empty")
        cols = SQL(", ").join(_identifier(key) for key in keys)
        vals = SQL(", ").join(SQL("%s") for _ in keys)
        conflict = SQL("")
        if on_conflict:
            targets = SQL(", ").join(_identifier(key.strip()) for key in on_conflict.split(","))
            conflict = SQL(" ON CONFLICT ({}) DO NOTHING").format(targets)
        query = SQL("INSERT INTO public.{} ({}) VALUES ({}){}").format(
            table_id, cols, vals, conflict) + SQL(" RETURNING *")
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(query, [_adapt(row[key]) for key in keys])
            result = cur.fetchone()
            return dict(result) if result else {}

    def upsert(self, table: str, row: dict[str, Any], *,
               on_conflict: str) -> dict[str, Any]:
        table_id = _identifier(table)
        keys = list(row)
        if not keys:
            raise ValueError("upsert row cannot be empty")
        conflict_keys = [key.strip() for key in on_conflict.split(",")]
        if not set(conflict_keys).issubset(keys):
            raise ValueError("upsert conflict columns must be present in the row")
        cols = SQL(", ").join(_identifier(key) for key in keys)
        vals = SQL(", ").join(SQL("%s") for _ in keys)
        updates = [key for key in keys if key not in conflict_keys]
        if updates:
            action = SQL("DO UPDATE SET ") + SQL(", ").join(
                SQL("{} = EXCLUDED.{}").format(_identifier(key), _identifier(key)) for key in updates)
        else:
            action = SQL("DO NOTHING")
        query = SQL("INSERT INTO public.{} ({}) VALUES ({}) ON CONFLICT ({}) ").format(
            table_id, cols, vals, SQL(", ").join(_identifier(key) for key in conflict_keys)) + action + SQL(" RETURNING *")
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(query, [_adapt(row[key]) for key in keys])
            result = cur.fetchone()
            if result:
                return dict(result)
        return self.select(table, filters={key: str(row[key]) for key in conflict_keys})[0]

    def update(self, table: str, row: dict[str, Any], *,
               filters: dict[str, str]) -> dict[str, Any]:
        if not filters:
            raise ValueError("update filters are required")
        table_id = _identifier(table)
        assignments = SQL(", ").join(
            SQL("{} = %s").format(_identifier(key)) for key in row)
        where, where_values = self._where(filters)
        query = SQL("UPDATE public.{} SET ").format(table_id) + assignments + where + SQL(" RETURNING *")
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(query, [_adapt(value) for value in row.values()] + where_values)
            result = cur.fetchone()
            return dict(result) if result else {}

    def delete(self, table: str, *, filters: dict[str, str]) -> list[dict[str, Any]]:
        if not filters:
            raise ValueError("delete filters are required")
        where, values = self._where(filters)
        query = SQL("DELETE FROM public.{} ").format(_identifier(table)) + where + SQL(" RETURNING *")
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(query, values)
            return [dict(row) for row in cur.fetchall()]

    def rpc(self, function: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        fn = _identifier(function)
        named_args = SQL(", ").join(
            SQL("{} => %s").format(_identifier(key)) for key in params)
        query = SQL("SELECT * FROM public.{}({})").format(fn, named_args)
        from uuid import UUID
        bound_values = []
        for value in params.values():
            if isinstance(value, str):
                try:
                    value = UUID(value)
                except ValueError:
                    pass
            bound_values.append(_adapt(value))
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(query, bound_values)
            rows = cur.fetchall()
            return [dict(row) if isinstance(row, dict) else {"result": row[0]} for row in rows]


@dataclass(slots=True)
class ArchiveScopedPostgresTransport:
    """Enforce the single configured archive scope on all archive-domain IO."""
    transport: PostgresTransport
    archive_id: str

    def _row(self, table: str, row: dict[str, Any]) -> dict[str, Any]:
        prepared = dict(row)
        if table in _ARCHIVE_TABLES:
            existing = prepared.get("archive_id")
            if existing is not None and str(existing) != self.archive_id:
                raise ValueError("cross-archive write rejected")
            prepared["archive_id"] = self.archive_id
        return prepared

    def _filters(self, table: str, filters: dict[str, str] | None) -> dict[str, str] | None:
        if table not in _ARCHIVE_TABLES:
            return dict(filters) if filters is not None else None
        prepared = dict(filters or {})
        existing = prepared.get("archive_id")
        if existing is not None and str(existing) != self.archive_id:
            raise ValueError("cross-archive read rejected")
        prepared["archive_id"] = self.archive_id
        return prepared

    def select(self, table: str, *, filters: dict[str, str] | None = None,
               columns: str = "*") -> list[dict[str, Any]]:
        return self.transport.select(table, filters=self._filters(table, filters), columns=columns)

    def insert(self, table: str, row: dict[str, Any], *,
               on_conflict: str | None = None) -> dict[str, Any]:
        return self.transport.insert(table, self._row(table, row), on_conflict=on_conflict)

    def upsert(self, table: str, row: dict[str, Any], *, on_conflict: str) -> dict[str, Any]:
        conflict = _ARCHIVE_CONFLICT_REWRITES.get((table, on_conflict), on_conflict)
        return self.transport.upsert(table, self._row(table, row), on_conflict=conflict)

    def update(self, table: str, row: dict[str, Any], *,
               filters: dict[str, str]) -> dict[str, Any]:
        return self.transport.update(table, row, filters=self._filters(table, filters) or {})

    def delete(self, table: str, *, filters: dict[str, str]) -> list[dict[str, Any]]:
        return self.transport.delete(table, filters=self._filters(table, filters) or {})

    def rpc(self, function: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        scoped = dict(params)
        if "target_archive_id" in scoped and str(scoped["target_archive_id"]) != self.archive_id:
            raise ValueError("cross-archive RPC rejected")
        return self.transport.rpc(function, scoped)


@dataclass(slots=True)
class PostgresAuthRepository:
    """Direct-SQL identity/session repository for native DLR authentication."""
    dsn: str | None = None

    def _connect(self):
        try:
            return connect(self.dsn or _database_dsn(), row_factory=dict_row,
                           connect_timeout=8, application_name="dlr-native-auth")
        except Exception as exc:
            raise PostgresRuntimeError("native authentication database unavailable") from exc

    def user_by_email(self, email: str) -> dict[str, Any] | None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM public.app_users WHERE lower(email) = %s LIMIT 1", (email,))
            row = cur.fetchone()
            return dict(row) if row else None

    def user_by_id(self, user_id: str) -> dict[str, Any] | None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM public.app_users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def create_session(self, user_id: str, token_hash: str, expires_at,
                       user_agent: str | None, ip_address: str | None) -> str:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO public.app_sessions (user_id, refresh_token_hash, expires_at, user_agent, ip_address) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (user_id, token_hash, expires_at, user_agent, ip_address),
            )
            return str(cur.fetchone()["id"])

    def active_session_by_refresh_hash(self, token_hash: str) -> dict[str, Any] | None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT id, user_id, expires_at FROM public.app_sessions "
                "WHERE refresh_token_hash = %s AND revoked_at IS NULL AND expires_at > now()",
                (token_hash,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def active_session_by_id(self, session_id: str) -> dict[str, Any] | None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT id, user_id, expires_at FROM public.app_sessions "
                "WHERE id = %s AND revoked_at IS NULL AND expires_at > now()",
                (session_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def rotate_session(self, session_id: str, old_hash: str, new_hash: str, expires_at) -> bool:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE public.app_sessions SET refresh_token_hash = %s, expires_at = %s, last_used_at = now() "
                "WHERE id = %s AND refresh_token_hash = %s AND revoked_at IS NULL AND expires_at > now() "
                "RETURNING id",
                (new_hash, expires_at, session_id, old_hash),
            )
            return cur.fetchone() is not None

    def revoke_session(self, session_id: str) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE public.app_sessions SET revoked_at = now() "
                "WHERE id = %s AND revoked_at IS NULL",
                (session_id,),
            )

    def update_password(self, user_id: str, password_hash: str, scheme: str) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE public.app_users SET password_hash = %s, password_scheme = %s, updated_at = now() WHERE id = %s",
                (password_hash, scheme, user_id),
            )

    def record_login(self, user_id: str) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("UPDATE public.app_users SET last_login_at = now() WHERE id = %s", (user_id,))

    def complete_approved_account(self, email: str, password_hash: str, approval_token: str, password_scheme: str = "argon2") -> str:
        try:
            with self._connect() as conn, conn.cursor() as cur:
                cur.execute("SELECT public.dlr_native_complete_approved_account(%s,%s,%s,%s) AS user_id",
                            (email.strip().lower(), password_hash, password_scheme, UUID(approval_token)))
                return str(cur.fetchone()["user_id"])
        except Exception as exc:
            _raise_native_operation_error(exc, "native account activation failed")

    def admin_user_account_action(self, caller_id: str, archive_id: str, target_user_id: str, action: str,
                                  password_hash: str | None = None, password_scheme: str = "argon2") -> None:
        try:
            with self._connect() as conn, conn.cursor() as cur:
                cur.execute("SELECT public.dlr_native_admin_user_account_action(%s,%s,%s,%s,%s,%s) AS success",
                            (UUID(caller_id), UUID(archive_id), UUID(target_user_id), action, password_hash, password_scheme))
                if not cur.fetchone()["success"]:
                    raise PostgresRuntimeError("native admin account action failed")
        except (PermissionError, LookupError, ValueError, PostgresRuntimeError):
            raise
        except Exception as exc:
            _raise_native_operation_error(exc, "native admin account action failed")

    def register_with_invite(self, email: str, password_hash: str, invite_code: str, password_scheme: str = "argon2") -> tuple[str, str]:
        try:
            with self._connect() as conn, conn.cursor() as cur:
                cur.execute("SELECT * FROM public.dlr_native_register_with_invite(%s,%s,%s,%s)",
                            (email.strip().lower(), password_hash, password_scheme, UUID(invite_code)))
                row = cur.fetchone()
                if not row:
                    raise ValueError("invalid invitation")
                return str(row["user_id"]), str(row["archive_role"])
        except ValueError:
            raise
        except Exception as exc:
            _raise_native_operation_error(exc, "native invitation registration failed")

    def confirm_user(self, user_id: str) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE public.app_users SET email_verified_at=COALESCE(email_verified_at,now()),is_disabled=false,updated_at=now() WHERE id=%s",
                (user_id,),
            )

    def link_google_user(self, email: str, google_subject: str) -> str:
        try:
            with self._connect() as conn, conn.cursor() as cur:
                cur.execute("SELECT public.dlr_native_link_google_identity(%s,%s) AS user_id",
                            (email.strip().lower(), google_subject))
                return str(cur.fetchone()["user_id"])
        except ValueError:
            raise
        except Exception as exc:
            _raise_native_operation_error(exc, "native Google identity link failed")
