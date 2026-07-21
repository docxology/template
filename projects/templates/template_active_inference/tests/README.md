# Tests

Project test suite for the multi-track Active Inference exemplar. Track counts are
registry-backed (`tracks.yaml`, `manuscript/sheaf/tracks.yaml`); tests should pin
behaviour and generated contracts, not copied numeric prose. Use real numerical
computations and fixed seeds rather than mocks.

- `test_free_energy.py`, `test_bernoulli_toy.py`, `test_decomposition.py`,
  `test_joint_dist.py` — analytical-track correctness.
- `test_si_runner.py`, `test_si_statistics.py`, `test_simulation_invariants.py` —
  pymdp rollout, logging, statistics, and invariant contracts.
- `test_gnn.py`, `test_semantic_sheaf.py`, `test_semantic_extensions.py` — GNN,
  ontology, semantic gluing, and promoted artifact concordance.
- `test_invariants.py`, `test_validation_spine.py`, `test_roadmap_promotion.py`,
  `test_track_consolidation_surface.py`, `test_track_consolidation_negative.py` —
  cross-track invariants, replay, provenance, canonical roadmap artifacts, and
  row/contract negative controls. Generated-artifact mutation tests use
  `gate_support.temporary_json_mutation()` so negative controls restore touched JSON
  even when the assertion path fails.
- `test_figures.py`, `test_figure_style.py` — figure registry parity, PNG dimensions, sheaf heatmaps.
- `test_sheaf_compose.py`, `test_sheaf_manifest.py`, `test_sheaf_registry.py`,
  `test_sheaf_coverage.py`, `test_sheaf_laws.py`, `test_layers_report.py` —
  compose, coverage matrix, manifest validation, finite sheaf laws, and generated
  layer tables.
- `test_manuscript_hydrate.py` — token substitution and fail-closed hydration.
- `test_manuscript_variables.py` — measured variables including sweep-derived `ising_mi_saturation`.
- `test_method_inventory.py` — generated method inventory coverage for every
  `def` and `class` under `src/` and `scripts/`.
- `test_support_modules.py`, `gates/` — `validate_manuscript` /
  `validate_outputs` / `build_lean` gates and negatives.
- `test_*_direct.py` with `direct_recompute_support.py` — leg-deterministic
  direct coverage of the recompute writers and validator failure branches,
  exercised against isolated project-tree copies so the coverage floor never
  depends on tracked-snapshot staleness (rules in `AGENTS.md`). Focused
  direct-only selections skip the unrelated real-tree gate prewarm.

## Fast iteration

Install the dev extras (adds `pytest-xdist` for parallelism) once:

```bash
uv sync --extra dev
```

Run the quick deterministic inner loop while iterating on a change:

```bash
uv run python -m pytest tests/ -m "not slow and not long_running" -q
```

The release profile retains every `slow` test while excluding only explicit
live-service and `long_running` lanes:

```bash
uv run python -m pytest tests/ -m "not requires_ollama and not requires_docker and not network and not bench and not benchmark and not performance and not long_running" -q
```

Analytical-track modules hold no shared project state, so they are safe to run
in parallel in isolation:

```bash
uv run pytest tests/test_free_energy.py tests/test_bernoulli_toy.py \
  tests/test_decomposition.py tests/test_joint_dist.py -n auto -q
```

Do **not** run the generated-artifact gates (`tests/gates/`,
`test_roadmap_promotion.py`, `test_track_consolidation_*.py`,
`test_simulation_invariants.py`) under `-n auto`: they mutate and restore shared
`manuscript/` and `output/` files, so parallel workers race on the same paths.
Run those serially (the default), then use `-n auto` only for the analytical and
other state-free modules above.

## Slow full-suite gates

The canonical full-suite evidence line lives in `TODO.md`; live pass counts
and measured coverage are tracked in
[`docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md), so no
suite counts or timings are pinned in this file. The slowest tests are
expected to be the end-to-end generated-artifact gates: manuscript mutation
negatives in `tests/gates/test_manuscript_gates.py`, claim-ledger negatives in
`tests/gates/test_claim_ledger.py`, roadmap artifact promotion in
`tests/test_roadmap_promotion.py`, validate-outputs orchestration in
`tests/test_simulation_invariants.py`, canonical sheaf row-only forgeries in
`tests/test_track_consolidation_negative.py`, `tests/test_track_consolidation_surface.py`, and the semantic fixed-point variable test
in `tests/test_manuscript_variables.py`.

For a reproducible complete run, prefer:

```bash
uv run python scripts/run_full_verification.py
```

Runtime is dominated by generated-artifact gates, but the verification script
runs coverage in separate pytest processes and appends the coverage data into
one final 90% gate. Use `--monolithic-coverage` only when diagnosing behavior
that specifically needs the legacy single pytest process.

The fixed-point direct tests share one isolated module copy. Authored GNN
contract defects fail before generated writers run, while missing formal-interop
outputs are regenerated through the owning artifact-builder registry and then
checked against the complete fixed-point validator. Any unresolved issue still
falls through to the full settlement loop; the fast paths do not bypass global
output-integrity checks.

Fixture-level performance candidates are the repeated marker variants in
`test_validate_manuscript_methods_sheaf_layers_negative_markers` and redundant
source mutations that currently force the same manuscript rebuild path. Keep at
least one end-to-end refresh characterization for each gate family; split only
the duplicate marker or row-only cases into cheaper source-contract checks.
