# `src/template_formal/storage/` — per-agent SQLite: typed schema, query builder, affine transactions

Every agent in the colony owns exactly one real, on-disk SQLite file — no
shared global database (per the ISA's `Out of Scope`). This package is the
whole storage stack for that file: a typed schema representation that
compiles to DDL, a `Result`-returning query builder over it, and a
single-use transaction handle.

## Modules

| File | Responsibility |
| --- | --- |
| `schema.py` | `Column`, `TableSchema`, `SqlType`, `SQL_IDENTIFIER_PATTERN`, `validate_sql_identifier`, `OBSERVATIONS_TABLE` — the typed schema representation and its identifier guard. |
| `db.py` | `Database`, `IsolationLevel`, `StorageError`, `QueryBuilder`, `open_database`, `open_fast_test_database`, `create_schema` — real SQLite connections and the typed query builder over them. |
| `transaction.py` | `TransactionHandle`, `ConsumedHandleError`, `begin_transaction` — the affine-discipline single-use transaction handle. |

## Public API (`__init__.py`)

```python
from template_formal.storage import (
    Database, IsolationLevel, QueryBuilder, StorageError,
    create_schema, open_database, open_fast_test_database,
    Column, OBSERVATIONS_TABLE, SQL_IDENTIFIER_PATTERN, SqlType, TableSchema,
    validate_sql_identifier,
    ConsumedHandleError, TransactionHandle, begin_transaction,
)
```

## Core invariant

**SQL identifiers are validated at construction, not at query time.**
Every raw SQL string this package builds interpolates a table or column
name directly — SQLite's `?` parameter binding covers *values*, never
*identifiers*. `Column.__post_init__` and `TableSchema.__post_init__` both
call `validate_sql_identifier` against `^[A-Za-z_][A-Za-z0-9_]*$`
(ISC-70): a name like `"id; DROP TABLE observations; --"` can never become
a `Column`/`TableSchema` instance in the first place, so it can never reach
an f-string. `db.py`'s `QueryBuilder` methods re-validate `self.table.name`
immediately before building each SQL string anyway, as a second,
defense-in-depth gate — a frozen dataclass's fields can still be
overwritten via `object.__setattr__` after construction, so the query
builder does not trust that a `TableSchema` reaching it was necessarily
built through its own constructor. The `column`/`values` keys `select_by`/
`insert` accept are separately checked for membership against
`self.table.column_names()` before either method builds a SQL string.

**The query builder returns `Result`, never raises, for expected failure
modes.** A missing row (`get_one`), an unknown column (`select_by`,
`insert`), or a constraint violation (`insert` against a `NOT NULL`/unique
column) all come back as `Err(StorageError(kind=..., message=...))`
(ISC-10) — `sqlite3.Error`/`sqlite3.IntegrityError` are still caught
explicitly at runtime; this is a *design* choice about which failures are
"expected" rather than a claim that mypy proves SQLite cannot raise.

**`:memory:` has exactly one, explicitly-named escape hatch.**
`open_database` always opens a real file; `open_fast_test_database` is the
sole `:memory:` path, named and docstringed as test-only so it can never be
mistaken for a durability claim (ISC-9, ISC-66 anti-criterion). Any test
asserting durability (rollback state, round-tripped rows across a reopen)
must use `open_database` against a real `tmp_path` file instead — see
`tests/storage/test_storage_transaction.py`'s rollback test for the
pattern.

**`TransactionHandle` is affine by runtime discipline, not by the type
system.** Python has no linear/affine type system, so nothing stops mypy
from accepting a second `handle.commit()` call. `TransactionHandle` is
`frozen(slots=True)` with a private `_consumed: bool` flag that `commit()`
and `rollback()` both check *before* issuing the underlying SQL call —
`_mark_consumed()` sets the flag first, so a partially-failed commit still
consumes the handle. A second call of either method raises
`ConsumedHandleError` (ISC-11, ISC-12, ISC-13) — this is a programmer-error
condition, not an expected outcome the caller should branch on, which is
why it raises instead of returning `Err`.

**Isolation level is a paired static+dynamic proof.** `IsolationLevel =
Literal["deferred", "immediate", "exclusive"]` (ISC-15); mypy --strict
rejects any other string literal at a call site
(`tests/mypy_fixtures/bad_isolation_level.py`), and `open_database` itself
re-checks membership against `_VALID_ISOLATION_LEVELS` at runtime for a
value that reached it through an untyped boundary
(`test_open_database_rejects_invalid_isolation_level_at_runtime`).
`Database.connection` is opened with `isolation_level=None` (manual-
transaction mode) specifically so `begin_transaction`'s `BEGIN
DEFERRED/IMMEDIATE/EXCLUSIVE` is the sole source of transaction
boundaries — sqlite3's own implicit-transaction heuristics are deliberately
disabled.

## Tests

| Test file | Covers |
| --- | --- |
| `tests/storage/test_storage_schema.py` | DDL fragment rendering, idempotent `CREATE TABLE IF NOT EXISTS` against a real file, and the SQL-identifier guard rejecting injection-shaped names for both `Column` and `TableSchema` (ISC-8, ISC-9, ISC-70). |
| `tests/storage/test_storage_db.py` | Real on-disk file creation, a full insert/select/get_one round trip through `QueryBuilder`, `Err` for a missing row / unknown column / constraint violation, the runtime isolation-level guard, and the `open_fast_test_database` `:memory:` escape hatch (ISC-9, ISC-10, ISC-15, ISC-66). |
| `tests/storage/test_storage_transaction.py` | A real rollback proven via `SELECT` against pre/post row counts on a `tmp_path` file, consumed-handle reuse raising on `commit()`→`commit()`, `commit()`→`rollback()`, and `rollback()`→`commit()`, `frozen`+`__slots__` enforcement, and all three isolation levels (ISC-11..15). |

The isolation-level negative control —
`tests/mypy_fixtures/bad_isolation_level.py` (ISC-15) — is type-checked by
`tests/test_mypy_oracle.py` against its own captured expected-error
substring (ISC-72), not this package's own test directory.

## ISA cross-reference

ISC-8 through ISC-15, ISC-66 (anti: no `:memory:`-backed durability claim),
ISC-70 (SQL-identifier construction-time guard). See `ISA.md` at the project
root for full criteria text.
