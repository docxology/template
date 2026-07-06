# validation/docs/ - Agent Guide

## Purpose

This directory validates repository documentation linting: Mermaid rendering,
relative links, consistency claims, shared scan scope, and folder-level doc-pair
coverage.

## Local Rules

- Build real temporary Markdown trees in tests.
- Keep generated/local exclusion behavior aligned with
  `infrastructure.validation.docs.scan_scope`.
- When adding a docs linter, add tests here and expose the linter through
  `scripts/audit/lint_docs.py` when it belongs in the CI docs gate.
- Do not use mocks for filesystem or subprocess paths; use `tmp_path` and real
  CLI invocations.

## Validation

```bash
uv run pytest tests/infra_tests/validation/docs/ -q
uv run python scripts/audit/lint_docs.py --doc-pairs-only --json
```

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
