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

- The default pipeline (`project_config.search.sources: [local]`) is fully offline and
  CI-safe, backed by the bundled `data/corpus.json`.
- LLM synthesis (`llm.enabled`) defaults to `false` so tests and CI never
  require an Ollama server.
- `deep_search` is enabled by default and exercises the multi-keyword
  arXiv/Crossref fan-out. Paperclip is fail-fast (not graceful) when
  `PAPERCLIP_API_KEY` is unset and is deliberately omitted from the default
  `sources` list; add it only alongside a real key.

### Measured 2026-08-02 publication pass

- pytest: **315 passed**, 97.80% coverage (gate `--cov-fail-under=90`).
- `prerender`, `stage_04_validate` (all checks PASS), `stage_05_copy`,
  and `check_template_drift --strict` (`no drift detected`) all green.
- Combined PDF: 59 pages, 0 `??`, 0 `^! ` LaTeX errors; abstract and results
  now show `300` unique deep-search papers (the previous shipped PDF rendered
  the `<deep-search not run>` sentinel invisibly).

## 2026-08-02 integrity fixes (publication pass)

- **Path portability.** `src/search_pipeline_cli.py` and `src/deep_search_cli.py`
  now write `run_summary.json` artifact paths as `<repo-root>`-relative
  placeholders instead of absolute resolved paths, matching the convention the
  standard `output/run_summary.json` already used. The deep-search summary
  previously shipped machine-local paths
  (`<home>/Documents/Git/HumOS/...`) from a run on another machine.
- **Dead module reference.** `src/figures.py` docstring named
  `scripts/generate_search_figures.py`; corrected to
  `scripts/y_generate_search_figures.py`.
- **Stale resolved evidence.** The committed `output/data/manuscript_variables.json`
  and `output/manuscript/*.md` carried `deep_unique_papers: "<deep-search not run>"`
  while the committed aggregate (`output/deep_search/aggregate.json`, 300 papers)
  existed — so the shipped PDF rendered the sentinel (invisible in LaTeX) as
  "with unique paper(s)". Re-running the canonical render with the aggregate
  present regenerated variables, resolved tree, PDF, slides, and web to the
  measured `300`.
- **Agent catalog completion.** Added `.agents/README.md` and
  `.agents/skills/README.md` (contract listed the files; the tree lacked them).
- **Test inventory.** `tests/AGENTS.md` now lists all 25 test modules grouped
  by subsystem so listing drift is detectable.

## Integrity and template-status gaps

- The bundled `data/corpus.json` is marked as a deterministic fixture in
  README, AGENTS, manuscript prose, and generated reports; fixture-backed
  synthesis is rejected when it uses high-confidence empirical assertion
  language. Keep this boundary intact when adding claim templates.
- Keep manuscript numbers (`RESULT_NUM_PAPERS`, `RESULT_WITH_ABSTRACT`,
  `RESULT_WITH_DOI`, etc.) sourced only from `output/run_summary.json` and
  `output/data/manuscript_variables.json`, never hand-typed.
- `output/deep_search/run_summary.json` was last generated on another machine
  and still embeds a machine-local checkout path (sanitized to
  `<home>/Documents/Git/HumOS/...`). The producer (`src/deep_search_cli.py`)
  now writes `<repo-root>`-relative paths; regenerate the file on the next
  live deep-search run rather than hand-editing it.

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

- `src/review_report.py` was at the 90% coverage floor — 10 additional
  no-mock tests added in `tests/test_review_report_additional.py` covering
  `_subprocess_env`, `ensure_review_summary` subprocess paths,
  `collect_infra_imports` SyntaxError handling, `_bs`, no-infra-imports
  branch, and stage skipped/disabled/not-materialised statuses. The module
  now sits comfortably above the gate.
- Add a negative control before widening retrieval-coverage claims beyond
  the bundled offline corpus.
- **Shipped:** fixture-honesty validation and an explicit `evidence_scope` in
  `output/run_summary.json`; extend the allowlisted assertion vocabulary only
  with a focused negative-control test.
- Keep the byte-identical-across-reruns test
  (`tests/test_pipeline.py::TestRunLiteraturePipeline::test_bibtex_byte_identical_across_reruns`)
  in sync as new pipeline stages are added.
- Observed (non-blocking): `s_compose_literature_review.py` reports 4 citation
  key(s) absent from `manuscript/references_deep.bib`
  (`anon2019replication`, `bu2026nonstationary`, `gong2026comparative`,
  `singer1980minimization`). They are cited only inside the per-keyword
  reading reports and `output/deep_search/aggregate_report.md` (not in the
  manuscript), so the composed S01 and the PDF resolve cleanly; the warning is
  the composer's upstream-check. Revisit when the deep-search corpus rotates.

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
