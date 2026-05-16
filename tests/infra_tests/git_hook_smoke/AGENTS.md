# git_hook_smoke/ - Agent Guide

## Purpose

This directory is the lightweight test subset run by the pre-push hook. It
protects high-value invariants without paying the full infra-suite cost.

## Local Rules

- Keep tests fast, deterministic, and subprocess-safe.
- Do not add slow integration scenarios here; put those in the relevant module
  test directory.
- Prefer smoke coverage for hook-critical commands and import paths.
- Keep the hook command in `.pre-commit-config.yaml` aligned with this folder.

## Validation

```bash
uv run pytest tests/infra_tests/git_hook_smoke/ -q --import-mode=importlib
```

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
