"""Prompt templates for research tasks."""
from infrastructure.llm.templates.base import ResearchTemplate
from infrastructure.llm.templates.helpers import (
    format_requirements,
    token_budget_awareness,
    content_requirements,
    section_structure,
    validation_hints,
)
from infrastructure.llm.templates.research import (
    SummarizeAbstract,
    LiteratureReview,
    CodeDocumentation,
    DataInterpretation,
    PaperSummarization,
    LiteratureReviewSynthesis,
    ScienceCommunicationNarrative,
    ComparativeAnalysis,
    ResearchGapIdentification,
    CitationNetworkAnalysis,
)
from infrastructure.llm.templates.manuscript import (
    ManuscriptExecutiveSummary,
    ManuscriptQualityReview,
    ManuscriptMethodologyReview,
    ManuscriptImprovementSuggestions,
    ManuscriptTranslationAbstract,
    REVIEW_MIN_WORDS,
    TRANSLATION_LANGUAGES,
)

from infrastructure.core.exceptions import LLMTemplateError
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

# Try to import prompt composer system
try:
    from infrastructure.llm.prompts.composer import PromptComposer
    PROMPT_COMPOSER_AVAILABLE = True
except ImportError:
    PROMPT_COMPOSER_AVAILABLE = False
    logger.debug("Prompt composer not available, using template system")


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
    'ResearchTemplate',
    # Helper functions
    'format_requirements',
    'token_budget_awareness',
    'content_requirements',
    'section_structure',
    'validation_hints',
    # Template classes
    'SummarizeAbstract',
    'LiteratureReview',
    'CodeDocumentation',
    'DataInterpretation',
    'PaperSummarization',
    'ManuscriptExecutiveSummary',
    'ManuscriptQualityReview',
    'ManuscriptMethodologyReview',
    'ManuscriptImprovementSuggestions',
    'ManuscriptTranslationAbstract',
    'LiteratureReviewSynthesis',
    'ScienceCommunicationNarrative',
    'ComparativeAnalysis',
    'ResearchGapIdentification',
    'CitationNetworkAnalysis',
    # Constants
    'REVIEW_MIN_WORDS',
    'TRANSLATION_LANGUAGES',
    # Functions
    'get_template',
    'TEMPLATES',
]
