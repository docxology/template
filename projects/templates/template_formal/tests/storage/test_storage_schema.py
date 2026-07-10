"""Behavioral tests for typed schema-to-DDL generation (ISC-8, ISC-9)."""

from __future__ import annotations

import sqlite3

import pytest

from template_formal.storage.schema import Column, OBSERVATIONS_TABLE, TableSchema, validate_sql_identifier


def test_column_to_ddl_fragment_marks_primary_key() -> None:
    column = Column("id", "INTEGER", primary_key=True)
    assert column.to_ddl_fragment() == "id INTEGER PRIMARY KEY"


def test_column_to_ddl_fragment_marks_not_null() -> None:
    column = Column("key", "TEXT", nullable=False)
    assert column.to_ddl_fragment() == "key TEXT NOT NULL"


def test_column_to_ddl_fragment_nullable_by_default() -> None:
    column = Column("note", "TEXT")
    assert column.to_ddl_fragment() == "note TEXT"


def test_table_schema_column_names_preserve_declaration_order() -> None:
    assert OBSERVATIONS_TABLE.column_names() == ("id", "key", "value")


def test_table_schema_to_ddl_is_real_executable_sqlite(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The generated DDL isn't just a string — it must actually create a table."""
    db_path = tmp_path / "schema_ddl.sqlite3"
    connection = sqlite3.connect(str(db_path))
    connection.execute(OBSERVATIONS_TABLE.to_ddl())
    connection.commit()

    cursor = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (OBSERVATIONS_TABLE.name,),
    )
    row = cursor.fetchone()
    connection.close()

    assert row is not None
    assert row[0] == "observations"


def test_table_schema_to_ddl_is_idempotent(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """CREATE TABLE IF NOT EXISTS must be safe to run twice against the same file."""
    db_path = tmp_path / "schema_idempotent.sqlite3"
    connection = sqlite3.connect(str(db_path))
    connection.execute(OBSERVATIONS_TABLE.to_ddl())
    connection.execute(OBSERVATIONS_TABLE.to_ddl())
    connection.commit()
    connection.close()


def test_custom_table_schema_ddl_shape() -> None:
    custom = TableSchema(
        name="pheromone_readings",
        columns=(
            Column("id", "INTEGER", primary_key=True),
            Column("cell", "TEXT", nullable=False),
            Column("concentration", "REAL", nullable=False),
        ),
    )
    ddl = custom.to_ddl()
    assert ddl.startswith("CREATE TABLE IF NOT EXISTS pheromone_readings (")
    assert "cell TEXT NOT NULL" in ddl
    assert "concentration REAL NOT NULL" in ddl


def test_observations_table_schema_still_passes_the_identifier_guard() -> None:
    """The shipped default schema must remain constructible after the guard lands."""
    assert OBSERVATIONS_TABLE.name == "observations"
    assert OBSERVATIONS_TABLE.column_names() == ("id", "key", "value")


def test_column_rejects_sql_injection_payload_as_name_at_construction() -> None:
    """A malformed/malicious column name must raise before it can reach raw SQL."""
    with pytest.raises(ValueError, match="invalid SQL identifier"):
        Column("id; DROP TABLE observations; --", "INTEGER")


def test_table_schema_rejects_sql_injection_payload_as_name_at_construction() -> None:
    """A malformed/malicious table name must raise before it can reach raw SQL."""
    with pytest.raises(ValueError, match="invalid SQL identifier"):
        TableSchema(
            name="observations; DROP TABLE observations; --",
            columns=(Column("id", "INTEGER", primary_key=True),),
        )


@pytest.mark.parametrize(
    "bad_name",
    [
        "",
        "1leading_digit",
        "has space",
        "has-hyphen",
        "quote'injection",
        "observations; DROP TABLE observations; --",
        "id) VALUES (1); --",
    ],
)
def test_validate_sql_identifier_rejects_malformed_names(bad_name: str) -> None:
    with pytest.raises(ValueError, match="invalid SQL identifier"):
        validate_sql_identifier(bad_name, what="column name")


@pytest.mark.parametrize("good_name", ["id", "_private", "observation_value", "A1"])
def test_validate_sql_identifier_accepts_plain_identifiers(good_name: str) -> None:
    validate_sql_identifier(good_name, what="column name")  # must not raise
