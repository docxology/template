# template_data_descriptor TODO

## Current validation evidence

- Project tests exercise descriptor loading, schema hashing, uniqueness checks, file inventory gates, field constraints, metadata-only release manifests, publication-readiness scoring, byte-level descriptor↔file verification (digest + row reconciliation), plot-ready figure preparers, and an end-to-end figure-generation integration test. `scripts/generate_release_artifacts.py` exports deterministic descriptor-review artifacts under `output/reports/`; `scripts/generate_figures.py` renders the five manuscript figures under `manuscript/figures/`.

## Integrity and template-status gaps

- Keep rendered manuscript outputs, figures, and descriptor-review artifacts regenerated after schema or fixture changes. Recompute fixture checksums/row counts and update `data/example_descriptor.json` whenever `data/fixtures/` changes.

## Configurable-surface gaps

- Extend `manuscript/config.yaml.example` when new descriptor fields become first-class.

## Documentation and signposting gaps

- Keep README, AGENTS, STANDALONE, and the per-directory README/AGENTS pairs aligned with the descriptor validator, verification, and figure modules.

## Test and validator gaps

- Add live checks for larger tabular files only after the fixture descriptor is stable; extend verification to non-CSV media types when a real dataset needs them.

## Ordered improvement ladder

1. Keep descriptor validation green.
2. Add external repository publication receipts after a real fork publishes.
