# infrastructure/project/drift/

Template drift detection for public canonical exemplar projects (`PUBLIC_PROJECT_NAMES`).

## Public API

- `run_drift_checks(repo_root, projects)` — run all drift checks, return `Report`
- `Finding`, `Report` — structured findings (`models.py`)
- Individual `check_*` functions in `checks.py` (used by tests), including `check_publication_metadata_consistency` (concept vs version DOI, CITATION.cff, `.zenodo.json`)
- `check_repo_thin_orchestrator_scripts` / `check_project_scripts` in `orchestrator.py` — AST + line-count thin-orchestrator enforcement for `scripts/` and `projects/*/scripts/`
- `run_drift_checks`, `print_human_report` / `print_github_report`, `exit_code_for_report` in `runner.py` — run checks over the exemplar roster (default `PUBLIC_PROJECT_NAMES`) and format/exit the report
- `PROJECT_CHECKS` / `REPO_CHECKS` tuples and `run_project_checks` / `run_repo_checks` in `registry.py` — single import surface aggregating every check callable
- Per-exemplar `check_*` functions in `checks_exemplar.py` — function-name, coverage-floor, dead-link, test-class, `__all__`, and publication-metadata drift plus required-files/signpost/config-example-parity checks
- `check_forkability_contract` in `checks_forkability.py` — `STANDALONE.md` / `domain_profile.yaml` / `experiment_plan.yaml` presence and validity, and rejection of unsafe raw `cp -r` / `rsync` fork instructions
- `check_project_src_infrastructure_boundary` in `checks_boundary.py` — AST-scans `src/**/*.py` for `infrastructure` imports against `manuscript/layer_contract.yaml` allowlists
- `check_docs_hardcoded_counts` / `check_shared_template_design_contract` in `checks_docs_counts.py` — repo-wide scan for hardcoded test/coverage counts in long-lived docs and the shared `projects/templates/DESIGN.md` contract

## Thin orchestrator rules (`orchestrator.py`)

| Scope | WARN | ERROR |
| --- | --- | --- |
| `projects/{name}/scripts/` | ≥120 lines with non-trivial helpers | ≥200 lines with ≥3 non-trivial functions or compute imports |
| `scripts/` (repo root) | — | ≥200 lines with ≥3 non-trivial functions or numpy/matplotlib/scipy imports |

Exempt: `_`-prefixed files, `fixtures/`, subprocess schedulers (`run_all.py`, `regression_gate.py`, `build_lean.py`, `build_mathlib_proofs.py`, …).

## Tests

`tests/infra_tests/test_check_template_drift.py`, `tests/infra_tests/project/test_thin_orchestrator_drift.py`
