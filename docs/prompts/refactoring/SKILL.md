---
name: template-refactoring
description: |
  Clean-break refactors with migration for the Research Project Template — move logic to src/,
  split modules, rename APIs with test updates. USE WHEN restructuring code, extracting
  modules, removing duplication, or migration without behavior change.
metadata:
  version: "1.0.0"
  last_updated: "2026-05-25"
  status: active
  data_access_level: raw
  task_type: open-ended
  modes:
    - behavior-preserving
  related_skills:
    - template-code-development
    - template-test-creation
---

# Refactoring

## Natural invoke

- "Extract analysis logic from scripts/ into src/"
- "Split infrastructure/validation monolith into smaller modules"
- "Rename public API with all call sites updated"

## Inputs to confirm

- **Scope** — paths/modules affected.
- **Behavior** — preserve externally observable behavior unless user requests breaking change.

## Workflow

1. **Baseline** — run tests on scope; record coverage.

2. **Move logic** — from scripts to `src/` or `infrastructure/`; keep orchestrators thin.

3. **Update imports** — repo-wide grep; fix tests and docs.

4. **Migration** — if breaking, document in project/infrastructure AGENTS.md; no silent API removal.

5. **Verify** — pytest + ruff/mypy on public scope paths; pipeline smoke if project scripts moved.

## Deliverables

- Before/after structure summary
- Test command output showing pass + coverage maintained

## Verification commands

```bash
uv run pytest <affected-test-path> -v
uv run python -m infrastructure.project.public_scope lint-paths | xargs uvx ruff check
uv run python scripts/pipeline/stage_01_test.py --project <project>  # when project scope
```

## When NOT to use

- **New capability** → [feature-addition](../feature-addition/SKILL.md)
- **Docs-only restructure** → [documentation-creation](../documentation-creation/SKILL.md)

## References

- [`docs/core/architecture.md`](../../core/architecture.md)
- Module line-count gate: `uv run python scripts/gates/module_line_count_check.py`
