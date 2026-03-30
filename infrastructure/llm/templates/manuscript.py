"""Manuscript review templates for LLM operations.

This module re-exports all manuscript template classes and constants from their
focused submodules. All public imports that previously worked against this module
continue to work unchanged.

Submodules:
    manuscript_reviews: ManuscriptExecutiveSummary, ManuscriptQualityReview
    manuscript_suggestions: ManuscriptMethodologyReview, ManuscriptImprovementSuggestions
    manuscript_translation: ManuscriptTranslationAbstract, TRANSLATION_LANGUAGES
"""

from __future__ import annotations

from infrastructure.llm.templates.manuscript_reviews import (
    ManuscriptExecutiveSummary,
    ManuscriptQualityReview,
)
from infrastructure.llm.templates.manuscript_suggestions import (
    ManuscriptImprovementSuggestions,
    ManuscriptMethodologyReview,
)
from infrastructure.llm.templates.manuscript_translation import (
    TRANSLATION_LANGUAGES,
    ManuscriptTranslationAbstract,
)

# Minimum word counts for quality validation
# Note: improvement_suggestions uses a lower threshold (200) because models often
# produce focused, actionable output that may be shorter but still high-quality.
# The retry mechanism catches truly short responses.
REVIEW_MIN_WORDS = {
    "executive_summary": 250,
    "quality_review": 300,
    "methodology_review": 300,
    "improvement_suggestions": 200,  # Lower threshold for focused actionable output
    "translation": 400,  # English abstract + translation (~200 words each)
}

__all__ = [
    "ManuscriptExecutiveSummary",
    "ManuscriptImprovementSuggestions",
    "ManuscriptMethodologyReview",
    "ManuscriptQualityReview",
    "ManuscriptTranslationAbstract",
    "REVIEW_MIN_WORDS",
    "TRANSLATION_LANGUAGES",
]
