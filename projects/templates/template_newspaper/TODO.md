# template_newspaper TODO

Forward-only backlog for the data-driven large-format newspaper layout engine
(ReportLab broadsheet). Keep this focused on making the layout engine forkable,
configurable, and honestly bounded as a template.

## Current validation evidence

- Manuscript pre-render gate: `uv run python -m infrastructure.validation.cli prerender projects/templates/template_newspaper/manuscript --repo-root .` — passed; no render-blocking pitfalls or undefined citations.
- Canonical core pipeline: `uv run python scripts/runner/execute_pipeline.py --project templates/template_newspaper --core-only` — all 8 stages completed successfully; infrastructure smoke 220 passed; project 150 passed at 99.70% coverage; analysis generated 13 figures and a 12-page newspaper; manuscript rendering, output validation, and copy passed.
- Focused project gate: `uv run pytest projects/templates/template_newspaper/tests --cov=projects/templates/template_newspaper/src --cov-fail-under=90` — 150 passed, 0 failed, 0 skipped, 99.70% coverage.
- Drift gate: `uv run python scripts/audit/check_template_drift.py --project templates/template_newspaper --strict` — passed.
- Render quality: front page raster inspection found no clipping, overlap, missing figures, unreadable text, broken columns, or excessive blank areas; PDF logs contain 0 `^! ` errors and extracted newspaper text contains 0 `??` tokens.
- Measured artifact: `output/data/render_report.json` reports `page_count: 12`, `all_pages_fit: true`; `pdfinfo` reports 12 pages for `output/pdf/the-triplicate.pdf`.
- Live test count and measured branch coverage → [`docs/_generated/COUNTS.md`](../../../docs/_generated/COUNTS.md) (regenerated, never hardcoded here).

## Integrity and template-status gaps

- Keep edition content fictional unless a fork adds real source provenance and fact-checking validators.
- Keep ReportLab layout logic in `src/`, with scripts as thin orchestration only.
- Add a machine-readable layout audit artifact for page-geometry glyph-collision auditing — e.g. detecting when a wrapped headline's descender-heavy last line sits too close to the next flowable (the class of bug fixed in `furniture.draw_lead_headline`'s `LEAD_HEAD_LEADING`/`LEAD_HEAD_GAP`/`LEAD_DECK_LEADING` constants, caught only by rasterizing rendered pages, not by `all_pages_fit`/overset checks). Overflow checks (`all_pages_fit`, oversets) and missing-image fallbacks are already implemented and tested (`tests/test_robustness.py`); this item is scoped to glyph-collision detection specifically.

## Review fixes completed

- Corrected the package `__version__` to match the 1.0.2 release markers in `pyproject.toml`, `CITATION.cff`, `codemeta.json`, `.zenodo.json`, and manuscript config.
- Corrected the manuscript's typography description from four logical roles to the three implemented font families: display, body, and sans.
- Updated the manuscript reproducibility coverage statement from the stale 95% to the measured 99.70%.
- Added the live render-format toggle block to `manuscript/config.yaml` and synchronized `config.yaml.example`, including the placeholder repository URL.
- Completed the `.agents/` catalog README files and aligned its project skill version with the release.
- Added exact on-disk script and test inventories to `scripts/AGENTS.md` and `tests/AGENTS.md`.
- Regenerated publication outputs through the canonical pipeline; validation and copy now pass with the current artifact manifest.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` aligned with publication metadata and render toggles.
- Add a content-schema example for a minimal one-page fork if `content/edition.yaml` gains required fields.

## Documentation and signposting gaps

- Keep README and docs clear that the newspaper PDF is produced by project scripts, while the manuscript PDF is produced by the monorepo renderer.
- Link any new content schema fields from `docs/syntax_guide.md` and the README quick-start.
- Document the platform-dependent `typography.py` `register_fonts()` fallback arc (base-14 path reachable only on Linux CI without macOS fonts) so future reviewers understand why that branch stays uncovered under the no-mocks policy.

## Test and validator gaps

- Register or suppress documentation-only README numbers in the evidence pass, and add a stable final artifact-manifest refresh path for single-stage checks. **Documented:** `infrastructure.core.pipeline.artifacts.snapshot_current_artifact_manifest` provides the stable refresh path.
- Keep the platform-only `typography.py` fallback branch documented rather than mock-covered; revisit only if the no-mocks policy or the CI font matrix changes.

## Ordered improvement ladder

1. Keep deterministic fictional edition generation and project tests green.
2. Add structured layout audit output and validation.
3. Add copy-and-customize content fixtures for small, medium, and long editions.
4. Promote real-news forks only with source provenance, fact checks, and clear publication approval gates.
