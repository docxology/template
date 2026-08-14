# Analysis Module — Agent Directives

## Overview

Seven deterministic analysis modules (`citation_network.py`, `descriptive_stats.py`,
`embeddings.py`, `entities.py`, `temporal_analysis.py`, `text_processing.py`,
`topic_modeling.py`; plus subfield keyword/registry helpers) computing all bibliometric, temporal, and semantic metrics
required for the manuscript. Orchestration: `analysis/pipeline_runner.py`
(`scripts/02_meta_analysis_pipeline.py`). No scripts-level logic belongs here — all computation lives in these
modules and is imported by `scripts/02_meta_analysis_pipeline.py`.

## Invariants Agents Must Preserve

- **Determinism**: All stochastic operations (`topic_modeling.py`) use fixed `seed=42`.
  Never remove or parameterize away the seed.
- **No mock policy**: Tests in `tests/analysis/` use real data arrays, not mocks.
  Do not introduce `unittest.mock` or `monkeypatch` replacements.
- **Pre-compiled patterns**: `subfield_registry.get_pattern_cache()` is built at import and
  rebuilt on `configure_subfields()`. Never call `re.compile()` inside `classify_paper()`.
- **Directed graph metrics**: `citation_network.compute_network_metrics()` computes `avg_in_degree`
  and `avg_out_degree` separately using `graph.in_degree()` / `graph.out_degree()`. Do not
  simplify to `num_edges / num_nodes` — that is only correct for undirected graphs.
- **CAGR as fraction**: `temporal_analysis.estimate_growth_rate()` returns `cagr` as a decimal
  fraction (e.g. `0.17` for 17%). `variables/compute.py` multiplies by 100 for display. Never output
  CAGR already multiplied — it would double-inflate the percentage.

## Key Algorithms

### Subfield classification priority
Config `subfield_keywords` override the generic defaults; each configured bucket's
priority comes from the prefix map in `subfield_registry.load_subfields_from_config`
(`C`=1, `B`=2, `A1`=3, otherwise 4). With the bundled modafinil taxonomy all six
buckets carry priority 4, so the classifier selects the bucket with the highest
keyword-match count; papers with no keyword matches fall to the catch-all (the
highest-priority bucket, first in definition order when tied).

### TF-IDF formula
```
TF-IDF(t, d) = (count(t,d)/|d|) × (log(N/(df(t)+1)) + 1)
```
Rows are L2-normalized. The outer `+1` guarantees strictly positive IDF for any term.

### NMF convergence
Early stopping when `|prev_error - error| / prev_error < 1e-4` (checked every 10 iterations).
The default `max_iter=200` is an upper bound, not the typical stopping point.

## Adding a New Analysis Module

1. Add `src/analysis/new_module.py` with pure functions (no side effects, no file I/O).
2. Import from `scripts/02_meta_analysis_pipeline.py`; handle I/O there.
3. Write tests in `tests/analysis/test_new_module.py` using real numerical data.
4. Export from `src/analysis/__init__.py` if needed by other modules.
5. Update this file and `README.md`.

## Known Limitations

- **Subfield classifier**: Papers using non-canonical vocabulary fall to the catch-all bucket
  (with the bundled taxonomy, the first configured bucket). Consider an embedding-based
  classifier for large future corpora.
- **Temporal CAGR**: Uses single-year endpoint counts; an incomplete current year (e.g. April 2026)
  will undercount that year's publications and deflate CAGR.
- **Citation resolution**: Only ~22% of references resolve to corpus papers in the tracked
  snapshot; API identifier formats (DOI, arXiv, S2 ID) rarely match exactly across engines.
  Cross-format fuzzy matching would improve this.
- **NMF initialization**: Random initialization means topics are locally optimal, not globally.
  Jaccard stability > 0.90 across alternative seeds has been verified empirically.
