"""Agent-local storage schema, framed as a functor ``Schema -> Set``.

Spivak's functorial data migration (Fong & Spivak, *An Invitation to
Applied Category Theory*) treats a database schema as a category — tables
are objects, foreign keys are morphisms — and an instance of that schema
as a functor from the schema category into **Set**, sending each table to
the set of its rows and each foreign key to the corresponding function
between row-sets. The dataclasses below play the role of that schema
category's objects: :class:`Column` is a typed field of a table, and
:class:`TableSchema` is a table's full column list plus the SQL DDL it
compiles to.

This is stated here as a *framing*, not a formal result — nothing in this
module is checked against Spivak's functoriality laws by mypy, a test, or
a proof assistant. Treat the analogy as a design lens (a schema really is
data with structure, and an instance really is a Set-valued assignment to
that structure) rather than a load-bearing mathematical claim. See
``manuscript`` §"What mypy proves" for the line between analogy and proof.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

SqlType = Literal["INTEGER", "REAL", "TEXT", "BLOB"]
"""The SQLite storage classes this schema layer is willing to emit DDL for."""

SQL_IDENTIFIER_PATTERN: re.Pattern[str] = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
"""The only shape a table or column name may take in this package.

:meth:`TableSchema.to_ddl` and every query in ``storage/db.py`` interpolate
``Column.name``/``TableSchema.name`` (and, in ``db.py``, a caller-supplied
column string checked for membership against those same names) directly
into raw SQL strings — SQLite's parameter-binding syntax (``?``) covers
*values*, never *identifiers*. Constraining the identifier's character set
at construction time is what makes that interpolation safe: a name such as
``"x; DROP TABLE observations; --"`` can never reach a raw SQL string in
the first place, because it can never become a :class:`Column` or
:class:`TableSchema` instance to begin with.
"""


def validate_sql_identifier(name: str, *, what: str) -> None:
    """Raise :class:`ValueError` unless ``name`` is a plain SQL identifier.

    Args:
        name: The candidate table or column name.
        what: A short label (e.g. ``"column name"``) used only to make the
            raised error message legible about which identifier failed.

    Raises:
        ValueError: If ``name`` does not match :data:`SQL_IDENTIFIER_PATTERN`
            — this is a construction-time guard, not a runtime-reachable
            code path for well-formed callers; it exists specifically to
            reject a malicious/malformed identifier before it can ever be
            interpolated into a raw SQL string.
    """
    if not SQL_IDENTIFIER_PATTERN.match(name):
        raise ValueError(f"invalid SQL identifier for {what}: {name!r} (must match {SQL_IDENTIFIER_PATTERN.pattern!r})")


@dataclass(frozen=True, slots=True)
class Column:
    """One typed column of a :class:`TableSchema`.

    Attributes:
        name: The column's SQL identifier. Validated against
            :data:`SQL_IDENTIFIER_PATTERN` in ``__post_init__`` — a
            malformed name (e.g. containing ``"; DROP TABLE"``) raises
            :class:`ValueError` at construction, before it can ever reach
            the raw SQL interpolation in :meth:`to_ddl_fragment` or
            ``storage/db.py``.
        sql_type: One of SQLite's storage classes (see :data:`SqlType`).
        primary_key: Whether this column is the table's primary key.
        nullable: Whether ``NULL`` is a legal value. Ignored (always
            effectively non-null) when ``primary_key`` is ``True``, since
            SQLite integer primary keys cannot be ``NULL``.
    """

    name: str
    sql_type: SqlType
    primary_key: bool = False
    nullable: bool = True

    def __post_init__(self) -> None:
        validate_sql_identifier(self.name, what="column name")

    def to_ddl_fragment(self) -> str:
        """Render this column as one comma-separated fragment of a ``CREATE TABLE``."""
        parts = [self.name, self.sql_type]
        if self.primary_key:
            parts.append("PRIMARY KEY")
        elif not self.nullable:
            parts.append("NOT NULL")
        return " ".join(parts)


@dataclass(frozen=True, slots=True)
class TableSchema:
    """A table's full column list, plus typed DDL generation.

    Generating DDL from this single typed representation — rather than
    hand-writing ``CREATE TABLE`` strings at each call site — is what
    ISC-9 requires: one source of truth for a table's shape, reused by
    both schema creation and the query builder's column validation.
    """

    name: str
    columns: tuple[Column, ...]

    def __post_init__(self) -> None:
        validate_sql_identifier(self.name, what="table name")

    def column_names(self) -> tuple[str, ...]:
        """Return this table's column names, in declaration order."""
        return tuple(column.name for column in self.columns)

    def to_ddl(self) -> str:
        """Render a full, idempotent ``CREATE TABLE IF NOT EXISTS`` statement."""
        fragments = ", ".join(column.to_ddl_fragment() for column in self.columns)
        return f"CREATE TABLE IF NOT EXISTS {self.name} ({fragments})"


OBSERVATIONS_TABLE = TableSchema(
    name="observations",
    columns=(
        Column("id", "INTEGER", primary_key=True),
        Column("key", "TEXT", nullable=False),
        Column("value", "REAL", nullable=False),
    ),
)
"""The default per-agent local schema: a flat key/value observation log.

Deliberately small — this template's storage layer exists to demonstrate
typed schema-to-DDL generation, a typed query builder, and affine
transaction handles, not a realistic ant-colony data model. A forking
project is expected to add its own :class:`TableSchema` instances beside
this one.
"""
