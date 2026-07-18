# template_sia TODO

Forward-only integrity backlog for the self-improvement-agent harness exemplar.
This template must stay honest about fixture replay versus live subprocess runs.

## Current validation evidence

- Manuscript pre-render gate: `uv run python -m infrastructure.validation.cli prerender projects/templates/template_sia/manuscript --repo-root .`
- Project tests and coverage (live counts in
  [`docs/_generated/COUNTS.md`](../../../docs/_generated/COUNTS.md), not pinned here):
  `uv run pytest projects/templates/template_sia/tests/ --cov=projects/templates/template_sia/src --cov-fail-under=90`
- Default loop execution replays recorded fixtures; `--live-sia` is bounded but does not apply code mutations.
- The `requires_ollama` project marker is excluded by default so the local
  coverage gate cannot accidentally import or contact the live LLM bridge.
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --strict`
- Style + type gates over public source paths:
  `uv run python -m infrastructure.project.public_scope source-paths` piped to ruff and mypy.
- Thin-orchestrator boundary: `src/loop.py` owns project configuration, fixture
  selection, shared-harness invocation, and derived artifacts; the CLI imports
  that API. `tests/test_architecture_contract.py` rejects a return to
  `src → scripts` imports or a second script-layer implementation.

## Integrity and template-status gaps

- Keep fixture replay as the default validated behavior.
- **Shipped:** `run_summary.json` distinguishes fixture replay from live
  subprocess execution and records whether later-generation feedback was
  applied or only recorded.
- Keep target-agent mutation out of the public exemplar until sandboxing, diff review, and rollback contracts exist.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` aligned with the `project_config.sia` block and safe defaults.
- Add typed config loading for new loop controls before exposing them in README commands.

## Documentation and signposting gaps

- Keep README, AGENTS, and docs explicit that the live mode is illustrative and non-mutating.
- Add a fork checklist for turning the harness into a real improvement loop with sandbox and approval boundaries.

## Test and validator gaps

- Keep negative controls (invalid run_summary payload, empty train CSV, all
  `validate_task_dir` failure modes) and metric edge cases as the suite grows.
- **Shipped:** stale claim-ledger artifact paths were corrected to the current
  run-summary, task-data, and reference-agent locations; Stage 04 now checks
  those paths fail-closed.

## Ordered improvement ladder

1. Keep fixture replay and artifact-manifest tests green.
2. Add stale-fixture and non-mutation validators.
3. Add typed config for any new live-loop controls.
4. Promote real live improvement only with sandboxing, diff review, rollback, and explicit human approval gates.
