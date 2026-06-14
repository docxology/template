# Visualizations

Registry-driven figures for analytical, simulation, and sheaf tracks.

| Module | Role |
| --- | --- |
| [`figures.yaml`](../../figures.yaml) | Style palette, typography/layout tokens, per-figure alt/caption, `section_figures` bindings |
| [`figure_style.py`](figure_style.py) | `load_figure_style`, `apply_style` (rcParams, palette roles, typography tokens) |
| [`figure_registry.py`](figure_registry.py) | `FigureSpec`, markdown rendering, `figure_output_path` |
| [`figure_helpers.py`](figure_helpers.py) | Shared styled figure context, axis cleanup, wrapped annotations, notes, arrows, and JSON artifact loading |
| [`figure_io.py`](figure_io.py) | RGB-normalized PNG save plus render metrics for mode, size, aspect ratio, and blank detection |
| [`figures.py`](figures.py) | Analytical + SI generators, `FIGURE_GENERATORS`, `run_figure`, `generate_all_figures` |
| [`figures_diagrams.py`](figures_diagrams.py) | Dashboard, schematic, graph, and concordance figures |
| [`figures_sheaf*.py`](figures_sheaf.py) | Coverage heatmap payload, draw helpers, layers overview |

The root registry defines publication PNG outputs, including sheaf verifier
maps such as `track_lane_promotion_map` and `artifact_contract_map`. All rendered
PNGs route through `figure_io.save_figure_png`; `image_render_metrics()` gives
the visualization audit a live check for RGB mode, nonblank pixels, dimensions,
and aspect-ratio bounds. Free-energy plots use `lambda_grid()` from
`analytical/hyperparameters.py` (same SSOT as `parameter_sweep.csv`). Sheaf
heatmap colors derive from `figures.yaml` palette roles when
`load_coverage_config(..., project_root=root)` is used.

Visualization quality is validated through generated source-map, hash-manifest,
section-binding, and statistical-bridge reports. A figure is not accepted merely
because its registry row exists; the live PNG and its metadata must agree with
the current generated audit rows. The audit also checks that figure modules use
shared style tokens instead of raw font-size literals and that non-registry
visual outputs are explicitly classified as auxiliary artifacts.

Entry point: `scripts/generate_figures.py` → `generate_all_figures()`.
