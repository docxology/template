# `tests/storage/` — per-agent SQLite layer tests

Behavioral tests for `src/template_formal/storage/{schema,db,transaction}.py`
— the real, on-disk, per-agent SQLite persistence layer. Every test opens a
real file via pytest's `tmp_path` fixture (never `:memory:`, except through
the one explicitly-named test-only helper `open_fast_test_database`); no
mocking of `sqlite3` anywhere.

**Speed:** fast unit-test directory. Every test opens a fresh, tiny SQLite
file and performs a handful of statements — no simulation loops, no
parameter sweeps. The whole directory runs in well under a second.

## Files

| File | Lines | Covers | What it actually tests |
| --- | --- | --- | --- |
| [`test_storage_schema.py`](test_storage_schema.py) | 114 | ISC-8, ISC-9 | `Column.to_ddl_fragment()` (primary-key / not-null / nullable-by-default DDL fragments), `TableSchema.column_names()` order preservation, and `TableSchema.to_ddl()` — proven to be *real, executable* SQLite DDL by actually creating a table from it (twice, to prove `CREATE TABLE IF NOT EXISTS` idempotence). The back half asserts `Column`/`TableSchema`/`validate_sql_identifier` raise `ValueError` on SQL-injection-shaped names (`"id; DROP TABLE observations; --"`, embedded quotes, leading digits, spaces, hyphens) — a construction-time guard, not a sanitize-on-use one. |
| [`test_storage_db.py`](test_storage_db.py) | 146 | ISC-9, ISC-10, ISC-15 | `open_database` creates a real non-empty file on disk; `QueryBuilder[RowT]` round-trips a typed row through `insert`/`select_all`/`select_by`/`get_one`, returning `Result[..., StorageError]` rather than raising for every *expected* failure mode this file exercises — missing row (`kind == "not_found"`), unknown column on `select_by`/`insert` (also `"not_found"`), and a real `sqlite3.IntegrityError` from a NOT NULL violation (`kind == "constraint_violation"`). Also covers the runtime half of the isolation-level guard (`open_database(..., isolation_level="bogus")` raises `ValueError` — the paired static half is `tests/mypy_fixtures/bad_isolation_level.py`) and `open_fast_test_database`'s explicitly-named `:memory:` escape hatch. |
| [`test_storage_transaction.py`](test_storage_transaction.py) | 136 | ISC-11, ISC-12, ISC-13, ISC-14 | The affine-discipline `TransactionHandle`: a real rollback leaves a real SQLite file's row count and contents exactly as they were pre-transaction (verified by a real `SELECT`, not an assumption); commit persists rows visible via a real `SELECT`; reusing a consumed handle — `commit()` then `commit()` again, `commit()` then `rollback()`, `rollback()` then `commit()` — always raises `ConsumedHandleError`, covering every consuming-call pairing, not just a repeated identical call; the handle is proven frozen and slotted (`not hasattr(txn, "__dict__")`, attribute reassignment raises); and each of the three `Literal["deferred","immediate","exclusive"]` isolation levels round-trips through `begin_transaction`. |

## Why construction-time SQL-identifier validation is here, not just in `schema.py`'s docstring

`test_column_rejects_sql_injection_payload_as_name_at_construction` and its
sibling on `TableSchema` are the concrete proof that a malformed/malicious
column or table name can never reach raw SQL string interpolation in the
first place — `validate_sql_identifier` runs inside `__post_init__`, so the
guard is unconditional, not something call sites have to remember to apply.
