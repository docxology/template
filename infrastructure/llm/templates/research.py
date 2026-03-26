"""Research task templates for LLM operations.

This module re-exports from focused submodules:
- paper_summarization: PaperSummarization template with domain-aware rendering
- literature_analysis: multi-paper analysis templates (synthesis, communication,
  comparative, gap identification, citation network)

Simple single-purpose templates (SummarizeAbstract, LiteratureReview,
CodeDocumentation, DataInterpretation) are defined directly here.
"""

from __future__ import annotations

from infrastructure.llm.templates.base import ResearchTemplate
from infrastructure.llm.templates.literature_analysis import (
    CitationNetworkAnalysis,
    ComparativeAnalysis,
    LiteratureReviewSynthesis,
    ResearchGapIdentification,
    ScienceCommunicationNarrative,
)
from infrastructure.llm.templates.paper_summarization import PaperSummarization

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


class SummarizeAbstract(ResearchTemplate):
    """Template for summarizing abstracts."""

    template_str = (
        "Please summarize the following abstract in 3-5 bullet points, "
        "highlighting the main contribution, methodology, and results:\n\n"
        "${text}"
    )


class LiteratureReview(ResearchTemplate):
    """Template for generating literature reviews."""

    template_str = (
        "Based on the following paper summaries, write a cohesive "
        "literature review paragraph:\n\n"
        "${summaries}"
    )


class CodeDocumentation(ResearchTemplate):
    """Template for documenting code."""

    template_str = (
        "Generate a Python docstring for the following code, "
        "including Args, Returns, and Raises sections:\n\n"
        "${code}"
    )


class DataInterpretation(ResearchTemplate):
    """Template for interpreting data."""

    template_str = (
        "Analyze the following data statistics and provide "
        "a scientific interpretation of the trends:\n\n"
        "${stats}"
    )


__all__ = [
    # Simple templates (defined here)
    "SummarizeAbstract",
    "LiteratureReview",
    "CodeDocumentation",
    "DataInterpretation",
    # Re-exported from paper_summarization
    "PaperSummarization",
    # Re-exported from literature_analysis
    "LiteratureReviewSynthesis",
    "ScienceCommunicationNarrative",
    "ComparativeAnalysis",
    "ResearchGapIdentification",
    "CitationNetworkAnalysis",
]
