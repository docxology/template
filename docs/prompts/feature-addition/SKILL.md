---
name: template-feature-addition
description: |
  End-to-end feature work across src/, scripts/, tests/, manuscript, and docs for the
  Research Project Template. USE WHEN adding a pipeline-visible feature, new analysis stage,
  manuscript-facing output, or cross-layer integration — even without feature_addition prompt.
---

# Feature addition

## Natural invoke

- "Add convergence plotting to template_code_project end-to-end"
- "New infrastructure gate wired into health CLI + tests + docs"
- "Feature: export manifest JSON from analysis stage"

## Inputs to confirm

- **Feature description** — user-facing behavior.
- **Layer** — infrastructure vs project (see [code-development](../code-development/SKILL.md)).
- **Project** — if project layer.

## Workflow

1. **Design** — logic in `src/` or `infrastructure/`; script coordinates only.

2. **Implement** — src modules first (TDD: tests alongside).

3. **Orchestrate** — `projects/<n>/scripts/` or root `scripts/` stage hook if pipeline-visible.

4. **Manuscript** — figures/data paths, `[[VAR:]]` or generated variables if numbers appear in prose.

5. **Docs** — AGENTS.md/README at affected dirs; no roster duplication.

6. **Verify** — project or infra tests; optional `./run.sh --project <n> --core-only` slice.

## Deliverables

- File list by layer
- Test + pipeline verification commands and exit codes

## Verification commands

```bash
uv run python scripts/01_run_tests.py --project <project>
uv run python scripts/execute_pipeline.py --project <project> --core-only
```

## When NOT to use

- **Single function, no pipeline/manuscript touch** → [code-development](../code-development/SKILL.md)
- **Refactor without new behavior** → [refactoring](../refactoring/SKILL.md)

## References

Checklist: [references/checklist.md](references/checklist.md)
