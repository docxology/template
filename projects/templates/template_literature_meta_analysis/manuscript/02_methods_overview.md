# Methods Overview

The pipeline is a sequence of deterministic stages, each reading the previous stage's
committed artifacts and writing its own. Business logic lives in tested `src/` modules;
the numbered `scripts/` are thin orchestrators that wire I/O.

1. **Retrieval** (`01_literature_search.py`) — dispatch the configured query across
   {{N_ENGINES}} engines ({{ENGINE_LIST}}), merge, and de-duplicate into `corpus.jsonl`.
2. **Meta-analysis** (`02_meta_analysis_pipeline.py`) — subfield classification, temporal
   metrics, TF-IDF, non-negative matrix factorization topics, and the citation network.
3. **Knowledge graph** (`03_build_knowledge_graph.py`, optional/LLM-gated) — extract
   assertions and score the {{N_HYPOTHESES}} configured hypotheses.
4. **Figures** (`04_generate_figures.py`) — render publication-ready visualizations.
5. **Injection** (`05_inject_variables.py`) — compute manuscript variables from the
   artifacts above and substitute them into these Markdown sections.

The system runs **offline and deterministically** by default: a committed synthetic
seed corpus drives every stage with fixed seeds, so re-running produces byte-identical
outputs. A live run with engines enabled and credentials supplied replaces the seed
corpus with real records. The template is domain-agnostic — the term, query, keyword
set, subfield taxonomy, and hypotheses all come from `manuscript/config.yaml`.
