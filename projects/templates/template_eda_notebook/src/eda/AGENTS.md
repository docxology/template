# `template_eda_notebook/src/eda/` - agent guide

## Purpose

Tested exploratory-data-analysis primitives: dataset loading, cleaning,
descriptive statistics, correlation ranking, and plot-ready figure data. The
walkthrough notebook and the thin scripts import from here.

## Rules

- Keep this subpackage standalone: import only `numpy`/`pandas`; never import
  `infrastructure.*` or a sibling project (no-cross-project-import drift rule).
- Never render plots here. Figure modules return plot-ready data structures;
  matplotlib stays in `scripts/` (thin-orchestrator contract).
- Surface missingness explicitly (no silent imputation) and keep every transform
  side-effect-free so tests stay deterministic.
- Re-export the public surface from `src/__init__.py` so callers write
  `from src import load_dataset` regardless of internal layout.

## See Also

- [`README.md`](README.md) - quick reference
- [`../AGENTS.md`](../AGENTS.md) - source-layer contract
