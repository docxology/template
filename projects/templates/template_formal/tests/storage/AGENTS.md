# `tests/storage/` — Agent Guide

Tests `src/template_formal/storage/{schema,db,transaction}.py`. See
[`README.md`](README.md) for the per-file test breakdown.

## Contract

- **Speed:** fast. Every test in this directory is expected to complete in
  milliseconds — a real but tiny on-disk SQLite file per test via
  `tmp_path`. If a change here makes any single test take more than a
  fraction of a second, that is itself a regression signal, not "storage
  tests are just slow."
- **No `:memory:` as a stand-in for durability.** `open_fast_test_database`
  is the one, explicitly-named exception (used only in
  `test_storage_db.py`'s last test) — every other test opens a real file
  via `tmp_path` and asserts against it, because the whole point of this
  module is that per-agent state survives on disk (see Out of Scope in
  `../../ISA.md`: no `:memory:`-only test-only path may substitute for the
  real durability claim).
- **`QueryBuilder` never raises for expected failure modes.** If you add a
  new expected-failure path (another constraint type, another malformed
  input), it must return `Err(StorageError(kind=...))`, and the test must
  assert the specific `kind`, not merely `isinstance(result, Err)`.
- **New `TransactionHandle`-consuming methods must be added to the
  cross-product of consumed-handle tests.** `test_storage_transaction.py`
  currently proves commit→commit, commit→rollback, and rollback→commit all
  raise `ConsumedHandleError` — a new consuming method needs its own pairing
  with both `commit` and `rollback`, not just a same-method-twice check.
- **SQL identifiers are validated at construction, not at use.** Any new
  `Column`/`TableSchema`-like construct must call `validate_sql_identifier`
  in `__post_init__`; do not add a code path that interpolates a
  caller-supplied name into raw SQL without that guard.
- **Isolation levels stay a closed `Literal`.** If you add a fourth SQLite
  isolation mode, extend the `Literal` in `storage/transaction.py`/`db.py`,
  add it to the parametrized isolation-level tests here, and update
  `tests/mypy_fixtures/bad_isolation_level.py`'s bound error substring in
  `tests/test_mypy_oracle.py` (the literal member list appears verbatim in
  mypy's error text).

## Running just this directory

```bash
uv run pytest projects/templates/template_formal/tests/storage/ -v
```
