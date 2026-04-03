"""Review generation utilities for manuscript review operations.

This module is the **public API façade** for the llm/review package.  It owns:
- ``_REVIEW_REGISTRY`` — the authoritative mapping of review types to their template
  classes and default temperatures.  Adding a new review type requires a single entry here.
- ``_make_review_fn`` — the factory that produces the four named public entry points
  (``generate_llm_executive_summary``, ``generate_quality_review``, etc.).

These are **not** leftovers from the submodule split; they are the intentional responsibility
of this module.  Implementation details live in the focused submodules below.

Error contract design:
- Text extraction helpers (extract_manuscript_text) return (None, metrics) on failure
  so the pipeline can report a graceful skip rather than aborting on missing files.
- LLM response validation (llm/validation/core.py) raises ValidationError immediately —
  an invalid response from the LLM is a programmer error or model failure that cannot
  be meaningfully recovered from in-line.
- These are intentionally different contracts for different failure domains.

Submodule re-exports (backwards compatibility):
- quality.py: review quality validation (validate_review_quality, ReviewType, etc.)
- ollama_setup.py: Ollama server management and client setup
- generation.py: core generation logic (generate_review_with_metrics, extract_manuscript_text, etc.)
"""

from __future__ import annotations

from collections.abc import Callable

from infrastructure.llm.core.client import LLMClient
from infrastructure.llm.templates.base import ResearchTemplate
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


# Registry mapping review_type → (review_name, template_class, default_temperature).
# Add new review types here; the _make_review_fn factory generates the public entry points.
_REVIEW_REGISTRY: dict[str, tuple[str, type[ResearchTemplate], float]] = {
    "executive_summary": ("executive summary", ManuscriptExecutiveSummary, 0.3),
    "quality_review": ("quality review", ManuscriptQualityReview, 0.3),
    "methodology_review": ("methodology review", ManuscriptMethodologyReview, 0.3),
    # improvement_suggestions uses 0.4 — generative ideation benefits from higher diversity
    "improvement_suggestions": ("improvement suggestions", ManuscriptImprovementSuggestions, 0.4),
}


def _make_review_fn(review_type: str) -> Callable[[LLMClient, str, str, float], tuple[str, ReviewMetrics]]:
    """Return a named review function bound to a specific review_type from _REVIEW_REGISTRY.

    The factory sets ``__name__`` / ``__qualname__`` on the generated function so that
    stack traces, profiling, and introspection show the concrete review name rather than
    the generic ``_review_fn``. This is the main reason to prefer the factory over a plain
    dispatch dict (``dict[str, Callable]``), which cannot set the function name.
    """
    review_name, template_class, default_temp = _REVIEW_REGISTRY[review_type]

    def _review_fn(
        client: LLMClient,
        text: str,
        model_name: str = "",
        temperature: float = default_temp,
    ) -> tuple[str, ReviewMetrics]:
        return generate_review_with_metrics(
            client=client,
            text=text,
            review_type=review_type,
            review_name=review_name,
            template_class=template_class,
            model_name=model_name,
            temperature=temperature,
            max_tokens=None,
        )

    _review_fn.__name__ = f"generate_{review_type}"
    _review_fn.__qualname__ = f"generate_{review_type}"
    return _review_fn





# Named public API entry points — generated from _REVIEW_REGISTRY to eliminate duplication.
# Each function binds a specific review_type, template_class, and default temperature.
generate_llm_executive_summary = _make_review_fn("executive_summary")
generate_quality_review = _make_review_fn("quality_review")
generate_methodology_review = _make_review_fn("methodology_review")
generate_improvement_suggestions = _make_review_fn("improvement_suggestions")
