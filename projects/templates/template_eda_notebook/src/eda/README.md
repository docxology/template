# `template_eda_notebook/src/eda/`

Tested exploratory-data-analysis library for the notebook exemplar.

The walkthrough notebook (`notebooks/eda_walkthrough.ipynb`) and the thin
analysis scripts call these functions instead of burying logic in cells or
shell glue, so the EDA workflow is reproducible and unit-tested.

## Files

| File | Role |
| --- | --- |
| `__init__.py` | Public EDA exports re-exported from `src/__init__.py`. |
| `dataset.py` | Load the deterministic CSV fixture; typed schema and numeric-column helpers. |
| `cleaning.py` | Drop missing-value rows (reported, not imputed) and z-score normalize numeric columns. |
| `statistics.py` | Per-column descriptive statistics and per-group means via `pandas`. |
| `correlation.py` | Pearson correlation matrix and ranked strongest off-diagonal feature pairs. |
| `figures.py` | Plot-ready figure data (histogram bins, heatmap matrix, group counts); no matplotlib. |

## See Also

- [`../README.md`](../README.md) - project source overview
- [`../AGENTS.md`](../AGENTS.md) - source-layer editing rules
