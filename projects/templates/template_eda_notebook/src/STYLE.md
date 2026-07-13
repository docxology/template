# Source Code Style Guide

Code style and design conventions for `src/` modules in the
`template_eda_notebook` exemplar.

## Pure, Side-Effect-Free Functions

All functions in `src/eda/` must be **side-effect-free**: they take a
DataFrame (or array) in and return data out. They never plot, never print,
and never write files.

```python
# ✅ CORRECT: returns plot-ready data; no matplotlib, no I/O
def histogram_data(frame: pd.DataFrame, column: str, bins: int = 10) -> HistogramFigureData:
    values = frame[column].dropna().to_numpy(dtype=float)
    counts, edges = np.histogram(values, bins=bins)
    return HistogramFigureData(column, [int(c) for c in counts], [float(e) for e in edges])

# ❌ WRONG: draws a figure and writes a file from inside src/
def histogram_data(frame, column, bins=10):
    plt.hist(frame[column])              # Side effect: plotting
    plt.savefig("hist.png")              # Side effect: file write
```

Plotting, file I/O, and orchestration belong in `scripts/` (and notebook
cells), not in `src/`. This is why every figure preparer returns a
dataclass of numbers instead of a Matplotlib object.

## Type Hints

Every public function has complete annotations. Use `pandas.DataFrame` for
tabular inputs, `@dataclass(frozen=True)` for structured returns, and
`str | Path | None` for optional path arguments.

```python
def load_dataset(path: str | Path | None = None) -> pd.DataFrame: ...
def summary_statistics(frame: pd.DataFrame, schema: DatasetSchema | None = None) -> list[ColumnSummary]: ...
```

## Docstring Format

Google-style docstrings with Args/Returns/Raises:

```python
def correlation_matrix(frame: pd.DataFrame, schema: DatasetSchema | None = None) -> pd.DataFrame:
    """Return the Pearson correlation matrix of the numeric columns.

    Args:
        frame: Dataset to analyze (should be cleaned of NaNs first).
        schema: Optional schema; defaults to DatasetSchema.

    Returns:
        A square DataFrame of pairwise correlations, in schema order.
    """
```

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Functions | `snake_case` | `summary_statistics` |
| Classes | `PascalCase` | `DatasetSchema`, `ColumnSummary` |
| Constants | `UPPER_SNAKE` | `_DEFAULT_DATASET` |
| Private | `_leading_underscore` | `_DEFAULT_ROOT` |
| Parameters | descriptive `snake_case` | `top_n`, `bins` |

## pandas / numpy Idioms

```python
# ✅ Vectorized aggregation
frame.groupby(schema.group_column)[cols].mean()

# ✅ Surface missingness, never silently impute
frame[column] = pd.to_numeric(frame[column], errors="coerce")
```

- Use `to_numeric(..., errors="coerce")` to turn garbage cells into NaN.
- Use `dropna(subset=...)` and **report** how many rows were dropped.
- Use `corr(method="pearson")` for correlation; never reimplement it.

## Error Handling

- Validate inputs at function entry (`bins must be positive`, etc.).
- Use `ValueError` for bad arguments and `KeyError` for missing columns.
- Include actual values in messages for debuggability.
- Never catch and silently swallow exceptions (no blanket `except Exception`).

## Module Exports

`src/__init__.py` re-exports the public API from the `src.eda` subpackage,
so callers can write `from src import load_dataset`. The export set is kept
in sync with `src/__init__.py` — drift is caught by
`scripts/audit/check_template_drift.py`'s `__all___doc_drift` rule:

```python
__all__ = [
    # dataset
    "DatasetSchema",
    "load_dataset",
    "default_dataset_path",
    "numeric_columns",
    # cleaning
    "CleaningReport",
    "clean_dataset",
    "normalize_numeric",
    # statistics
    "ColumnSummary",
    "summary_statistics",
    "group_means",
    # correlation
    "correlation_matrix",
    "strongest_pairs",
    # figure-data preparers
    "HistogramFigureData",
    "CorrelationFigureData",
    "GroupCountFigureData",
    "EdaFigureSpec",
    "CORRELATION_COLOR_LIMITS",
    "EDA_FIGURE_SPECS",
    "FIGURE_REGISTRY_SCHEMA",
    "histogram_data",
    "correlation_heatmap_data",
    "group_count_data",
    "eda_figure_spec",
]
```

`src/project_paths.py` exposes path helpers (`project_output_dirs`,
`resolve_project_root`) used by the thin analysis script; they are
orchestration plumbing, not part of the EDA data API, so they are
intentionally NOT in `__init__.py.__all__`.

## See Also

- [AGENTS.md](AGENTS.md) — API reference and infrastructure integration.
- [../tests/PATTERNS.md](../tests/PATTERNS.md) — How to test code written here.
- [../scripts/CONVENTIONS.md](../scripts/CONVENTIONS.md) — How scripts use this code.
