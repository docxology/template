---
name: template-code-development
description: |
  Standards-compliant code for the Research Project Template — infrastructure or project
  src/, thin orchestrators, type hints, no mocks. USE WHEN implementing an algorithm, utility,
  analysis method, optimizer, new module in projects/*/src or infrastructure/, or user says
  add code following template architecture — even without docs/prompts. Not for end-to-end
  feature spanning manuscript + pipeline (use template-feature-addition).
metadata:
  version: "1.0.0"
  last_updated: "2026-05-25"
  status: active
  data_access_level: raw
  task_type: open-ended
  modes:
    - implementation
  related_skills:
    - template-test-creation
    - template-refactoring
---

# Code development

## Natural invoke

- "Implement gradient descent in template_code_project src/"
- "Add a generic CSV validator in infrastructure/"
- "New analysis method with tests and logging"

## Inputs to confirm

- **Task** — what to implement.
- **Layer** — `infrastructure` (generic, 60% cov) vs `project` (domain, 90% cov).
- **Project** — if layer is project, from [`docs/_generated/active_projects.md`](../../_generated/active_projects.md).

## Workflow

1. **Place logic correctly** — computation in `infrastructure/` or `projects/<n>/src/`; scripts only orchestrate I/O and plotting.

2. **Implement** — type hints on public APIs; `get_logger(__name__)`; custom exceptions extending `TemplateError`; Google docstrings.

3. **Tests** — real data, temp files, subprocess, or pytest-httpserver; no mocks ([`docs/rules/testing_standards.md`](../../rules/testing_standards.md)).

4. **Docs** — update module/folder AGENTS.md + README.md when adding public surface.

5. **Verify** — ruff/mypy on touched paths; pytest with coverage gate.

## Deliverables

- Module(s) with tests meeting coverage floor
- List of files touched and verification command output

## Verification commands

```bash
uv run python -m infrastructure.project.public_scope source-paths | xargs uvx ruff check
uv run python -m infrastructure.project.public_scope source-paths | xargs uv run mypy
uv run pytest projects/<project>/tests/ --cov=projects/<project>/src --cov-fail-under=90 -q
# or infra:
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-fail-under=60 -q
```

## When NOT to use

- **End-to-end feature spanning manuscript + pipeline** → [feature-addition](../feature-addition/SKILL.md)
- **Tests only for existing code** → [test-creation](../test-creation/SKILL.md)
- **New infrastructure package skeleton** → [infrastructure-module](../infrastructure-module/SKILL.md)

## References

- [`docs/rules/`](../../rules/) — normative standards
- [`docs/core/architecture.md`](../../core/architecture.md) — two layers, thin orchestrator
- Code patterns: [references/patterns.md](references/patterns.md)
