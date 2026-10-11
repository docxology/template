# Architecture: Multi-Phase Thin Orchestrator Flow

Project-owned business logic lives in `src/`; scripts coordinate it with the declared Meta engine. The configured phase-scoped searches merge into one corpus, retaining each phase's temporal boundary, engine set and filter chain. Shared analysis, knowledge-graph and visualization methods then consume that combined result.

## Two kinds of modules

| Kind | Modules | Rule |
| --- | --- | --- |
| **Declared shared provider** | `template_literature_meta_analysis.analysis`, `.knowledge_graph`, `.reproducibility`, `.visualization` | Canonical methods live in the Meta project's `src/` and are imported through its namespaced distribution. Prepare the exact provider declared in `pyproject.toml`; installed acceptance requires its admitted wheel. Advanced exports do not duplicate these packages. |
| **Project-specific (advanced)** | `src/multi_phase/`, `src/literature/`, `src/manuscript/variables/`, `src/deep_research/`, `src/config.py`, `src/config_loader.py`, `src/config_validation.py` | Owned here. Implements the phase policy, retrieval adapters, sampling, provenance and phase-aware manuscript variables. |

This boundary lets Advanced focus its own code and tests on phase policy while the Meta engine supplies common scientific methods. A shared change needs provider tests and consumer parity controls. The dated `ISA.md` decisions describe the earlier design; the declared dependency and current script imports define the executable boundary.

## Layers

| Layer | Files | Responsibility | Tested by |
| --- | --- | --- | --- |
| **Phase-aware retrieval** | `src/multi_phase/models.py`, `src/multi_phase/llm_filter.py`, `src/multi_phase/search.py`, `src/literature/query_router.py` | Keep phase/paper records and optional LLM filtering in focused modules; `search.py` remains the public orchestration façade that executes each configured phase's query set, applies deterministic filters, and preserves phase provenance | `TestPhaseMetadata`, `TestDeterministicFilters`, `TestMultiPhaseConfig` |
| **Retrieval engines** | `src/literature/{arxiv,openalex,semantic_scholar,crossref,pubmed,europepmc,biorxiv,sovietrxiv}_client.py`, `search_runner.py`, `engine_dispatch.py` | Dispatch a query to each enabled engine; parse responses into `Paper`; degrade to `skipped` on error | engine + dispatch test classes (shared contract with the single-term sibling) |
| **Model & cross-phase de-dup** | `src/literature/models.py`, `corpus.py` | Canonical `Paper` record; merge duplicates by DOI/arXiv/S2/OpenAlex/title-hash across phases, per `phase_integration.duplicate_resolution` | `TestCorpusCoverage`, `TestPhaseOverlap` |
| **Full text** | `src/literature/fulltext_download.py`, `fulltext_download_cli.py`, `fulltext_assessment.py` | Resolve + download OA PDFs (opt-in); summarize availability | full-text test module |
| **Analysis** (provider) | `template_literature_meta_analysis.analysis` | Descriptive stats + meta-report, entities, embeddings, topics, temporal trends, citation network — runs once over the combined corpus | Meta source suite and Advanced consumer parity |
| **Knowledge graph** (provider, optional) | `template_literature_meta_analysis.knowledge_graph` | Assertion extraction, hypothesis scoring, RDF/TriG nanopublications (local-model gated) | Meta source suite and Advanced consumer parity |
| **Reproducibility** (provider, optional) | `template_literature_meta_analysis.reproducibility` | Workflow-graph reproducibility assessment | Meta source suite and Advanced consumer parity |
| **Deep research** (project-specific, optional) | `src/deep_research/dispatch.py` | Deterministic offline replay of a recorded deep-research report; opt-in live dispatch | deep-research dispatch tests |
| **Visualization** (provider) | `template_literature_meta_analysis.visualization` | Headless matplotlib figures from analysis JSON | Meta source suite and Advanced consumer parity |
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
  citation network) — provider                                     nanopublications) — provider, optional
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
| Copying shared provider methods into Advanced | Creates a second implementation that can drift from the admitted provider | Change Meta's canonical `src/`, prepare its exact declared distribution, and verify both provider and consumer contracts |
| Hard-coding a phase name, domain term, or temporal boundary in `src/multi_phase/` | Breaks retargeting to a new domain/phase design | Read phase definitions from `manuscript/config.yaml` → `project_config.search_phases` |
| Adding a new phase without a `depends_on` entry when it should cross-validate an earlier phase | Silently breaks `phase_integration.citation_validation` | Declare `depends_on` explicitly, matching `phase_2_jwst`/`phase_3_molecules` in `config.yaml` |
