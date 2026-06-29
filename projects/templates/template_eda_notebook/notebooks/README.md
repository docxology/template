# `template_eda_notebook/notebooks/`

Interactive exploratory-data-analysis walkthrough for the notebook exemplar.

## Files

| File | Role |
| --- | --- |
| `eda_walkthrough.ipynb` | Top-to-bottom EDA walkthrough: load fixture, surface missingness, descriptive stats, per-group means, correlation ranking, and diagnostic figure data. |

The notebook demonstrates the core lesson of this exemplar: a notebook is the
fast, interactive entry point a researcher reaches for first, but the moment a
computation matters it moves into [`../src/eda/`](../src/eda/README.md) where it
is typed, tested (>= 90% coverage), and reusable from scripts and the
manuscript. Every cell calls a tested library function; no business logic lives
in the cells. The test suite runs the notebook structurally, so it cannot drift
from the library it imports.

## See Also

- [`../src/eda/README.md`](../src/eda/README.md) - the tested EDA library
- [`../AGENTS.md`](../AGENTS.md) - project agent guide
