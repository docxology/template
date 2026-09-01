# Scope, Related Work, and Positioning {#sec:scope}

This section situates the exemplar and states explicit boundaries. The goal is
not to compete with comprehensive treatments of exploratory data analysis
[@tukey1977eda] or statistical graphics [@wilkinson2005grammar], but to show how
a minimal, test-backed EDA story fits the template's reproducibility and
rendering stack [@peng2011reproducible].

## Exploratory data analysis

The practice of examining a dataset before formal modelling — looking at
distributions, missingness, and relationships — traces to Tukey's foundational
work [@tukey1977eda] and is supported in modern practice by the pandas data
analysis toolkit [@mckinney2010pandas] and the broader scientific-Python
stack [@harris2020numpy]. The present manuscript restricts attention to a
**first pass** on a **small tabular dataset**: load, surface missingness, compute
descriptive statistics and per-group means, and rank features by Pearson
correlation.

## Modelling and inference (out of scope)

What comes *after* a first EDA pass — hypothesis testing, regression,
dimensionality reduction, or predictive modelling — is deliberately **out of
scope**. The exemplar keeps the analysis minimal so the architectural lesson
(notebook -> tested src extraction) stays visible rather than buried under
statistical machinery.

## What this project proves about the template

The analytical steps here are standard. The **non-standard** contribution is
procedural: the same tested functions in `src/eda/` back the interactive
notebook, the headless analysis script, and this manuscript, so the figures and
the summary table always refer to the same code. That pattern is what downstream
projects should copy — whether the domain is survey data, sensor logs, or
experimental measurements.

## Explicit limitations

1. **Dataset size**: a single small synthetic cohort (120 rows) is used for
   transparent, fast reproduction; no large-scale or streaming data is handled.
2. **Cleaning policy**: only listwise deletion is implemented; imputation is left
   as a documented extension.
3. **Correlation method**: only Pearson correlation is computed; rank-based
   (Spearman) or non-linear association measures are out of scope.
4. **Statics only**: the library returns plot-ready data; interactive widgets and
   dashboards are not part of the exemplar.

These limitations are intentional: they narrow the surface so that the
reproducibility concerns — tested functions, a thin script, and a structurally
verified notebook — remain visible rather than buried under analytical
complexity.
