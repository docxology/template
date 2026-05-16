# core/pipeline/ - Agent Guide

## Purpose

This directory validates lower-level pipeline execution helpers that sit beneath
the orchestration CLI.

## Local Rules

- Use real temporary project trees for discovery and execution behavior.
- Keep worker functions module-level when tests exercise process pools.
- Assert log and output isolation per project.
- Avoid shared global state that can leak across multiprocessing starts.

## Validation

```bash
uv run pytest tests/infra_tests/core/pipeline/ -q
```

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
