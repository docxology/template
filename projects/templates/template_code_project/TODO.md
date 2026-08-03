# template_code_project TODO

Forward-only backlog for the code-first numerical exemplar — the reference
thin-orchestrator control-positive path for code-centric research projects.

## Current validation evidence

- Manuscript pre-render gate: `uv run python -m infrastructure.validation.cli prerender projects/templates/template_code_project/manuscript --repo-root .`
- Project tests and coverage: `uv run pytest projects/templates/template_code_project/tests/ --cov=projects/templates/template_code_project/src --cov-fail-under=90`
- Stage 02 analysis must write `output/data/optimization_results.csv` before strict manuscript-variable generation: `uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_code_project`
- Stage 03 manuscript render: `uv run python scripts/pipeline/stage_03_render.py --project templates/template_code_project`
- Stage 04 output validation: `uv run python scripts/pipeline/stage_04_validate.py --project templates/template_code_project`
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --strict`
- Code quality: `uv run ruff check projects/templates/template_code_project/src/` and `uv run mypy projects/templates/template_code_project/src/` must both pass clean.
- Benchmark reproducibility: tracked benchmark reports and figures contain only deterministic facts; wall-clock timing is logged as a runtime diagnostic, and two-run byte-equality tests enforce the boundary.
- Live test count and measured coverage percentage → [`docs/_generated/COUNTS.md`](../../../docs/_generated/COUNTS.md) (regenerated, never hardcoded here; both numbers drift faster than this file).

## Accuracy pass — 2026-08-02 (measured)

- Prerender: clean (no render-blocking pitfalls, no undefined citations).
- pytest: **242 passed**, **97.67 %** coverage on `src/` (floor 90 %).
- Stage 02: 8/8 analysis scripts; 46 manuscript variables generated.
- Stage 03: combined PDF rendered (25 pages), `Valid PDFs: 1/1`; 0 `^! ` lines in compile logs; 0 `??` in `pdftotext`.
- Stage 04: all checks pass (PDF, bookends, markdown, structure, figure registry, evidence registry, design overlays, artifact manifest); rendered-provenance receipt written (54 sources / 18 config / 72 outputs).
- Drift: `check_template_drift.py --project templates/template_code_project --strict` → no drift detected.

### Fixed in this pass

- `fig:complexity` caption corrected to the actual 3×2 six-panel layout; replaced the false "both saturate at the iteration cap" claim (α=2.5 terminates via `non_finite`) and described the stability-width and cross-profile bottom panels.
- Agency-category boundary corrected to the code's `α < 0.3` threshold (`manuscript/03_results.md`).
- Removed literal `{{CONFIG_*}}` / `{{RESULT_*}}` wildcard prose in `01_introduction.md` and `07_scope_and_related_work.md` so the rendered PDF no longer leaks raw braces.
- `scripts/AGENTS.md` + `scripts/README.md`: listed the on-disk `04_benchmark_stage.py`, `08_connector_search.py`, `09_provenance_record.py`, `10_research_workflow.py`, `__init__.py`; replaced stale `[0.01, 0.05, 0.1, 0.2]` step-size grids with the configured six-value grid.
- `tests/AGENTS.md` + `tests/README.md`: added `test_benchmark_support.py` to diagram, class line, and bullets.
- Root `AGENTS.md`: refreshed `SRC_F` / `M_F` mermaid listings, ProgressBar grid, stray `##` heading.
- `docs/AGENTS.md`: corrected the `{{VARIABLE}}` token count (28 → 46) and stale per-file line counts; `docs/syntax_guide.md`: `CONFIG_VERSION` 2.5.2, added missing `RESULT_*` / `ARTIFACT_*` / `STABILITY_FUNCTION` rows, corrected the "never use `\begin{equation}`" guidance (the manuscript uses that form and it resolves).
- `manuscript/AGENTS.md`: version 2.5.2; File Inventory token lists now match the live per-file `{{TOKEN}}` usage exactly (verified programmatically).
- `docs/README.md`: removed the stale "127 files, 14 subdirectories" literal (COUNTS.md is authoritative).
- Added `.agents/README.md` and `.agents/skills/README.md` per the shared exemplar catalog contract; all relative cross-references resolve.

## Integrity and template-status gaps

- Keep this exemplar as the smallest reliable control-positive path for code-centric research projects.
- Keep dashboard, API docs, figures, and manuscript variables generated from source, not hand-maintained output snapshots.
- Add a project-local output validation script only if it checks artifacts beyond the generic Stage 04 validators.
- Add or document a stable final artifact-manifest refresh path for single-stage analysis/render/copy checks. **Documented:** `infrastructure.core.pipeline.artifacts.snapshot_current_artifact_manifest` serves this role.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` as the richer copy-and-customize template for publication, LLM, testing, and steganography toggles.
- Add any future optimizer hyperparameter config under typed source loaders rather than reading ad hoc YAML from scripts.

## Documentation and signposting gaps

- Keep README quick-start commands aligned with the qualified project name `templates/template_code_project`.
- Link new public artifacts from README, AGENTS, and `docs/_generated/exemplar_roster.md` through the generator.

## Test and validator gaps

- Add a negative control before widening optimizer claims beyond the bundled deterministic objectives.
- Add dashboard schema assertions whenever dashboard fields or chart payloads change.
- Close remaining infrastructure-path branch misses in `analysis/scientific_reports.py` and `analysis/workflow.py` with subprocess isolation tests mirroring `TestImportFallback` if coverage gates tighten further.

## Ordered improvement ladder

1. Preserve the strict analysis-to-manuscript variable contract.
2. Add focused validators for any new generated artifact family.
3. Expand benchmark scenarios only with deterministic seeds, expected-shape tests, and documented claim boundaries.
4. Refresh generated docs after any public-surface change.
