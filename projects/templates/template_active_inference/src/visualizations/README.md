# Visualizations

Registry-driven figures for analytical, simulation, and sheaf tracks.

| Module | Role |
| --- | --- |
| [`figures.yaml`](../../figures.yaml) | Style palette, per-figure alt/caption, `section_figures` bindings |
| [`figure_style.py`](figure_style.py) | `load_figure_style`, `apply_style` (rcParams + palette roles) |
| [`figure_registry.py`](figure_registry.py) | `FigureSpec`, markdown rendering, `figure_output_path` |
| [`figure_helpers.py`](figure_helpers.py) | Shared styled figure context, axis cleanup, wrapped annotations, notes, arrows, and JSON artifact loading |
| [`figure_io.py`](figure_io.py) | RGB-normalized PNG save plus render metrics for mode, size, aspect ratio, and blank detection |
| [`figures.py`](figures.py) | Analytical + SI generators, `FIGURE_GENERATORS`, `run_figure`, `generate_all_figures` |
| [`figures_diagrams.py`](figures_diagrams.py) | Dashboard, schematic, graph, and concordance figures |
| [`figures_sheaf*.py`](figures_sheaf.py) | Coverage heatmap payload, draw helpers, layers overview |

The root registry currently defines 20 publication PNG outputs. All rendered
PNGs route through `figure_io.save_figure_png`; `image_render_metrics()` gives
the visualization audit a live check for RGB mode, nonblank pixels, dimensions,
and aspect-ratio bounds. Free-energy plots use `lambda_grid()` from
`analytical/hyperparameters.py` (same SSOT as `parameter_sweep.csv`). Sheaf
heatmap colors derive from `figures.yaml` palette roles when
`load_coverage_config(..., project_root=root)` is used.

Visualization quality is validated through generated source-map, hash-manifest,
section-binding, and statistical-bridge reports. A figure is not accepted merely
because its registry row exists; the live PNG and its metadata must agree with
the current generated audit rows.

Entry point: `scripts/generate_figures.py` → `generate_all_figures()`.
