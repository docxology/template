# Analysis Module

Bibliometric, temporal, and text-analytics pipeline for the literature meta-analysis.
All computation resides here; scripts in `scripts/` are thin orchestrators that import these modules.

## Components

### Subfield classification (`subfield_classifier.py`, `subfield_defaults.py`, `subfield_registry.py`)

Classifies papers into one of the configured subfield domains using priority-weighted word-boundary
keyword matching. Keyword data lives in `subfield_defaults.py`; config loading and the compiled
pattern cache live in `subfield_registry.py`; `subfield_classifier.py` exposes the public API.

Key functions:
- `classify_paper(paper) -> str` — classify one paper
- `classify_corpus(papers, config_path) -> dict[str, list[Paper]]` — classify full corpus
- `configure_subfields(config_path)` — reload keyword set from YAML

### `temporal_analysis.py`
Computes publication trend metrics from paper year data: year counts (with gap-filling),
cumulative totals, 3-year smoothed moving averages, peak year, mean year-over-year growth rate,
doubling time (`ln2 / ln(1 + g̅)`), and CAGR (`(end/start)^(1/years) - 1`).

Key functions:
- `compute_temporal_metrics(papers) -> dict` — returns year_counts, cumulative, smoothed_annual, first/last/peak year
- `estimate_growth_rate(year_counts) -> dict` — returns annual_growth_rates, mean_growth_rate, doubling_time, cagr

### `text_processing.py`
Manual TF-IDF implementation with smoothed IDF (`log(N/(df+1))+1`) and L2 row normalization.
Vocabulary selection excludes terms appearing in >95% of documents (corpus-level stopwords) when
the corpus has ≥ 20 documents. 66 hardcoded English stopwords; custom extras can be passed.

Key functions:
- `tokenize(text) -> list[str]` — lowercase alphanumeric tokens length ≥ 2
- `remove_stopwords(tokens, extra_stopwords) -> list[str]`
- `build_tfidf_matrix(documents, max_features) -> (np.ndarray, list[str])` — (n_docs × n_features), vocabulary

### `topic_modeling.py`
NMF topic discovery using multiplicative update rules (`V ≈ W @ H`). Converges when relative
reconstruction error change between 10-iteration checkpoints drops below `tol=1e-4`, or after
`max_iter=200` iterations. Fixed random seed (42) ensures deterministic topic alignment.

Key functions:
- `fit_nmf_topics(tfidf_matrix, feature_names, n_topics, seed, top_n, max_iter) -> list[dict]`
- `get_document_topics(tfidf_matrix, n_topics, seed, max_iter) -> np.ndarray` — (n_docs, n_topics)

### `citation_network.py`
Builds a `networkx.DiGraph` from paper corpus and resolved citations. Computes PageRank,
HITS hub/authority scores, correct per-direction in/out-degree distributions (not the common
`num_edges/num_nodes` approximation), network density, weakly connected components, and greedy
modularity community detection. Reference resolution handles DOI, arXiv ID, Semantic Scholar ID,
and OpenAlex ID via a cross-format index.

Key functions:
- `build_citation_graph(papers, citations) -> nx.DiGraph`
- `compute_network_metrics(graph, hits_max_iter, hits_tol) -> dict`
- `detect_communities(graph) -> dict[str, int]` — node_id → community_id
- `build_reference_index(papers) -> dict[str, str]`
- `resolve_citations(papers, ref_index, logger) -> list[Citation]`

## Algorithmic Choices

| Module | Choice | Rationale |
|---|---|---|
| Subfield | Priority-weighted keyword matching | Interpretable; config-driven; no training data needed |
| Subfield | Pre-compiled regex | ~10× faster than per-call `re.compile()` on 800-paper corpus |
| Text | Smoothed IDF `log(N/(df+1))+1` | Prevents zero IDF for hapax legomena; `+1` outer ensures positive weights |
| Text | 95% DF upper cap | Removes corpus-level stopwords (e.g. "inference") that survive the STOPWORDS list |
| NMF | Multiplicative updates | Guarantees non-negativity; standard for topic modeling |
| NMF | Early stopping at Frobenius tol=1e-4 | Avoids wasted iterations; typically converges in 40–80 iterations |
| CAGR | `(end_year/start_year)^(1/n) - 1` | Measures annual field activity rate, not cumulative size |
| Citation | Directed in/out degree (not `edges/nodes`) | Correct for directed graphs; in-degree ≠ out-degree in citation networks |

See [AGENTS.md](AGENTS.md) for agent-specific constraints.
