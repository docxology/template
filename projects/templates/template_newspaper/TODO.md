# template_newspaper TODO

Forward-only backlog for the data-driven large-format newspaper layout engine
(ReportLab broadsheet). Keep this focused on making the layout engine forkable,
configurable, and honestly bounded as a template.

## Current validation evidence

- Manuscript pre-render gate: `uv run python -m infrastructure.validation.cli prerender projects/templates/template_newspaper/manuscript --repo-root .`
- Project tests and coverage: `uv run pytest projects/templates/template_newspaper/tests/ --cov=projects/templates/template_newspaper/src --cov-fail-under=90`
- Stage 02 newspaper PDF generation: `uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_newspaper` (broadsheet PDF stays in Stage 02 scripts; the repository manuscript PDF is the standard Stage 03 artifact).
- Stage 03 manuscript render: `uv run python scripts/pipeline/stage_03_render.py --project templates/template_newspaper`
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --strict`
- Live test count and measured branch coverage → [`docs/_generated/COUNTS.md`](../../../docs/_generated/COUNTS.md) (regenerated, never hardcoded here).

## Integrity and template-status gaps

- Keep edition content fictional unless a fork adds real source provenance and fact-checking validators.
- Keep ReportLab layout logic in `src/`, with scripts as thin orchestration only.
- Add a machine-readable layout audit artifact for page geometry, overflow checks, and missing image fallbacks.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` aligned with publication metadata and render toggles.
- Add a content-schema example for a minimal one-page fork if `content/edition.yaml` gains required fields.

## Documentation and signposting gaps

- Keep README and docs clear that the newspaper PDF is produced by project scripts, while the manuscript PDF is produced by the monorepo renderer.
- Link any new content schema fields from `docs/syntax_guide.md` and the README quick-start.
- Document the platform-dependent `typography.py` `register_fonts()` fallback arc (base-14 path reachable only on Linux CI without macOS fonts) so future reviewers understand why that branch stays uncovered under the no-mocks policy.

## Test and validator gaps

- Register or suppress documentation-only README numbers in the evidence pass, and add a stable final artifact-manifest refresh path for single-stage checks.
- Keep the platform-only `typography.py` fallback branch documented rather than mock-covered; revisit only if the no-mocks policy or the CI font matrix changes.

## Ordered improvement ladder

1. Keep deterministic fictional edition generation and project tests green.
2. Add structured layout audit output and validation.
3. Add copy-and-customize content fixtures for small, medium, and long editions.
4. Promote real-news forks only with source provenance, fact checks, and clear publication approval gates.
