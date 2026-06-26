# template_sia TODO

Forward-only integrity backlog for the self-improvement-agent harness exemplar.
This template must stay honest about fixture replay versus live subprocess runs.

## Current validation evidence

- Manuscript pre-render gate: `uv run python -m infrastructure.validation.cli prerender projects/templates/template_sia/manuscript --repo-root .`
- Project tests and coverage: `uv run pytest projects/templates/template_sia/tests/ --cov=projects/templates/template_sia/src --cov-fail-under=90`
  - 2026-06-25: 64 tests, 99.52% coverage (was 41 tests, 94.25%).
- Default loop execution replays recorded fixtures; `--live-sia` is bounded but does not apply code mutations.
- Repo drift gate: `uv run python scripts/check_template_drift.py --strict`
- ruff + mypy: both clean on `src/` (fixed unused `y_off` variable, unused `numpy` import, and `FancyArrowPatch` explicit kwargs for mypy compliance).
- Stage 04 warning snapshot, 2026-06-20: figure registry and artifact manifest pass; evidence registry still reports unsupported illustrative `85%` and `90%` manuscript thresholds.

## Integrity and template-status gaps

- Keep fixture replay as the default validated behavior.
- Add a run-summary artifact that distinguishes fixture generations, live subprocess execution, and unapplied feedback notes.
- Keep target-agent mutation out of the public exemplar until sandboxing, diff review, and rollback contracts exist.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` aligned with the `sia:` block and safe defaults.
- Add typed config loading for new loop controls before exposing them in README commands.

## Documentation and signposting gaps

- Keep README, AGENTS, and docs explicit that the live mode is illustrative and non-mutating.
- Add a fork checklist for turning the harness into a real improvement loop with sandbox and approval boundaries.

## Test and validator gaps

- ✅ Added negative controls: invalid run_summary payload, empty train CSV, all four `validate_task_dir` failure modes.
- ✅ Added edge-case tests: single-generation delta/metric figures, empty-metrics placeholder PNGs, metrics > 1.0 (non-percentage range), non-dict YAML config, outside-root artifact manifest path.
- ✅ Added `SIA_METRIC_DELTA = "0"` path tests for non-numeric metric values.
- Register the remaining manuscript threshold numbers as configured facts, or rewrite them as qualitative defaults, before treating Stage 04 as warning-free.

## Ordered improvement ladder

1. Keep fixture replay and artifact-manifest tests green.
2. Add stale-fixture and non-mutation validators.
3. Add typed config for any new live-loop controls.
4. Promote real live improvement only with sandboxing, diff review, rollback, and explicit human approval gates.
