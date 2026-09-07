# infrastructure/core/testing

The pytest/testing cluster of Layer-1 core: per-project pytest execution,
marker/profile configuration, public-matrix receipts, coverage-capability
probes, and test-selection planning. Re-homed from the flat
`infrastructure/core/` top level by `CORE-TESTING-REHOME-1`; the old
`infrastructure/core/<module>.py` paths remain as one-file backwards-compat
shims so every historical import keeps resolving (new code imports from
`infrastructure.core.testing.<module>` directly).

## Modules

| Module | Role |
| --- | --- |
| `test_runner.py` | `run_per_project_pytest` — one pytest process per exemplar, combined coverage gate, receipt finalization. |
| `test_runner_outputs.py` | Output-tree visibility, declared-output artifacts, and isolation digests. |
| `test_runner_cache.py` | Cache identity inputs and roster revision for public-matrix receipts. |
| `project_test_matrix.py` | Bounded deterministic execution of project test subprocesses. |
| `pytest_orchestration.py` | Union pytest command construction, suite parsing, worker config. |
| `pytest_profiles.py` | Test profile resolution (quick/release) and concurrency validation. |
| `pytest_marker_exprs.py` | Marker-expression assembly per profile. |
| `public_matrix_receipt.py` | Deterministic public-matrix receipt build/validate/write. |
| `coverage_policy.py` | pytest-cov capability probes. |
| `test_impact.py` | Advisory changed-surface test-lane planner. |
| `test_performance.py` | Performance-test harness and output redaction. |

General-purpose core utilities that happen to be consumed by tests
(`determinism.py`, `script_discovery.py`, `logging/`, `runtime/`, …)
deliberately stay at the `infrastructure/core/` top level: this package is
for test-execution machinery, not for every module a test touches.
