# Experimental Setup {#sec:experimental_setup}

This section details the dataset, schema, and software environment used to
produce the results. The exemplar deliberately avoids manuscript token
injection: concrete numbers are reproduced by running the analysis script, and
the figures are regenerated from tested code, so nothing here can silently
drift from a hardcoded value.

## Dataset

The analysis uses a shipped, deterministic CSV fixture
(`data/measurements.csv`) generated once with a fixed NumPy seed. It contains
120 subject records with the following columns:

| Column | Role | Type |
|---|---|---|
| `subject_id` | per-row identifier | string |
| `group` | categorical group (`alpha`, `beta`, `gamma`) | string |
| `height_cm` | numeric feature | float |
| `weight_kg` | numeric feature | float |
| `resting_hr_bpm` | numeric feature | float |

These roles are declared once in `src/eda/dataset.py::DatasetSchema`, which the
statistics, correlation, and figure functions consult. The generating process
makes weight depend positively on height (a strong correlation) while resting
heart rate is only weakly related, and a few numeric cells are left blank to
exercise the missing-data path.

## Analysis conditions

The experiment overlay (`experiment_plan.yaml`) declares three conditions:

- **raw_dataset** (reference) — as loaded, with missing cells as `NaN`.
- **cleaned_dataset** (proposed) — rows with any missing numeric feature dropped
  via `clean_dataset()`, which reports the count removed.
- **normalized_dataset** (variant) — the cleaned dataset with numeric columns
  z-score standardized by `normalize_numeric()` for cross-feature comparison.

The primary descriptive lens is the pairwise Pearson correlation among the
numeric features.

## Computational environment

- **Language**: Python (see root `pyproject.toml` for the supported range).
- **Core dependencies**: `numpy`, `pandas`, `matplotlib` (declared in
  `domain_profile.yaml::required_packages`).
- **Headless plotting**: the analysis script sets `MPLBACKEND=Agg` before
  importing matplotlib.

## Pipeline ordering

The typical analysis order is:

1. `scripts/eda_analysis.py` — loads and cleans the dataset, then writes
   `output/figures/*.png` and `output/data/summary_statistics.csv`, printing each
   output path for manifest collection.
2. PDF rendering reads `manuscript/*.md` and `config.yaml` so figure paths and
   prose match the analysis that just completed.

## Relation to figures

| Figure ([@sec:results]) | Figure-data preparer (`src/eda/figures.py`) | Primary inputs |
|---|---|---|
| Height histogram | `histogram_data()` | `height_cm` column, 10 bins |
| Rows per group | `group_count_data()` | `group` column |
| Correlation heatmap | `correlation_heatmap_data()` | all numeric features |

This table is descriptive documentation only; it is not executed as code during
the build.
