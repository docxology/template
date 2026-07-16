# Pipeline Scripts — Agent Directives

Scripts are thin entrypoints over project code in `src/`. The stage order is:

1. `01_multi_phase_search.py` — intentional live retrieval and phase provenance
2. `02_meta_analysis_pipeline.py` — deterministic corpus analysis
3. `03_build_knowledge_graph.py` — optional LLM knowledge-graph extraction
4. `04_generate_figures.py` — figures
5. `05_inject_variables.py` — manuscript variables
6. `06_fulltext_assessment.py` — full-text availability assessment
7. `07_literature_evaluation.py` — retrieval/evidence evaluation
8. `08_deep_research_dispatch.py` — thin CLI over deterministic `src/deep_research/dispatch.py` replay
9. `09_export_bibliography.py` — bibliography export
10. `10_reproducibility_assessment.py` — reproducibility scoring
11. `11_fulltext_download.py` — explicit network download

The default `analysis.scripts` list excludes stages 10 and 11. For enrichment,
run stage 11 before stage 10, then rerun stage 05 so manuscript variables reflect
the new evidence. Use `uv run`; never add business logic to numbered scripts.
