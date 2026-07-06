# Tests

Tests import project code as `src.<module>` (see `tests/conftest.py` and `pyproject.toml` `pythonpath`). Do not use mocks.

| File | Focus |
| --- | --- |
| `test_config.py` | Config schema, visualization controls, explicit/default origins, defaults, validation failures, and extended loader edge cases. |
| `test_tokens.py` | Deterministic token selection, digest invariants, provenance, and TokenPlan property coverage. |
| `test_composition_and_analysis.py` | Section composition, tables, configured-field inventory, artifact JSON, figure registry, disabled-visualization branches, `analysis_fields`, and `src` public API surface. |
| `test_manuscript_variables.py` | Token map, title/table/figure variables, manuscript cross-reference, and hydration script. |

Run:

```bash
uv run pytest projects/templates/template_madlib/tests/ --cov=projects/templates/template_madlib/src --cov-fail-under=90
```

When method documentation changes, add tests that prove the config rows and generated prose changed together. At minimum, cover the method protocol row, the pipeline phase, the QA probe or failure mode, and the generated table or body paragraph that exposes the new responsibility. If the change affects review handoff, assert the review packet includes data, reports, figures, validation results, and copy statistics rather than only PDF/HTML.
