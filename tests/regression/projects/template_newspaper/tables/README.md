# `template_newspaper` — layout-statistics regression tests

> One file per manuscript claim group. Re-derives each layout/render
> statistic via the project's deterministic layout engine and
> compares to the pinned ground truth in
> [`../../../pinned_values/template_newspaper.json`](../../../pinned_values/template_newspaper.json).

Pinned claims (all re-derived from `src`, matching
`manuscript/04_reproducibility.md` and `data/claim_ledger.yaml`):

- **page count** — `load_edition(content).page_count` == 12
- **trim width (pt)** — `load_newspaper_config(content).geometry().width` == 792.0
- **trim height (pt)** — `load_newspaper_config(content).geometry().height` == 1224.0
- **figure count** — `len(figures.generate_all(tmp))` == 13 (6 scenes + 4 color ads + 3 charts)
