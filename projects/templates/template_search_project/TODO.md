# template_search_project TODO

This backlog is future-only. Completed validation and dated review evidence are preserved in
[`docs/maintenance/exemplar-backlog-history.md`](../../../docs/maintenance/exemplar-backlog-history.md)
or in source-owned generated receipts. Each active row must retain a stable ID, size, dependency,
proving artifact, acceptance command, and negative control; absence of an owner or external receipt
keeps a capability blocked rather than silently promoting it.

## Backlog operating rules

- Keep deterministic and offline defaults unchanged unless an upcoming row explicitly scopes an opt-in.
- Do not close a row until its producer, artifact, consumer, gate, and failing negative control are present.
- Treat unavailable network, LLM, container, formal-tool, and publication paths as explicit skips
  or blockers.
- Re-derive counts and receipts from live source data; never copy measurements into this planning file.

## Integrity and template-status gaps

- The bundled `data/corpus.json` is marked as a deterministic fixture in
  README, AGENTS, manuscript prose, and generated reports; fixture-backed
  synthesis is rejected when it uses high-confidence empirical assertion
  language. Keep this boundary intact when adding claim templates.
- Keep manuscript numbers (`RESULT_NUM_PAPERS`, `RESULT_WITH_ABSTRACT`,
  `RESULT_WITH_DOI`, etc.) sourced only from `output/run_summary.json` and
  `output/data/manuscript_variables.json`, never hand-typed.
- `output/deep_search/run_summary.json`, `aggregate_report.md`,
  `composition_summary.json`, and the self-contained dashboard now use
  `<repo-root>`-relative paths. Puppeteer metadata still records its cache
  executable as `<home>/.cache/puppeteer/...`; this is renderer-owned metadata
  and requires a shared infrastructure normalization rather than a project
  output edit.

## Configurable-surface gaps

- Retargeting the query, sources, and deep-search keywords should remain
  entirely `manuscript/config.yaml`-owned; avoid hard-coding search terms in
  `src/`.
- Keep the Ollama budget knobs (`context_window`, `long_max_tokens`,
  `max_input_length`, `review_timeout`) explicit in config rather than
  falling back silently to client defaults.

## Documentation and signposting gaps

- Keep README, AGENTS.md, and `docs/_generated/exemplar_roster.md`
  synchronized through the generator.
- Keep `docs/quickstart.md` and `docs/troubleshooting.md` aligned with the
  qualified project name `templates/template_search_project`.

## Test and validator gaps

- Keep `src/review_report.py` above the project coverage floor with no-mock
  tests for subprocess environment policy, syntax-error handling, import
  boundaries, and explicit skipped/disabled/not-materialised statuses.
- Add a negative control before widening retrieval-coverage claims beyond
  the bundled offline corpus.
- Keep fixture-honesty validation and the explicit `evidence_scope` field in
  `output/run_summary.json`; extend assertion vocabulary only with a focused
  negative-control test.
- Keep the byte-identical-across-reruns test
  (`tests/test_pipeline.py::TestRunLiteraturePipeline::test_bibtex_byte_identical_across_reruns`)
  in sync as new pipeline stages are added.
- Keep `manuscript/references_deep.bib` derived from the committed deep-search
  aggregate and fail when citation keys or source revisions drift.

## Minor upcoming

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `SEARCH-DEEP-1` | Minor | Deep-search query plan | deterministic deep-search manifest | byte-repeat and claim tests | changed query order must change receipt |

## Medium upcoming

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `SEARCH-CACHE-1` | Medium | Offline cache schema | cache identity/age receipt | project tests with network disabled | stale cache must degrade explicitly |
| `SEARCH-FULLTEXT-1` | Medium | Full-text fixture/license boundary | full-text coverage report | focused retrieval validators | missing full text must not count as retrieved |

## Major upcoming

No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked major row is a deliberate boundary, not a skipped success.
