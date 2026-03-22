# special_number_proximity — project documentation

## Purpose

Empirical study of $\delta_Q(x) = \min_{p,q:\,1\leq q\leq Q}|x-p/q|$ for named reals vs random reference laws, with modular, tested Python and a multi-section manuscript.

## Pipeline integration

- **Discovery:** Valid project under `projects/special_number_proximity/` (`src/`, `tests/`, `manuscript/config.yaml`).
- **Tests:** `scripts/01_run_tests.py --project special_number_proximity`
- **Analysis:** `scripts/02_run_analysis.py` discovers and runs `scripts/02_lattice_crosscheck.py` then `scripts/proximity_monte_carlo.py` (lexicographic order)
- **PDF:** `scripts/03_render_pdf.py --project special_number_proximity`

## Subdirectories

Each of `src/`, `tests/`, `scripts/`, `manuscript/` carries `README.md` + `AGENTS.md`.

## Key source files

- `src/rational_distance.py` — $\delta_Q$ and $\mu_Q$ ($q^2|x-p/q|$) via the three-$p$ scan
- `src/diophantine_bounds.py` — scaled-lattice form $\min_q \|qx\|/q$ and Dirichlet residual tools
- `src/cf_distance.py` — convergent-only distance certificate
- `src/statistics_compare.py` — vectorised batches, percentiles, comparison rows (optional $\mu_Q$ ranks)
- `scripts/02_lattice_crosscheck.py` — JSON cross-check of implementations
- `scripts/proximity_monte_carlo.py` — YAML-driven study, two histograms, optional `q_sensitivity`
- `docs/` — architecture, testing philosophy, agent instructions
