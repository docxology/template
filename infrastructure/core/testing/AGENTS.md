# infrastructure/core/testing — agent contract

Test-execution machinery for the template: the per-project pytest runner,
profiles/markers, receipts, coverage probes, and the advisory test-impact
planner. Re-homed from the flat `infrastructure/core/` top level by
`CORE-TESTING-REHOME-1`.

## Invariants

1. Callers import `infrastructure.core.testing.<module>` directly.
2. Private names are package-internal; public helpers belong to their owning
   testing module.
3. General core utilities (`determinism.py`, `script_discovery.py`,
   `runtime/`, `logging/`, …) stay at the core top level — membership here
   means "test-execution machinery", not "used by tests".

## Public surface

See `README.md` for the module table. Key entry points:
`run_per_project_pytest`, `build_union_pytest_command`, `resolve_test_profile`,
`write_public_matrix_receipt`, `run_project_test_matrix`, `output_tree_digest`,
`declared_output_relpaths`, `classify_changed_paths`, `check_cov_datafile_support`.

## Cross-refs

- `infrastructure/core/AGENTS.md` — the parent core contract.
- `tests/infra_tests/core/` — the suite exercising this package.
- Root `TO-DO.md` row `CORE-TESTING-REHOME-1` (closed by this re-home).

## Release acceptance modules

| Module | Role |
| --- | --- |
| `project_test_runtime.py` | Admission of an already prepared project test interpreter; never a resolver. |

Default functional CI uses `ci_smoke.py` and the explicit `.github/project-smoke.json` selections. Full matrices and coverage union remain available in the manual hardening workflow.
