# Architecture: The Thin Orchestrator Flow

All business logic lives in `src/`; `scripts/` only orchestrate I/O. The pipeline is a
linear flow from a search term to a rendered manuscript.

## Layers

| Layer | Files | Responsibility | Tested by |
| --- | --- | --- | --- |
| **Retrieval** | `src/literature/{arxiv,openalex,semantic_scholar,crossref,pubmed}_client.py`, `search_runner.py` | Dispatch a query to each enabled engine; parse responses into `Paper`; degrade to `skipped` on error | engine + dispatch test classes |
| **Model & de-dup** | `src/literature/models.py`, `corpus.py` | Canonical `Paper` record; merge duplicates by DOI/arXiv/S2/OpenAlex/title-hash | `TestPaperCanonicalId`, `TestCorpusAdd`, `TestCorpusMerge` |
| **Full text** | `src/literature/fulltext_download.py`, `fulltext_assessment.py` | Resolve + download OA PDFs (opt-in); summarise availability | full-text test module |
| **Analysis** | `src/analysis/` | Descriptive stats + meta-report, entities, embeddings, topics, temporal trends, citation network | analysis test classes |
| **Knowledge graph** (optional) | `src/knowledge_graph/` | Assertion extraction, hypothesis scoring, RDF/TriG nanopublications (LLM-gated) | KG test classes |
| **Visualization** | `src/visualization/` | Headless matplotlib figures from analysis JSON | figure test classes |
| **Manuscript** | `src/manuscript/variables/` | Compute `{{TOKEN}}` values; inject into manuscript sections | `TestComputeVariables`, `TestInjectVariables` |

## Data flow

```
config.yaml (term) ─→ search_runner ─→ corpus.jsonl (deduped Paper records)
                                          │
        ┌─────────────────────────────────┼───────────────────────────────┐
        ▼                                 ▼                                ▼
  analysis/ (stats, entities,      visualization/ (figures)        knowledge_graph/
  embeddings, topics, temporal,                                    (assertions, hypotheses,
  citation network)                                               nanopublications — optional)
        └─────────────────────────────────┼───────────────────────────────┘
                                          ▼
                          manuscript/variables/ ─→ injected manuscript ─→ PDF/HTML
```

Offline, `corpus.jsonl` is seeded from the committed synthetic fixture
(`data/fixtures/<term>_corpus.jsonl`) so the whole flow runs with no network.

## Rules

| Anti-pattern | Why it's wrong | Fix |
| --- | --- | --- |
| Math/parsing inside `scripts/` | Cannot be unit-tested without running the script | Move to `src/`, add a test class |
| `from infrastructure import …` in domain `src/` | Breaks the standalone boundary | Use `scripts/`, or declare the file in `manuscript/layer_contract.yaml` |
| Hard-coding the domain term in `src/` | Breaks genericity | Read it from `manuscript/config.yaml` |
