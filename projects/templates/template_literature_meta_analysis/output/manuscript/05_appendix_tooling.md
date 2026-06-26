# Appendix A: Tooling and Reproduction

The pipeline is a two-layer system: generic infrastructure (rendering, validation,
logging) shared across the template monorepo, and project-local `src/` modules that
implement the meta-analysis. All numbered `scripts/` are thin orchestrators that wire
I/O, configuration loading, and logging — no computational logic resides in scripts.

## Reproduce the Offline Default Run

No network, no language model required:

```bash
uv run python scripts/generate_fixture_corpus.py --out output/data/corpus.jsonl
uv run python scripts/02_meta_analysis_pipeline.py
uv run python scripts/03_build_knowledge_graph.py --max-papers 0
uv run python scripts/04_generate_figures.py --dpi 300
uv run python scripts/05_inject_variables.py
```

## Reproduce the Live Run

This manuscript was generated from a live retrieval run. To reproduce:

```bash
# Live search (all 7 engines, max 1000 per engine)
uv run python scripts/01_literature_search.py --query modafinil --max-results 1000 --no-resume

# Analysis pipeline
uv run python scripts/02_meta_analysis_pipeline.py
uv run python scripts/03_build_knowledge_graph.py --max-papers 0
uv run python scripts/04_generate_figures.py --dpi 300
uv run python scripts/05_inject_variables.py
uv run python scripts/06_fulltext_assessment.py
```

## Re-target to Another Topic

Edit `manuscript/config.yaml` — `project_config.search.term`, `query`,
`relevance_keywords`, `subfield_keywords`, and `hypothesis_definitions` — then regenerate
the seed corpus and re-run. No code changes are required; the manuscript re-targets
through token injection.

## Live Retrieval

Enable engines under `project_config.search.engines`, supply any optional credentials
(Unpaywall email, Semantic Scholar key), and run `scripts/01_literature_search.py`; absent
engines degrade to skipped sources. The CLI supports per-engine skip flags:
`--skip-arxiv`, `--skip-s2`, `--skip-openalex`, `--skip-crossref`, `--skip-pubmed`,
`--skip-sovietrxiv`, `--skip-chinarxiv`.

## Test Suite

Every stage is covered by a no-mocks test suite (real computation and
`pytest-httpserver` for network adapters) gated at $\geq 90\%$ statement coverage on
`src/`. The suite includes 819 tests covering:

- Record models and serialization (deduplication, canonical ID hierarchy)
- All 7 engine clients (arXiv, Semantic Scholar, OpenAlex, Crossref, PubMed, SovietRxiv,
  ChinaRxiv) with pytest-httpserver integration tests
- Search runner (multi-engine dispatch, relevance filtering, resume/clear, YAML config)
- Bibliometric analysis (subfield classification, temporal metrics, TF-IDF, NMF, citation
  network)
- Knowledge graph (schema, nanopublications, hypothesis scoring, LLM extraction)
- Visualization (headless figure generation, style config)
- Manuscript variable computation and injection
