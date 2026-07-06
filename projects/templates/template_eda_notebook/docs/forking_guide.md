# Forking Guide — template_eda_notebook

> A 5-minute walkthrough for copying this exemplar into a new EDA project. The
> point is to make every decision explicit: what's required vs aesthetic, what's
> enforced vs convention, and what you'll hit friction on.

## TL;DR

```bash
# 0. From the repo root, install deps once
uv sync

# 1. Clean-copy the exemplar to your new project name
uv run python scripts/audit/copy_exemplar.py \
  --source templates/template_eda_notebook \
  --dest projects/working/my_eda_project \
  --new-name my_eda_project

# 2. Run the tests against your fork
uv run pytest projects/working/my_eda_project/tests \
    --cov=projects/working/my_eda_project/src --cov-fail-under=90 -q

# 3. Run the analysis against your fork
uv run python projects/working/my_eda_project/scripts/eda_analysis.py
```

**⚠️ Confidentiality invariant.** The repo `.gitignore` is configured so that
only the public canonical exemplars under `projects/templates/` are ever
git-tracked. Your fork (`projects/working/my_eda_project/`) is local-only and
won't be pushed even if you `git add -f` it. Read
[`../../../../CLAUDE.md`](../../../../CLAUDE.md) "CONFIDENTIALITY INVARIANT" for
the full fence.

## What you're forking

A **computational-notebook skeleton**: pure-data `src/eda/`, a thin analysis
script, real-data `tests/`, a walkthrough notebook, and a manuscript. The
included measurements dataset and three figures are throwaway scaffolding for
the **transferable pattern**: explore in a cell, then extract any computation
that matters into a tested `src/eda/` function. Your fork should preserve that
discipline regardless of the dataset you swap in.

## REQUIRED vs AESTHETIC

The full inventory lives in [`AGENTS.md`](AGENTS.md); the short version:

| Class | Examples | Action |
|---|---|---|
| REQUIRED — pipeline gate | `src/eda/*.py`, `src/__init__.py`, `data/measurements.csv`, all `tests/test_*.py`, `pyproject.toml`, `manuscript/config.yaml`, `manuscript/*.md`, `manuscript/references.bib`, `manuscript/preamble.md` | Keep them; the 90% coverage gate + LaTeX render depend on them |
| REQUIRED — orchestration | `scripts/eda_analysis.py`, `notebooks/eda_walkthrough.ipynb` | The analysis entry point and the archetype this template demonstrates |
| AESTHETIC | `docs/*.md`, `*/STYLE.md`, `*/PATTERNS.md`, `*/CONVENTIONS.md`, `*/AGENTS.md`, `*/README.md` | Drift detected only by `scripts/audit/check_template_drift.py`; update them when code changes |

## Concrete first steps after fork

### 1. Replace the dataset

Drop your CSV in at `data/measurements.csv` (or another path) and update
`src/eda/dataset.py::DatasetSchema` so `numeric_columns`, `group_column`, and
`id_column` match your columns. Keep `src/eda/` **infrastructure-free** — numpy
and pandas only.

### 2. Extend the EDA library

Add transforms to `src/eda/` (loading, cleaning, statistics, correlation, figure
data). Each is a pure function returning data — never plot or write files inside
`src/eda/`. Re-export new public functions from `src/eda/__init__.py` and
`src/__init__.py`.

### 3. Update the test suite

`tests/` enforces the [Zero-Mock Policy](testing_philosophy.md): real CSV / real
frames / `tmp_path`, no `unittest.mock` / `MagicMock` / `@patch`. Choose inputs
so the expected statistic is exact. Keep `tests/test_notebook.py` passing — it
verifies the notebook binds to your public surface and carries no logic in cells.

### 4. Update the notebook and script

Point the notebook cells and `scripts/eda_analysis.py` at your new functions.
The notebook must contain no `def`/`class`; the script plots the returned data
and writes to `output/`.

### 5. Run the drift checker before pushing

```bash
uv run python scripts/audit/check_template_drift.py --strict
```

## Common friction points (and fixes)

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: src` | Running a script from inside `src/` | `cd` to the repo root and use the full `projects/.../scripts/eda_analysis.py` path |
| `FileNotFoundError: dataset CSV not found` | `data/measurements.csv` missing or renamed | Restore the CSV or pass `load_dataset(path=...)` / update `DatasetSchema` |
| `test_notebook.py` fails on imports | A cell imports a name not in `src.__all__` | Export the name from `src/__init__.py` or remove the import |
| `MPLBACKEND` / display errors | Script imports pyplot before setting Agg | Set `os.environ.setdefault("MPLBACKEND", "Agg")` before importing pyplot |
| Stale `*.egg-info/` after rename | editable install under the old name | `rm -rf src/*.egg-info/`; `.gitignore` already covers future occurrences |

## See also

- [`AGENTS.md`](AGENTS.md) — full doc inventory and reading order.
- [`agent_instructions.md`](agent_instructions.md) — hard rules.
- [`architecture.md`](architecture.md) — module boundaries.
- [`testing_philosophy.md`](testing_philosophy.md) — zero-mock standard.
- [`output_inventory.md`](output_inventory.md) — producer/stage graph.
- [`troubleshooting.md`](troubleshooting.md) — symptom-driven fixes.
