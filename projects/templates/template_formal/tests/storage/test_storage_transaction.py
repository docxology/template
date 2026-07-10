"""Behavioral tests for the affine-discipline TransactionHandle (ISC-11..14)."""

from __future__ import annotations

import sqlite3

import pytest

from template_formal.storage.db import Database, QueryBuilder, create_schema, open_database
from template_formal.storage.schema import OBSERVATIONS_TABLE
from template_formal.storage.transaction import ConsumedHandleError, begin_transaction
from template_formal.types.result import Ok


def _fresh_observations_db(tmp_path) -> Database:  # type: ignore[no-untyped-def]
    database = open_database(tmp_path / "agent.sqlite3", isolation_level="deferred")
    create_schema(database, OBSERVATIONS_TABLE)
    return database


def _count_rows(connection: sqlite3.Connection) -> int:
    cursor = connection.execute("SELECT COUNT(*) FROM observations")
    (count,) = cursor.fetchone()
    return int(count)


def test_rollback_leaves_a_real_sqlite_file_in_its_pre_transaction_state(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = _fresh_observations_db(tmp_path)

    # Seed one committed row, outside any transaction under test.
    seed_txn = begin_transaction(database)
    database.connection.execute("INSERT INTO observations (key, value) VALUES (?, ?)", ("baseline", 1.0))
    assert isinstance(seed_txn.commit(), Ok)

    pre_rollback_count = _count_rows(database.connection)
    assert pre_rollback_count == 1

    txn = begin_transaction(database)
    database.connection.execute("INSERT INTO observations (key, value) VALUES (?, ?)", ("should_vanish", 2.0))
    # Real SELECT inside the open transaction sees the uncommitted insert.
    assert _count_rows(database.connection) == 2

    rollback_result = txn.rollback()
    assert isinstance(rollback_result, Ok)

    # Real SELECT after rollback proves the DB is back to its pre-transaction state.
    post_rollback_count = _count_rows(database.connection)
    assert post_rollback_count == pre_rollback_count == 1

    cursor = database.connection.execute("SELECT key FROM observations")
    remaining_keys = [row["key"] for row in cursor.fetchall()]
    assert remaining_keys == ["baseline"]

    database.connection.close()


def test_commit_persists_rows_visible_via_real_select(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = _fresh_observations_db(tmp_path)
    builder = QueryBuilder(
        database=database,
        table=OBSERVATIONS_TABLE,
        row_factory=lambda row: (row["id"], row["key"], row["value"]),
    )

    txn = begin_transaction(database)
    inserted = builder.insert({"key": "persisted", "value": 3.5})
    assert isinstance(inserted, Ok)
    commit_result = txn.commit()
    assert isinstance(commit_result, Ok)

    assert _count_rows(database.connection) == 1
    database.connection.close()


def test_reusing_a_consumed_transaction_handle_raises_consumed_handle_error(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = _fresh_observations_db(tmp_path)
    txn = begin_transaction(database)

    assert isinstance(txn.commit(), Ok)

    with pytest.raises(ConsumedHandleError):
        txn.commit()

    database.connection.close()


def test_commit_then_rollback_on_same_handle_raises(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """ISC-13: commit() followed by ANY second consuming call must raise, never
    silently succeed or double-write — not merely a repeated commit()."""
    database = _fresh_observations_db(tmp_path)
    txn = begin_transaction(database)

    assert isinstance(txn.commit(), Ok)

    with pytest.raises(ConsumedHandleError):
        txn.rollback()

    database.connection.close()


def test_rollback_then_reuse_also_raises(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = _fresh_observations_db(tmp_path)
    txn = begin_transaction(database)

    assert isinstance(txn.rollback(), Ok)

    with pytest.raises(ConsumedHandleError):
        txn.commit()

    database.connection.close()


def test_transaction_handle_is_frozen_and_uses_slots(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = _fresh_observations_db(tmp_path)
    txn = begin_transaction(database)

    assert not hasattr(txn, "__dict__")

    with pytest.raises((AttributeError, TypeError)):
        txn.txn_id = txn.txn_id  # type: ignore[misc]

    txn.rollback()
    database.connection.close()


@pytest.mark.parametrize("isolation_level", ["deferred", "immediate", "exclusive"])
def test_begin_transaction_honors_each_valid_isolation_level(tmp_path, isolation_level) -> None:  # type: ignore[no-untyped-def]
    db_path = tmp_path / f"agent_{isolation_level}.sqlite3"
    database = open_database(db_path, isolation_level=isolation_level)
    create_schema(database, OBSERVATIONS_TABLE)

    txn = begin_transaction(database)
    assert txn.isolation_level == isolation_level
    assert txn.rollback().tag == "ok"

    database.connection.close()
