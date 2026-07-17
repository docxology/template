# Architecture: Multi-Phase Thin Orchestrator Flow

All business logic lives in `src/`; `scripts/` only orchestrate I/O. Unlike the single-term sibling, the pipeline is not one linear flow from a search term to a rendered manuscript — it is **three phase-scoped searches that merge into one corpus**, each phase carrying its own temporal boundary, engine set, and filter chain, before the shared analysis/knowledge-graph/visualization layers run once over the combined result.

## Two kinds of modules

| Kind | Modules | Rule |
| --- | --- | --- |
| **Symlinked (shared)** | `src/analysis/`, `src/knowledge_graph/`, `src/reproducibility/`, `src/visualization/`, `src/config_loader.py` | Real symlinks into `../../template_literature_meta_analysis/src/`. Edit at the source (the sibling project); this project inherits fixes automatically. `scripts/audit/copy_exemplar.py` materializes them as regular files on standalone export — see `STANDALONE.md`. |
| **Project-specific (advanced)** | `src/multi_phase/`, `src/literature/` (multi-phase additions), `src/manuscript/variables/`, `src/deep_research/`, `src/config.py`, `src/config_validation.py` | Owned here. Implements the multi-phase search, provenance, and phase-aware manuscript variables. |

This split (ARL-7 in `ISA.md`) exists so the advanced template can focus its own code and tests on multi-phase orchestration rather than reimplementing bibliometrics, LLM extraction, reproducibility scoring, or figure generation.

## Layers

| Layer | Files | Responsibility | Tested by |
| --- | --- | --- | --- |
| **Phase-aware retrieval** | `src/multi_phase/search.py`, `src/literature/multi_phase_search.py`, `src/literature/query_router.py` | Execute each configured phase's query set against its engine set; apply the phase's `deterministic_filters`; preserve phase provenance | `TestPhaseMetadata`, `TestDeterministicFilters`, `TestMultiPhaseConfig` |
| **Retrieval engines** | `src/literature/{arxiv,openalex,semantic_scholar,crossref,pubmed,europepmc,biorxiv,sovietrxiv}_client.py`, `search_runner.py`, `engine_dispatch.py` | Dispatch a query to each enabled engine; parse responses into `Paper`; degrade to `skipped` on error | engine + dispatch test classes (shared contract with the single-term sibling) |
| **Model & cross-phase de-dup** | `src/literature/models.py`, `corpus.py` | Canonical `Paper` record; merge duplicates by DOI/arXiv/S2/OpenAlex/title-hash across phases, per `phase_integration.duplicate_resolution` | `TestCorpusCoverage`, `TestPhaseOverlap` |
| **Full text** | `src/literature/fulltext_download.py`, `fulltext_download_cli.py`, `fulltext_assessment.py` | Resolve + download OA PDFs (opt-in); summarize availability | full-text test module |
| **Analysis** (symlinked) | `src/analysis/` | Descriptive stats + meta-report, entities, embeddings, topics, temporal trends, citation network — runs once over the combined corpus | analysis test classes (sibling contract) |
| **Knowledge graph** (symlinked, optional) | `src/knowledge_graph/` | Assertion extraction, hypothesis scoring, RDF/TriG nanopublications (LLM-gated) | KG test classes (sibling contract) |
| **Reproducibility** (symlinked, optional) | `src/reproducibility/` | Workflow-graph reproducibility assessment | reproducibility test classes (sibling contract) |
| **Deep research** (project-specific, optional) | `src/deep_research/dispatch.py` | Deterministic offline replay of a recorded deep-research report; opt-in live dispatch | deep-research dispatch tests |
| **Visualization** (symlinked) | `src/visualization/` | Headless matplotlib figures from analysis JSON | figure test classes (sibling contract) |
| **Manuscript** | `src/manuscript/variables/` | Compute `{{TOKEN}}` values including phase-aware ones (`extractors/multi_phase.py`, `extractors/hypotheses.py`); inject into manuscript sections | manuscript variable test classes |

## Data flow

```
manuscript/config.yaml (search_phases: phase_1_foundation, phase_2_jwst, phase_3_molecules)
        │
        ▼
scripts/01_multi_phase_search.py ─→ per-phase corpora
   output/data/phase_1_foundation_corpus.jsonl
   output/data/phase_2_jwst_corpus.jsonl
   output/data/phase_3_molecules_corpus.jsonl
        │  (phase_integration: duplicate_resolution, citation_validation, quality_gates)
        ▼
   output/data/combined_corpus.jsonl  +  output/data/phase_metadata.json
        │
        ┌─────────────────────────────────┼───────────────────────────────┐
        ▼                                 ▼                                ▼
  analysis/ (stats, entities,      visualization/ (figures)        knowledge_graph/
  embeddings, topics, temporal,                                    (assertions, hypotheses,
  citation network) — symlinked                                    nanopublications) — symlinked, optional
        └─────────────────────────────────┼───────────────────────────────┘
                                          ▼
                    manuscript/variables/ (phase-aware) ─→ injected manuscript ─→ PDF/HTML
```

Offline, each phase's corpus is seeded from tracked evidence
(`output/data/combined_corpus.jsonl` and the per-phase `*_corpus.jsonl` files)
so the whole flow runs with no network by default. `scripts/01_multi_phase_search.py`
is the explicit live/network refresh path — see `agent_instructions.md` Rule 5.

## Rules

| Anti-pattern | Why it's wrong | Fix |
| --- | --- | --- |
| Math/parsing inside `scripts/` | Cannot be unit-tested without running the script | Move to `src/`, add a test class |
| Editing a symlinked module's content by opening the path under this project | Edits land in `template_literature_meta_analysis/src/` and silently affect both templates | Edit at the sibling project directly; confirm with `git status` which repo path actually changed |
| Hard-coding a phase name, domain term, or temporal boundary in `src/multi_phase/` | Breaks retargeting to a new domain/phase design | Read phase definitions from `manuscript/config.yaml` → `project_config.search_phases` |
| Adding a new phase without a `depends_on` entry when it should cross-validate an earlier phase | Silently breaks `phase_integration.citation_validation` | Declare `depends_on` explicitly, matching `phase_2_jwst`/`phase_3_molecules` in `config.yaml` |
