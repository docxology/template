# template_data_descriptor TODO

## Current validation evidence

- Project tests exercise descriptor loading, schema hashing, uniqueness checks, file inventory gates, field constraints, metadata-only release manifests, publication-readiness scoring, byte-level descriptor↔file verification (digest + row reconciliation), plot-ready figure preparers, and an end-to-end figure-generation integration test. `scripts/generate_release_artifacts.py` exports deterministic descriptor-review artifacts under `output/reports/`; `scripts/generate_figures.py` renders the five manuscript figures under `manuscript/figures/`.
- Latest publication pass (2026-08-02): 40/40 project tests passed at 98.8% coverage (`stage_01_test.py --project-only`), pre-render validation clean, render produced the 12-page combined PDF with zero `^! ` log errors and zero unresolved `??` markers, stage 04 validation all-PASS, and `check_template_drift.py --project templates/template_data_descriptor --strict` reported no findings for this exemplar.
- Doc-completeness pass added the missing `.agents/README.md` and `.agents/skills/README.md`, upgraded `.agents/AGENTS.md`, `.agents/skills/AGENTS.md`, `.agents/skills/template-data-descriptor/AGENTS.md`, and `tests/AGENTS.md` from stubs to substantive contracts, and realigned `tests/README.md` to the quick-reference role. All relative `.md` cross-references resolve.

## Integrity and template-status gaps

- Keep rendered manuscript outputs, figures, and descriptor-review artifacts regenerated after schema or fixture changes. Recompute fixture checksums/row counts and update `data/example_descriptor.json` whenever `data/fixtures/` changes.
- Re-run `scripts/generate_figures.py` and `scripts/generate_release_artifacts.py` after any change to `src/data_descriptor/` so `output/figures/figure_registry.json` and `output/reports/*` stay in sync with the source.

## Configurable-surface gaps

- Extend `manuscript/config.yaml.example` when new descriptor fields become first-class.

## Documentation and signposting gaps

- Keep README, AGENTS, STANDALONE, and the per-directory README/AGENTS pairs aligned with the descriptor validator, verification, and figure modules.

## Test and validator gaps

- Add live checks for larger tabular files only after the fixture descriptor is stable; extend verification to non-CSV media types when a real dataset needs them.

## Ordered improvement ladder

1. Keep descriptor validation green.
2. Add external repository publication receipts after a real fork publishes.
3. When a real (non-synthetic) dataset is forked in, extend `_MEDIA_TYPES` and row-count verification to the formats that dataset needs, and pin the new fixture checksums in the descriptor.
