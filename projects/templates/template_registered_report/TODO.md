# template_registered_report TODO

## Current validation evidence

- Tests cover registration freezing, required sections, duplicate hypotheses, outcome drift, deviation classification, stage/ethics metadata, sensitivity-analysis validation, review packets, and exploratory-claim boundaries. `scripts/generate_review_artifacts.py` exports deterministic frozen-registration, adherence, deviation-ledger, and review-packet artifacts under `output/reports/`.

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
5. Add publication receipts for a real exemplar.
