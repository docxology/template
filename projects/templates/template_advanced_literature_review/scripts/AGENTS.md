# Pipeline Scripts — Agent Directives

Scripts are thin entrypoints over project code in `src/`. The stage order is:

1. `01_multi_phase_search.py` — intentional live retrieval and phase provenance
2. `01b_fixture_phase_replay.py` — deterministic replay of the committed corpus
   through the phase-provenance contract (default offline lane)
3. `02_meta_analysis_pipeline.py` — deterministic corpus analysis
4. `03_build_knowledge_graph.py` — optional LLM knowledge-graph extraction
5. `04_generate_figures.py` — figures
6. `05_inject_variables.py` — manuscript variables
7. `06_fulltext_assessment.py` — full-text availability assessment
8. `07_literature_evaluation.py` — retrieval/evidence evaluation
9. `08_deep_research_dispatch.py` — thin CLI over deterministic `src/deep_research/dispatch.py` replay
10. `09_export_bibliography.py` — bibliography export
11. `10_reproducibility_assessment.py` — reproducibility scoring
12. `11_fulltext_download.py` — explicit network download
13. `11_validate_outputs.py` — deterministic artifact-manifest + coverage validation report

Two scripts share the `11_` prefix by design: `11_fulltext_download.py` (network
enrichment, must run before `10_reproducibility_assessment.py`) and
`11_validate_outputs.py` (publication validation; runs after the repo-level
pipeline stages). Support modules that are not pipeline stages:

- `_bootstrap.py` — shared `sys.path` bootstrap and `--project` argument handling
- `_io.py` — shared script I/O helpers
- `generate_fixture_corpus.py` — writes the deterministic synthetic fixture corpus

The default `analysis.scripts` list in `manuscript/config.yaml` excludes stages
10 and 11 (both) and runs `01b_fixture_phase_replay.py` instead of the live
`01_multi_phase_search.py`. For enrichment, run stage 11 (`11_fulltext_download.py`)
before stage 10, then rerun stage 05 so manuscript variables reflect the new
evidence. Use `uv run`; never add business logic to numbered scripts.
