# tests/publish/ — agent contract

Behavior tests for `src/template_search_project/publish/` (one-to-one mirror
per SUBMODULAR-SEARCH-1). Pure-domain tests only: no mocks, no network;
subprocess invocations target this project's own entrypoints. Keep test
files co-located with their subject module's subpackage; move a test only
when its subject module moves, via `git mv`.

## Files

- `README.md` — scope of this cluster.

## See Also

- [`../AGENTS.md`](../AGENTS.md) — shared testing contract.
- [`../../src/template_search_project/AGENTS.md`](../../src/template_search_project/AGENTS.md) — package-level module map covering `publish/`.
