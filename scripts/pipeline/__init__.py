"""Pipeline stage scripts — numbered orchestrators for the build pipeline.

Each ``stage_NN_*.py`` module is a thin orchestrator delegating to an
``infrastructure/`` module.  The canonical stage order and tags live in
``infrastructure/core/pipeline/pipeline.yaml``; this package only holds
the entry-point scripts.

Stages present in this package:

    stage_00_setup           – environment setup (Python version, deps, dirs)
    stage_01_test            – infrastructure + project test orchestration
    stage_02_analysis        – project-script discovery and execution
    stage_03_render          – manuscript PDF rendering
    stage_04_validate        – output validation
    stage_05_copy            – copy outputs to final destination
    stage_06_llm_review      – LLM review and translation
    stage_07_executive_report– multi-project executive reporting
    stage_08_connector_search– connector-backed search (opt-in)
    stage_09_provenance_record– provenance recording (opt-in)
    stage_10_research_workflow– research workflow orchestration (opt-in)
    stage_11_ebook           – ebook generation (EPUB/MOBI/DOCX; opt-in)
    stage_12_metadata        – metadata package (ONIX/OPF/JSON; opt-in)
"""

__all__ = [
    "stage_00_setup",
    "stage_01_test",
    "stage_02_analysis",
    "stage_03_render",
    "stage_04_validate",
    "stage_05_copy",
    "stage_06_llm_review",
    "stage_07_executive_report",
    "stage_08_connector_search",
    "stage_09_provenance_record",
    "stage_10_research_workflow",
    "stage_11_ebook",
    "stage_12_metadata",
]
