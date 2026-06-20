# template_newspaper TODO

Forward-only integrity backlog for the data-driven newspaper layout exemplar.
Keep this focused on making the layout engine forkable, configurable, and
honestly bounded as a template.

## Current validation evidence

- Manuscript pre-render gate: `uv run python -m infrastructure.validation.cli prerender projects/templates/template_newspaper/manuscript --repo-root .`
- Project tests and coverage: `uv run pytest projects/templates/template_newspaper/tests/ --cov=projects/templates/template_newspaper/src --cov-fail-under=90`
- Newspaper PDF generation stays in Stage 02 scripts; the repository manuscript PDF is the standard Stage 03 artifact.
- Repo drift gate: `uv run python scripts/check_template_drift.py --strict`
- Stage 04 warning snapshot, 2026-06-20: all hard validators pass; evidence registry records one non-failing README number warning; artifact manifest reports advisory drift after single-stage regeneration.

## Integrity and template-status gaps

- Keep edition content fictional unless a fork adds real source provenance and fact-checking validators.
- Add a machine-readable layout audit artifact for page geometry, overflow checks, and missing image fallbacks.
- Keep ReportLab layout logic in `src/`, with scripts as thin orchestration only.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` aligned with publication metadata and render toggles.
- Add a content-schema example for a minimal one-page fork if `content/edition.yaml` gains required fields.

## Documentation and signposting gaps

- Keep README and docs clear that the newspaper PDF is produced by project scripts, while the manuscript PDF is produced by the monorepo renderer.
- Link any new content schema fields from `docs/syntax_guide.md` and the README quick-start.

## Test and validator gaps

- Add negative controls for text overflow, missing image assets, invalid column geometry, and unsafe page counts.
- Add a snapshot-free layout audit so tests assert geometry and content coverage rather than image pixels alone.
- Register or suppress documentation-only README numbers in the evidence pass, and add a stable final artifact-manifest refresh path for single-stage checks.

## Ordered improvement ladder

1. Keep deterministic fictional edition generation and project tests green.
2. Add structured layout audit output and validation.
3. Add copy-and-customize content fixtures for small, medium, and long editions.
4. Promote real-news forks only with source provenance, fact checks, and clear publication approval gates.
