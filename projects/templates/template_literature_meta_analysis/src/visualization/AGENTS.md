# Visualization Module — Agent Directives

## Overview

Plotting modules generate publication-ready PNG figures. Orchestration:
`visualization/figure_runner.py` (`scripts/04_generate_figures.py`). All figures are fully
decoupled from computation: they consume pre-serialized JSON outputs from Stage 2/3 and write
static PNG files. No analysis logic belongs here.

## Invariants Agents Must Preserve

- **Agg backend**: `matplotlib.use("Agg")` must appear at the top of every module that imports
  matplotlib. This guarantees headless rendering in CI and during testing. Never import a
  display backend (`TkAgg`, `Qt5Agg`, etc.).
- **Fixed DPI**: Figure runners propagate the CLI `--dpi` value into `VIZ_CONFIG["dpi"]` (default 300). Do not hardcode a different
  DPI or omit the `dpi` argument to `fig.savefig()`.
- **Colorblind palette**: Use only `VIZ_CONFIG["palette"]` (Wong 2011, 8 colors). When more
  than 8 categories are needed, use a continuous colormap (`viridis`, `plasma`) rather than
  extending the discrete palette.
- **Font size floor**: `apply_visual_style()` enforces ≥ 16pt fonts. Do not manually set
  font sizes below 16pt in any plot — it would violate accessibility requirements.
- **Term heatmap discriminativeness**: `plot_term_heatmap` selects terms by **between-subfield
  variance**, not global mean TF-IDF. This is intentional — do not revert to global mean.
- **No side effects**: Each function creates its figure, saves to disk, closes it, and returns
  the path. Never keep figures open (causes memory leaks in batch runs).
- **Empty-data handling**: Every function must handle empty input gracefully (produce a blank
  figure with a "No data available" message). Never raise on empty data.

## Adding a New Figure

1. Add a function to the appropriate module following the signature:
   ```python
   def plot_something(data: ..., output_path: Path, ...) -> Path:
   ```
2. Apply `apply_visual_style()` at the top of the function.
3. Always call `plt.close(fig)` before returning.
4. Register the figure in `src/visualization/figure_runner.py` and the script-visible registry.
5. Add a `\includegraphics` reference in the manuscript section and a `\caption` + `\label`.
6. Add a test in `tests/visualization/` using a `tmp_path` fixture and real numerical data.

## Known Behavioral Notes

- **Word cloud**: `from wordcloud import WordCloud` is a lazy import inside the function body.
  If `wordcloud` is not installed, the function will raise `ImportError` only when called, not
  at module import time.
- **Spring layout**: `plot_citation_network` uses `seed=42` for reproducibility, but layout
  quality degrades for graphs with > 500 nodes; the function caps at `max_nodes=200` by default.
- **Heatmap term labels**: Long term labels rotate 45° and may overlap if `n_terms` > 25.
  Keep `n_terms` ≤ 20 for readable output.
- **PCA loading arrows**: Arrows scale by maximum absolute loading coordinate. Weak loadings
  may appear as very short arrows; this is expected behavior, not a rendering bug.

## Style Reference

```python
from visualization.style import VIZ_CONFIG, SUBFIELD_NAMES, HYPOTHESIS_NAMES, apply_visual_style

apply_visual_style()  # call once per function
palette = VIZ_CONFIG["palette"]        # list of 8 hex colors
figsize = VIZ_CONFIG["figsize"]        # (12, 7)
dpi = VIZ_CONFIG["dpi"]               # 300
title_size = VIZ_CONFIG["title_size"] # 20
font_size = VIZ_CONFIG["font_size"]   # 16 (minimum)
```
