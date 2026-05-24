---
name: template-infrastructure-module
description: |
  Add or extend generic infrastructure/ packages — Layer 1 modules with SKILL.md, AGENTS.md,
  tests in tests/infra_tests/, 60% coverage. USE WHEN new reusable package under
  infrastructure/, extending validation/rendering/llm, or skill manifest entry — even without
  infrastructure_module prompt.
---

# Infrastructure module

## Natural invoke

- "Add infrastructure/foo/ package with CLI and tests"
- "Extend infrastructure/validation with a new gate"
- "New generic utility reusable across projects"

## Inputs to confirm

- **Module name** — under `infrastructure/<package>/`.
- **Public API** — functions/classes to export in `__init__.py` and `__all__`.

## Workflow

1. **Layout** — `__init__.py`, core logic module(s), optional `cli.py`, `AGENTS.md`, `README.md`, `SKILL.md` with YAML frontmatter.

2. **Implement** — generic (no project-specific paths hard-coded); type hints; `TemplateError` hierarchy.

3. **Tests** — `tests/infra_tests/<package>/`; no mocks; ≥60% on `infrastructure/`.

4. **Exports** — re-exporting `__init__.py` must declare `__all__` (MED5).

5. **Register skill** — `uv run python -m infrastructure.skills write` after adding `SKILL.md`.

6. **Wire docs** — update `infrastructure/AGENTS.md` module map if significant.

## Deliverables

- Package tree + test path
- Coverage snippet from pytest

## Verification commands

```bash
uv run pytest tests/infra_tests/<area>/ -v --cov=infrastructure --cov-fail-under=60
uv run python -m infrastructure.skills check
uv run python -m infrastructure.skills check --all-exports
```

## When NOT to use

- **Project-specific domain code** → [code-development](../code-development/SKILL.md) in `projects/*/src/`

## References

- [`infrastructure/AGENTS.md`](../../../infrastructure/AGENTS.md)
- [`docs/rules/api_design.md`](../../rules/api_design.md) — `__all__` for re-exporters
