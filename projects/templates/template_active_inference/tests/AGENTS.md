# Test Notes

No mocks — use real data, fixed RNG seeds, and `tmp_path` for I/O. Each gate and
invariant should have a negative control that proves it fails on bad input.

Gate negative controls live under `tests/gates/` (`test_output_gates.py`,
`test_manuscript_gates.py`, `test_claim_ledger.py`) plus `test_lean_gate.py`.
Use `gate_support.temporary_json_mutation()` for generated-artifact negative
controls so failures restore the mutated JSON byte-for-byte. Small support
helpers remain in `test_support_modules.py`.

Sheaf tests are split by concern: `test_sheaf_manifest.py`, `test_sheaf_registry.py`,
`test_sheaf_compose.py`, `test_sheaf_coverage.py`, `test_sheaf_cli.py`,
`test_coverage_pipeline.py`, `test_sweep_io.py` (no monolithic `test_sheaf.py`).

## Leg-deterministic direct coverage (`test_*_direct.py`)

The `test_*_direct.py` family exists so the 90% coverage floor never depends on
whether the tracked `output/` snapshot happens to read stale on a given CI leg
(py3.10 float drift used to be the only thing exercising the heavy recompute
modules). These tests call the recompute writers directly against an isolated
copy of the project tree built by `direct_recompute_support.copy_project_tree()`
— the tracked snapshot is never rewritten. Rules for this family:

- Never assert that the tracked snapshot (or a fresh copy of it) validates as
  current BEFORE an in-session settlement — the py3.10 leg reads it stale.
  Settle first, then assert the non-rewriting fast path.
- Mutations of a copy restore byte-for-byte in `finally`, against the state
  written THIS session (not the tracked bytes).
- `gates/lean.py` subprocess/parse paths are driven by a scripted stub `lake`
  executable on `PATH` (a real subprocess with test-scripted responses — the
  CLI analogue of the sanctioned `pytest-httpserver` pattern), so they stay
  covered on CI runners with no Lean toolchain.
- Focused selections containing only `test_*_direct.py` modules skip the
  real-tree gate-artifact prewarm. Mixed and full-suite selections still run
  the prewarm once, before per-test timeout accounting starts.

## Runtime and parallelism

Measured cost structure (py3.12, serial): the suite is ~280s without coverage
and roughly double that with it — branch coverage instrumentation is the
single largest cost, and `COVERAGE_CORE=sysmon` cannot remove it before
Python 3.14 (sys.monitoring cannot measure branches earlier; coverage.py falls
back with a `no-sysmon` warning). Do not trade `branch = true` away for speed.
The fixed-point coverage singleton has a 2,400-second group ceiling aligned
with its forced-settlement item. The twelve-group coverage plan gives canonical
sheaf negative controls and consolidation surface checks separate 1,800-second
groups, then divides the former 57-module remainder into explicit 29-module,
seven-module manuscript/pipeline, seven-module rendering/semantic-validation,
eight-node semantic certificate-integrity, and seven-node semantic
dependency/evidence/manuscript cohorts plus a computed 13-module terminal
cohort. The semantic cohorts are explicit pytest node IDs whose union and order
must equal the AST-derived set of supported top-level nonparametrized tests;
unsupported dynamic or class-based collection fails closed. Only the 13-module
terminal cohort reports and enforces the aggregate coverage floor. Every group
other than fixed-point remains at 1,800 seconds, and the fixed-point exception
must not spread to unrelated coverage or producer commands.

This suite is NOT xdist-safe: gate tests compose and validate the REAL project
tree and the autouse conftest fixture restores tracked sources/outputs after
every test, so parallel workers race each other (observed corrupting readiness
mid-run under `-n 6`) — and any test that merely READS the real tree races
with another worker's restore-writes. Run it serially. The safe multi-core
design, if wall-clock ever matters more than simplicity, is per-worker
whole-tree copies (each worker gets its own project copy and a coverage
`[paths]` remap), not in-process `-n N`.

The gate tests call `compose_all_sections` / `ensure_coverage_artifacts` on the
real project root, which rewrites tracked manuscript, GNN, ontology, and config
sources to reflect whatever artifacts the run produced. The autouse fixture in
`conftest.py` snapshots mutable tracked project sources at session start and
restores them after every test, so long runs do not let a mutation or composed
status table leak into later checks. Never `git commit -a` a degraded status
table after a run.

Run full verification from this project root:
`uv run --extra dev python scripts/run_full_verification.py`. It runs gate-heavy coverage in
separate pytest processes and appends coverage into one final 90% gate. Use
focused `-q` commands only for package-local development loops. The legacy
single-process coverage run is available as `--monolithic-coverage` for
diagnostics only.

The project `pyproject.toml` explicitly assigns that command to the
single-project template Stage-01 lane. The adapter does not infer it from the
filename and does not lower the floor: it requires a fresh nonce-bound receipt,
aggregates real JUnit outcomes from the final coverage groups once, and reads
the resulting coverage database independently. The all-project union runner
continues to use its isolated generic pytest policy; GitHub's per-project
public matrix invokes this single-project contract.

Generic Stage-01 profile flags do not silently rewrite a project's declared
argv. For an intentional bounded direct loop use
`uv run --extra dev python scripts/run_full_verification.py --profile quick`; use
`--profile release` or `--profile exhaustive` explicitly when that selection is
the intended evidence. The declared pipeline command omits `--profile` and
therefore preserves this project's historical comprehensive selection.

Standard pytest expects the committed gate-artifact snapshot under `output/` to
be present and semantically current. It fails fast when the snapshot is stale
instead of rebuilding the full research pipeline inside test collection. Set
`TEMPLATE_ACTIVE_INFERENCE_ALLOW_GATE_REBUILD=1` only for an intentional local
refresh run that will regenerate and review the tracked outputs.

`--collect-only` discovery must remain read-only and skip gate prewarming. The
real test process performs the readiness check; discovery timeouts must not
leave partially refreshed artifacts behind for the run that follows.

Long in-process runs restore tracked `output/` snapshots after each test. Tests
may exercise real writers against the project tree, but they must not leave
canonical gate artifacts stale for later `ensure_gate_artifacts()` calls.

Coverage-only documentation measurement is therefore run from a symlink-free
disposable copy owned by the outer counts process. Per-test teardown is not a
crash-safety boundary: collection prewarm occurs before the session output
snapshot, and an outer timeout can kill pytest before fixture restoration.
