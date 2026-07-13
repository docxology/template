# Source Code - Agent Directives

Project source for the literature meta-analysis exemplar. All domain behavior lives here; scripts are thin stage wrappers.

## Core Rules

1. Keep logic in `src/`, not in `scripts/`.
2. Keep tests real: no mocks, local HTTP servers for HTTP behavior, temp files for I/O.
3. Keep stochastic analysis deterministic with seed `42` unless config explicitly overrides it.
4. Keep config-driven domain policy in `manuscript/config.yaml`.
5. Link `../../../docs/_generated/COUNTS.md` for live test/coverage facts instead of hardcoding them.

## Dependency Graph

```text
literature        -> no project-src dependencies
analysis          -> literature.models
knowledge_graph   -> literature.models
visualization     -> serialized analysis/KG JSON inputs
manuscript        -> output JSON + config only
deep_research     -> infrastructure.search.deep_research (offline fixture replay)
scripts           -> src modules + optional infrastructure helpers
```

Do not introduce cycles across these layers.

## Runner Modules

| Module | Script | Role |
| --- | --- | --- |
| `literature/search_runner.py` | `01_literature_search.py` | Multi-engine retrieval, relevance filtering, corpus persistence, and deterministic per-engine `retrieval_report.json` provenance |
| `analysis/pipeline_runner.py` | `02_meta_analysis_pipeline.py` | Bibliometrics, text analytics, topics, citation graph |
| `knowledge_graph/kg_runner.py` | `03_build_knowledge_graph.py` | Optional LLM assertions, hypothesis scores, nanopublications |
| `visualization/figure_runner.py` | `04_generate_figures.py` | Figure generation and registry writing |
| `manuscript/variables/` | `05_inject_variables.py` | Token computation and manuscript hydration |
| `literature/fulltext_assessment.py` | `06_fulltext_assessment.py` | Full-text availability report |
| `literature/evaluation.py` | `07_literature_evaluation.py` | Corpus-quality/routing summary and fixture-honesty audit (`literature/fixture_honesty.py`) |
| `deep_research/deep_research_adapter.py` | `08_deep_research_dispatch.py` | Offline-fixture-replay demo of the provider-neutral deep-research request |

## Support Modules

| Module | Used by | Role |
| --- | --- | --- |
| `config_loader.py` | `literature/search_runner.py`, `knowledge_graph/kg_runner.py` | YAML config loading (`load_search_config`, `load_kg_config`) shared across runners |
