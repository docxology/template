# tests/helpers/ — Shared Test Utility Modules

## Purpose

Plain Python helper modules imported by tests in `tests/integration/` and `tests/infra_tests/`. **Not** pytest fixtures (those live in `conftest.py`) and **not** collected by pytest itself — pytest does not run any tests from this directory.

## Files

- `__init__.py` — empty marker so the directory is importable as `tests.helpers`
- `log_parser.py` — parses structured (JSON-line) log output produced by scripts when `STRUCTURED_LOGGING=true`. Provides `LogEntry` (frozen dataclass), `parse_structured_logs`, `filter_by_level`, `filter_by_logger`, `contains_message` for typed assertions in `tests/integration/test_logging.py` and `tests/integration/test_full_pipeline.py`

## Public API

```python
from tests.helpers.log_parser import (
    LogEntry,
    parse_structured_logs,
    filter_by_level,
    filter_by_logger,
    contains_message,
)
```

## Notes

- This directory is not a test package — it has no `test_*.py` files. pytest discovery skips it because nothing matches the test pattern.
- If you add new shared helpers, mirror this convention: pure Python module + clear docstring + no pytest fixtures.

## See Also

- [`../AGENTS.md`](../AGENTS.md)
- [`../integration/AGENTS.md`](../integration/AGENTS.md) — primary consumer of `log_parser`
- [`README.md`](README.md)

- `workspace_ownership.py` — read-only guard for persistent named test workspaces.
  Preexisting paths and new leaks are preserved; pytest tmp_path owns disposable
  cleanup. A new persistent path is a test error, never evidence of ownership.
  Body exceptions retain their original type; the guard never deletes data.

## Owned process controls

`owned_process.py` supplies `owned_process_fixture` and `OwnedProcessFixture` for
real ordinary-group and detached-session process controls. Its child publishes
actual startup/PID/session/clock records; the parent requires a native live
observation. `assert_cleaned` requires exact native absence or a genuine zombie
before accepting the delayed-write condition. Missing or failing native tools
fail the positive control. The context manager attempts cleanup only for the
observed PID whose untruncated native argv retains its unique owned token; it
preserves the original test/operator exception. It never treats a missing startup
receipt as proof of cleanup, changes a production deadline, or replaces a provider.
