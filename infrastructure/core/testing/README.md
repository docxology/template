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
| `test_runner.py` | `run_per_project_pytest` — isolated ordinary pytest or admitted source-declared verifier per exemplar, retained exact coverage databases, combined coverage gate and receipt finalization. |
| `test_runner_outputs.py` | Output-tree visibility, declared-output artifacts, and isolation digests. |
| `test_runner_cache.py` | Cache identity inputs and roster revision for public-matrix receipts. |
| `project_test_matrix.py` | Bounded deterministic execution of project test subprocesses. |
| `pytest_orchestration.py` | Union pytest command construction, suite parsing, worker config. |
| `pytest_profiles.py` | Test profile resolution (quick/release) and concurrency validation. |
| `pytest_marker_exprs.py` | Marker-expression assembly per profile. |
| `pytest_scratch.py` | Fresh private pytest fixture directories outside Source, Git and the selected runtime, with held-directory identity checks and descriptor-based cleanup. |
| `public_matrix_receipt.py` | Deterministic public-matrix receipt build/validate/write. |
| `coverage_policy.py` | pytest-cov capability probes. |
| `ci_smoke.py` | Complete public roster with focused functional tests; no whole-suite coverage claim. |
| `ci_selection.py` | Conservative changed-project selection with declared transitive consumers; shared or ambiguous changes select the complete public roster. |
| `ci_infra.py`, `ci_contracts.py` | Exact complementary smoke shards and full-module contract jobs; the aggregate refuses missing, repeated or overlapping executed members. Broad routine selections keep at most 20 modules per automatic job and isolate declared process-heavy modules, including the multi-project run matrix; byte sizes balance placement, without predicting runtime. The 540-second operation and per-test clocks stay unchanged. Opt-in pytest observations flush bounded case starts, phase durations and explicitly truncated failure text to diagnostic-only JSONL, so a hard kill can retain partial attribution; complete execution receipts remain required. |
| `ci_test_ownership.py` | Explicit focused test owners for shared Source changes, retaining the complete legacy smoke selection. |
| `ci_execution_user.py` | Explicit hosted Linux account preparation, unprivileged original-command execution and byte-identical readiness transport; strict process observation remains unchanged. |
| `pytest_receipt.py`, `pytest_observations.py` | Explicitly enabled nonce-bound original pytest collection/outcome records and independent readback. |
| `project_test_measurement.py` | Compose a complete original serial Stage-01 branch-aware combined coverage measurement into the same pipeline, using the original producer hash carried by the stage worker. |
| `_pytest_runtime_controls.py` | Private default-only benchmark storage relocation; absent/disabled plugins and explicit user destinations retain their behavior. |
| `ci_infra_partition.py` | Source-declared complete ordinary-CI module partition and selection admission. |
| `ci_infra_shard_plugin.py` | Explicit pytest/xdist collection partition, actual completion accounting and bounded diagnostics-only controller records. |
| `ci_infra_coverage.py` | Confined shard transfer checks and the complete ≥60% branch-coverage union. |
| `test_impact.py` | Advisory changed-surface test-lane planner. |
| `test_performance.py` | Performance-test harness and output redaction. |

General-purpose core utilities that happen to be consumed by tests
(`determinism.py`, `script_discovery.py`, `logging/`, `runtime/`, …)
deliberately stay at the `infrastructure/core/` top level: this package is
for test-execution machinery, not for every module a test touches.

Ordinary project tests use an existing selected interpreter and validate its exact runner stack without installing packages. Explicit environment preparation is separate. A nominated unusable project `.venv` blocks with exit 75; malformed declarations use exit 2 and real deadline/interruption outcomes remain 124/130.

The generic project runner nominates confined benchmark storage under
`output/.pipeline/benchmarks` and explicitly loads the private runtime-control
plugin. Its first configure hook replaces only pytest-benchmark's unchanged
`file://./.benchmarks` default, before the benchmark session initializes. This
prevents plugin startup from creating a new Source directory even when benchmark
cases are deselected. An absent or disabled plugin needs no benchmark-specific
option, explicit nondefault user storage is respected, and test selection,
workloads, coverage, deadlines and receipt behavior are unchanged.

The hosted Linux execution profile is prepared after dependencies and tools,
before source custody. It preserves global process visibility, original command
arguments and exit status, and copies readiness bytes for the runner's artifact
reader. Setup or transport success does not establish a passing observation.
See [the action contract](../../../.github/actions/setup-ci-execution-user/README.md)
for caller ordering and verification boundaries.

Functional CI keeps the Source-owned quick marker profile. Original pytest
callbacks record the complete collection before filtering, explicitly deselected
cases, selected outcomes, and effective invocation/profile. The consumer requires
`collected = selected ⊎ deselected`, every requested file, the fixed functional
argv and Source marker/keyword defaults; ambient pytest arguments are refused.
A wholly slow module can therefore be accounted for without claiming its cases
executed. Missing observations, overlap, substituted profiles and failed or
incomplete selected outcomes still fail. The full Root release profile and
coverage floors are unchanged.

Manual hardening partitions its existing marker-filtered infrastructure collection into four disjoint module shards for each existing OS/runtime pair. The plugin is explicitly enabled only by that invocation and by the manual slow lane's `--infra-ci-observer-only slow` mode, which records the same bounded controller diagnostics without partition, selection or completion admission; nested pytest commands retain their declared semantics. Both modes write `output/readiness/ordinary-infra-ci/diagnostics/shard-<lane>.json` as diagnostics-only DATA (declared public test families, member hashes, phases, failures and worker loss; no parameter values, private paths or failure bodies) that the hosted jobs retain as `infra-diagnostics-*` artifacts; it cannot grant selection, coverage or acceptance. Selection receipts bind infrastructure, scripts, tests and CI configuration bytes, and preserve actual pytest failure codes. These are ordinary CI records, not the complete Root release acceptance profile. The required `coverage-infra` job validates all four Python 3.14/Linux receipts and coverage hashes, merges actual arcs into an isolated temporary data file and enforces the existing 60% floor before Codecov upload. An invalid shard invocation or partition refusal exits 2 (pytest's usage error is 4); because pytest's interrupted session also exits 2, every refusal prints its diagnostic (collection refusals from xdist workers reach the controller summary) and leaves no complete shard receipt, so neither a refusal nor an interruption can export coverage.

Public Root and project runtime workers create private fixture scratch outside
Source, ancestor Git checkouts and the selected runtime. Only the actual worker
adds that fresh path to its pytest call. Receipt, XML and coverage paths retain
their declared evidence locations and all original deadlines. Scratch cleanup
requires the same held physical directory; transported paths grant no cleanup.
