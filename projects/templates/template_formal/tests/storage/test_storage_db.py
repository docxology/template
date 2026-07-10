"""Behavioral tests for the real on-disk SQLite query builder (ISC-9, ISC-10, ISC-15).

Every test that makes a claim about durable per-agent state opens a real
file via ``tmp_path`` (per ISC-66 / Out of Scope: ``:memory:`` is only
used through the explicitly-named, test-only
``open_fast_test_database`` helper, never as a stand-in for durability).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

import pytest

from template_formal.storage.db import (
    Database,
    QueryBuilder,
    StorageError,
    create_schema,
    open_database,
    open_fast_test_database,
)
from template_formal.storage.schema import OBSERVATIONS_TABLE
from template_formal.types.result import Err, Ok


@dataclass(frozen=True, slots=True)
class ObservationRow:
    """A typed row for the ``observations`` table — the ``RowT`` in tests."""

    id: int
    key: str
    value: float


def _observation_from_sqlite_row(row: sqlite3.Row) -> ObservationRow:
    return ObservationRow(id=row["id"], key=row["key"], value=row["value"])


def _fresh_observations_db(tmp_path) -> Database:  # type: ignore[no-untyped-def]
    database = open_database(tmp_path / "agent.sqlite3", isolation_level="deferred")
    create_schema(database, OBSERVATIONS_TABLE)
    return database


def test_open_database_creates_a_real_file_on_disk(tmp_path) -> None:  # type: ignore[no-untyped-def]
    db_path = tmp_path / "agent.sqlite3"
    assert not db_path.exists()
    database = _fresh_observations_db(tmp_path)
    assert db_path.exists()
    assert db_path.stat().st_size > 0
    database.connection.close()


def test_query_builder_round_trips_a_real_row(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = _fresh_observations_db(tmp_path)
    builder = QueryBuilder(database=database, table=OBSERVATIONS_TABLE, row_factory=_observation_from_sqlite_row)

    inserted = builder.insert({"key": "temperature", "value": 21.5})
    database.connection.commit()

    assert isinstance(inserted, Ok)
    rowid = inserted.value

    all_rows = builder.select_all()
    assert isinstance(all_rows, Ok)
    assert len(all_rows.value) == 1
    assert all_rows.value[0] == ObservationRow(id=rowid, key="temperature", value=21.5)

    by_key = builder.select_by("key", "temperature")
    assert isinstance(by_key, Ok)
    assert by_key.value[0].value == 21.5

    one = builder.get_one("key", "temperature")
    assert isinstance(one, Ok)
    assert one.value.key == "temperature"

    database.connection.close()


def test_get_one_missing_row_returns_err_not_found(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = _fresh_observations_db(tmp_path)
    builder = QueryBuilder(database=database, table=OBSERVATIONS_TABLE, row_factory=_observation_from_sqlite_row)

    result = builder.get_one("key", "does-not-exist")

    assert isinstance(result, Err)
    assert isinstance(result.error, StorageError)
    assert result.error.kind == "not_found"
    database.connection.close()


def test_select_by_unknown_column_returns_err_without_touching_sqlite(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = _fresh_observations_db(tmp_path)
    builder = QueryBuilder(database=database, table=OBSERVATIONS_TABLE, row_factory=_observation_from_sqlite_row)

    result = builder.select_by("nonexistent_column", "x")

    assert isinstance(result, Err)
    assert result.error.kind == "not_found"
    database.connection.close()


def test_insert_unknown_column_returns_err(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = _fresh_observations_db(tmp_path)
    builder = QueryBuilder(database=database, table=OBSERVATIONS_TABLE, row_factory=_observation_from_sqlite_row)

    result = builder.insert({"not_a_real_column": 1})

    assert isinstance(result, Err)
    assert result.error.kind == "not_found"
    database.connection.close()


def test_insert_constraint_violation_returns_err_never_raises(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Omitting a NOT NULL column triggers a real sqlite3.IntegrityError, caught as Err."""
    database = _fresh_observations_db(tmp_path)
    builder = QueryBuilder(database=database, table=OBSERVATIONS_TABLE, row_factory=_observation_from_sqlite_row)

    result = builder.insert({"key": "missing_value_column"})

    assert isinstance(result, Err)
    assert result.error.kind == "constraint_violation"
    database.connection.close()


def test_open_database_rejects_invalid_isolation_level_at_runtime(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Static rejection is proved by tests/mypy_fixtures/bad_isolation_level.py; this is the
    runtime backstop for a value that reached this function through an untyped boundary."""
    with pytest.raises(ValueError):
        open_database(tmp_path / "agent.sqlite3", isolation_level="bogus")  # type: ignore[arg-type]


def test_open_fast_test_database_is_a_real_sqlite_connection_but_not_durable() -> None:
    database = open_fast_test_database()
    create_schema(database, OBSERVATIONS_TABLE)
    builder = QueryBuilder(database=database, table=OBSERVATIONS_TABLE, row_factory=_observation_from_sqlite_row)

    inserted = builder.insert({"key": "ephemeral", "value": 1.0})
    assert isinstance(inserted, Ok)

    all_rows = builder.select_all()
    assert isinstance(all_rows, Ok)
    assert len(all_rows.value) == 1
    database.connection.close()
