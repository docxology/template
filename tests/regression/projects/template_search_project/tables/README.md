# `template_search_project` — table / snapshot regression tests

> One file per manuscript table or snapshot claim. Re-derives each
> value via the project's deterministic **offline** pipeline over the
> committed `data/corpus.json` and compares to the pinned ground
> truth in
> [`../../../pinned_values/template_search_project.json`](../../../pinned_values/template_search_project.json).

- `test_run_snapshot_claims.py` — binds the abstract / results
  "Run snapshot" paragraph (`{{RESULT_NUM_PAPERS}}`,
  `{{RESULT_WITH_DOI}}`, `{{RESULT_WITH_ABSTRACT}}`) plus the
  auto-populated `references.bib` entry count and collision-free
  citation-key count. Includes the mandatory negative-control
  mutation test (non-vacuity).
