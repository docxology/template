# `tests/regression/projects/template_newspaper/` — regression suite

> Pinned numerical regression tests for `template_newspaper`
> layout/render statistics. Loads ground truth from
> [`../../pinned_values/template_newspaper.json`](../../pinned_values/template_newspaper.json).

## Layout

- `tables/` — one test file per manuscript claim group (currently
  `test_layout_statistics_claims.py`, binding the page count, trim
  dimensions and figure count that `manuscript/04_reproducibility.md`
  names as this project's quantitative claims and that
  `data/claim_ledger.yaml` registers)

Because this exemplar renders a newspaper rather than reporting a
scientific result, the pins bind *layout/render* numbers — but they
are re-derived from `src` (not read from prose) exactly like every
other regression suite here. See [`../../README.md`](../../README.md)
for the philosophy.
