# scripts/

Thin orchestrators (no domain math). Executed by `scripts/02_run_analysis.py` in lexicographic order.

| Script | Outputs |
|--------|---------|
| `01_generate_density_tables.py` | `output/data/density_summary.json`, `preset_densities.csv` |
| `02_plot_density_overview.py` | `output/figures/density_overview.png` |

Each script prints absolute paths to generated files on success.
