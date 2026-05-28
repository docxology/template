# Visualizations

Registry-driven figures for analytical, simulation, and sheaf tracks.

| Module | Role |
| --- | --- |
| [`figures.yaml`](../../figures.yaml) | Style palette, per-figure alt/caption, `section_figures` bindings |
| [`figure_style.py`](figure_style.py) | `load_figure_style`, `apply_style` (rcParams + palette roles) |
| [`figure_registry.py`](figure_registry.py) | `FigureSpec`, markdown rendering, `figure_output_path` |
| [`figure_io.py`](figure_io.py) | `save_figure_png` — RGB-normalized PNG save for PDF pipeline |
| [`figures.py`](figures.py) | Analytical + SI generators, `FIGURE_GENERATORS`, `run_figure`, `generate_all_figures` |
| [`figures_sheaf*.py`](figures_sheaf.py) | Coverage heatmap payload, draw helpers, layers overview |

All analytical/SI PNGs route through `figure_io.save_figure_png` via `_save_styled_figure`.
Free-energy plots use `lambda_grid()` from `analytical/hyperparameters.py` (same SSOT as
`parameter_sweep.csv`). Sheaf heatmap colors derive from `figures.yaml` palette roles when
`load_coverage_config(..., project_root=root)` is used.

Entry point: `scripts/generate_figures.py` → `generate_all_figures()`.
