# Output Conventions

Every artifact this project produces has a fixed location, a fixed
producer, and a documented consumer. This file is the single source of
truth for that mapping.

## Tree

```mermaid
flowchart TB
    P[/projects/template_search_project//]
    P --> DAT[/data/<br/>committed]
    P --> MAN[/manuscript/]
    P --> OUT[/output/<br/>regeneratable · gitignored]

    DAT --> CORP_IN[corpus.json<br/>offline default corpus]

    MAN --> M_CFG[config.yaml<br/>single source of truth]
    MAN --> M_PRE[preamble.md<br/>injected into Pandoc]
    MAN --> M_S00[00_abstract.md]
    MAN --> M_S01[01_introduction.md]
    MAN --> M_S02[02_methodology.md]
    MAN --> M_S03[03_results.md]
    MAN --> M_S04[04_conclusion.md]
    MAN --> M_S05[05_pipeline_internals.md]
    MAN --> M_S06[06_reproducibility.md]
    MAN --> M_S01S[S01_literature_review.md<br/>optional · deep-search supplement]
    MAN --> M_S99[99_references.md]
    MAN --> M_BIB[references.bib<br/>⚠ auto-generated · do not edit]
    MAN --> M_BIBD[references_deep.bib<br/>⚠ deep search · auto-generated]

    OUT --> O_CORP[corpus.json<br/>enriched corpus]
    OUT --> O_ELOG[enrichment_log.json<br/>per-fetcher status]
    OUT --> O_RS[run_summary.json]
    OUT --> O_RR[reading_report.md]
    OUT --> O_DATA[/data/]
    OUT --> O_MSM[/manuscript/<br/>resolved .md + .bib for render]
    OUT --> O_FIG[/figures/]
    OUT --> O_SR[/search/]
    OUT --> O_CC[/cache/]
    OUT --> O_LLM[/llm/]

    O_DATA --> O_MV[manuscript_variables.json]

    O_FIG --> O_F1[papers_per_source.png]
    O_FIG --> O_F2[year_histogram.png]
    O_FIG --> O_F3[score_distribution.png]

    O_SR --> O_RES[results.json<br/>SearchResult]
    O_SR --> O_SC[/cache/search_HASH.json/]

    O_CC --> O_ABS[/abs/SAFE_ID.txt/<br/>cached abstracts]
    O_CC --> O_PDF[/pdf/SAFE_ID.pdf and .txt/]

    O_LLM --> O_SYN[synthesis.md<br/>corpus-level LLM synthesis]
    O_LLM --> O_PP[/per_paper/SAFE_ID.md/]

    classDef dir fill:#0f172a,stroke:#0f172a,color:#fff
    classDef src fill:#1e3a8a,stroke:#0f172a,color:#fff
    classDef gen fill:#0f766e,stroke:#0f172a,color:#fff
    classDef warn fill:#7c2d12,stroke:#0f172a,color:#fff
    class P,DAT,MAN,OUT,O_DATA,O_MSM,O_FIG,O_SR,O_CC,O_LLM dir
    class CORP_IN,M_CFG,M_PRE,M_S00,M_S01,M_S02,M_S03,M_S04,M_S05,M_S06,M_S01S,M_S99 src
    class O_CORP,O_ELOG,O_RS,O_RR,O_MSM,O_MV,O_F1,O_F2,O_F3,O_RES,O_SC,O_ABS,O_PDF,O_SYN,O_PP gen
    class M_BIB,M_BIBD warn
```

## Producer / consumer table

| Artifact | Produced by | Consumed by |
|---|---|---|
| `output/search/results.json` | `run_search_pipeline.py` | `y_generate_search_figures.py`, `z_generate_manuscript_variables.py`, downstream tooling |
| `output/search/cache/search_*.json` | `infrastructure.search.literature.SearchCache` | next run of `run_search_pipeline.py` |
| `output/cache/abs/*.txt` | `infrastructure.search.literature.AbstractFetcher` | re-runs of the same fetcher |
| `output/cache/pdf/*.{pdf,txt}` | `infrastructure.search.literature.FulltextFetcher` | re-runs of the same fetcher; LLM prompts |
| `output/corpus.json` | `run_search_pipeline.py` (`write_corpus`) | future `LocalBackend` runs; archival |
| `manuscript/references.bib` | `run_search_pipeline.py` | Combined PDF (Pandoc `--natbib` + BibTeX; merged with other `manuscript/*.bib`) |
| `manuscript/references_deep.bib` | `run_deep_search.py` | Same; supplemental [`S01_literature_review.md`](../manuscript/S01_literature_review.md) |
| `output/enrichment_log.json` | `run_search_pipeline.py` (via `pipeline._serialise_enrichment_log`) | debugging only |
| `output/figures/*.png` | `y_generate_search_figures.py` | manuscript via `infrastructure.documentation.FigureManager` |
| `output/data/manuscript_variables.json` | `z_generate_manuscript_variables.py` | debugging / tooling; same run fills `output/manuscript/` |
| `output/manuscript/*` | `z_generate_manuscript_variables.py` | PDF-rendering stage (preferred manuscript root when `*.md` present); resolved `{{…}}` text, copied `config.yaml` and `manuscript/*.bib` |
| `output/llm/per_paper/*.md` | `run_search_pipeline.py` (LLM stage) | reading report assembly |
| `output/llm/synthesis.md` | `run_search_pipeline.py` (LLM stage) | reading report assembly |
| `output/reading_report.md` | `run_search_pipeline.py` | humans |
| `output/run_summary.json` | `run_search_pipeline.py` | downstream tooling, dashboards |
| `output/deep_search/aggregate.json` | `run_deep_search.py` | `s_compose_literature_review.py`, `z_generate_manuscript_variables.py` |
| `output/deep_search/aggregate_report.md` | `run_deep_search.py` | humans |
| `output/deep_search/run_summary.json` | `run_deep_search.py` | downstream tooling, dashboards |
| `output/deep_search/<keyword_slug>/papers.json` | `run_deep_search.py` | `s_compose_literature_review.py` |
| `output/deep_search/<keyword_slug>/reading_report.md` | `run_deep_search.py` | humans |
| `output/deep_search/<keyword_slug>/per_paper/<safe_id>.md` | `run_deep_search.py` (LLM stage) | `s_compose_literature_review.py` (extracts Contribution / Significance) |
| `output/deep_search/composition_summary.json` | `s_compose_literature_review.py` | downstream tooling |
| `manuscript/S01_literature_review.md` | `s_compose_literature_review.py` | combined PDF stage |
| `output/review/stage_*.json` + `summary.json` | `scripts/review` | humans, CI dashboards |

## Conventions

* **Stable filenames.** Every output file has a fixed name; downstream
  consumers never need globbing.
* **JSON for state, Markdown for narrative.** State files are pretty-printed
  JSON for greppability. Narrative files are CommonMark Markdown.
* **No timestamps in filenames.** Timestamps live inside JSON
  (`_cached_at`); filenames stay stable across runs so diffs are
  meaningful.
* **PNG only for figures.** 300 dpi, colour-blind-safe palette, 6 inches
  wide by default.
* **`<safe_id>` derivation.** `re.sub(r"[^A-Za-z0-9._-]", "_", paper.id)`,
  identical across `AbstractFetcher`, `FulltextFetcher`, and
  `run_search_pipeline.py`.
