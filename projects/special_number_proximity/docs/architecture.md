# Architecture — `special_number_proximity`

## Flow

1. **`manuscript/config.yaml`** — `experiment.*` drives seeds, sample sizes, `q_max`, `quadratic_candidates`, `compare_mod1`, `q_sensitivity`, and histogram caps.
2. **`scripts/proximity_monte_carlo.py`** — loads YAML, builds pooled reference draws, computes `batch_min_rational_distances` and `batch_min_q_squared_errors`, emits `compare_constant_table` rows, writes JSON/CSV, saves three PNG histograms ($\delta_Q$ uniform subsample, $\delta_Q$ pooled subsample, $\mu_Q$ pooled subsample).
3. **`scripts/02_lattice_crosscheck.py`** — independent check that scaled-lattice and brute-force $\delta_Q$ agree on a short list of reals.
4. **`output/data/*.json`**, **`output/figures/*.png`** — consumed by manuscript sections (especially `04_results.md`).

## Module boundaries

| Layer | Location | Role |
|-------|----------|------|
| Domain | `src/*.py` | $\delta_Q$, $\mu_Q$, CF helpers, sampling, statistics |
| Orchestration | `scripts/*.py` | I/O, plotting, YAML |
| Verification | `tests/*.py` | No mocks; numeric parity and small-$Q$ exhaustives |

Infrastructure imports (`get_logger`) are optional fallbacks to stdlib logging when the repo root is not on `PYTHONPATH`.
