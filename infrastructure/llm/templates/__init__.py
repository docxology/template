"""Prompt templates for research tasks."""

from __future__ import annotations

from infrastructure.core.exceptions import LLMTemplateError
from infrastructure.core.logging_utils import get_logger
from infrastructure.llm.templates.base import ResearchTemplate
from infrastructure.llm.templates.helpers import (
    content_requirements,
    format_requirements,
    section_structure,
    token_budget_awareness,
    validation_hints,
)
from infrastructure.llm.templates.manuscript import (
    REVIEW_MIN_WORDS,
    TRANSLATION_LANGUAGES,
    ManuscriptExecutiveSummary,
    ManuscriptImprovementSuggestions,
    ManuscriptMethodologyReview,
    ManuscriptQualityReview,
    ManuscriptTranslationAbstract,
)
from infrastructure.llm.templates.research import (
    CitationNetworkAnalysis,
    CodeDocumentation,
    ComparativeAnalysis,
    DataInterpretation,
    LiteratureReview,
    LiteratureReviewSynthesis,
    PaperSummarization,
    ResearchGapIdentification,
    ScienceCommunicationNarrative,
    SummarizeAbstract,
)

logger = get_logger(__name__)

from infrastructure.llm.core._prompt_availability import PROMPT_COMPOSER_AVAILABLE  # noqa: F401


# Registry of available templates
TEMPLATES: dict[str, type[ResearchTemplate]] = {
    # Original templates
    "summarize_abstract": SummarizeAbstract,
    "literature_review": LiteratureReview,
    "code_doc": CodeDocumentation,
    "data_interpret": DataInterpretation,
    "paper_summarization": PaperSummarization,
    # Manuscript review templates
    "manuscript_executive_summary": ManuscriptExecutiveSummary,
    "manuscript_quality_review": ManuscriptQualityReview,
    "manuscript_methodology_review": ManuscriptMethodologyReview,
    "manuscript_improvement_suggestions": ManuscriptImprovementSuggestions,
    "manuscript_translation_abstract": ManuscriptTranslationAbstract,
    # Literature analysis templates
    "literature_review_synthesis": LiteratureReviewSynthesis,
    "science_communication_narrative": ScienceCommunicationNarrative,
    "comparative_analysis": ComparativeAnalysis,
    "research_gap_identification": ResearchGapIdentification,
    "citation_network_analysis": CitationNetworkAnalysis,
}


def get_template(name: str) -> ResearchTemplate:
    """Get a template by name."""
    if name not in TEMPLATES:
        raise LLMTemplateError(f"Template not found: {name}")
    return TEMPLATES[name]()


# Public API exports
__all__ = [
    # Base class
    "ResearchTemplate",
    # Helper functions
    "format_requirements",
    "token_budget_awareness",
    "content_requirements",
    "section_structure",
    "validation_hints",
    # Template classes
    "SummarizeAbstract",
    "LiteratureReview",
    "CodeDocumentation",
    "DataInterpretation",
    "PaperSummarization",
    "ManuscriptExecutiveSummary",
    "ManuscriptQualityReview",
    "ManuscriptMethodologyReview",
    "ManuscriptImprovementSuggestions",
    "ManuscriptTranslationAbstract",
    "LiteratureReviewSynthesis",
    "ScienceCommunicationNarrative",
    "ComparativeAnalysis",
    "ResearchGapIdentification",
    "CitationNetworkAnalysis",
    # Constants
    "REVIEW_MIN_WORDS",
    "TRANSLATION_LANGUAGES",
    # Functions
    "get_template",
    "TEMPLATES",
]
