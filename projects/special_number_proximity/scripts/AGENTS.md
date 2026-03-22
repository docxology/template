# scripts/ — technical reference

## `proximity_monte_carlo.py`

- **Config:** `manuscript/config.yaml` → `experiment`: `rng_seed`, `q_max`, `n_uniform`, `n_quadratic`, `n_beta`, `beta_a`, `beta_b`, `quadratic_candidates`, `compare_mod1`, `q_sensitivity`, `histogram_uniform_cap`.
- **CLI:** `--project-dir PATH` selects the project root (default: parent of `scripts/`).
- **API:** `main(project_dir: Path | None = None)`, `run_proximity_study(...)`, `save_outputs(...)`.
- **Imports:** Prepends `project_root/src` to `sys.path`; uses `constants`, `sampling`, `statistics_compare`.
- **Logging:** `infrastructure.core.logging_utils.get_logger` when importable; else stdlib logging.
- **Outputs:** `output/data/proximity_summary.json` (includes `reference_q_squared_summary`, optional `q_sensitivity`), `proximity_constants.csv`, `output/figures/proximity_histogram.png`, `proximity_histogram_pooled.png`, `proximity_histogram_mu.png`.
- **Stdout:** Prints absolute paths to all five artifacts.

## `02_lattice_crosscheck.py`

Exports `output/data/lattice_crosscheck.json` comparing `min_rational_distance` and `min_rational_distance_via_scaled_lattice` on a fixed list of reals.
