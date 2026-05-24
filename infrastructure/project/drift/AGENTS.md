# infrastructure/project/drift/

Template drift detection for canonical exemplar projects (`template_code_project`,
`template_prose_project`).

## Public API

- `run_drift_checks(repo_root, projects)` — run all drift checks, return `Report`
- `Finding`, `Report` — structured findings (`models.py`)
- Individual `check_*` functions in `checks.py` (used by tests)
- `check_repo_thin_orchestrator_scripts` / `check_project_scripts` in `orchestrator.py` — AST + line-count thin-orchestrator enforcement for `scripts/` and `projects/*/scripts/`

## Thin orchestrator rules (`orchestrator.py`)

| Scope | WARN | ERROR |
| --- | --- | --- |
| `projects/{name}/scripts/` | ≥120 lines with non-trivial helpers | ≥200 lines with ≥3 non-trivial functions or compute imports |
| `scripts/` (repo root) | — | ≥200 lines with ≥3 non-trivial functions or numpy/matplotlib/scipy imports |

Exempt: `_`-prefixed files, `fixtures/`, subprocess schedulers (`run_all.py`, `regression_gate.py`, `build_lean.py`, `build_mathlib_proofs.py`, …).

## Tests

`tests/infra_tests/test_check_template_drift.py`, `tests/infra_tests/project/test_thin_orchestrator_drift.py`
