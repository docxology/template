# tests/search/ — agent contract

Behavior tests for `src/template_search_project/search/` (one-to-one mirror
per SUBMODULAR-SEARCH-1). No mocks or external-service access. Enrichment controls may use the owned
`pytest-httpserver` loopback server with actual PDF extraction and cache replay;
subprocess invocations target this project's own entrypoints. Keep test
files co-located with their subject module's subpackage; move a test only
when its subject module moves, via `git mv`.

## Files

- `README.md` — scope of this cluster.

## See Also

- [`../AGENTS.md`](../AGENTS.md) — shared testing contract.
- [`../../src/template_search_project/AGENTS.md`](../../src/template_search_project/AGENTS.md) — package-level module map covering `search/`.
