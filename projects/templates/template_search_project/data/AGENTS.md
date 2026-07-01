# Data Directory — Agent Guide

Versioned project **inputs** only. Pipeline outputs must not be committed here.

## `corpus.json`

Curated offline literature corpus (6 papers, keyed by `_comment` +
`papers` list) shipped so the pipeline runs deterministically in CI with
no network access. Each paper record carries `id`, `title`, `authors`,
`year`, `doi`, `url`, `venue`, `venue_type`, `volume`, `issue`, `pages`,
`publisher`, `abstract`, `keywords`, and `source`.

To regenerate from a live search run instead of the offline fixture,
point an arXiv/Crossref client at `write_corpus(...)` — see
[`docs/quickstart.md`](../docs/quickstart.md).

## Edit protocol

1. Treat `corpus.json` as a fixture: edits should keep the corpus
   deterministic and network-free for CI.
2. Preserve the full per-paper field set above when adding or editing
   entries — downstream `infrastructure/search/` and
   `infrastructure/reference/` consumers depend on it.
3. Do not store generated CSV/JSON/PNG under `data/` — those go to
   `output/`.

Quick orientation: [`README.md`](README.md).
