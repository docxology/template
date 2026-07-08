"""Output validation for LLM responses.

Provides comprehensive validation including:
- JSON validation and parsing
- Length and structure validation
- Citation extraction
- Formatting quality checks
- Repetition detection for LLM output loops

Error contract:
- Schema-level validators (validate_json, validate_structure) raise ValidationError
  on failure because callers cannot recover from invalid structure.
- Signal validators (validate_length, validate_short_response, validate_long_response,
  validate_formatting) return bool so callers can choose to warn, log, or retry.
- validate_complete raises ValidationError for structural problems (empty, bad schema)
  and returns bool for format/length problems.
"""

import json
import re
from typing import Any, Literal

from infrastructure.core.exceptions import ValidationError
from infrastructure.core.logging.utils import get_logger
from infrastructure.llm.core.config import ResponseMode
from infrastructure.llm.core.log_preview import preview_for_log

# Import from split modules
from infrastructure.llm.validation.repetition import deduplicate_sections, detect_repetition

logger = get_logger(__name__)

_PLACEHOLDER_RE = re.compile(
    r"(?:\{\{[^{}]+\}\}|<<[^<>]+>>|\[(?:insert|placeholder|todo|tbd)[^\]]*\]|\[citation needed\]|__+[A-Z0-9_\- ]+__+|\b(?:todo|tbd|placeholder)\b)",
    re.IGNORECASE,
)
_PLACEHOLDER_LINE_RE = re.compile(r"(?im)^\s*(?:todo|tbd|insert placeholder|placeholder)\b.*$")
_DOUBLE_BLANK_RE = re.compile(r"\n{3,}")


def validate_json(content: str) -> Any:
    """Validate and parse JSON output."""
    try:
        # Try to find JSON block if wrapped in markdown
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        return json.loads(content.strip())
    except json.JSONDecodeError as e:
        raise ValidationError(
            "LLM output is not valid JSON",
            context={
                "error": str(e),
                "content_len": len(content),
                "content_preview": preview_for_log(content, 48),
            },
        ) from e


def validate_length(content: str, min_len: int = 0, max_len: int | None = None) -> bool:
    """Validate output length.

    Returns True if within bounds, False if too short or too long.
    """
    length = len(content)
    if length < min_len:
        logger.warning(f"Output too short ({length} < {min_len})")
        return False
    if max_len and length > max_len:
        logger.warning(f"Output too long ({length} > {max_len})")
        return False
    return True


def estimate_tokens(content: str) -> int:
    """Estimate token count (simple heuristic: 1 token ≈ 4 chars)."""
    return len(content) // 4


def validate_short_response(content: str, max_tokens: int = 150) -> bool:
    """Validate short response format (< 150 tokens)."""
    tokens = estimate_tokens(content)
    if tokens > max_tokens:
        logger.warning(f"Short response exceeds limit: {tokens} > {max_tokens} tokens")
        return False
    return True


def validate_long_response(content: str, min_tokens: int = 500) -> bool:
    """Validate long response format (> 500 tokens)."""
    tokens = estimate_tokens(content)
    if tokens < min_tokens:
        logger.warning(f"Long response below minimum: {tokens} < {min_tokens} tokens")
        return False
    return True


def validate_structure(content: dict[str, Any], schema: dict[str, Any]) -> Literal[True]:
    """Validate structured response against schema.

    Returns True on success. Raises ValidationError on failure (never returns False).
    """
    required_keys = schema.get("required", [])
    properties = schema.get("properties", {})

    # Check required fields
    for key in required_keys:
        if key not in content:
            raise ValidationError(
                f"Missing required field in structure: {key}",
                context={
                    "required": required_keys,
                    "present": list(content.keys()),
                },
            )

    # Type validation (basic)
    for key, value in content.items():
        if key in properties:
            expected_type = properties[key].get("type")
            if expected_type and not _check_type(value, expected_type):
                raise ValidationError(
                    f"Field '{key}' has wrong type",
                    context={
                        "field": key,
                        "expected": expected_type,
                        "got": type(value).__name__,
                    },
                )

    return True


def _check_type(value: Any, expected_type: str) -> bool:
    """Check if value matches expected type."""
    type_map = {
        "string": str,
        "number": (int, float),
        "integer": int,
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    expected = type_map.get(expected_type)
    if expected is None:
        return True
    return isinstance(value, expected)


def validate_citations(content: str) -> list[str]:
    """Extract and validate citations in content."""
    # Look for common citation patterns
    patterns = [
        r"\(([A-Z][a-z]+(?:\s+&\s+[A-Z][a-z]+)*\s+\d{4})\)",  # (Author Year)
        r"\[(\d+)\]",  # [1]
        r"@(\w+)",  # @key
    ]

    citations = []
    for pattern in patterns:
        citations.extend(re.findall(pattern, content))

    return citations


def strip_placeholder_tokens(content: str) -> str:
    """Remove placeholder tokens from text."""
    content = _PLACEHOLDER_RE.sub("", content)
    content = _PLACEHOLDER_LINE_RE.sub("", content)
    return content


def normalize_output_whitespace(content: str) -> str:
    """Normalize whitespace in agent output."""
    lines = [line.rstrip() for line in content.splitlines()]
    text = "\n".join(lines)
    text = _DOUBLE_BLANK_RE.sub("\n\n", text)
    return text.strip()


def citation_density(content: str) -> float:
    """Return the citation density of a text."""
    words = max(len(content.split()), 1)
    return len(validate_citations(content)) * 1000.0 / words


def validate_citation_density(
    content: str,
    min_per_1000_words: float = 0.0,
    max_per_1000_words: float | None = None,
) -> tuple[bool, dict[str, Any]]:
    """Validate that citation density meets thresholds."""
    density = citation_density(content)
    details = {
        "citation_density_per_1000_words": density,
        "min_per_1000_words": min_per_1000_words,
        "max_per_1000_words": max_per_1000_words,
        "citations_found": len(validate_citations(content)),
    }
    if density < min_per_1000_words:
        logger.warning(
            "Citation density too low: %.2f < %.2f per 1000 words",
            density,
            min_per_1000_words,
        )
        return False, details
    if max_per_1000_words is not None and density > max_per_1000_words:
        logger.warning(
            "Citation density too high: %.2f > %.2f per 1000 words",
            density,
            max_per_1000_words,
        )
        return False, details
    return True, details


def clean_agent_output(
    content: str,
    *,
    max_repetitions: int = 2,
) -> str:
    """Clean and normalize LLM agent output."""
    cleaned = strip_placeholder_tokens(content)
    cleaned = clean_repetitive_output(cleaned, max_repetitions=max_repetitions)
    cleaned = normalize_output_whitespace(cleaned)
    return cleaned


def validate_formatting(content: str) -> bool:
    """Validate basic formatting quality of LLM output.

    Uses intentionally lightweight heuristics (not full linguistic analysis):
    - ``!!!`` / ``???`` catches LLM over-emphasis artifacts common in low-quality responses.
    - Double spaces catches copy-paste or template interpolation artifacts.
    These are advisory signals (caller logs a warning); they do not block the pipeline.
    """
    issues = []

    # Check for excessive punctuation (common LLM artifact in low-quality responses)
    if "!!!" in content or "???" in content:
        issues.append("Excessive punctuation detected")

    # Check for common typos/issues
    if "  " in content:
        issues.append("Double spaces detected")
    if _PLACEHOLDER_RE.search(content) or _PLACEHOLDER_LINE_RE.search(content):
        issues.append("Placeholder tokens detected")

    if issues:
        logger.warning(f"Formatting issues: {', '.join(issues)}")
        return False

    return True


def validate_complete(
    content: str, mode: ResponseMode = ResponseMode.STANDARD, schema: dict[str, Any] | None = None
) -> bool:  # True or raises for STRUCTURED/RAW/STANDARD; True or False for SHORT/LONG
    """Validate LLM response content based on the response mode.

    Args:
        content: Response text to validate.
        mode: Expected response mode — SHORT, LONG, STRUCTURED, STANDARD, or RAW.
        schema: Required when mode is ``STRUCTURED``; ignored otherwise.

    Returns:
        ``True`` when content passes validation.
        ``False`` only when ``mode`` is ``SHORT`` or ``LONG`` and content fails
        the length/format check — callers should not test the return value
        against ``False`` for other modes.
        Standard and raw modes always return ``True`` (formatting issues are
        logged as warnings, not failures).
        Structured mode always returns ``True`` or raises ``ValidationError``
        — it never returns ``False``.

    Raises:
        ValidationError: If content is empty, if mode is ``STRUCTURED`` and
            *schema* is None, or if structured content fails schema validation.
    """
    if not content or not content.strip():
        raise ValidationError("Empty response")

    # Mode-specific validation. ResponseMode(str, Enum) so == matches both enum
    # members and plain string equivalents for callers that pass string literals.
    if mode == ResponseMode.SHORT:
        return validate_short_response(content)
    elif mode == ResponseMode.LONG:
        return validate_long_response(content)
    elif mode == ResponseMode.STRUCTURED:
        if schema is None:
            raise ValidationError("Structured mode requires a schema")
        data = validate_json(content)
        return validate_structure(data, schema)
    elif mode == ResponseMode.RAW:
        # Raw mode is unvalidated — skip all formatting checks
        return True
    elif mode != ResponseMode.STANDARD:
        logger.warning(
            "Unknown response mode %r; treating as standard for validation",
            mode,
        )
        mode = ResponseMode.STANDARD

    # Standard mode: formatting issues are advisory only
    formatting_ok = validate_formatting(content)
    if not formatting_ok:
        logger.warning("Response has formatting issues")
    return True


def validate_no_repetition(
    content: str,
    max_allowed_ratio: float = 0.3,
) -> tuple[bool, dict[str, Any]]:
    """Validate that response doesn't contain excessive repetition."""
    has_repetition, duplicates, unique_ratio = detect_repetition(content)

    details = {
        "has_repetition": has_repetition,
        "unique_ratio": unique_ratio,
        "duplicates_found": len(duplicates),
        "duplicate_samples": duplicates[:3],  # First 3 examples
    }

    # Calculate repetition ratio
    repetition_ratio = 1.0 - unique_ratio
    is_valid = repetition_ratio <= max_allowed_ratio

    if not is_valid:
        logger.warning(
            f"Excessive repetition detected: {repetition_ratio:.1%} repeated (max allowed: {max_allowed_ratio:.1%})"
        )

    return is_valid, details


def clean_repetitive_output(
    content: str,
    max_repetitions: int = 2,
) -> str:
    """Clean repetitive content from LLM output."""
    # Use balanced mode with lower content preservation threshold
    # since the purpose of this function is to aggressively clean repetition
    return deduplicate_sections(content, max_repetitions, mode="balanced", min_content_preservation=0.3)


__all__ = [
    "validate_json",
    "validate_length",
    "estimate_tokens",
    "validate_short_response",
    "validate_long_response",
    "validate_structure",
    "validate_citations",
    "strip_placeholder_tokens",
    "normalize_output_whitespace",
    "citation_density",
    "validate_citation_density",
    "clean_agent_output",
    "validate_formatting",
    "validate_complete",
    "validate_no_repetition",
    "clean_repetitive_output",
]
