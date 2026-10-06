# `template_eda_notebook/notebooks/` - agent guide

## Purpose

Holds the interactive walkthrough notebook that demonstrates the
notebook-to-tested-`src` extraction workflow. The notebook is the fast entry
point; all analytical logic lives in `src/template_eda_notebook/eda/`.

## Rules

- Cells contain **no business logic**. Every analytical step calls a function
  from the tested `template_eda_notebook.eda` library — if a computation matters, it belongs in
  `src/` (typed, tested, reusable), not in a cell.
- Keep run order strictly top-to-bottom. Structural tests and real NBClient
  fresh-kernel execution bind the notebook to the source library and an
  independent NumPy/Pandas numerical oracle. Saved outputs never prove success.
- Do not commit large or non-deterministic outputs; the notebook reads the
  shipped deterministic CSV fixture under `data/`.

## See Also

- [`README.md`](README.md) - quick reference
- [`../src/template_eda_notebook/eda/README.md`](../src/template_eda_notebook/eda/README.md) - the library the notebook calls
- [`../AGENTS.md`](../AGENTS.md) - project agent guide
