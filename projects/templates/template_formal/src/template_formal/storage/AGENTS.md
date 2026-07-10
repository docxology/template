# `src/template_formal/storage/` — Agent Guide

One real, on-disk SQLite file per agent. Typed schema-to-DDL, a
`Result`-returning query builder, and an affine-discipline transaction
handle. See `README.md` for the full contract.

**Contents.** `schema.py` — `Column`/`TableSchema`/`validate_sql_identifier`/
`OBSERVATIONS_TABLE`. `db.py` — `Database`/`IsolationLevel`/`StorageError`/
`QueryBuilder`/`open_database`/`open_fast_test_database`/`create_schema`.
`transaction.py` — `TransactionHandle`/`ConsumedHandleError`/
`begin_transaction`.

**Contract.** Never build a raw SQL string from a table/column name that
hasn't passed `validate_sql_identifier` — `Column`/`TableSchema` already
enforce this at construction (`__post_init__`), so a new call site should
route through those types rather than re-deriving names as bare strings. Use
`open_database` against a real path for anything that claims durability;
`open_fast_test_database`'s `:memory:` connection is test-only and must
never back a rollback/reopen assertion (ISC-66). Every `TransactionHandle`
method that commits/rolls back must check `_consumed` and raise
`ConsumedHandleError` on reuse *before* touching the connection — don't add
a new consuming method that skips `_mark_consumed()`. `QueryBuilder` methods
return `Result`, never raise, for a missing row / unknown column /
constraint violation — a new method following that pattern should catch
`sqlite3.Error`/`sqlite3.IntegrityError` explicitly rather than letting them
propagate.

See the project [`AGENTS.md`](../../../AGENTS.md) and [`ISA.md`](../../../ISA.md)
for the full map and ISC-1..92 criteria.
