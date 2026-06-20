# Tests

| File | Focus |
| --- | --- |
| `test_config.py` | Config schema, expanded manuscript/design/phase/evaluation/probe/failure/authoring/visualization controls, explicit/default origins, defaults, and validation failures. |
| `test_tokens.py` | Deterministic token selection, seed sensitivity, category sensitivity, and provenance. |
| `test_composition_and_analysis.py` | Section composition, generated Methods body concepts, generated Markdown tables, design/phase/evaluation/probe/failure/authoring rows, configured-field inventory, expanded method-surface declarations, review-packet and fork-migration declarations, artifact JSON, cover config, figure registry, and nonblank generated figures. |
| `test_manuscript_variables.py` | Token map, title/table/figure variables, manuscript cross-reference, and hydration script. |

Run:

```bash
uv run pytest projects/templates/template_madlib/tests/ --cov=projects/templates/template_madlib/src --cov-fail-under=90
```

When method documentation changes, add tests that prove the config rows and generated prose changed together. At minimum, cover the method protocol row, the pipeline phase, the QA probe or failure mode, and the generated table or body paragraph that exposes the new responsibility. If the change affects review handoff, assert the review packet includes data, reports, figures, validation results, and copy statistics rather than only PDF/HTML.
