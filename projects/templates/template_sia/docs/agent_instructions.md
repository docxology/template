# Agent instructions — template_sia

Read this file before modifying any file in this project.

## Seven rules

1. **Layer boundaries.** Harness logic belongs in `infrastructure/sia/` (Layer 1) or `src/` (Layer 2). Scripts under `scripts/` coordinate only — no generation state machines in scripts.

2. **Deterministic default.** CI and default pipeline runs use `live=False` fixture replay from `src/fixtures/recorded_generations/`. Do not require network, Ollama, or subprocess execution of generated agents in default tests.

3. **Task layout contract.** Every task under `tasks/<name>/` must expose `data/public/`, `data/private/`, `reference/`, and a public `evaluate.py` that writes `results.json` with keys `metric_name`, `metric_value`, `n_samples`.

4. **No mocks.** Tests use real temp directories, real CSV fixtures, real subprocess calls to `evaluate.py`, and real JSON artifacts. Never import `unittest.mock`, `MagicMock`, or `@patch`.

5. **Coverage gate.** `src/` must stay ≥ 90% line+branch. Live counts: [`docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md).

6. **Manuscript tokens.** Numeric results in prose use `{{SIA_*}}` placeholders hydrated by `scripts/z_generate_manuscript_variables.py` after analysis — never hard-code generation metrics in committed manuscript sources.

7. **Scope.** This exemplar demonstrates the harness contract inspired by [arXiv:2605.27276](https://arxiv.org/abs/2605.27276). Do not vendor upstream `hexo-ai/sia` code or claim benchmark SOTA without live runs.

## Verification checklist

Before submitting changes:

```bash
uv run python scripts/01_run_tests.py --project templates/template_sia --project-only
uv run python -m infrastructure.sia.cli validate projects/templates/template_sia/tasks/mini_classify
uv run python scripts/check_template_drift.py --strict --project templates/template_sia
```
