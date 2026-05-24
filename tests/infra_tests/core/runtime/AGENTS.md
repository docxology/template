# core/runtime/ - Agent Guide

## Purpose

Tests for `infrastructure.core.runtime` setup and environment helpers (dependency checks, subprocess env, Python interpreter resolution).

## Local Rules

- Use real subprocess or filesystem state under `tmp_path`; no mocks.
- Keep platform-specific branches explicit (skip or assert guidance when tools are absent).
- Prefer hermetic env via `get_subprocess_env()` when invoking CLIs.

## Validation

```bash
uv run pytest tests/infra_tests/core/runtime/ -q
```

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
- [`../../../../infrastructure/core/runtime/`](../../../../infrastructure/core/runtime/)
