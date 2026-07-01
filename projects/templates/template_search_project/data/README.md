# template_search_project/data

Project-maintained **inputs** for the literature-search exemplar (not
pipeline outputs).

## Quick reference

| File | Role |
| --- | --- |
| `corpus.json` | Offline, deterministic 6-paper literature corpus the pipeline loads with no network access |

`corpus.json` is a static fixture; regenerate it from a live arXiv/Crossref
search via `write_corpus(...)` (see [`docs/quickstart.md`](../docs/quickstart.md))
rather than hand-editing individual paper records where avoidable. Generated
analysis outputs belong under `output/` during pipeline runs, not here.

Schema and edit protocol: [`AGENTS.md`](AGENTS.md).
