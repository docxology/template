# doctor/ - Agent Guide

## Purpose

This directory validates `infrastructure.doctor`: diagnostics, safe fix planning,
mutation journaling, undo, scoring, and CLI output.

## Local Rules

- Exercise real temporary repo trees.
- Keep every mutating test inside `tmp_path`; never target the shared workspace.
- Test `--plan` paths as non-mutating and `mutate` paths as reversible.
- Add detector tests, fix-plan tests, and reporter assertions for each new doctor
  capability.

## Validation

```bash
uv run pytest tests/infra_tests/doctor/ -q
```

## See Also

- [`README.md`](README.md)
- [`../../infrastructure/doctor/AGENTS.md`](../../../infrastructure/doctor/AGENTS.md)
