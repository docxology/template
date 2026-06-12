# Literature Data Flow

A core architectural diagram showing how a topic string becomes a citation
in a rendered PDF, and where every artifact lands.

## Stages

```mermaid
flowchart TB
    TOPIC([Research topic string]) --> Q[1 - SearchQuery<br/>text · year_min · year_max · max_results · sources]

    Q --> CLIENT[2 - LiteratureClient<br/>aggregator]

    subgraph BACKENDS [Backends - parallel, failure-isolated]
        direction LR
        ARXIV[ArxivBackend<br/>Atom XML]
        CROSSREF[CrossrefBackend<br/>JSON]
        LOCAL[LocalBackend<br/>JSON corpus on disk]
        PAPERCLIP[PaperclipBackend<br/>JSON · API key]
    end

    CLIENT --> BACKENDS
    BACKENDS --> MERGE{{merge_papers<br/>DOI / arXiv / title-year dedup}}
    MERGE --> RESULT[3 - SearchResult<br/>papers · per_source_counts · errors]

    RESULT --> ABS[4a - AbstractFetcher<br/>arXiv → Paper.abstract]
    RESULT --> FULL[4b - FulltextFetcher<br/>PDF → pypdf → Paper.fulltext]
    RESULT --> CORPUS[4c - write_corpus<br/>→ output/corpus.json]

    ABS --> EXPORT[5 - paper_to_bibentry<br/>BibEntry · BibDatabase]
    FULL --> EXPORT
    CORPUS --> EXPORT

    EXPORT --> BIB[6a - write_bibfile<br/>→ manuscript/references.bib]
    ABS --> LLM[6b - LLM synthesis<br/>abstracts + fulltext<br/>→ output/llm/*.md]
    FULL --> LLM

    BIB --> PDF[7 - Pandoc --natbib<br/>→ output/&lt;project&gt;/pdf/]
    LLM --> REPORT[7 - Reading report<br/>→ output/reading_report.md]

    classDef stage fill:#1e3a8a,stroke:#0f172a,color:#fff
    classDef io fill:#0f766e,stroke:#0f172a,color:#fff
    classDef external fill:#7c2d12,stroke:#0f172a,color:#fff
    class Q,CLIENT,RESULT,EXPORT stage
    class ABS,FULL,CORPUS,BIB,LLM,REPORT,PDF io
    class ARXIV,CROSSREF,LOCAL,PAPERCLIP external
```

## On-Disk Layout

A typical run lands the following artefacts:

```mermaid
flowchart TB
    PROJ[projects/archive/template_search_project/<br/>local copy under projects/ only]
    PROJ --> OUTPUT[output]
    PROJ --> MANUSCRIPT[manuscript]

    OUTPUT --> SEARCH[search]
    OUTPUT --> CACHE[cache]
    OUTPUT --> LLM_DIR[llm]
    OUTPUT --> PDF_DIR[pdf]
    OUTPUT --> CORPUS_F[corpus.json<br/>LocalBackend-compatible]

    SEARCH --> RES_F[results.json<br/>SearchResult]
    SEARCH --> SC[cache/search_HASH.json<br/>deterministic SearchCache]

    CACHE --> ABS_DIR[abs/SAFE_ID.txt<br/>cached abstracts]
    CACHE --> PDF_CACHE[pdf/SAFE_ID.pdf and .txt<br/>cached fulltext]

    LLM_DIR --> SYNTH[synthesis.md<br/>cross-corpus narrative]
    LLM_DIR --> PER_PAPER[per_paper/SAFE_ID.md]

    PDF_DIR --> FINAL[template_search_project.pdf]

    MANUSCRIPT --> BIBF[references.bib<br/>auto-populated · Pandoc-ready]

    classDef dir fill:#0f172a,stroke:#0f172a,color:#fff
    classDef file fill:#0f766e,stroke:#0f172a,color:#fff
    class PROJ,OUTPUT,MANUSCRIPT,SEARCH,CACHE,LLM_DIR,PDF_DIR dir
    class CORPUS_F,RES_F,SC,ABS_DIR,PDF_CACHE,SYNTH,PER_PAPER,FINAL,BIBF file
```

## Stage Idempotency

| Stage | Re-runs incur cost? | Caching mechanism |
|---|---|---|
| 2. Search | only on cache miss | `SearchCache` (JSON files keyed by query hash) |
| 4a. Abstract fetch | only on cache miss | `AbstractFetcher.cache_dir` |
| 4b. Fulltext fetch | only on cache miss | `FulltextFetcher.cache_dir` |
| 5. BibTeX export | always (fast, in-memory) | n/a |
| 6b. LLM synthesis | always unless `seed=` pinned and cache layered above | callers' responsibility |
| 7. PDF render | always; reads `references.bib` + figures | infrastructure pipeline |

## Failure Surfaces

* **Network outages** → `SearchResult.errors[backend_name] = message`; the
  search itself still returns whatever the surviving backends produced.
* **Corpus missing/corrupt** → `BackendError` raised by `LocalBackend`; CLI
  surfaces it but does not abort multi-backend searches.
* **PDF parse failure** → `FetchResult.status = "error"` with the message
  `pypdf unavailable; PDF cached but text not extracted`. The cached PDF
  is still on disk for downstream tooling.
* **BibTeX write conflict** → `paper_to_bibentry` uses deterministic key
  generation but does not detect collisions; callers should
  `db.find(key)` before `db.add(entry)` if uniqueness is critical.

## See Also

* [`docs/architecture/two-layer-architecture.md`](../architecture/two-layer-architecture.md) — generic Layer-1/Layer-2 split.
* [`docs/modules/literature-search-and-references.md`](../modules/literature-search-and-references.md) — module reference.
* [`docs/guides/literature-workflow-guide.md`](../guides/literature-workflow-guide.md) — hands-on walkthrough.
