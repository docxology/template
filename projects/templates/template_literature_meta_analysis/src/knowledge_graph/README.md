# Knowledge Graph Module

Evidence synthesis engine for the literature meta-analysis. Converts LLM-extracted
assertions into RDF/TriG nanopublications and computes citation-weighted hypothesis scores.

## Components

### `schema.py`
RDF namespace and URI definitions. `AIF_NAMESPACE` (`http://activeinference.institute/ontology/`),
`ASSERTION_TYPES` (predicate URIs for supports/contradicts/neutral), `HYPOTHESIS_CATEGORIES`, and
`SUBFIELD_URIS`. Call `configure_hypothesis_categories(hypothesis_ids)` to sync after changing
the active hypothesis set.

### `hypothesis.py`
Scores the hypotheses declared in config (names/scope are configuration-driven,
PREDICTIVE_CODING, SCALABILITY, CLINICAL_UTILITY, MORPHOGENESIS, LANGUAGE_AIF). Computes
citation-weighted hypothesis scores using:

```
score(H) = (Σ_{a∈S(H)} w(a) − Σ_{a∈C(H)} w(a)) / Σ_{a∈A(H)} w(a)
w(a) = log(1 + citations(a)) × confidence(a)
```

Score in [−1, +1]. Also computes temporal trends: `score(H, t)` using only assertions from
papers published ≤ year t.

Key functions:
- `score_hypothesis(assertions, hypothesis_id) -> float`
- `score_all_hypotheses(assertions) -> dict[str, float]`
- `temporal_trend(assertions, hypothesis_id, papers) -> dict[int, float]`
- `configure_hypotheses(config_path) -> list[Hypothesis]`

### `nanopublication.py`
`Assertion` and `Nanopublication` dataclasses following the nanopublication standard
(https://nanopub.net/). Each nanopublication serializes to 4 named RDF graphs: HEAD, ASSERTION,
PROVENANCE, PUBINFO. Persistence formats: JSON Lines (incremental runs) and RDF/TriG
(nanopub.net-compliant).

Key functions:
- `create_nanopub(assertion, attribution) -> Nanopublication`
- `serialize_nanopubs(nanopubs, path)` — write JSON Lines
- `deserialize_nanopubs(path) -> list[Nanopublication]` — read JSON Lines
- `merge_nanopubs(existing, new) -> list[Nanopublication]` — deduplicate, new wins on (paper_id, hypothesis_id)
- `append_nanopubs(new_nanopubs, path) -> list[Nanopublication]` — atomic append+merge
- `nanopub_to_rdf(nanopub, base_uri) -> rdflib.Dataset`
- `serialize_nanopubs_to_trig(nanopubs, path, base_uri)`

### `graph_builder.py`
`KnowledgeGraph` class wrapping rdflib (preferred) or networkx (fallback). Unified API for adding
papers, assertions, citations, and subfield assignments. In-memory `_assertion_map` indexes
assertions by paper and hypothesis for fast lookup.

Key methods:
- `add_paper(paper)`, `add_assertion(assertion)`, `add_citation(src, tgt)`, `add_subfield(paper_id, subfield)`
- `get_assertions_for_paper(paper_id) -> list[str]`
- `get_papers_for_hypothesis(hypothesis_id) -> list[str]`
- `to_networkx() -> nx.DiGraph`

### `llm_extraction.py`
LLM-based assertion extraction via Ollama API (`/api/generate`). Default model: `gemma3:4b`.
Processes papers incrementally — skips papers already present in `nanopublications.jsonl`.
Checkpoints every `checkpoint_interval` papers. Retry with exponential backoff (configurable
`max_retries`, `retry_delay`). Minimum confidence threshold (`min_confidence: 0.6`) filters
low-confidence assertions before persistence.

Key types:
- `LLMConfig: dataclass` — base_url, model, temperature, max_tokens, timeout_seconds, max_retries, retry_delay, nanopub_path, checkpoint_interval, max_papers, min_confidence
- `extract_assertions_llm(papers, config) -> list[Assertion]`

### `extraction.py`
Thin wrapper: `extract_assertions(papers, llm_config) -> list[Assertion]`.

### `query.py`
High-level query helpers over `KnowledgeGraph`: `query_papers_by_hypothesis`,
`query_supporting_papers`, `query_contradicting_papers`, `count_triples_by_type`.

## Scoring Formula

See `manuscript/06_appendix_technical.md §Citation-Weighted Hypothesis Scoring Formula` and
`hypothesis.py:score_hypothesis()`. Key edge case: `score = 0` is ambiguous — it can mean no
assertions OR perfectly balanced support/contradict. Always report assertion counts alongside scores.

See [AGENTS.md](AGENTS.md) for agent-specific constraints.
