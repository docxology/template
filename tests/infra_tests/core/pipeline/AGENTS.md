# core/pipeline/ - Agent Guide

## Purpose

This directory validates lower-level pipeline execution helpers that sit beneath
the orchestration CLI.

## Local Rules

- Use real temporary project trees for discovery and execution behavior.
- Keep worker functions module-level when tests exercise process pools.
- Assert log and output isolation per project.
- Avoid shared global state that can leak across multiprocessing starts.
- Close every preview-only or direct-stage `PipelineExecutor` with
  `contextlib.closing`; full execution closes its own handlers. Never reset the
  global logging registry to compensate for an unclosed fixture owner.
- Distribution fixtures must supply required `Name` and `Version` metadata
  headers; compare actual stdlib observations and mutations, not historical
  malformed-header behavior.

## Validation

```bash
uv run pytest tests/infra_tests/core/pipeline/ -q
```

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
