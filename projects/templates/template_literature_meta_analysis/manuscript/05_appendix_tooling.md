# Appendix A: Tooling and Reproduction

The pipeline is a two-layer system: generic infrastructure (rendering, validation,
logging) shared across the template monorepo, and project-local `src/` modules that
implement the meta-analysis. All numbered `scripts/` are thin orchestrators.

**Reproduce the offline default run** (no network, no language model):

```bash
uv run python scripts/generate_fixture_corpus.py          # committed synthetic seed corpus
uv run python scripts/02_meta_analysis_pipeline.py        # subfields, temporal, topics, citation network
uv run python scripts/04_generate_figures.py              # figures
uv run python scripts/05_inject_variables.py --project templates/template_literature_meta_analysis
```

**Re-target to another topic.** Edit `manuscript/config.yaml` —
`project_config.search.term`, `query`, `relevance_keywords`, `subfield_keywords`, and
`hypothesis_definitions` — then regenerate the seed corpus and re-run. No code changes
are required; the manuscript re-targets through token injection.

**Live retrieval.** Enable engines under `project_config.search.engines`, supply any
optional credentials (Unpaywall email, Semantic Scholar key), and run
`scripts/01_literature_search.py`; absent engines degrade to skipped sources.

Every stage is covered by a no-mocks test suite (real computation and `pytest-httpserver`
for network adapters) gated at $\geq 90\%$ statement coverage on `src/`.
