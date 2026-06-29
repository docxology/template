# Quick Start Guide

Get up and running with the `template_eda_notebook` exemplar in 5 minutes.

## Prerequisites

- Python 3.10 or higher
- [`uv`](https://github.com/astral-sh/uv) package manager (repo invariant — see the root `CLAUDE.md`)
- Git

## Setup (One-Time)

```bash
# 1. Clone the template repository (if you haven't already)
git clone https://github.com/docxology/template.git
cd template

# 2. Install dependencies at the repository root
uv sync

# 3. Verify installation
uv run python --version
```

## Run the Test Suite

Validate the environment and check that the project test suite passes with the
≥90% coverage gate:

```bash
uv run pytest projects/templates/template_eda_notebook/tests -v --tb=short
```

Expected: passing tests and coverage above the 90% gate. Live collection counts
are tracked in [`../../../docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md).

## Execute the Analysis Pipeline

Generate the EDA figures and the summary table:

```bash
uv run python projects/templates/template_eda_notebook/scripts/eda_analysis.py
```

**Outputs created under `projects/templates/template_eda_notebook/output/`:**
- `figures/` — `height_histogram.png`, `correlation_heatmap.png`, `group_counts.png`
- `data/` — `summary_statistics.csv`

## Explore Interactively

Open the walkthrough notebook, which calls the same tested `src.eda` functions:

```
notebooks/eda_walkthrough.ipynb
```

The cells contain no business logic — each one imports from `src` and calls a
tested function. This is the notebook -> tested src extraction workflow in
action.

## Render the Publication PDF

```bash
uv run python scripts/03_render_pdf.py --project templates/template_eda_notebook
```

## View Results

- **Figures**: browse `projects/templates/template_eda_notebook/output/figures/`
- **Summary table**: `cat projects/templates/template_eda_notebook/output/data/summary_statistics.csv`
- **PDF manuscript**: under `output/.../pdf/` after rendering

## Common Next Steps

- **Use your own data**: replace `data/measurements.csv` and update
  `src/eda/dataset.py::DatasetSchema`, then re-run the analysis.
- **Add a new EDA step**: extend a module in `src/eda/`, add a test, then call it
  from the notebook and `scripts/eda_analysis.py` (see `docs/architecture.md`).
- **Modify the manuscript**: edit markdown files under `manuscript/`, then
  re-render.

## Getting Help

- **Full documentation**: [`docs/README.md`](README.md) — navigation hub.
- **Agent rules**: [`docs/agent_instructions.md`](agent_instructions.md).
- **Troubleshooting**: [`docs/troubleshooting.md`](troubleshooting.md).
- **FAQ**: [`docs/faq.md`](faq.md).

## Quick Command Reference

| Task | Command |
|---|---|
| Run tests | `uv run pytest projects/templates/template_eda_notebook/tests -v` |
| Run analysis | `uv run python projects/templates/template_eda_notebook/scripts/eda_analysis.py` |
| Render PDF | `uv run python scripts/03_render_pdf.py --project templates/template_eda_notebook` |
| Copy final deliverables | `uv run python scripts/05_copy_outputs.py --project templates/template_eda_notebook` |
| Clean outputs | `rm -rf projects/templates/template_eda_notebook/output/` |
