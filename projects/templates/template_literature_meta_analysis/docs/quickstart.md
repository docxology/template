# Quick Start Guide

Run a deterministic synthetic literature corpus through the single-topic
analysis pipeline before choosing live retrieval. The default topic is
`modafinil`; the configured search adapters are a separate explicit network
path. Fixture rows, generated identifiers and bibliometric plots are not
retrieved studies or evidence of a clinical effect.

## Prerequisites

- Python 3.14 (3.14 and 3.15 are the supported minors)
- [`uv`](https://github.com/astral-sh/uv) package manager (repo invariant — see the root `CLAUDE.md`)
- Git
- Network access is needed only for explicitly selected live retrieval/enrichment.
- Optional local-model work requires its separately prepared, authorized provider;
  the first offline route does not acquire or call a model.

## Setup (One-Time)

```bash
# 1. Clone the template repository (if you haven't already)
git clone https://github.com/docxology/template.git
cd template

# 2. Prepare Root and this project's declared own development environment
uv sync --locked
uv sync --locked --project projects/templates/template_literature_meta_analysis --extra dev \
  --python "$PWD/.venv/bin/python"

# 3. Enter the project directory; subsequent local commands use its own interpreter
cd projects/templates/template_literature_meta_analysis
.venv/bin/python --version
```

## Run the Test Suite

For whole own-suite coverage, use the prepared project interpreter and enable
the declared 90% gate explicitly. This is not complete installed/native or
live-provider acceptance; retain any declared missing capabilities rather than
promoting skips to a pass.

```bash
.venv/bin/python -I -m pytest tests/ -v --tb=short --cov=src --cov-fail-under=90
```

Actual retained collection facts are in the monorepo's
[COUNTS](../../../../docs/_generated/COUNTS.md); this guide does not assert a run result.

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
    engines: { arxiv: true, openalex: true, semantic_scholar: true, crossref: true, pubmed: true, sovietrxiv: true, chinarxiv: true, europepmc: true, biorxiv: true, medrxiv: true }
```

To run a literature review on a different topic, edit `term`, `query`, `arxiv_queries`,
`relevance_keywords`, `subfield_keywords`, and `hypothesis_definitions`, then re-run the stages
below — no code changes required.

## Execute the offline demonstration

From the prepared project directory:

```bash
# The generator's default is data/fixtures/...; explicitly prepare the analysis input.
.venv/bin/python scripts/generate_fixture_corpus.py --out output/data/corpus.jsonl
.venv/bin/python scripts/02_meta_analysis_pipeline.py
.venv/bin/python scripts/04_generate_figures.py
.venv/bin/python scripts/05_inject_variables.py
```

This uses generated records and does not contact a retrieval engine or prove
literature coverage. Keep the actual corpus and generated artifacts when
interpreting counts. To perform a separately authorized live search, replace
the fixture deliberately with `scripts/01_literature_search.py
--clear-corpus --no-resume` and retain its genuine retrieval report. Do not mix
fixture rows into a claimed live yield or promise a paper count or elapsed time.
Optional knowledge-graph work (`scripts/03_build_knowledge_graph.py`) has its own
prepared model/provider requirements; it is not part of the first offline run.

## Outputs

**Under `projects/templates/template_literature_meta_analysis/output/`:**
- `data/corpus.jsonl` — the deduplicated corpus (one paper per line)
- `data/*.json` — `subfield_classification`, `temporal_analysis`, `tfidf_data`, `topics`,
  `citation_network`, `subfield_timeline`, plus `hypothesis_scores`/`nanopublications.trig` if stage 3 ran
- `data/citation_graph.gml` — citation network (Gephi/NetworkX-readable)
- `figures/*.png` — figure set is dynamic: each figure renders only when its source JSON
  input exists (caption registry in `src/visualization/figure_runner.py` → `FIGURE_CAPTIONS`,
  21 possible figures: field summary, subfield distribution, growth curve, subfield timeline,
  citation network, degree distribution, word cloud, topic-term bars, PCA embeddings,
  term heatmap, dendrogram, co-occurrence matrix, and more)

## Render the Publication PDF

Return to the repository root before using the repository renderer. It consumes
the already generated project artifacts and separately prepared rendering tools:

```bash
cd ../../..
uv run --no-sync --offline python scripts/pipeline/stage_03_render.py --project templates/template_literature_meta_analysis
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

Project-local producer commands above run from the prepared project directory;
`scripts/pipeline/` commands run from the monorepo root. Use the
[shared run surface](../../../README.md#run-surface) for preparation and the
[standalone guide](../STANDALONE.md) for independent exports. A live retrieval,
model operation, corpus replacement or cleanup is an explicit separate action,
not a hidden quickstart step.
