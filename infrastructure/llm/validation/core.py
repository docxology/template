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

from __future__ import annotations

import json
import re
from typing import Any

from infrastructure.core.exceptions import ValidationError
from infrastructure.core.logging_utils import get_logger
from infrastructure.llm.core.config import ResponseMode

# Import from split modules
from infrastructure.llm.validation.repetition import deduplicate_sections, detect_repetition

logger = get_logger(__name__)


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
            context={"error": str(e), "content": content[:100]},
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


def validate_structure(content: dict[str, Any], schema: dict[str, Any]) -> bool:
    """Validate structured response against schema."""
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


def validate_formatting(content: str) -> bool:
    """Validate basic formatting quality."""
    issues = []

    # Check for excessive punctuation
    if "!!!" in content or "???" in content:
        issues.append("Excessive punctuation detected")

    # Check for common typos/issues
    if "  " in content:
        issues.append("Double spaces detected")

    if issues:
        logger.warning(f"Formatting issues: {', '.join(issues)}")
        return False

    return True


def validate_complete(
    content: str, mode: ResponseMode | str = "standard", schema: dict[str, Any] | None = None
) -> bool:
    """Validate LLM response content based on the response mode.

    Args:
        content: Response text to validate.
        mode: Expected response mode — short, long, structured, standard, or raw.
        schema: Required when mode is ``structured``; ignored otherwise.

    Returns:
        True when the content meets the mode's requirements.

    Raises:
        ValidationError: If content is empty, or if mode is ``structured`` and
            *schema* is None.
    """
    if not content or not content.strip():
        raise ValidationError("Empty response")

    # Basic formatting check — result is used for standard/raw modes below
    formatting_ok = validate_formatting(content)
    if not formatting_ok:
        logger.warning("Response has formatting issues")

    # Mode-specific validation
    if mode in (ResponseMode.SHORT, "short"):
        return validate_short_response(content)
    elif mode in (ResponseMode.LONG, "long"):
        return validate_long_response(content)
    elif mode in (ResponseMode.STRUCTURED, "structured"):
        if schema is None:
            raise ValidationError("Structured mode requires a schema")
        data = validate_json(content)
        return validate_structure(data, schema)

    # Standard / raw / unknown: non-empty content passes; formatting issues are warnings only
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
            f"Excessive repetition detected: {repetition_ratio:.1%} repeated "
            f"(max allowed: {max_allowed_ratio:.1%})"
        )

    return is_valid, details


def clean_repetitive_output(
    content: str,
    max_repetitions: int = 2,
) -> str:
    """Clean repetitive content from LLM output."""
    # Use balanced mode with lower content preservation threshold
    # since the purpose of this function is to aggressively clean repetition
    return deduplicate_sections(
        content, max_repetitions, mode="balanced", min_content_preservation=0.3
    )


__all__ = [
    "validate_json",
    "validate_length",
    "estimate_tokens",
    "validate_short_response",
    "validate_long_response",
    "validate_structure",
    "validate_citations",
    "validate_formatting",
    "validate_complete",
    "validate_no_repetition",
    "clean_repetitive_output",
]
