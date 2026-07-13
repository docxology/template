# Reproducibility {#sec:reproducibility}

This section explains how to regenerate every artifact in the study from a clean
checkout. The exemplar's reproducibility guarantee is structural: each result is
produced by a tested function and a thin script, never transcribed by hand.

## How to regenerate everything

From the repository root:

```bash
# 1. Run the analysis (writes figures + summary CSV, prints output paths)
uv run python projects/templates/template_eda_notebook/scripts/eda_analysis.py

# 2. Run the test suite with the coverage gate
uv run pytest projects/templates/template_eda_notebook/tests \
    --cov=projects/templates/template_eda_notebook/src --cov-fail-under=90

# 3. Render the manuscript
uv run python scripts/pipeline/stage_03_render.py --project templates/template_eda_notebook
```

## Generated artifact registry

The analysis script writes the following artifacts under
`projects/templates/template_eda_notebook/output/`:

| Artifact | Produced by |
|---|---|
| `figures/height_histogram.png` | `histogram_data()` + analysis script |
| `figures/correlation_heatmap.png` | `correlation_heatmap_data()` + analysis script |
| `figures/group_counts.png` | `group_count_data()` + analysis script |
| `data/summary_statistics.csv` | `summary_statistics()` + analysis script |

The `output/` tree is disposable and regenerated on every run; it is not the
source of truth.

## Determinism

- The dataset (`data/measurements.csv`) is a static, committed fixture with
  fixed content — the same file is read on every run, so every statistic is
  reproducible bit-for-bit.
- The figure-data preparers are pure transforms with no RNG; the same inputs
  always produce the same bin counts, correlation values, and group counts.
- `clean_dataset()` reports exactly how many rows it removed, so the
  complete-case row count is a checkable invariant.

## Verification (no hand-transcribed numbers)

Every quantitative claim in [@sec:results] is either reproduced by running the
analysis script or registered in `data/claim_ledger.yaml` for evidence-registry
validation. The manuscript intentionally does not embed volatile values, so
prose and artifacts cannot disagree. The notebook itself is verified
structurally by `tests/test_notebook.py`, which confirms it is valid nbformat,
that its `from src` imports resolve to the library's public surface, and that no
cell defines its own logic.
