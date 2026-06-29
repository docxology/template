# Testing Philosophy: The Zero-Mock Standard

This EDA exemplar strictly forbids mocking in data-analysis validation.

## Why Zero Mocks?

The core insight is architectural: if a function requires a mock to be tested,
it is doing I/O, plotting, or producing side-effects — which means it belongs in
`scripts/` (a thin orchestrator) or a notebook cell, not in `src/eda/` (pure
data logic). The purity of `src/eda/` is what makes zero-mock testing
achievable. Every function takes a DataFrame (or array) in and returns data out,
so tests simply call functions with the real shipped CSV or a tiny real frame
and verify real numeric outputs.

If you ever feel the urge to mock something in a test for `src/`, treat it as a
signal: move that code to `scripts/` and test the `src/` boundary directly.

## The Validation Suite

| File | Role |
| --- | --- |
| `test_dataset.py` | `load_dataset`, `DatasetSchema`, `numeric_columns`, NaN preservation, temp-CSV round trips |
| `test_cleaning.py` | `clean_dataset` row-drop reporting, `normalize_numeric` z-scores, no input mutation |
| `test_statistics.py` | `summary_statistics` exact values, `group_means` per-group aggregation |
| `test_correlation.py` | `correlation_matrix` symmetry/unit-diagonal, `strongest_pairs` ranking + sign |
| `test_figures.py` | Figure-data preparers: histogram bins, heatmap values, group counts |
| `test_project_paths.py` | `project_output_dirs` and `resolve_project_root` path plumbing |
| `test_eda_analysis_script.py` | Thin script `run_eda()` writes real figures + summary CSV to a temp root |
| `test_notebook.py` | Notebook is valid nbformat; imports bind to `src.__all__`; cells define no logic |

Configuration: `projects/templates/template_eda_notebook/pyproject.toml`
(`fail_under = 90`, matching the root pipeline gate).

Conftest: `projects/templates/template_eda_notebook/tests/conftest.py`
(sets `MPLBACKEND=Agg`, adds `src/` and the repo root to `sys.path`).

Live test count and coverage percentage:
[`docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md)
(or `uv run pytest tests/ --collect-only -q` from the project directory).

## Test Class Inventory

The classes below all exist in `tests/`. Keep this list and `tests/AGENTS.md`
in sync — the `test_class_drift` gate fails if a doc names a class that does not
exist.

| Class | File | Covers |
| --- | --- | --- |
| `TestDatasetSchema` | `test_dataset.py` | Frozen schema fields and `all_columns` |
| `TestLoadDataset` | `test_dataset.py` | CSV load, dtype coercion, NaN preservation, missing-file error |
| `TestNumericColumns` | `test_dataset.py` | Schema-driven numeric column selection |
| `TestCleanDataset` | `test_cleaning.py` | Drop-incomplete-rows reporting and index reset |
| `TestNormalizeNumeric` | `test_cleaning.py` | Z-scoring, constant-column guard, immutability |
| `TestSummaryStatistics` | `test_statistics.py` | Exact mean/std/min/median/max per column |
| `TestGroupMeans` | `test_statistics.py` | Per-group means; missing-group-column error |
| `TestCorrelationMatrix` | `test_correlation.py` | Pearson matrix shape, symmetry, unit diagonal |
| `TestStrongestPairs` | `test_correlation.py` | Absolute-correlation ranking, sign, `top_n` guard |
| `TestHistogramData` | `test_figures.py` | Bin counts/edges; positive-bins and missing-column errors |
| `TestCorrelationHeatmapData` | `test_figures.py` | Heatmap labels and square value grid |
| `TestGroupCountData` | `test_figures.py` | Sorted labels and aligned counts |
| `TestProjectOutputDirs` | `test_project_paths.py` | Output directory map under a root |
| `TestResolveProjectRoot` | `test_project_paths.py` | Module-attribute override and default fallback |
| `TestEdaAnalysisScript` | `test_eda_analysis_script.py` | `run_eda()` artifact writing |
| `TestNotebookStructure` | `test_notebook.py` | Valid nbformat; markdown + code cells present |
| `TestNotebookSrcBinding` | `test_notebook.py` | Imports resolve to `src.__all__`; no logic in cells |

## Coverage Mechanics

```toml
[tool.coverage.run]
source = ["src"]
branch = true
omit = ["tests/*", "*/__init__.py", "*/test_*.py"]

[tool.coverage.report]
fail_under = 90
```

Authoritative gate (measures all of `src/`):

```bash
cd projects/templates/template_eda_notebook
uv run pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=90
```

## Zero-Mock Checklist

- [ ] Test uses the real shipped CSV or a real DataFrame / temp CSV as input.
- [ ] Test calls `src/eda/` functions directly with real data.
- [ ] Test asserts numeric properties (exact stats, correlation signs, bin
      counts), not call counts.
- [ ] No `unittest.mock`, `MagicMock`, `create_autospec`, `@patch`, or mock
      factories anywhere.
- [ ] File I/O tests use `tmp_path` real files, not patched `open`/`read_csv`.

## Structural Rule: If You Need a Mock, Move the Code

- **`src/eda/*`** — pure data transforms; no plotting, no file I/O, no
  `infrastructure.*` imports.
- **`scripts/eda_analysis.py`** — the only place matplotlib and file writes
  live; tested by `test_eda_analysis_script.py` against a temp root.

## Running the Gate

A green exit code is **not** proof the suite ran. Confirm **N collected > 0 AND
coverage ≥ 90%**.

```bash
cd projects/templates/template_eda_notebook
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
```

See [`troubleshooting.md`](troubleshooting.md).
