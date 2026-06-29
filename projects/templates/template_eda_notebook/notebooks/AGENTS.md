# `template_eda_notebook/notebooks/` - agent guide

## Purpose

Holds the interactive walkthrough notebook that demonstrates the
notebook-to-tested-`src` extraction workflow. The notebook is the fast entry
point; all analytical logic lives in `src/eda/`.

## Rules

- Cells contain **no business logic**. Every analytical step calls a function
  from the tested `src.eda` library — if a computation matters, it belongs in
  `src/` (typed, tested, reusable), not in a cell.
- Keep run order strictly top-to-bottom; the test suite exercises the notebook
  structurally so it cannot silently drift from the library it imports.
- Do not commit large or non-deterministic outputs; the notebook reads the
  shipped deterministic CSV fixture under `data/`.

## See Also

- [`README.md`](README.md) - quick reference
- [`../src/eda/README.md`](../src/eda/README.md) - the library the notebook calls
- [`../AGENTS.md`](../AGENTS.md) - project agent guide
