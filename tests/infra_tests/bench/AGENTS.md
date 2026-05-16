# bench/ - Agent Guide

## Purpose

Benchmark selected infrastructure paths using real files, subprocesses, and
`pytest-benchmark`. These tests are intentionally opt-in.

## Local Rules

- Mark every benchmark with `@pytest.mark.bench`.
- Keep benchmark inputs synthetic but realistic enough to exercise the real
  infrastructure path.
- Do not use mocks, monkeypatches, or fake replacements for the measured code.
- Keep wall time bounded with explicit benchmark rounds and pytest timeouts.

## Validation

```bash
uv run pytest tests/infra_tests/bench/ -m bench --benchmark-only --timeout=180
```

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
