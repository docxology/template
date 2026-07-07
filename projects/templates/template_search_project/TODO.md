# template_search_project TODO

Forward-only integrity backlog for the literature-search exemplar. Keep this
file about template status, validation depth, and forkability — not general
feature ideas.

## Current validation evidence

Run from the template repository root:

```bash
uv run pytest projects/templates/template_search_project/tests/ \
  --cov=projects/templates/template_search_project/src --cov-fail-under=90
uv run python scripts/audit/check_template_drift.py --strict --project templates/template_search_project
uv run python -m infrastructure.validation.cli markdown projects/templates/template_search_project/manuscript/
```

Live test counts and coverage snapshots belong in
[`docs/_generated/COUNTS.md`](../../../docs/_generated/COUNTS.md), not this
file.

- The default pipeline (`search.sources: [local]`) is fully offline and
  CI-safe, backed by the bundled `data/corpus.json`.
- LLM synthesis (`llm.enabled`) defaults to `false` so tests and CI never
  require an Ollama server.
- `deep_search` is enabled by default and exercises the multi-keyword
  arXiv/Crossref fan-out. Paperclip is fail-fast (not graceful) when
  `PAPERCLIP_API_KEY` is unset and is deliberately omitted from the default
  `sources` list; add it only alongside a real key.

## Integrity and template-status gaps

- Keep the bundled `data/corpus.json` clearly marked as a synthetic,
  deterministic fixture in README, manuscript prose, and generated reports —
  never phrase its contents as a real literature finding.
- Keep manuscript numbers (`RESULT_NUM_PAPERS`, `RESULT_WITH_ABSTRACT`,
  `RESULT_WITH_DOI`, etc.) sourced only from `output/run_summary.json` and
  `output/data/manuscript_variables.json`, never hand-typed.

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

- Add a negative control before widening retrieval-coverage claims beyond
  the bundled offline corpus.
- Add a fixture-honesty check that fails if `data/corpus.json`-derived
  results are phrased as empirical literature findings in generated prose.
- Keep the byte-identical-across-reruns test
  (`tests/test_pipeline.py::TestRunLiteraturePipeline::test_bibtex_byte_identical_across_reruns`)
  in sync as new pipeline stages are added.

## Ordered improvement ladder

1. Preserve offline-by-default reproducibility and synthetic-fixture honesty.
2. Add focused validators for any new generated artifact family (search
   cache, fulltext cache, deep-search aggregate).
3. Expand live-backend coverage only with graceful degradation and
   documented claim boundaries.
4. Refresh generated docs after any public-surface change.

## Promotion Rule

Move an item out of this file only after its source producer, generated
artifact, documentation, and focused tests are updated together.
