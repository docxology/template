# Agent Instructions — AutoScientists

## Operational Constraints

1. **Never mock.** All tests use real data and real computation.
2. **Keep scripts thin.** Business logic belongs in `src/`.
3. **Deterministic by default.** Tests must pass without network access,
   without LLM calls, and without any live agent backend.
4. **Honest reporting.** Effect-size tables must include null results.
   Do not suppress negative findings.
5. **Ablation safety.** Running `scripts/run_ablation.py` should never
   modify source code — only produce output figures and data.

## Workflow

Commands below are fully qualified relative to the repo root (the monorepo
root above `projects/`), matching README.md and TODO.md.

1. Edit coordination logic in `src/`.
2. Regenerate ablation results: `uv run python projects/templates/template_autoscientists/scripts/run_ablation.py`.
3. Verify: `uv run pytest projects/templates/template_autoscientists/tests/ --cov=projects/templates/template_autoscientists/src --cov-fail-under=90`.
4. Regenerate outputs (run from the repo root — `scripts/pipeline/` is a repo-root path, not a project-local one): `uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_autoscientists`.
