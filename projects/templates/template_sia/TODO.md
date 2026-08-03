# template_sia TODO

Forward-only integrity backlog for the self-improvement-agent harness exemplar.
This template must stay honest about fixture replay versus live subprocess runs.

## Current validation evidence

- Manuscript pre-render gate: `uv run python -m infrastructure.validation.cli prerender projects/templates/template_sia/manuscript --repo-root .`
  → clean (no render-blocking pitfalls, no undefined citations), 2026-08-02.
- Project tests and coverage (live counts in
  [`docs/_generated/COUNTS.md`](../../../docs/_generated/COUNTS.md), not pinned here):
  `uv run pytest projects/templates/template_sia/tests/ --cov=projects/templates/template_sia/src --cov-fail-under=90`
  → 66 passed, 1 deselected (`requires_ollama`), isolated coverage 99.69% (2026-08-02).
- Default loop execution replays recorded fixtures; `--live-sia` is bounded but does not apply code mutations.
- The `requires_ollama` project marker is excluded by default so the local
  coverage gate cannot accidentally import or contact the live LLM bridge.
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --strict`
  → `template_drift: no drift detected` for `templates/template_sia` (2026-08-02).
- Canonical stage run (2026-08-02): Stage 02 analysis 2/2 scripts,
  Stage 03 render green, Stage 04 all checks pass (PDF, bookends, markdown,
  structure, figure registry, evidence registry, design overlays, artifact
  manifest, rendered-provenance bind), Stage 05 copy complete.
  Render quality: 0 `^! ` LaTeX errors, 0 `??` in `pdftotext`, combined PDF 9 pages.
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
- **Shipped:** Stage 04's rendered-provenance bind is green. The artifact
  manifest must attest the whole stable output tree (pdf, web, hydrated
  manuscript, release, composition). After manual stage-by-stage runs (without
  `PipelineExecutor`), rebaseline with
  `uv run python scripts/maintenance/refresh_artifact_manifests.py --project templates/template_sia`
  or run `scripts/maintenance/refresh_rendered_provenance.py --project templates/template_sia`
  (render → snapshot → validate → receipt) before/after `stage_04_validate.py`;
  do not run `stage_04_validate.py` twice back-to-back without a rebaseline.
- Keep target-agent mutation out of the public exemplar until sandboxing, diff review, and rollback contracts exist.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` aligned with the `project_config.sia` block and safe defaults.
- Add typed config loading for new loop controls before exposing them in README commands.

## Documentation and signposting gaps

- Keep README, AGENTS, and docs explicit that the live mode is illustrative and non-mutating.
- **Shipped:** `tests/AGENTS.md` now lists all 13 on-disk test files with roles
  (was a bare bullet list); `.agents/README.md` and `.agents/skills/README.md`
  added so the `.agents/` catalog matches the shared exemplar contract.
- Add a fork checklist for turning the harness into a real improvement loop with sandbox and approval boundaries.

## Test and validator gaps

- Keep negative controls (invalid run_summary payload, empty train CSV, all
  `validate_task_dir` failure modes) and metric edge cases as the suite grows.
- **Shipped:** stale claim-ledger artifact paths were corrected to the current
  run-summary, task-data, and reference-agent locations; Stage 04 now checks
  those paths fail-closed.
- **Known gap:** `data/claim_ledger.yaml` declares `public-train-split: 0.7`,
  but no 70/30 split exists — `tasks/mini_classify/data/public/train.csv` and
  `tasks/mini_classify/data/private/labels.csv` both hold the same 6 rows and
  evaluation covers all 6. The measured fact is `public-train-rows: 6`, and the
  row's `source` string still names the stale path `tasks/mini_classify/public/`
  (should be `tasks/mini_classify/data/public/`). No test or prose binds this
  claim, so it is inert; correct the row (and regenerate the evidence registry
  via `stage_04_validate.py`) before the next ledger-touching edit.

## Ordered improvement ladder

1. Keep fixture replay and artifact-manifest tests green.
2. Add stale-fixture and non-mutation validators.
3. Add typed config for any new live-loop controls.
4. Promote real live improvement only with sandboxing, diff review, rollback, and explicit human approval gates.
