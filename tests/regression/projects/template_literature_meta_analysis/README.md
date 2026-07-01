# `tests/regression/projects/template_literature_meta_analysis/` — regression suite

> Pinned numerical regression tests for `template_literature_meta_analysis`
> manuscript values. Loads ground truth from
> [`../../pinned_values/template_literature_meta_analysis.json`](../../pinned_values/template_literature_meta_analysis.json).

## Layout

- `tables/` — one test file per manuscript results group (currently the
  field-overview corpus/identifier claims and the descriptive-bibliometrics
  citation claims in `03a_results_field_overview.md`)

All values are re-derived **offline** from the committed deterministic seed
corpus `data/fixtures/modafinil_corpus.jsonl` (the exemplar's live retrieval
pipeline hits the network; the regression tier never does), via the real
`src.literature.corpus.Corpus.load` + `src.analysis.descriptive_stats` +
`src.analysis.temporal_analysis` functions — the same functions whose outputs
`src/manuscript/variables.py` injects into the manuscript tokens.

See [`../../README.md`](../../README.md) for the philosophy.
