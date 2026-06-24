# Quick Start Guide

Get up and running with the `template_literature_meta_analysis` exemplar in ~5 minutes. This
template performs a full, reproducible literature review for a **single search term** across
five academic search engines, then de-duplicates, analyzes, and visualizes the corpus. The
bundled default term is **`modafinil`**; change one config key to re-target any topic.

## Prerequisites

- Python 3.10 or higher
- [`uv`](https://github.com/astral-sh/uv) package manager (repo invariant — see the root `CLAUDE.md`)
- Git
- Network access for the live search stage (arXiv, OpenAlex, Crossref, PubMed are keyless;
  Semantic Scholar works without a key but is aggressively rate-limited — it degrades gracefully)
- *(Optional)* a local [Ollama](https://ollama.com) server with `gemma3:4b` for the knowledge-graph stage

## Setup (One-Time)

```bash
# 1. Clone the template repository (if you haven't already)
git clone https://github.com/docxology/template.git
cd template

# 2. Install dependencies at the repository root
uv sync

# 3. Verify installation
uv run python --version
```

## Run the Test Suite

Validate the environment and confirm the project test suite passes with the ≥90% coverage gate:

```bash
uv run pytest projects/templates/template_literature_meta_analysis/tests/ -v --tb=short
```

Expected: a passing suite (768+ tests). Live collection counts are tracked in
[`../../../docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md).

## The Single Control Surface

Everything is driven by [`manuscript/config.yaml`](../manuscript/config.yaml) →
`project_config.search`. The bundled defaults:

```yaml
project_config:
  search:
    term: "modafinil"                                    # <- change THIS to re-target
    query: '"modafinil" OR "provigil" OR "armodafinil"'
    start_year: 1990
    max_results: 1000
    engines: { arxiv: true, openalex: true, semantic_scholar: true, crossref: true, pubmed: true }
```

To run a literature review on a different topic, edit `term`, `query`, `arxiv_queries`,
`relevance_keywords`, `subfield_keywords`, and `hypothesis_definitions`, then re-run the stages
below — no code changes required.

## Execute the Pipeline (modafinil)

Run from the template directory: `cd projects/templates/template_literature_meta_analysis`.

```bash
# Stage 1 — Multi-engine search + cross-engine de-duplication -> output/data/corpus.jsonl
#   --clear-corpus --no-resume forces a fresh live search (omit to resume an existing corpus)
uv run python scripts/01_literature_search.py --clear-corpus --no-resume

# Stage 2 — Meta-analysis: subfields, temporal growth, TF-IDF, NMF topics, citation network
uv run python scripts/02_meta_analysis_pipeline.py

# Stage 3 — (Optional) Knowledge graph + hypothesis scoring + RDF/TriG nanopublications.
#   Requires Ollama. Cap the sample while testing with --max-papers; omit for the full corpus.
uv run python scripts/03_build_knowledge_graph.py --max-papers 25

# Stage 4 — Render publication-grade figures (PNG)
uv run python scripts/04_generate_figures.py

# Stage 5 — Inject computed variables into the manuscript Markdown
uv run python scripts/05_inject_variables.py
```

A fresh modafinil run typically yields ~2,300 unique papers in under a minute (OpenAlex +
Crossref + PubMed dominate; arXiv is near-empty for clinical terms; S2 may return 0 on a 429).
De-duplication is by `canonical_id` (priority `doi > arxiv_id > s2_id > openalex_id > title-hash`).

## Outputs

**Under `projects/templates/template_literature_meta_analysis/output/`:**
- `data/corpus.jsonl` — the deduplicated corpus (one paper per line)
- `data/*.json` — `subfield_classification`, `temporal_analysis`, `tfidf_data`, `topics`,
  `citation_network`, `subfield_timeline`, plus `hypothesis_scores`/`nanopublications.trig` if stage 3 ran
- `data/citation_graph.gml` — citation network (Gephi/NetworkX-readable)
- `figures/*.png` — up to 12 figures (field summary, subfield distribution donut, growth curve,
  subfield timeline, citation network, degree distribution, word cloud, topic-term bars,
  PCA embeddings, term heatmap, dendrogram, co-occurrence matrix)

## Render the Publication PDF

Run this one **from the repository root** (`scripts/03_render_pdf.py` is a repo-level
orchestrator, distinct from the project's own `scripts/03_build_knowledge_graph.py`):

```bash
uv run python scripts/03_render_pdf.py --project template_literature_meta_analysis
```

Final PDF: `projects/templates/template_literature_meta_analysis/output/pdf/template_literature_meta_analysis_combined.pdf`

## Common Next Steps

- **Re-target the topic**: edit `manuscript/config.yaml` → `project_config.search.term` (and the
  query/keyword/subfield/hypothesis blocks), then re-run stages 1–5.
- **Add a search engine**: implement a client in `src/literature/`, register it in
  `src/literature/search_runner.py`, and add a toggle under `project_config.search.engines`.
- **Tune embeddings**: `project_config.embeddings` (default offline `tfidf_svd`; set
  `method: transformer` + install the `embeddings` extra to upgrade).

## Getting Help

- **Full documentation**: [`docs/README.md`](README.md) — navigation hub
- **Architecture**: [`docs/architecture.md`](architecture.md)
- **Agent rules**: [`docs/agent_instructions.md`](agent_instructions.md)
- **Troubleshooting**: [`docs/troubleshooting.md`](troubleshooting.md)
- **FAQ**: [`docs/faq.md`](faq.md)

## Quick Command Reference

| Task | Command |
|---|---|
| Run tests | `uv run pytest projects/templates/template_literature_meta_analysis/tests/ -v` |
| Literature search | `uv run python scripts/01_literature_search.py --clear-corpus --no-resume` |
| Meta-analysis | `uv run python scripts/02_meta_analysis_pipeline.py` |
| Knowledge graph (optional, Ollama) | `uv run python scripts/03_build_knowledge_graph.py --max-papers 25` |
| Generate figures | `uv run python scripts/04_generate_figures.py` |
| Inject manuscript variables | `uv run python scripts/05_inject_variables.py` |
| Render PDF | `uv run python scripts/03_render_pdf.py --project template_literature_meta_analysis` |
| Clean outputs | `rm -rf projects/templates/template_literature_meta_analysis/output/` |
