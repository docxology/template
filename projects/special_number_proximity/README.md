# special_number_proximity

Finite-denominator rational proximity $\delta_Q(x)$ and scaled quality $\mu_Q(x)$ for classical constants versus Monte Carlo baselines.

## Commands

```bash
uv run pytest projects/special_number_proximity/tests/ --cov=projects/special_number_proximity/src --cov-fail-under=90
uv run python projects/special_number_proximity/scripts/02_lattice_crosscheck.py
uv run python projects/special_number_proximity/scripts/proximity_monte_carlo.py
uv run python projects/special_number_proximity/scripts/proximity_monte_carlo.py --project-dir projects/special_number_proximity
uv run python scripts/01_run_tests.py --project special_number_proximity --project-only
```

`manuscript/config.yaml` → `experiment`: `rng_seed`, `q_max`, `n_uniform`, `n_quadratic`, `n_beta`, `beta_a`, `beta_b`, `quadratic_candidates`, `compare_mod1`, `q_sensitivity`, `histogram_uniform_cap`.

Design notes: [`docs/architecture.md`](docs/architecture.md).

## Layout

- `src/` — $\delta_Q$, $\mu_Q$, continued fractions, scaled-lattice checks, sampling, batch statistics
- `tests/` — 90%+ coverage, zero mocks
- `scripts/` — `02_lattice_crosscheck.py`, `proximity_monte_carlo.py`
- `manuscript/` — sections `00_`–`09_`, `03a`–`03f`, `config.yaml`
- `docs/` — architecture, testing philosophy, [`manuscript_conventions.md`](docs/manuscript_conventions.md) (authoring rules; not in the PDF)
