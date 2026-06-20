# template_template TODO

Forward-only integrity backlog for the meta-template exemplar. Keep this file
focused on preserving the repository-introspection contract.

## Current validation evidence

- Manuscript pre-render gate: `uv run python -m infrastructure.validation.cli prerender projects/templates/template_template/manuscript --repo-root .`
- Project tests and coverage: `uv run pytest projects/templates/template_template/tests/ --cov=projects/templates/template_template/src --cov-fail-under=90`
- Public/private confidentiality behavior is exercised by the project test suite.
- Repo drift gate: `uv run python scripts/check_template_drift.py --strict`
- Stage 04 warning snapshot, 2026-06-20: figure registry passes; evidence registry reports 56 unsupported generated-count or percentage tokens; artifact manifest reports advisory drift after single-stage regeneration.

## Integrity and template-status gaps

- Keep this exemplar as the template-about-template reference for architecture, metrics, and confidentiality invariants.
- Keep generated metrics derived from the live tree and generated-doc sources rather than copied literals.
- Add a compatibility note when public roster or confidentiality policy changes.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` as the copy-and-customize metadata starting point.
- Add explicit config keys before any new manuscript metric becomes user-tunable.

## Documentation and signposting gaps

- Keep README and AGENTS linked to generated public-scope docs instead of duplicating rotating project lists.
- Add a short "how to fork the meta-template" note if downstream users copy this exemplar for repository-method papers.

## Test and validator gaps

- Add negative controls for stale generated metrics and accidental inclusion of local-only project paths.
- Add schema tests before changing metrics JSON consumed by the manuscript.
- Bind generated count/percentage claims into the evidence registry so the meta-template's introspection numbers validate without warnings.
- Add or document a stable final artifact-manifest refresh path for single-stage analysis/render/copy checks.

## Ordered improvement ladder

1. Keep confidentiality and metrics tests green under coverage.
2. Add stale-metric detection for any new generated field.
3. Expand architecture visualization only with deterministic inputs and documented omissions.
4. Refresh generated docs after public roster or metric-surface changes.
