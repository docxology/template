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
