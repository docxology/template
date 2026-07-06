---
name: template-reproducibility-audit
description: |
  Deterministic reproducibility audit — fixed seeds, regenerate-from-clean, double-run
  diff before Zenodo/arXiv/release. USE WHEN outputs drift between runs, "worked on my
  machine", need regenerate-from-clean proof, or pre-release reproducibility check — even
  without naming docs/prompts.
metadata:
  version: "1.0.0"
  last_updated: "2026-05-25"
  status: active
  data_access_level: verified_only
  task_type: open-ended
  modes:
    - double-run
    - release-readiness
  related_skills:
    - template-manuscript-claim-verification
    - template-validation-quality
---

# Reproducibility audit

Complements [manuscript-claim-verification](../manuscript-claim-verification/SKILL.md) (claim truth) by focusing on **stability of artifacts**.

## Natural invoke

- "Prove template_code_project is reproducible before Zenodo"
- "Numbers in the PDF don't match after a clean rebuild"
- "Double-run the pipeline and diff outputs"

## Inputs to confirm

- **Project** — from [`docs/_generated/active_projects.md`](../../_generated/active_projects.md).

## Workflow

1. **Determinism** — fixed RNG seeds, `MPLBACKEND=Agg`; no wall-clock/hostname/path leaks. List nondeterministic sources.

2. **Regenerate from clean** — wipe working outputs, run core pipeline, regenerate manuscript variables. Capture exit status per stage.

3. **Diff** — compare regenerated `output/<name>/` and manuscript variables vs prose assertions. Hand-typed numbers not from generated variables are findings even if equal.

4. **Double-run stability** — regenerate twice with clean tree between; any run-1 vs run-2 diff is hard failure.

5. **Fix** — seed injection, variable-ize hard-typed numbers, remove timestamp leakage. Update `projects/<n>/AGENTS.md` and README.md with regeneration command. Never hand-edit `output/`.

## Deliverables

- Drift table: artifact | committed | regenerated | action.
- Commands + raw output; no invented coverage numbers.

## Verification commands

```bash
uv sync
uv run python scripts/execute_pipeline.py --project <project> --core-only
uv run python projects/<project>/scripts/z_generate_manuscript_variables.py
git stash --include-untracked -- output/<project> 2>/dev/null || true
uv run python scripts/execute_pipeline.py --project <project> --core-only
git status --porcelain output/<project>
uv run python scripts/pipeline/stage_01_test.py --project <project>
uv run python -m infrastructure.validation.cli prerender projects/<project>/manuscript --repo-root .
uv run python -m infrastructure.validation.cli pdf output/<project>/pdf/
uv run python -m infrastructure.validation.cli integrity output/<project>/
```

## When NOT to use

- **Stage fails during regeneration** → [pipeline-debugging](../pipeline-debugging/SKILL.md)
- **Per-sentence claim audit** → [manuscript-claim-verification](../manuscript-claim-verification/SKILL.md)
