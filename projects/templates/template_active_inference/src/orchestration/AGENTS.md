# Orchestration Notes

The manifest is the contract between scripts and outputs. Keep it in sync with
`../../scripts/` and the gate artifact manifest in `../gates/artifact_manifest.py`;
a stage that declares an output must actually produce it.

**Sheaf coverage artifact order (canonical):** `compose_all_sections` →
`emit_coverage_artifacts` (JSON only). `generate_all_figures` →
`ensure_coverage_artifacts` (JSON if stale, heatmap PNG, coverage page) then
`FIGURE_GENERATORS` dispatch. Prefer `ensure_coverage_artifacts` when adding new
entry points; use `run_coverage_pipeline(..., force=True)` for explicit full refresh.

`scripts/run_full_verification.py` executes the complete ordered analysis
manifest, including SI simulations, animation, validation-spine producers,
promoted roadmap tracks, and manuscript variables before output validation. Do
not add a producer to `manuscript/config.yaml` or `pipeline_manifest.py` without
also keeping this full-verification path capable of regenerating it from a
stale output tree. It also regenerates the source-derived method inventory
before checking it, so adding a documented method cannot leave the verification
lane permanently stale.

The project explicitly declares this script as its single-project Stage-01
verifier because the 90% branch-coverage contract is reached through isolated
`--cov-append` groups, not the diagnostic monolithic quick lane. When the
generic runner supplies `TEMPLATE_PROJECT_TEST_RECEIPT`, the verifier records
JUnit outcomes only from the final coverage groups (never the duplicate
pre-pass), parses them with `defusedxml`, combines pytest-produced warning and
discovery sidecars, and writes the nonce-bound receipt after every postflight
gate has passed. Coverage groups use the outer adapter's exact pinned
interpreter rather than a nested `uv run` environment. Direct invocations
without that environment remain unchanged.

`scripts/run_full_verification.py --coverage-only --profile <name>` runs only
the same twelve coverage groups: the first starts a fresh Coverage database and
groups two through twelve append. Canonical sheaf negative controls and
consolidation surface checks run in separate bounded groups; the sixth
singleton owns `tests/test_fixed_point_direct.py`; and the former 57-module
remainder is split into an explicit 29-module analytical/figure/formal group,
an explicit seven-module manuscript/pipeline/precision/configuration group, an
explicit seven-module rendering/scholarship/semantic-validation group, a
source-derived semantic sheaf split with explicit eight-node certificate and
seven-node dependency/evidence/manuscript cohorts, and a computed 13-module
simulation/support/visualization terminal group. Only that twelfth group reports
and enforces the floor. The selector validator rejects missing, duplicate,
invented, dynamically generated, class-based, parametrized, or bare-module
semantic selections while keeping every ordinary test module exact-once. Both
the coverage-only route and the receipt-bearing full verifier use this validated
partition. It omits verifier-owned refresh, hydration, output-gate, and receipt
phases. The documentation counts measurer invokes this route only from a
disposable copy of the complete project tree; do not point it at the canonical
publication tree when measuring release coverage.
The exact fixed-point coverage group has a 2,400-second inner ceiling aligned
with its slowest item; every other command retains the 1,800-second default, and
the counts parent bounds the complete Active measurement at 6,900 seconds,
aligned with the declared Stage-01 verifier and below the shared 7,200-second
stage boundary. That aggregate wall-clock boundary does not reserve or sum each
group's independent maximum.
