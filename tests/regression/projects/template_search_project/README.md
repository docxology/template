# `tests/regression/projects/template_search_project/` — regression suite

> Pinned numerical regression tests for `template_search_project`
> manuscript values. Loads ground truth from
> [`../../pinned_values/template_search_project.json`](../../pinned_values/template_search_project.json).

`template_search_project` is a literature-search → BibTeX →
LLM-synthesis template. These tests bind the "Run snapshot"
quantitative claims in `manuscript/00_abstract.md` and
`manuscript/03_results.md` (paper count, DOI coverage, abstract
coverage) plus the auto-populated `references.bib` entry count and
collision-free citation-key count in `manuscript/02_methodology.md`
to a fresh, **offline** re-derivation from the committed
deterministic corpus `data/corpus.json` (6 curated papers) — never
the network, never the regeneratable `output/` artefacts.

## Layout

- `figures/` — one test file per manuscript figure (none pinned yet)
- `tables/` — one test file per manuscript table / snapshot claim

See [`../../README.md`](../../README.md) for the philosophy and
[`AGENTS.md`](AGENTS.md) for the import-isolation rationale.
