"""Typed failure receipts and durable state after real SQLite connection loss."""

from __future__ import annotations

from pathlib import Path

import pytest

from template_formal.storage.db import QueryBuilder, create_schema, open_database
from template_formal.storage.schema import OBSERVATIONS_TABLE
from template_formal.storage.transaction import ConsumedHandleError, begin_transaction
from template_formal.types.result import Err, Ok


def test_closed_query_builder_returns_connection_errors_without_changing_durable_rows(tmp_path: Path) -> None:
    database = open_database(tmp_path / "agent.sqlite3")
    create_schema(database, OBSERVATIONS_TABLE)
    builder = QueryBuilder(
        database=database,
        table=OBSERVATIONS_TABLE,
        row_factory=lambda row: (row["key"], row["value"]),
    )
    assert isinstance(builder.insert({"key": "baseline", "value": 1.0}), Ok)
    database.connection.commit()
    database.connection.close()

    results = (
        builder.select_all(),
        builder.select_by("key", "baseline"),
        builder.get_one("key", "baseline"),
        builder.insert({"key": "must_not_persist", "value": 2.0}),
    )
    for result in results:
        assert isinstance(result, Err)
        assert result.error.kind == "connection_error"
        assert "closed" in result.error.message.lower()

    reopened = open_database(database.path)
    try:
        rows = reopened.connection.execute("SELECT key, value FROM observations").fetchall()
        assert [tuple(row) for row in rows] == [("baseline", 1.0)]
    finally:
        reopened.connection.close()


@pytest.mark.parametrize("operation", ["commit", "rollback"])
def test_connection_loss_consumes_transaction_and_preserves_committed_state(tmp_path: Path, operation: str) -> None:
    database = open_database(tmp_path / "agent.sqlite3")
    create_schema(database, OBSERVATIONS_TABLE)
    database.connection.execute("INSERT INTO observations (key, value) VALUES (?, ?)", ("baseline", 1.0))
    transaction = begin_transaction(database)
    database.connection.execute("INSERT INTO observations (key, value) VALUES (?, ?)", ("uncommitted", 2.0))
    assert database.connection.execute("SELECT COUNT(*) FROM observations").fetchone()[0] == 2
    database.connection.close()

    result = transaction.commit() if operation == "commit" else transaction.rollback()
    assert isinstance(result, Err)
    assert result.error.kind == "connection_error"
    assert "closed" in result.error.message.lower()
    with pytest.raises(ConsumedHandleError):
        transaction.commit()
    with pytest.raises(ConsumedHandleError):
        transaction.rollback()

    reopened = open_database(database.path)
    try:
        rows = reopened.connection.execute("SELECT key, value FROM observations").fetchall()
        assert [tuple(row) for row in rows] == [("baseline", 1.0)]
    finally:
        reopened.connection.close()
