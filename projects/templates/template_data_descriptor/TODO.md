# template_data_descriptor TODO

## Current validation evidence

- Project tests exercise descriptor loading, schema hashing, uniqueness checks, file inventory gates, field constraints, metadata-only release manifests, and publication-readiness scoring. `scripts/generate_release_artifacts.py` exports deterministic descriptor-review artifacts under `output/reports/`.

## Integrity and template-status gaps

- Keep rendered manuscript outputs and descriptor-review artifacts regenerated after schema or fixture changes.

## Configurable-surface gaps

- Extend `manuscript/config.yaml.example` when new descriptor fields become first-class.

## Documentation and signposting gaps

- Keep README, AGENTS, and STANDALONE aligned with the descriptor validator.

## Test and validator gaps

- Add live checks for larger tabular files only after the fixture descriptor is stable.

## Ordered improvement ladder

1. Keep descriptor validation green.
2. Field-level unit constraints — shipped in source/tests.
3. Metadata-only release manifest generation — shipped in source/tests/script.
4. Rendered descriptor-review artifacts — shipped in script/output generation.
5. Add external repository publication receipts after a real fork publishes.
