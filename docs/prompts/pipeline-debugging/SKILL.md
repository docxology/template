---
name: template-pipeline-debugging
description: |
  Systematic pipeline DAG failure triage for the Research Project Template. USE WHEN
  ./run.sh or execute_pipeline.py fails, a stage stalls (setup, tests, analysis, render,
  validate, LLM, copy), pytest/coverage gate fails mid-pipeline, PDF render or validate
  breaks, Project Analysis finishes too fast with no figures, or user says pipeline debug,
  stage failed, resume checkpoint, core-only triage — even without naming this skill or docs/prompts.
metadata:
  version: "1.0.0"
  last_updated: "2026-05-25"
  status: active
  data_access_level: raw
  task_type: open-ended
  modes:
    - stage-triage
    - resume
  related_skills:
    - template-validation-quality
    - template-reproducibility-audit
---

# Pipeline debugging

## Natural invoke

- "My pipeline failed at PDF render for template_code_project"
- "Project Analysis finishes in under a second with no figures — help debug"
- "run.sh --pipeline failed; what's the first real error?"
- "Resume from checkpoint after fixing project tests"

## Inputs to confirm

- **Project** — from [`docs/_generated/active_projects.md`](../../_generated/active_projects.md); infer from context if obvious.
- **Invocation** — full vs `--core-only`, `--resume`, `--skip-infra`, multi-project.
- **Failing stage** — if unknown, reproduce first.

## Workflow

1. **Reproduce** — re-run the failing invocation verbatim; capture full stderr/stdout and exit status. Quote the **first** real error, not the last line. Name the failing stage (setup, infra tests, project tests, analysis, render, validate, LLM review, LLM translations, copy).

2. **Isolate** — run that stage's underlying command directly (pytest target, analysis script, validation CLI, renderer). Use `--resume` to skip good upstream stages while iterating.

3. **Classify** — dependency/uv gap, missing system tool (LaTeX/pandoc-crossref), nondeterministic input, coverage gate, undefined citation/cross-ref, thin-orchestrator violation (logic in `scripts/` not `src/`), or logic bug. When **Project Analysis** completes in under a second with no figures, treat as import/dependency failure and isolate via `scripts/02_run_analysis.py`. Trace where bad state **enters**; fix at ingestion.

4. **Fix minimally** — re-run full pipeline green; confirm `--resume` shows no upstream regression. Update `projects/<n>/AGENTS.md` / `README.md` if the failure mode was non-obvious.

## Deliverables

- Failing stage, first real error (quoted), root cause, minimal patch (file + snippet).
- Exact commands + raw exit status proving green.
- Do not claim "fixed" without a clean full-pipeline run.

## Verification commands

```bash
uv sync
uv run python scripts/execute_pipeline.py --project <project>
uv run python scripts/execute_pipeline.py --project <project> --resume
uv run python scripts/execute_pipeline.py --project <project> --core-only
uv run python scripts/01_run_tests.py --project <project>
uv run pytest projects/<project>/tests/ --cov=projects/<project>/src --cov-fail-under=90 -q
uv run python -m infrastructure.validation.cli prerender projects/<project>/manuscript --repo-root .
uv run python -m infrastructure.validation.cli pdf output/<project>/pdf/
uv run python -m infrastructure.rendering.latex_package_validator
LOG_LEVEL=0 uv run python scripts/execute_pipeline.py --project <project> --resume
```

Stage semantics: [`docs/RUN_GUIDE.md`](../../RUN_GUIDE.md), [`AGENTS.md`](../../../AGENTS.md).

## When NOT to use

- **Determinism / double-run drift only** → [reproducibility-audit](../reproducibility-audit/SKILL.md)
- **Claim truth in prose** → [manuscript-claim-verification](../manuscript-claim-verification/SKILL.md)
- **Validation infrastructure deep dive without a failing stage** → [validation-quality](../validation-quality/SKILL.md)
