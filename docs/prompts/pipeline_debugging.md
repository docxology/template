# Prompt: Pipeline debugging

## Purpose

A **copy-paste template** for systematic triage of a failing or stuck
pipeline run — isolating which of the named DAG stages broke, why, and the
smallest fix — instead of guessing from the final error line. Pairs with
[`reproducibility_audit.md`](reproducibility_audit.md) (a stage that fails only
on regenerate) and
[`manuscript_claim_verification.md`](manuscript_claim_verification.md) (a
render/validate stage that fails on claims).

Stage definitions and `--resume`/`--core-only` semantics are authoritative in
[`../RUN_GUIDE.md`](../RUN_GUIDE.md) and [`../../AGENTS.md`](../../AGENTS.md).
Do not restate stage numbers here — link those.

## Copy-paste prompt

```
You are debugging a pipeline failure for project [name from
docs/_generated/active_projects.md]. Work the DAG, not the symptom.

1. REPRODUCE — re-run the failing invocation verbatim and capture the FULL
   stderr/stdout and the exact exit status. Quote the first real error, not the
   last line. Identify the failing named stage (setup / infra tests / project
   tests / analysis / render / validate / LLM review / LLM translations / copy).

2. ISOLATE — re-run just that stage's underlying command directly (its pytest
   target, its analysis script, the validation CLI subcommand, the renderer)
   so the failure is observed without the orchestrator in the way. Use
   --resume to skip already-good upstream stages while iterating.

3. CLASSIFY the root cause: dependency/uv-workspace gap, missing system tool
   (LaTeX/pandoc-crossref), nondeterministic input, coverage gate, undefined
   citation/cross-ref, thin-orchestrator violation (logic in scripts/ instead
   of src/ or infrastructure/), or genuine logic bug. Trace where the bad state
   ENTERS the system; fix at ingestion, not at the symptom.

4. FIX minimally and re-run the full pipeline to confirm green, then --resume
   confirm no regression upstream. Update projects/<n>/AGENTS.md / README.md
   troubleshooting notes if the failure mode was non-obvious.

DELIVER: failing stage, first real error (quoted), root cause, the minimal
patch (file + snippet), and the exact commands + raw exit status proving green.
Do not claim "fixed" without a clean full-pipeline run shown.
```

## Commands (reference)

Resolve `<project>` via
[`../_generated/active_projects.md`](../_generated/active_projects.md).

```bash
uv sync

# Reproduce + resume
uv run python scripts/execute_pipeline.py --project <project>
uv run python scripts/execute_pipeline.py --project <project> --resume
uv run python scripts/execute_pipeline.py --project <project> --core-only

# Isolate individual stages
uv run python scripts/01_run_tests.py --project <project>
uv run pytest projects/<project>/tests/ \
  --cov=projects/<project>/src --cov-fail-under=90 -q
uv run python -m infrastructure.validation.cli prerender \
  projects/<project>/manuscript --repo-root .
uv run python -m infrastructure.validation.cli pdf output/<project>/pdf/

# Common environment fault: LaTeX / crossref toolchain
uv run python -m infrastructure.rendering.latex_package_validator

# Verbose logging
LOG_LEVEL=0 uv run python scripts/execute_pipeline.py --project <project> --resume
```

## Checklist

### Pre-flight

- [ ] Failing invocation reproduced; full output + exit status captured.
- [ ] Failing named stage identified from `RUN_GUIDE.md` semantics.

### During triage

- [ ] Failing stage isolated and run without the orchestrator.
- [ ] Root cause classified; ingestion point of the bad state named.
- [ ] Fix applied at the cause, not the symptom; thin-orchestrator preserved.

### Reporting

- [ ] Full pipeline re-run green; `--resume` shows no upstream regression.
- [ ] Non-obvious failure recorded in `projects/<n>/AGENTS.md`/`README.md`.
- [ ] No invented coverage numbers; exit status quoted, not paraphrased.

## See also

- [`reproducibility_audit.md`](reproducibility_audit.md) — stage fails only on regenerate.
- [`manuscript_claim_verification.md`](manuscript_claim_verification.md) — render/validate stage fails on claims.
- [`validation_quality.md`](validation_quality.md) — validation-infrastructure detail.
- [`README.md`](README.md) — prompt index.
