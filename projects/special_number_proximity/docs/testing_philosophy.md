# Testing philosophy

- **No mocks:** All assertions use real floating-point data, NumPy RNG streams with fixed seeds, or subprocess-free imports of script modules.
- **Reference implementation:** `rational_at_min_distance` defines $\delta_Q$; exhaustive enumeration for $x \in [0,1)$ and $Q \leq 30$ guards the three-$p$ scan.
- **Parity checks:** Vectorised batch helpers match scalar loops; `min_rational_distance_via_scaled_lattice` matches the scan; convergent-only distances are $\geq \delta_Q$.
- **Script smoke:** `test_proximity_monte_carlo_module` calls `run_proximity_study` with tiny samples and inspects JSON-shaped dicts.

Coverage target: **90%+** on `projects/special_number_proximity/src` (CI uses `scripts/01_run_tests.py`).
