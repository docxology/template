# Style Guide

This document defines the coding and communication style for the
`template_eda_notebook` exemplar. Every rule has a concrete consequence for test
correctness, reproducibility, or manuscript accuracy.

---

## 1. Zero-Mock Policy

The most critical rule is the absolute prohibition of mocking. The following are
**forbidden** anywhere inside
`projects/templates/template_eda_notebook/tests/`:

- `import unittest.mock`
- `from unittest.mock import MagicMock, patch, create_autospec, Mock, AsyncMock`
- `@patch(...)` decorators
- monkeypatching a real function with a fake callable

**Why**: `src/eda/` contains pure data transforms. You can always test them with
the real shipped CSV or a small real DataFrame and real results. A test that
requires a mock tests the wrong thing.

**Forbidden pattern**:
```python
# BAD — tests behavior, not correctness
from unittest.mock import MagicMock
frame = MagicMock()
summary_statistics(frame)
```

**Correct pattern** (from `tests/test_statistics.py`):
```python
# GOOD — tests real output with a designed frame
frame = pd.DataFrame({"group": ["a", "a"], "height_cm": [10.0, 20.0],
                      "weight_kg": [1.0, 2.0], "resting_hr_bpm": [100.0, 90.0]})
summaries = summary_statistics(frame)
assert next(s for s in summaries if s.column == "height_cm").mean == 15.0
```

**Verify cleanliness**:
```bash
grep -r "unittest.mock\|MagicMock\|@patch" projects/templates/template_eda_notebook/tests/ || echo "Clean"
```

---

## 2. Library Purity (no infrastructure, no plotting, no I/O)

| File | May Import | Must NOT Import / Do |
|---|---|---|
| `src/eda/*.py` | `numpy`, `pandas`, `dataclasses`, `typing` | **Anything from `infrastructure.*`; matplotlib; file writes** |
| `scripts/eda_analysis.py` | `src.eda`, `src.project_paths`, `matplotlib` | Analysis math (statistics, correlations) |
| `tests/test_*.py` | `src.*`, `pandas`, `numpy`, `pytest` | `unittest.mock.*`, `infrastructure.*` |

**Verify `src/` is clean**:
```bash
grep -r "from infrastructure\|import infrastructure" projects/templates/template_eda_notebook/src/ || echo "Clean"
```

---

## 3. The Thin Orchestrator Pattern

The notebook and `scripts/eda_analysis.py` may load data, plot, and write files,
but must not compute statistics or correlations that belong in `src/eda/`.

**Forbidden** — analysis re-implemented in a script/cell:
```python
# BAD — correlation logic belongs in src/eda/correlation.py
corr = frame[["height_cm", "weight_kg"]].corr()
```

**Correct** — call the tested function:
```python
# GOOD
matrix = correlation_matrix(frame)
```

**Decision rule**: if a line of code in a cell or script computes an analysis
result (not just its visualization), move it to `src/eda/` and write a test.

---

## 4. Manuscript "Show, Not Tell"

Use explicit, verifiable references instead of vague descriptions.

| BAD (vague) | GOOD (concrete) |
|---|---|
| "The library finds related features." | "`src/eda/correlation.py::strongest_pairs()` ranks feature pairs by absolute correlation while preserving sign." |
| "We validated the statistics." | "`tests/test_statistics.py::TestSummaryStatistics` asserts the exact mean/std/min/median/max for a designed frame." |

---

## 5. Explicit File Paths

Refer to files by their path relative to the repository root:

| Short Name | Path (from repo root) |
|---|---|
| dataset loader | `projects/templates/template_eda_notebook/src/eda/dataset.py` |
| analysis script | `projects/templates/template_eda_notebook/scripts/eda_analysis.py` |
| notebook | `projects/templates/template_eda_notebook/notebooks/eda_walkthrough.ipynb` |
| config | `projects/templates/template_eda_notebook/manuscript/config.yaml` |
| dataset CSV | `projects/templates/template_eda_notebook/data/measurements.csv` |

Never hardcode an absolute filesystem path in code — resolve relative to the
project root (see `src/eda/dataset.py`).

---

## 6. Dataclass and Type Hint Standards

- Use Python 3.10+ union syntax: `str | Path | None`, not `Optional[...]`.
- Use `pd.DataFrame` for tabular inputs; `@dataclass(frozen=True)` for structured
  returns (`DatasetSchema`, `ColumnSummary`, `CleaningReport`, the figure-data
  dataclasses).
- All public functions have complete annotations and Google-style docstrings.

```python
@dataclass(frozen=True)
class ColumnSummary:
    column: str
    count: int
    mean: float
    std: float
    minimum: float
    median: float
    maximum: float
```

---

## 7. Error Message Format

All `ValueError` / `KeyError` raises must include the actual problematic value.

**Forbidden**:
```python
raise ValueError("bad argument")
```

**Correct** (following the pattern in `src/eda/`):
```python
raise ValueError("bins must be positive")
raise ValueError("top_n must be non-negative")
raise KeyError(f"column {column!r} not in frame")
raise FileNotFoundError(f"dataset CSV not found: {csv_path}")
```
