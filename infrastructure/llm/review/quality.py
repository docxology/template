"""Review quality validation for manuscript review responses.

Validates LLM review output for quality, formatting, and section completeness
across different review types (executive summary, quality, methodology,
improvement suggestions, translation).
"""

from __future__ import annotations

import re
from typing import Any, Callable, Literal, TypedDict

from infrastructure.core.logging.utils import get_logger
from infrastructure.llm.templates.manuscript import REVIEW_MIN_WORDS
from infrastructure.llm.validation.repetition import detect_repetition
from infrastructure.llm.validation.format import is_off_topic, check_format_compliance

logger = get_logger(__name__)

_SMALL_MODEL_SUFFIXES = frozenset(["3b", "4b", "7b", "8b"])


def _is_small_model(model_name: str) -> bool:
    """Return True if model_name indicates a small parameter-count model."""
    lower = model_name.lower()
    return any(s in lower for s in _SMALL_MODEL_SUFFIXES)


ReviewType = Literal[
    "executive_summary",
    "quality_review",
    "methodology_review",
    "improvement_suggestions",
    "translation",
]


class ReviewQualityDetails(TypedDict, total=False):
    """Known shape of the details dict returned by validate_review_quality."""

    sections_found: list[str]
    scores_found: list[str]
    format_compliance: dict[str, Any]
    repetition: dict[str, Any]
    repetition_warning: str
    format_warnings: list[str]
    word_count: int
    min_required: int
    sections_required: int
    has_assessment: bool


def validate_review_quality(
    response: str,
    review_type: ReviewType,
    min_words: int | None = None,
    model_name: str = "",
) -> tuple[bool, list[str], ReviewQualityDetails]:
    """Validate the quality and formatting of an LLM review response."""
    issues = []
    details: ReviewQualityDetails = {
        "sections_found": [],
        "scores_found": [],
        "format_compliance": {},
        "repetition": {},
    }
    response_lower = response.lower()

    if is_off_topic(response):
        issues.append("Response appears off-topic or confused")
        return False, issues, details

    has_repetition, duplicates, unique_ratio = detect_repetition(response)
    details["repetition"] = {
        "has_repetition": has_repetition,
        "unique_ratio": unique_ratio,
        "duplicates_found": len(duplicates),
    }

    if unique_ratio < 0.5:
        issues.append(f"Excessive repetition detected: {unique_ratio:.0%} unique content")
        return False, issues, details
    elif has_repetition:
        details["repetition_warning"] = (
            f"Some repeated content detected ({len(duplicates)} duplicates)"
        )
        logger.debug(f"Repetition warning: {unique_ratio:.0%} unique content")

    is_format_compliant, format_issues, format_details = check_format_compliance(response)
    details["format_compliance"] = format_details

    if not is_format_compliant:
        details["format_warnings"] = format_issues

    default_min = REVIEW_MIN_WORDS.get(review_type, 200)
    if _is_small_model(model_name):
        default_min = int(default_min * 0.8)
    min_word_count = min_words or default_min

    word_count = len(response.split())
    details["word_count"] = word_count
    details["min_required"] = min_word_count

    tolerance = max(1, int(min_word_count * 0.05))
    effective_min = min_word_count - tolerance

    if word_count < effective_min:
        issues.append(
            f"Too short: {word_count} words (minimum: {min_word_count}, effective: {effective_min} with tolerance)"  # noqa: E501
        )

    validator = _REVIEW_TYPE_VALIDATORS.get(review_type)
    if validator:
        validator(response_lower, details, issues)

    is_valid = len(issues) == 0
    return is_valid, issues, details


def _validate_executive_summary_section(
    response_lower: str, details: dict[str, Any], issues: list[str]
) -> None:
    header_variations = [
        (["overview", "summary", "introduction", "abstract"], "overview"),
        (
            ["key contributions", "contributions", "main findings", "key findings", "highlights"],
            "contributions",
        ),
        (["methodology", "methods", "approach", "method", "techniques"], "methodology"),
        (["results", "findings", "principal results", "outcomes", "key results"], "results"),
        (["significance", "impact", "implications", "importance", "takeaway"], "significance"),
    ]
    found_sections = [
        name
        for variations, name in header_variations
        if any(v in response_lower for v in variations)
    ]
    details["sections_found"] = found_sections
    details["sections_required"] = 1
    if not found_sections:
        issues.append("Missing expected structure (found: none of 5 expected sections)")


def _validate_quality_review_section(
    response_lower: str, details: dict[str, Any], issues: list[str]
) -> None:
    score_patterns = [
        (r"\*\*score:\s*(\d)/5\*\*", "**Score: X/5**"),
        (r"score:\s*(\d)/5", "Score: X/5"),
        (r"\*\*(\d)/5\*\*", "**X/5**"),
        (r"score\s*:\s*(\d)", "Score: X"),
        (r"rating\s*:\s*(\d)", "Rating: X"),
        (r"\[(\d)/5\]", "[X/5]"),
        (r"(\d)\s*out\s*of\s*5", "X out of 5"),
        (r"(\d)/5", "X/5"),
    ]
    scores_found = [
        (m, name) for pattern, name in score_patterns for m in re.findall(pattern, response_lower)
    ]
    details["scores_found"] = scores_found
    has_assessment = any(
        kw in response_lower
        for kw in ("clarity", "structure", "readability", "technical accuracy", "overall quality")
    )
    details["has_assessment"] = has_assessment
    if not scores_found and not has_assessment:
        issues.append("Missing scoring or quality assessment")


def _validate_methodology_review_section(
    response_lower: str, details: dict[str, Any], issues: list[str]
) -> None:
    methodology_sections = [
        (["strengths", "strong points", "advantages", "positives", "pros"], "strengths"),
        (
            ["weaknesses", "limitations", "concerns", "issues", "weak points", "cons", "gaps"],
            "weaknesses",
        ),
        (["suggestions", "recommendations", "improvements", "future work"], "recommendations"),
    ]
    found_sections = [
        name
        for variations, name in methodology_sections
        if any(v in response_lower for v in variations)
    ]
    details["sections_found"] = found_sections
    has_methodology_content = any(
        kw in response_lower
        for kw in ("research design", "methodology", "approach", "methods", "experimental")
    )
    details["has_methodology_content"] = has_methodology_content
    if not found_sections and not has_methodology_content:
        issues.append(f"Missing expected sections (found: {found_sections or 'none'})")


def _validate_improvement_suggestions_section(
    response_lower: str, details: dict[str, Any], issues: list[str]
) -> None:
    priority_variations = [
        (["high priority", "critical", "urgent", "must fix", "immediate", "major"], "high"),
        (["medium priority", "moderate", "should address", "important", "significant"], "medium"),
        (["low priority", "minor", "nice to have", "optional", "consider", "cosmetic"], "low"),
    ]
    found_priorities = [
        name
        for variations, name in priority_variations
        if any(v in response_lower for v in variations)
    ]
    details["priorities_found"] = found_priorities
    has_recommendations = any(
        kw in response_lower for kw in ("recommendation", "suggest", "improve", "fix", "address")
    )
    details["has_recommendations"] = has_recommendations
    if not found_priorities and not has_recommendations:
        issues.append("Missing priority sections or recommendations")


def _validate_translation_section(
    response_lower: str, details: dict[str, Any], issues: list[str]
) -> None:
    has_english = (
        "english abstract" in response_lower
        or "## english" in response_lower
        or ("abstract" in response_lower and "english" in response_lower)
    )
    details["has_english_section"] = has_english
    has_translation = any(
        kw in response_lower
        for kw in ("translation", "chinese", "hindi", "russian", "中文", "हिंदी", "русский")
    )
    details["has_translation_section"] = has_translation
    if not has_english:
        issues.append("Missing English abstract section")
    if not has_translation:
        issues.append("Missing translation section")


# Module-level dispatch table — built once after all validators are defined.
_ValidatorFn = Callable[[str, dict[str, Any], list[str]], None]
_REVIEW_TYPE_VALIDATORS: dict[str, _ValidatorFn] = {
    "executive_summary": _validate_executive_summary_section,
    "quality_review": _validate_quality_review_section,
    "methodology_review": _validate_methodology_review_section,
    "improvement_suggestions": _validate_improvement_suggestions_section,
    "translation": _validate_translation_section,
}
