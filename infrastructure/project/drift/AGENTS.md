# infrastructure/project/drift/

Template drift detection for canonical exemplar projects (`template_code_project`,
`template_prose_project`).

## Public API

- `run_drift_checks(repo_root, projects)` — run all drift checks, return `Report`
- `Finding`, `Report` — structured findings (`models.py`)
- Individual `check_*` functions in `checks.py` (used by tests)

## CLI

```bash
uv run python scripts/check_template_drift.py
uv run python scripts/check_template_drift.py --project template_code_project --strict
```

## Tests

`tests/infra_tests/test_check_template_drift.py`
