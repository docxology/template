# infrastructure/core/testing

The pytest/testing cluster of Layer-1 core: per-project pytest execution,
marker/profile configuration, public-matrix receipts, coverage-capability
probes, and test-selection planning. Re-homed from the flat
`infrastructure/core/` top level by `CORE-TESTING-REHOME-1`; the old
`infrastructure/core/<module>.py` paths were removed; import from
`infrastructure.core.testing.<module>` directly.

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
| `ci_infra_partition.py` | Source-declared complete ordinary-CI module partition and selection admission. |
| `ci_infra_shard_plugin.py` | Explicit pytest/xdist collection partition and actual completion accounting. |
| `ci_infra_coverage.py` | Confined shard transfer checks and the complete ≥60% branch-coverage union. |
| `test_impact.py` | Advisory changed-surface test-lane planner. |
| `test_performance.py` | Performance-test harness and output redaction. |

General-purpose core utilities that happen to be consumed by tests
(`determinism.py`, `script_discovery.py`, `logging/`, `runtime/`, …)
deliberately stay at the `infrastructure/core/` top level: this package is
for test-execution machinery, not for every module a test touches.

Ordinary project tests use an existing selected interpreter and validate its exact runner stack without installing packages. Explicit environment preparation is separate. A nominated unusable project `.venv` blocks with exit 75; malformed declarations use exit 2 and real deadline/interruption outcomes remain 124/130.

Ordinary hosted infrastructure CI partitions its existing marker-filtered collection into four disjoint module shards for each existing OS/runtime pair. The plugin is explicitly enabled only by that invocation; nested pytest commands retain their declared semantics. Selection receipts bind infrastructure, scripts, tests and CI configuration bytes, and preserve actual pytest failure codes. These are ordinary CI records, not the complete Root release acceptance profile. The required `coverage-infra` job validates all four Python 3.14/Linux receipts and coverage hashes, merges actual arcs into an isolated temporary data file and enforces the existing 60% floor before Codecov upload. An invalid shard invocation or partition refusal exits 2 (pytest's usage error is 4); because pytest's interrupted session also exits 2, every refusal prints its diagnostic (collection refusals from xdist workers reach the controller summary) and leaves no complete shard receipt, so neither a refusal nor an interruption can export coverage.
