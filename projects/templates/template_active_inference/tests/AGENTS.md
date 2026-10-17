# Test Notes

No mocks — use real data, fixed RNG seeds, and `tmp_path` for I/O. Each gate and
invariant should have a negative control that proves it fails on bad input.

Gate negative controls live under `tests/gates/` (`test_output_gates.py`,
`test_manuscript_gates.py`, `test_claim_ledger.py`) plus `test_lean_gate.py`.
Use `gate_support.temporary_json_mutation()` for generated-artifact negative
controls so failures restore the mutated JSON byte-for-byte. Coverage-partition
helpers live in `_coverage_partition_helpers.py`; the former monolith is split
into `test_support_modules.py`, `test_full_verification_runs.py`, and
`test_full_verification_coverage.py`.

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
- `test_lean_gate_direct.py` exercises `gates/lean.py` with genuine exact-pinned
  Lean elaboration and axiom audits. Prepare the declared compiler explicitly
  before running these controls; gates do not silently acquire a toolchain.
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
groups, then divides the former 59-module remainder into explicit 29-module,
seven-module manuscript/pipeline, seven-module rendering/semantic-validation,
eight-node semantic certificate-integrity, and seven-node semantic
dependency/evidence/manuscript cohorts plus a computed terminal
cohort. The semantic cohorts are explicit pytest node IDs whose union and order
must equal the AST-derived set of supported top-level nonparametrized tests;
unsupported dynamic or class-based collection fails closed. Only the computed
terminal cohort reports and enforces the aggregate coverage floor. Every group
other than fixed-point remains at 1,800 seconds, and the fixed-point exception
must not spread to unrelated coverage or producer commands.

Run the suite serially within each project process. Collection prewarm and
fixtures share one disposable whole-project session copy. Gate controls and
composition restore that copy's mutable inputs after each test; they never
rewrite canonical source or publication bytes. This provides process isolation
for the existing coverage groups; it does not establish xdist compatibility.

Run full verification from this project root:
`uv run --extra dev python scripts/run_full_verification.py`. It runs gate-heavy coverage in
separate pytest processes and appends coverage into one final 90% gate. Use
focused `-q` commands only for package-local development loops. The legacy
single-process coverage run is available as `--monolithic-coverage` for
diagnostics only.

The project `pyproject.toml` assigns `scripts/run_full_verification.py
--coverage-only` to the single-project template Stage-01 lane. This runs the
complete coverage partition once on prepared artifacts, omitting research
preparation and duplicate noncoverage passes. The adapter does not infer it from the
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

Standard pytest expects the prepared gate-artifact snapshot under `output/` to
be present and semantically current. It fails fast when the snapshot is stale
instead of rebuilding the full research pipeline inside test collection. Set
`TEMPLATE_ACTIVE_INFERENCE_ALLOW_GATE_REBUILD=1` only for an intentional local
refresh run. Test collection rebuilds only its disposable session copy;
publication generation commands refresh the canonical outputs explicitly.

`--collect-only` discovery must remain read-only and skip gate prewarming. As a
negative control, `tests/test_gate_support_contracts.py::test_session_prewarm_skips_collect_only`
and `::test_collection_hook_skips_collect_only_before_selection` drive collect-only
sessions with a stub that raises if any prewarm or mutation is attempted, so the
skip path is proven rather than assumed. The
real test process performs the readiness check; discovery timeouts must not
leave partially refreshed artifacts behind for the run that follows.

Long in-process runs restore the disposable session copy's output snapshots
after each test so one negative control cannot invalidate the next test.

Coverage-only documentation measurement is therefore run from a symlink-free
disposable copy owned by the outer counts process. Per-test teardown is not a
crash-safety boundary: collection prewarm occurs before the session output
snapshot, and an outer timeout can kill pytest before fixture restoration.
