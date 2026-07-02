# Agent Instructions — AutoScientists

## Operational Constraints

1. **Never mock.** All tests use real data and real computation.
2. **Keep scripts thin.** Business logic belongs in `src/coordination/`.
3. **Deterministic by default.** Tests must pass without network access,
   without LLM calls, and without any live agent backend.
4. **Honest reporting.** Effect-size tables must include null results.
   Do not suppress negative findings.
5. **Ablation safety.** Running `scripts/run_ablation.py` should never
   modify source code — only produce output figures and data.

## Workflow

1. Edit coordination logic in `src/coordination/`.
2. Regenerate ablation results: `uv run python scripts/run_ablation.py`.
3. Verify: `uv run pytest tests/ --cov=src --cov-fail-under=90`.
4. Regenerate outputs: `uv run python scripts/02_run_analysis.py --project templates/template_autoscientists`.
