# Tests

Project test suite for the multi-track Active Inference exemplar (7 required pipeline
tracks, 10 sheaf fragment types; no mocks; real numerical computations with fixed seeds).

- `test_free_energy.py`, `test_bernoulli_toy.py`, `test_decomposition.py`,
  `test_joint_dist.py` — analytical-track correctness.
- `test_gnn.py` — GNN parsing and concordance.
- `test_invariants.py` — cross-track invariants.
- `test_figures.py`, `test_figure_style.py` — figure registry parity, PNG dimensions, sheaf heatmaps.
- `test_sheaf.py` — compose, coverage matrix, manifest validation.
- `test_manuscript_hydrate.py` — token substitution and fail-closed hydration.
- `test_manuscript_variables.py` — measured variables including sweep-derived `ising_mi_saturation`.
- `test_support_modules.py` — `validate_manuscript` / `validate_outputs` / `build_lean` gates and negatives.
