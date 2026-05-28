# Sheaf Track Coverage {#sec:sheaf_coverage}

This page summarizes which **sheaf fragment tracks** are bound for each IMRAD row in `manuscript/sheaf/manifest.yaml`. The matrix is regenerated at compose time.

**Totals:** 47 present / 47 bound / 0 missing (gray).

| Color | Meaning |
| --- | --- |
| Black | Track **present** (bound and fragment exists) |
| White | **Absent** (not bound for this row) |
| Gray | **Missing** (bound but fragment file absent) |

## Introduction

- **Introduction** *(group)*
-   **Motivation and scope**
-   **Contributions**
## Methods

- **Methods** *(group)*
-   **Bernoulli–Ising analytical model**
-   **pymdp simulation harness**
-   **Lean formalization boundary**
-   **Sheaf composition**
## Results

- **Results** *(group)*
-   **Mutual-information parameter sweep**
-   **Free-energy decomposition**
-   **T-maze sophisticated inference**
-   **Validation invariants**
## Discussion

- **Discussion** *(group)*
-   **Limitations and outlook**
## Appendix

-   **Appendix: full track coverage**

![Heatmap matrix of IMRAD manuscript rows versus 10 sheaf fragment track columns. Black cells mean the track is bound and the fragment file exists; white cells mean the track is not bound; gray cells mean bound but missing. Rows are grouped by IMRAD block with indented subsection labels; column headers list track ids.](../output/figures/sheaf_coverage_heatmap.png){#fig:sheaf_coverage_heatmap width=95%}

*Coverage overview. Sheaf track coverage matrix: 16 IMRAD rows × 10 fragment columns. Black = present (P), white = absent (—), gray = missing (M). Counts: 47 present / 47 bound / 0 missing.*

Appendix row `16_appendix_full_sheaf.md` binds 9 fragment track types as a composability proof (registry defines 10 types; optional `layers` is methods-only).
