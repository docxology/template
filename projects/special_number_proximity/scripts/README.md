# scripts/

| Script | Purpose |
|--------|---------|
| `02_lattice_crosscheck.py` | JSON witness: lattice vs brute $\delta_Q$ |
| `proximity_monte_carlo.py` | YAML-driven Monte Carlo; JSON, CSV, two histogram PNGs |

```bash
uv run python projects/special_number_proximity/scripts/02_lattice_crosscheck.py
uv run python projects/special_number_proximity/scripts/proximity_monte_carlo.py
uv run python projects/special_number_proximity/scripts/proximity_monte_carlo.py --project-dir projects/special_number_proximity
```
