# `template_eda_notebook/notebooks/`

Interactive exploratory-data-analysis walkthrough for the notebook exemplar.

## Files

| File | Role |
| --- | --- |
| `eda_walkthrough.ipynb` | Top-to-bottom EDA walkthrough: load fixture, surface missingness, descriptive stats, per-group means, correlation ranking, and diagnostic figure data. |

The notebook demonstrates the core lesson of this exemplar: a notebook is the
fast, interactive entry point a researcher reaches for first, but the moment a
computation matters it moves into [`../src/template_eda_notebook/eda/`](../src/template_eda_notebook/eda/README.md) where it
is typed, tested (>= 90% coverage), and reusable from scripts and the
manuscript. Every cell calls a tested library function; no business logic lives
in the cells. The test suite checks structure and executes a fresh NBClient kernel with an
independent numerical oracle, so it cannot drift
from the library it imports.

## See Also

- [`../src/template_eda_notebook/eda/README.md`](../src/template_eda_notebook/eda/README.md) - the tested EDA library
- [`../AGENTS.md`](../AGENTS.md) - project agent guide

From the monorepo root, run
`uv run python projects/templates/template_eda_notebook/scripts/execute_notebook.py`.
Use `--python` to select the kernel interpreter and positive
`--startup-timeout`, `--cell-timeout` and `--run-timeout` values to bound execution.
Saved outputs never establish acceptance; the source notebook stays unchanged.
