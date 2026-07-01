# `tests/regression/projects/template_eda_notebook/` — agent guide

Read [`../../AGENTS.md`](../../AGENTS.md) first.

New regression tests for `template_eda_notebook` go under
`figures/` or `tables/`. Use the `pinned_values` fixture; do not
hardcode expected numbers in test bodies. Every pinned value must be
re-derived from the deterministic `src/eda/*` functions against the
shipped `data/measurements.csv`, never transcribed from prose.
