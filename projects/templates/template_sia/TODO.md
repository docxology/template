# template_sia TODO

Forward-only integrity backlog for the self-improvement-agent harness exemplar.
This template must stay honest about fixture replay versus live subprocess runs.

## Current validation evidence

- Manuscript pre-render gate: `uv run python -m infrastructure.validation.cli prerender projects/templates/template_sia/manuscript --repo-root .`
- Project tests and coverage (live counts in
  [`docs/_generated/COUNTS.md`](../../../docs/_generated/COUNTS.md), not pinned here):
  `uv run pytest projects/templates/template_sia/tests/ --cov=projects/templates/template_sia/src --cov-fail-under=90`
- Default loop execution replays recorded fixtures; `--live-sia` is bounded but does not apply code mutations.
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --strict`
- Style + type gates over public source paths:
  `uv run python -m infrastructure.project.public_scope source-paths` piped to ruff and mypy.

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

- Keep negative controls (invalid run_summary payload, empty train CSV, all
  `validate_task_dir` failure modes) and metric edge cases as the suite grows.
- Register the remaining illustrative manuscript threshold numbers (`85%`, `90%`)
  as configured facts, or rewrite them as qualitative defaults, before treating
  Stage 04 as warning-free.

## Ordered improvement ladder

1. Keep fixture replay and artifact-manifest tests green.
2. Add stale-fixture and non-mutation validators.
3. Add typed config for any new live-loop controls.
4. Promote real live improvement only with sandboxing, diff review, rollback, and explicit human approval gates.
