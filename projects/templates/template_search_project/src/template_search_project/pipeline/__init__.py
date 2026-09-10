"""Pipeline-stage modules for the literature workflow: pure orchestration,
LLM synthesis, composition, LLM runtime setup, and dotenv utilities.

These modules are re-exported from ``template_search_project`` for
backwards compatibility; import them from the package root.
"""

from template_search_project.pipeline.composition import compose_literature_review
from template_search_project.pipeline.dotenv import load_dotenv, parse_dotenv
from template_search_project.pipeline.llm_runtime import build_llm_callable
from template_search_project.pipeline.pipeline import (
    LiteratureRunArtifacts,
    run_literature_pipeline,
)
from template_search_project.pipeline.synthesis import (
    SynthesisResult,
    build_corpus_block,
    build_paper_block,
    synthesise_corpus,
    synthesise_per_paper,
)

__all__ = [
    "LiteratureRunArtifacts",
    "SynthesisResult",
    "build_corpus_block",
    "build_llm_callable",
    "build_paper_block",
    "load_dotenv",
    "parse_dotenv",
    "run_literature_pipeline",
    "synthesise_corpus",
    "synthesise_per_paper",
    "compose_literature_review",
]
