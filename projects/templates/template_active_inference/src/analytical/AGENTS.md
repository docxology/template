# Analytical Track Notes

Closed-form reference implementation for the manuscript formalism. This lane is
the deterministic oracle for MI, free-energy decomposition, coupling, and
invariant checks used by manuscript variables and toy sweep artifacts.

## Where To Look

| Task | Location |
| --- | --- |
| Bernoulli K=2 model | `bernoulli_toy.py` |
| Joint distribution helpers | `joint_dist.py` |
| Free energy and MI terms | `free_energy.py`, `decomposition.py` |
| Coupling and hyperparameters | `coupling.py`, `hyperparameters.py` |
| Analytical invariant registry | `invariants.py` |
| Sweep persistence/statistics | `sweep_io.py` |

## Contracts

- Prefer exact expressions and deterministic grids over sampling. Any randomness
  must have a fixed seed and an explicit reason.
- Keep public function signatures stable; tests and scripts import these modules
  directly.
- Cross-check formulas against Lean statements under `../../lean/`, GNN model
  declarations, and simulation outputs before changing manuscript claims.
- Persisted sweep columns are a contract for `scripts/run_analytical_sweep.py`,
  `scripts/z_generate_manuscript_variables.py`, and downstream figures.
- Add or update invariant coverage when changing a formula that appears in the
  manuscript.

## Commands

```bash
uv run python scripts/run_analytical_sweep.py
uv run pytest tests/test_bernoulli_toy.py tests/test_decomposition.py tests/test_free_energy.py tests/test_joint_dist.py tests/test_sweep_io.py
```
