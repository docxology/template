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
  counterexamples, and canonical roadmap artifacts.
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
