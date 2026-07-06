# tests

Tests import project code as `src.<module>` (see `tests/conftest.py`). Do not use mocks.

Coverage must stay at or above 90% for `src/`:

```bash
uv run pytest projects/templates/template_madlib/tests/ --cov=projects/templates/template_madlib/src --cov-fail-under=90
```

When adding schema controls, update `tests/helpers.py` and cover both the valid path and at least one malformed input path. Design principles, pipeline phases, evaluation criteria, QA probes, failure modes, authoring obligations, and visualization controls need both table-generation or artifact-generation coverage and malformed-row coverage. When adding manuscript placeholders, update `test_manuscript_variables.py` so unresolved-token checks remain meaningful.

Methods changes need prose and table coverage. Assert that generated Methods body text exposes the method concept, and assert that the corresponding protocol, phase, probe, failure-mode, audit-rule, or claim-ledger surface exists.

Figure and review-packet tests should fail on drift. Check that every generated figure reference has a registry entry, that every registered figure has an artifact path, and that the handoff contract includes data, reports, figures, validation results, and `output/reports/output_statistics.json`.
