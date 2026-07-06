# template_prose_project TODO

Forward-only integrity backlog for the prose-review exemplar. Keep this file
about template status, validation depth, and forkability.

## Current validation evidence

- Manuscript pre-render gate: `uv run python -m infrastructure.validation.cli prerender projects/templates/template_prose_project/manuscript --repo-root .`
- Project tests and coverage: `uv run pytest projects/templates/template_prose_project/tests/ --cov=projects/templates/template_prose_project/src --cov-fail-under=90`
  - 120 tests · 100% branch coverage as of 2026-06-25
- Prose analysis is offline by default and uses real markdown and BibTeX fixtures.
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --strict`
- Stage 04 warning snapshot, 2026-06-20: PDF, markdown, output structure, figure registry, evidence registry, and design overlays pass; artifact manifest reports advisory drift after single-stage regeneration.
- ruff + mypy: clean on all 8 src/ files.

## Integrity and template-status gaps

- Keep editorial metrics framed as diagnostics, not publication approval.
- Add a generated evidence summary that separates readability, citation density, bibliography consistency, and structural outline results.
- Keep prose pipeline orchestration thin over `src/` and `infrastructure/prose`.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` stricter than the bundled exemplar config so forks see realistic editorial defaults.
- Add migration tests if prose threshold names or report output keys change.

## Documentation and signposting gaps

- Keep README and AGENTS clear that no LLM or Ollama dependency is required for the default review.
- Link any new report sections from `docs/architecture.md` and `docs/quickstart.md`.

## Test and validator gaps

- ✅ Negative controls for skipped heading levels added (`TestNegativeControls`, `TestCheckUnits`).
- ✅ Negative controls for citation-density regressions added.
- ✅ Negative controls for missing bibliography entries added.
- ✅ `HeadingView` and `render_outline` fallback path covered (`test_prose_facade.py`).
- ✅ `parse_bib_keys` now correctly skips `@comment{}` blocks (negative lookahead); tested.
- ✅ `write_review_report` with empty manuscript (no files) tested and confirmed correct.
- ✅ `run_configured_checks` with all optional checks disabled tested.
- ✅ 100% branch coverage on all src/ files.
- Add report-schema tests before downstream docs depend on new report fields.
- Add or document a stable final artifact-manifest refresh path for single-stage analysis/render/copy checks.

## Ordered improvement ladder

1. Keep offline prose checks green under project coverage.
2. Add structured evidence summary output if report consumers need stable machine-readable fields.
3. Add stricter editorial profiles only as named config presets with tests.
4. Add optional LLM review only behind explicit config and offline-safe defaults.
