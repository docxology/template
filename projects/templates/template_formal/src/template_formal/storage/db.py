"""Real, per-agent, on-disk SQLite access — a typed query builder over it.

Every agent in the colony owns exactly one SQLite file on disk (see
``Out of Scope``: this is a decentralization-*shaped* simulation, real
local files, no shared global database). :func:`open_database` opens that
file; there is exactly one documented ``:memory:`` escape hatch,
:func:`open_fast_test_database`, named and docstringed as test-only so it
can never be mistaken for a durability claim (per repo Anti-criterion
ISC-66: no test may use ``:memory:`` to support a claim about durable
per-agent state).

:class:`QueryBuilder` never raises for the failure modes a caller should
expect from ordinary use — a missing row, a violated ``UNIQUE``/``NOT
NULL`` constraint — those come back as ``Err(StorageError(...))`` values
via :class:`~template_formal.types.result.Result`. This is a *design*
choice about which failures are "expected" versus "programmer error", not
a claim that mypy proves SQLite operations cannot raise; ``sqlite3.Error``
subclasses are still caught explicitly, at runtime, by the methods below.

Every method below interpolates ``self.table.name`` directly into a raw SQL
string — SQLite's parameter-binding syntax (``?``) covers values, never
identifiers. ``TableSchema.__post_init__`` already rejects a malformed
table name at construction time (``storage/schema.py``), but the methods
below re-validate ``self.table.name`` against
:func:`~template_formal.storage.schema.validate_sql_identifier`
immediately before building the SQL string anyway, as a defense-in-depth
second gate: a frozen dataclass's fields can still be overwritten via
``object.__setattr__`` after construction, and the query builder should
not trust that a ``TableSchema`` reaching it was necessarily built through
its own constructor. The ``column``/``values`` keys accepted by
``select_by``/``insert`` are checked for membership against
``self.table.column_names()`` first, which already guarantees they equal
one of those construction-time-validated column names before either
method ever builds a SQL string from them.

The isolation level a caller may request is restricted to
``Literal["deferred", "immediate", "exclusive"]`` (ISC-15) — mypy --strict
rejects any other string at the call site (see
``tests/mypy_fixtures/bad_isolation_level.py``). A runtime membership
check backs this up because an untyped caller (e.g. a value read from an
external config file at a boundary mypy cannot see through) could still
reach this function with an arbitrary ``str``; the ``Literal`` type gives
edit-time/CI-time safety only, never a runtime guarantee.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Generic, Literal, Mapping, TypeVar

from template_formal.storage.schema import TableSchema, validate_sql_identifier
from template_formal.types.result import Err, Ok, Result

IsolationLevel = Literal["deferred", "immediate", "exclusive"]

_VALID_ISOLATION_LEVELS: frozenset[str] = frozenset({"deferred", "immediate", "exclusive"})

RowT = TypeVar("RowT")


@dataclass(frozen=True, slots=True)
class StorageError:
    """A typed, expected storage failure — never raised, always returned as ``Err``.

    Attributes:
        kind: A coarse classification of the failure.
        message: A human-readable detail string (e.g. the underlying
            ``sqlite3.Error`` message), for logging/debugging only.
    """

    kind: Literal["not_found", "constraint_violation", "connection_error"]
    message: str


@dataclass(frozen=True, slots=True)
class Database:
    """A handle to one agent's real, on-disk SQLite file.

    Attributes:
        path: The on-disk file path (or ``:memory:`` only via
            :func:`open_fast_test_database`).
        isolation_level: The default transaction isolation level this
            database's transactions begin with (see
            ``storage/transaction.py``).
        connection: The underlying ``sqlite3.Connection``, opened in
            manual-transaction mode (``isolation_level=None``) so that
            ``BEGIN DEFERRED/IMMEDIATE/EXCLUSIVE`` issued by
            ``begin_transaction`` is the sole source of transaction
            boundaries — sqlite3's own implicit-transaction heuristics
            are deliberately disabled.
    """

    path: Path
    isolation_level: IsolationLevel
    connection: sqlite3.Connection


def open_database(path: Path, *, isolation_level: IsolationLevel = "deferred") -> Database:
    """Open (creating if absent) a real on-disk SQLite file for one agent.

    Args:
        path: Filesystem path to the agent's SQLite file. Never
            ``:memory:`` — use :func:`open_fast_test_database` for that.
        isolation_level: The default isolation level future transactions
            on this database begin with.

    Returns:
        A :class:`Database` wrapping an open connection.

    Raises:
        ValueError: If ``isolation_level`` is not one of the three
            documented literals. Reachable only if a caller bypasses
            mypy's static check (e.g. via ``# type: ignore`` or an
            untyped boundary) — this is the runtime half of ISC-15's
            paired static+dynamic proof.
    """
    if isolation_level not in _VALID_ISOLATION_LEVELS:
        raise ValueError(f"invalid isolation level: {isolation_level!r}")
    connection = sqlite3.connect(str(path), isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return Database(path=path, isolation_level=isolation_level, connection=connection)


def open_fast_test_database() -> Database:
    """Open an in-process ``:memory:`` database — fast-test-only, never durable.

    This is the single documented ``:memory:`` escape hatch in this
    module (per ``Out of Scope`` / ISC-66). It exists for tests that need
    a real ``sqlite3`` connection but make no claim about data surviving
    process exit — anything that *does* claim durability (rollback state,
    round-tripped rows across a reopen) must use :func:`open_database`
    against a real ``tmp_path`` file instead.
    """
    connection = sqlite3.connect(":memory:", isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return Database(path=Path(":memory:"), isolation_level="deferred", connection=connection)


def create_schema(database: Database, table: TableSchema) -> None:
    """Create ``table`` in ``database`` from its typed DDL (idempotent)."""
    database.connection.execute(table.to_ddl())
    database.connection.commit()


@dataclass(frozen=True, slots=True)
class QueryBuilder(Generic[RowT]):
    """A typed query builder over one table, returning ``Result`` never raising.

    Attributes:
        database: The :class:`Database` to query.
        table: The typed schema describing the table being queried; also
            used to reject queries against unknown columns before any
            SQL is issued.
        row_factory: Converts one ``sqlite3.Row`` into a ``RowT`` value
            (e.g. a frozen dataclass), keeping row-shape knowledge in one
            typed place instead of scattered tuple-indexing at call sites.
    """

    database: Database
    table: TableSchema
    row_factory: Callable[[sqlite3.Row], RowT]

    def select_all(self) -> Result[list[RowT], StorageError]:
        """Return every row in the table, or ``Err`` on a connection failure."""
        validate_sql_identifier(self.table.name, what="table name")
        try:
            cursor = self.database.connection.execute(f"SELECT * FROM {self.table.name}")
            rows = [self.row_factory(row) for row in cursor.fetchall()]
        except sqlite3.Error as exc:
            return Err(StorageError(kind="connection_error", message=str(exc)))
        return Ok(rows)

    def select_by(self, column: str, value: object) -> Result[list[RowT], StorageError]:
        """Return rows where ``column == value``.

        An unknown ``column`` (not part of ``self.table``'s schema) is an
        expected failure mode, not a crash: it comes back as ``Err``, not
        a ``KeyError``.
        """
        if column not in self.table.column_names():
            return Err(
                StorageError(kind="not_found", message=f"unknown column {column!r} on table {self.table.name!r}")
            )
        validate_sql_identifier(self.table.name, what="table name")
        try:
            cursor = self.database.connection.execute(f"SELECT * FROM {self.table.name} WHERE {column} = ?", (value,))
            rows = [self.row_factory(row) for row in cursor.fetchall()]
        except sqlite3.Error as exc:
            return Err(StorageError(kind="connection_error", message=str(exc)))
        return Ok(rows)

    def get_one(self, column: str, value: object) -> Result[RowT, StorageError]:
        """Return the single row where ``column == value``, or ``Err(not_found)``."""
        found = self.select_by(column, value)
        match found:
            case Ok(value=rows):
                if not rows:
                    return Err(StorageError(kind="not_found", message=f"no row with {column}={value!r}"))
                return Ok(rows[0])
            case Err(error=error):
                return Err(error)

    def insert(self, values: Mapping[str, object]) -> Result[int, StorageError]:
        """Insert one row; return its ``rowid``, or ``Err`` on constraint violation.

        Args:
            values: Column name -> value for the new row. Every key must
                name a column of ``self.table``.

        Returns:
            ``Ok(rowid)`` on success. ``Err(StorageError(kind="constraint_violation", ...))``
            on a ``sqlite3.IntegrityError`` (e.g. a ``NOT NULL`` or
            uniqueness violation) — this is an expected failure mode, not
            a bug, so it is never raised to the caller.
        """
        unknown = set(values) - set(self.table.column_names())
        if unknown:
            return Err(
                StorageError(
                    kind="not_found", message=f"unknown column(s) {sorted(unknown)!r} on table {self.table.name!r}"
                )
            )
        validate_sql_identifier(self.table.name, what="table name")
        columns = ", ".join(values.keys())
        placeholders = ", ".join("?" for _ in values)
        try:
            cursor = self.database.connection.execute(
                f"INSERT INTO {self.table.name} ({columns}) VALUES ({placeholders})",
                tuple(values.values()),
            )
        except sqlite3.IntegrityError as exc:
            return Err(StorageError(kind="constraint_violation", message=str(exc)))
        except sqlite3.Error as exc:
            return Err(StorageError(kind="connection_error", message=str(exc)))
        return Ok(int(cursor.lastrowid or 0))
