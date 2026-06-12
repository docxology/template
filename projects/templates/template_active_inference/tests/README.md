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
  `test_track_consolidation.py` — cross-track invariants, replay, provenance,
  counterexamples, and canonical roadmap artifacts. Generated-artifact mutation
  tests use `gate_support.temporary_json_mutation()` so negative controls restore
  touched JSON even when the assertion path fails.
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

## Slow full-suite gates

The 2026-06-12 full run
`COVERAGE_FILE=/tmp/template_ai.coverage uv run pytest tests/ --cov=src --cov-fail-under=90 --durations=20 -q`
passed 383 tests above the 90% gate (measured coverage tracked in
[`docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md)) in
1385.87 seconds. The slowest tests are
expected to be the end-to-end generated-artifact gates: manuscript mutation
negatives in `tests/gates/test_manuscript_gates.py`, claim-ledger negatives in
`tests/gates/test_claim_ledger.py`, roadmap artifact promotion in
`tests/test_roadmap_promotion.py`, validate-outputs orchestration in
`tests/test_simulation_invariants.py`, canonical sheaf row-only forgeries in
`tests/test_track_consolidation.py`, and the semantic fixed-point variable test
in `tests/test_manuscript_variables.py`.

Fixture-level performance candidates are the repeated marker variants in
`test_validate_manuscript_methods_sheaf_layers_negative_markers` and redundant
source mutations that currently force the same manuscript rebuild path. Keep at
least one end-to-end refresh characterization for each gate family; split only
the duplicate marker or row-only cases into cheaper source-contract checks.
