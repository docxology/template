# Standalone Fork Guide

## Purpose

`template_eda_notebook` is the canonical exploratory-data-analysis exemplar: a
walkthrough notebook backed by a fully-tested, standalone EDA library, a thin
analysis script, and publication-ready metadata.

## Copy This When

Use it for exploratory data analysis on tabular data where every computation
should trace to a tested function rather than living in a notebook cell.

## Clean Copy Command

From the template repository root:

```bash
uv run python scripts/copy_exemplar.py \
  --source templates/template_eda_notebook \
  --dest projects/working/my_eda_project \
  --new-name my_eda_project
```

Fallback when the helper is unavailable (rsync with explicit exclusions):

```bash
rsync -a \
  --exclude '.venv/' --exclude '.pytest_cache/' --exclude '.ruff_cache/' \
  --exclude 'htmlcov/' --exclude 'output/' --exclude 'rendered/' --exclude '*.egg-info/' \
  projects/templates/template_eda_notebook/ projects/working/my_eda_project/
```

## Required Post-Fork Edits

- Update `manuscript/config.yaml`, `domain_profile.yaml`, `experiment_plan.yaml`,
  `CITATION.cff`, `.zenodo.json`, `codemeta.json`, and `pyproject.toml`.
- Replace `data/measurements.csv` with your dataset and update
  `src/eda/dataset.py::DatasetSchema` to match its columns.
- Extend or replace the EDA functions in `src/eda/` and their tests; update the
  notebook cells to call them.
- Regenerate figures and the summary table before updating manuscript claims.

## Validation Commands

From the template repository root after copying into `projects/working/`:

```bash
uv run pytest projects/working/my_eda_project/tests \
  --cov=projects/working/my_eda_project/src --cov-fail-under=90
uv run python projects/working/my_eda_project/scripts/eda_analysis.py
```

For the public exemplar:

```bash
uv run pytest projects/templates/template_eda_notebook/tests \
  --cov=projects/templates/template_eda_notebook/src --cov-fail-under=90
```

## Standalone By Design

Unlike some exemplars, the EDA library is fully standalone: `src/eda/` imports
only `numpy` and `pandas` and never imports `infrastructure.*`. The only place
that touches shared infrastructure is the thin analysis script and the
manuscript-rendering pipeline, so the library itself is forkable as an
infrastructure-free package.

## What Not To Claim

Do not claim new EDA findings from a renamed fork until the figures
(`output/figures/*.png`) and the summary table
(`output/data/summary_statistics.csv`) have been regenerated from the forked
dataset and code.
