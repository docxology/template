# Reproducibility

## Software

- Python $\geq 3.10$, NumPy, Matplotlib, PyYAML (declared in `projects/special_number_proximity/pyproject.toml`; root `uv sync` supplies the environment).
- Tests: `uv run pytest projects/special_number_proximity/tests/ --cov=projects/special_number_proximity/src --cov-fail-under=90`.

## Regenerating artifacts

```bash
uv run python projects/special_number_proximity/scripts/proximity_monte_carlo.py
# Optional: alternate project root (e.g. temporary checkout)
uv run python projects/special_number_proximity/scripts/proximity_monte_carlo.py --project-dir /path/to/projects/special_number_proximity
```

The script prints absolute paths to **five** outputs: JSON summary, CSV constant table, and three PNG figures (`proximity_histogram.png`, `proximity_histogram_pooled.png`, `proximity_histogram_mu.png`).

Edits to `manuscript/config.yaml` under `experiment:` change seeds, sample sizes, `q_max`, `quadratic_candidates`, `compare_mod1`, `q_sensitivity`, `histogram_uniform_cap`, and Beta parameters without editing Python.

## Data paths

| Artifact | Path |
|----------|------|
| Summary JSON | `projects/special_number_proximity/output/data/proximity_summary.json` |
| Table CSV | `projects/special_number_proximity/output/data/proximity_constants.csv` |
| Uniform $\delta_Q$ histogram | `projects/special_number_proximity/output/figures/proximity_histogram.png` |
| Pooled $\delta_Q$ histogram | `projects/special_number_proximity/output/figures/proximity_histogram_pooled.png` |
| Pooled $\mu_Q$ histogram | `projects/special_number_proximity/output/figures/proximity_histogram_mu.png` |
| Lattice cross-check | `projects/special_number_proximity/output/data/lattice_crosscheck.json` |

Run `uv run python projects/special_number_proximity/scripts/02_lattice_crosscheck.py` to refresh the lattice JSON.

## Combined manuscript build

```bash
uv run python scripts/03_render_pdf.py --project special_number_proximity
python3 -m infrastructure.validation.cli markdown projects/special_number_proximity/manuscript/
```

Authoring conventions for Markdown and cross-refs: [`docs/manuscript_conventions.md`](../docs/manuscript_conventions.md).
