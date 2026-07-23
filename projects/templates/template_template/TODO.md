# template_template TODO

Forward-only backlog for the autopoietic meta-template that introspects the
infrastructure and the public exemplar roster.

## Current validation evidence

- Manuscript pre-render gate:
  `uv run python -m infrastructure.validation.cli prerender projects/templates/template_template/manuscript --repo-root .`
- Project tests and coverage:
  `uv run pytest projects/templates/template_template/tests/ --cov=projects/templates/template_template/src --cov-fail-under=90`
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --strict`
- Live test counts and coverage snapshots belong in
  `../../../docs/_generated/COUNTS.md`, not hardcoded here.

## Integrity and template-status gaps

- Keep this exemplar as the template-about-template reference for architecture,
  metrics, and confidentiality invariants.
- Keep every generated metric derived from the live tree and generated-doc
  sources rather than copied literals.
- Add a compatibility note when the public roster or confidentiality policy
  changes.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` as the copy-and-customize metadata
  starting point.
- Add explicit config keys before any new manuscript metric becomes
  user-tunable.

## Documentation and signposting gaps

- Keep README and AGENTS linked to generated public-scope docs instead of
  duplicating the rotating project list.
- Add a short "how to fork the meta-template" note if downstream users copy this
  exemplar for repository-method papers.

## Test and validator gaps

- Add negative controls for stale generated metrics and accidental inclusion of
  local-only project paths. **Shipped:** `tests/test_stale_metrics_control.py`
  verifies metrics dict key presence, positive counts, generated-vs-live
  consistency, and absence of private path segments.
- Add schema tests before changing the metrics JSON consumed by the manuscript.
- Keep the manuscript evidence-contract test green as new generated metrics or
  cited empirical values are introduced; live counts remain token-injected, and
  policy percentages remain bound to executable configuration.
- Add or document a stable final artifact-manifest refresh path for
  single-stage analysis, render, and copy checks. **Documented:**
  `infrastructure.core.pipeline.artifacts.snapshot_current_artifact_manifest`
  serves this role — it writes a current-output snapshot manifest labeled
  `current-output-snapshot` without requiring a full `PipelineExecutor` run.
- Document the structurally unreachable introspection branches (the `dir()`
  fallback, the redundant `is_dir()` re-check, and the `ImportError` version
  fallback) in `tests/AGENTS.md` rather than covering them with mocks.

## Ordered improvement ladder

1. Keep confidentiality and metrics tests green under coverage.
2. Add stale-metric detection for any new generated field.
3. Expand architecture visualization only with deterministic inputs and
   documented omissions.
4. Refresh generated docs after public-roster or metric-surface changes.
