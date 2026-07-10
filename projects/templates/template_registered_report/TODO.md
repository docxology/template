# template_registered_report TODO

## Current validation evidence

- Tests cover registration freezing, required sections, duplicate hypotheses, outcome drift, deviation classification, stage/ethics metadata, sensitivity-analysis validation, review packets, exploratory-claim boundaries, and the deterministic demonstration study (seeded data synthesis, permutation test, plan-driven analysis binding, and figure-data helpers). `scripts/generate_review_artifacts.py` exports deterministic frozen-registration, adherence, deviation-ledger, and review-packet artifacts under `output/reports/`; `scripts/generate_figures.py` renders four committed manuscript figures and writes the executed analysis to `output/data/demo_analysis.json`, to which the manuscript numbers are bound.

## Integrity and template-status gaps

- Keep rendered manuscript outputs and registered-report review artifacts regenerated after fixture, deviation, or sensitivity-analysis changes.

## Configurable-surface gaps

- Keep ethics-review and registered-report-stage metadata aligned with any future journal-specific fixtures.

## Documentation and signposting gaps

- Keep standalone fork guidance synchronized with the validator API.

## Test and validator gaps

- Add rendered sensitivity-analysis tables once manuscript table generation consumes the review packet.

## Ordered improvement ladder

1. Keep preregistration tests green.
2. Deviation-ledger export — shipped in source/tests.
3. Registered-report review packet — shipped in source/tests/script.
4. Rendered registration packet outputs — shipped in script/output generation.
5. Deterministic demonstration study + four manuscript figures — shipped in source/tests/script/manuscript.
6. Add publication receipts for a real exemplar.
