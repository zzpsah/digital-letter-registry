from __future__ import annotations

import pytest
from psycopg.sql import Composed, Identifier, SQL

from letter_registry.postgres_runtime import (
    ArchiveScopedPostgresTransport,
    PostgresTransport,
    _identifier,
)


def test_identifier_rejects_sql_injection() -> None:
    with pytest.raises(ValueError):
        _identifier("letters; DROP TABLE letters")


def test_identifier_allows_schema_object_names() -> None:
    assert isinstance(_identifier("letter_processing"), Identifier)


def test_where_builds_parameterized_equality_filters() -> None:
    where, values = PostgresTransport._where({"archive_id": "abc", "is_active": "true"})
    assert isinstance(where, Composed)
    assert values == ["abc", "true"]


def test_archive_scope_injected_on_reads_and_writes() -> None:
    class FakeTransport:
        def select(self, table, *, filters=None, columns="*"):
            return [{"table": table, "filters": filters, "columns": columns}]
        def insert(self, table, row, *, on_conflict=None):
            return {"table": table, "row": row}
        def upsert(self, table, row, *, on_conflict):
            return {"table": table, "row": row}
        def update(self, table, row, *, filters):
            return {"table": table, "filters": filters}
        def delete(self, table, *, filters):
            return [{"table": table, "filters": filters}]
        def rpc(self, function, params):
            return [{"function": function, "params": params}]

    scoped = ArchiveScopedPostgresTransport(FakeTransport(), "archive-1")
    assert scoped.select("letters")[0]["filters"] == {"archive_id": "archive-1"}
    assert scoped.insert("letters", {"title": "A"})["row"]["archive_id"] == "archive-1"
    assert scoped.update("letters", {"title": "B"}, filters={"id": "1"})["filters"]["archive_id"] == "archive-1"
    assert scoped.select("archives")[0]["filters"] is None


def test_archive_scope_rejects_cross_archive_access() -> None:
    class UnusedTransport:
        def select(self, *args, **kwargs):
            raise AssertionError("must reject before database call")
        def insert(self, *args, **kwargs):
            raise AssertionError("must reject before database call")
    scoped = ArchiveScopedPostgresTransport(UnusedTransport(), "archive-1")
    with pytest.raises(ValueError):
        scoped.select("letters", filters={"archive_id": "archive-2"})
    with pytest.raises(ValueError):
        scoped.insert("letters", {"archive_id": "archive-2"})
