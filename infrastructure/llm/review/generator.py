"""Review generation utilities for manuscript review operations.

Error contract design:
- Text extraction helpers (extract_manuscript_text) return (None, metrics) on failure
  so the pipeline can report a graceful skip rather than aborting on missing files.
- LLM response validation (llm/validation/core.py) raises ValidationError immediately —
  an invalid response from the LLM is a programmer error or model failure that cannot
  be meaningfully recovered from in-line.
- These are intentionally different contracts for different failure domains.

This module re-exports from focused submodules for backwards compatibility:
- quality.py: review quality validation (validate_review_quality, ReviewType, etc.)
- ollama_setup.py: Ollama server management and client setup
- generation.py: core generation logic (generate_review_with_metrics, extract_manuscript_text, etc.)
"""

from __future__ import annotations

from infrastructure.llm.core.client import LLMClient
from infrastructure.llm.templates.manuscript import (
    ManuscriptExecutiveSummary,
    ManuscriptImprovementSuggestions,
    ManuscriptQualityReview,
    ManuscriptMethodologyReview,
)

from infrastructure.llm.review.metrics import ReviewMetrics

# Re-exports from quality.py — all public names that external code imports from generator.
from infrastructure.llm.review.quality import (  # noqa: F401
    ReviewType,
    ReviewQualityDetails,
    validate_review_quality,
    _is_small_model,
)

# Re-exports from ollama_setup.py — all public names that external code imports from generator.
from infrastructure.llm.review.ollama_setup import (  # noqa: F401
    get_manuscript_review_system_prompt,
    create_review_client,
    select_and_start_ollama_model,
    warmup_model,
)

# Re-exports from generation.py — core generation logic.
from infrastructure.llm.review.generation import (  # noqa: F401
    extract_manuscript_text,
    generate_review_with_metrics,
    generate_translation,
)


def generate_llm_executive_summary(
    client: LLMClient, text: str, model_name: str = "", temperature: float = 0.3
) -> tuple[str, ReviewMetrics]:
    """Named public API entry point for executive summary reviews.

    Binds review_type='executive_summary' and ManuscriptExecutiveSummary template.
    Callers use the named function rather than the generic generate_review_with_metrics
    to avoid having to know the template class and review_type string.

    Args:
        client: LLM client to use for generation.
        text: Manuscript text to review.
        model_name: Optional model override. Defaults to client's configured model.
        temperature: Sampling temperature. Defaults to 0.3 (factual analysis).
    """
    return generate_review_with_metrics(
        client=client,
        text=text,
        review_type="executive_summary",
        review_name="executive summary",
        template_class=ManuscriptExecutiveSummary,
        model_name=model_name,
        temperature=temperature,
        max_tokens=None,
    )


def generate_quality_review(
    client: LLMClient, text: str, model_name: str = "", temperature: float = 0.3
) -> tuple[str, ReviewMetrics]:
    """Named public API entry point for quality reviews.

    Binds review_type='quality_review' and ManuscriptQualityReview template.
    Callers use the named function rather than the generic generate_review_with_metrics
    to avoid having to know the template class and review_type string.

    Args:
        client: LLM client to use for generation.
        text: Manuscript text to review.
        model_name: Optional model override. Defaults to client's configured model.
        temperature: Sampling temperature. Defaults to 0.3 (factual analysis).
    """
    return generate_review_with_metrics(
        client=client,
        text=text,
        review_type="quality_review",
        review_name="quality review",
        template_class=ManuscriptQualityReview,
        model_name=model_name,
        temperature=temperature,
        max_tokens=None,
    )

def generate_methodology_review(
    client: LLMClient, text: str, model_name: str = "", temperature: float = 0.3
) -> tuple[str, ReviewMetrics]:
    """Named public API entry point for methodology reviews.

    Binds review_type='methodology_review' and ManuscriptMethodologyReview template.
    Callers use the named function rather than the generic generate_review_with_metrics
    to avoid having to know the template class and review_type string.

    Args:
        client: LLM client to use for generation.
        text: Manuscript text to review.
        model_name: Optional model override. Defaults to client's configured model.
        temperature: Sampling temperature. Defaults to 0.3 (factual analysis).
    """
    return generate_review_with_metrics(
        client=client,
        text=text,
        review_type="methodology_review",
        review_name="methodology review",
        template_class=ManuscriptMethodologyReview,
        model_name=model_name,
        temperature=temperature,
        max_tokens=None,
    )

def generate_improvement_suggestions(
    client: LLMClient, text: str, model_name: str = "", temperature: float = 0.4
) -> tuple[str, ReviewMetrics]:
    """Named public API entry point for improvement suggestions (ManuscriptImprovementSuggestions template).

    Uses temperature=0.4 (vs 0.3 for other reviews) because generative ideation
    benefits from higher diversity — the task is proposing novel directions, not
    accurate analysis.

    Args:
        client: LLM client to use for generation.
        text: Manuscript text to review.
        model_name: Optional model override. Defaults to client's configured model.
        temperature: Sampling temperature. Defaults to 0.4 (generative ideation).
    """
    return generate_review_with_metrics(
        client=client,
        text=text,
        review_type="improvement_suggestions",
        review_name="improvement suggestions",
        template_class=ManuscriptImprovementSuggestions,
        model_name=model_name,
        temperature=temperature,
        max_tokens=None,
    )
