# Lab — Case Studies {#sec:lab_part_III_case_studies}

<!-- chapter-metadata-badge -->
> Lab · 75 min · Materials: the project installed (`uv sync`),
> `assets/data/sample_dataset.csv`

## Objectives

After this lab you will be able to (1) load grouped data, (2) compute per-group
means and an overall summary, (3) fit a dose–response trend, and (4) state where
the fit may and may not be trusted.

## Background

This lab operationalises [@sec:part_III_case_studies]. You will reproduce the
chapter's numbers (group means $2.20$, $3.50$, $4.95$; fitted slope $\approx
1.375$) and then probe the fit's limits by adding a condition.

## Procedure

1. Read `assets/data/sample_dataset.csv` into three groups (control, low, high).
2. Compute each group's mean and the overall summary with
   `textbook.models.descriptive_statistics`.
3. Encode dose as $0, 1, 2$ and fit a line with `textbook.models.linear_fit`.
   Confirm slope $\approx 1.375$, intercept $\approx 2.175$, $R^2 \approx 0.999$.
4. Add a hypothetical fourth condition (dose `3`) with a *saturating* response —
   use the fixture value `5.3` rather than the line's `6.3` prediction — refit,
   and compare the new slope and $R^2$.

## Analysis

Tabulate the slope, intercept, and $R^2$ for the three-point and four-point fits.
In two sentences, explain why the four-point fit's slope falls and what that
implies about extrapolating the original line.

## Computational Workflow

```python
import csv
import numpy as np
from textbook import models

rows = list(csv.DictReader(open("manuscript/assets/data/sample_dataset.csv")))
groups: dict[str, list[float]] = {}
for r in rows:
    groups.setdefault(r["condition"], []).append(float(r["measurement"]))

means = {k: float(np.mean(v)) for k, v in groups.items()}
dose = np.array([0.0, 1.0, 2.0])
response = np.array([means["control"], means["treatment_low"], means["treatment_high"]])
print(models.linear_fit(dose, response))
```

## Reflection

1. The intercept of the fit was close to the control mean. Why is that a useful
   internal consistency check?
2. Your four-point fit changed the slope. Which is the more honest summary of the
   system, and what would you measure next to decide?
3. When is a straight-line dose–response model adequate, and when does the
   saturating model from [@sec:part_I_first_principles] become necessary?
