# tables/ — agent guide

One test file per manuscript table / snapshot claim (e.g.
`test_run_snapshot_claims.py`). Use the `load_pinned_values`
fixture; load from `tables.<key>` in
[`../../../pinned_values/template_search_project.json`](../../../pinned_values/template_search_project.json).

Every value is re-derived **offline** from the committed
`data/corpus.json` by calling the real source functions
(`LiteratureClient.search` over a `LocalBackend`,
`src.pipeline._build_citation_keys`,
`src.manuscript_variables.compute_variables`) — no mocks, no
network. Import isolation uses a project-scoped `sys.meta_path`
finder (see [`../AGENTS.md`](../AGENTS.md)). Provenance discipline
per [`../../../AGENTS.md`](../../../AGENTS.md).
