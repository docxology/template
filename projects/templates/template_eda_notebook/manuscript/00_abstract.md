# Abstract {#sec:abstract}

Exploratory data analysis (EDA) is the most common entry point in applied
research, yet it is also where reproducibility most often breaks down: logic
accumulates in notebook cells that are never tested and quietly drift from the
prose describing them. This paper presents the **computational-notebook
exemplar** of the [Research Project Template](https://github.com/docxology/template):
an interactive walkthrough notebook
(`projects/templates/template_eda_notebook/notebooks/eda_walkthrough.ipynb`)
that imports a small, fully-tested EDA library rather than carrying logic in its
cells.

We ship a deterministic dataset (`data/measurements.csv`) with a designed
correlation structure and a handful of missing values, then load, clean,
summarize, correlate, and visualize it entirely through tested functions in
`src/eda/`. The library is side-effect-free — no plotting and no file I/O — and
standalone (numpy and pandas only), so it is covered above the 90% project gate
and reused identically from the notebook, the thin analysis script
(`scripts/eda_analysis.py`), and this manuscript.

Contributions are **methodological** and **architectural**. On the methods side,
we walk the canonical first EDA pass: surface missingness explicitly rather than
imputing it, compute per-column descriptive statistics and per-group means, and
rank features by Pearson correlation. On the architecture side, we demonstrate
the notebook-to-tested-source extraction workflow — explore fast in a cell, and
the moment a computation matters, move it into the library behind a failing
test — verified by a zero-mock suite and a structural notebook-binding check
([@sec:reproducibility]).
