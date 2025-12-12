"""Output validation for LLM responses.

Provides comprehensive validation including:
- JSON validation and parsing
- Length and structure validation
- Citation extraction
- Formatting quality checks
- Repetition detection for LLM output loops
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from infrastructure.core.exceptions import ValidationError
from infrastructure.core.logging_utils import get_logger

# Import from split modules
from infrastructure.llm.validation.repetition import (
    detect_repetition,
    deduplicate_sections,
)
from infrastructure.llm.validation.format import (
    check_format_compliance,
    is_off_topic,
    has_on_topic_signals,
    detect_conversational_phrases,
)
from infrastructure.llm.validation.structure import (
    validate_section_completeness,
    extract_structured_sections,
    validate_response_structure,
)

logger = get_logger(__name__)


class OutputValidator:
    """Validates LLM outputs for quality and correctness."""

    @staticmethod
    def validate_json(content: str) -> Dict[str, Any]:
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
                context={"error": str(e), "content": content[:100]}
            )

    @staticmethod
    def validate_length(content: str, min_len: int = 0, max_len: Optional[int] = None) -> bool:
        """Validate output length."""
        length = len(content)
        if length < min_len:
            raise ValidationError(
                f"Output too short ({length} < {min_len})",
                context={"length": length}
            )
        if max_len and length > max_len:
            raise ValidationError(
                f"Output too long ({length} > {max_len})",
                context={"length": length}
            )
        return True

    @staticmethod
    def estimate_tokens(content: str) -> int:
        """Estimate token count (simple heuristic: 1 token ≈ 4 chars)."""
        return len(content) // 4

    @staticmethod
    def validate_short_response(content: str, max_tokens: int = 150) -> bool:
        """Validate short response format (< 150 tokens)."""
        tokens = OutputValidator.estimate_tokens(content)
        if tokens > max_tokens:
            logger.warning(
                f"Short response exceeds limit: {tokens} > {max_tokens} tokens"
            )
            return False
        return True

    @staticmethod
    def validate_long_response(content: str, min_tokens: int = 500) -> bool:
        """Validate long response format (> 500 tokens)."""
        tokens = OutputValidator.estimate_tokens(content)
        if tokens < min_tokens:
            logger.warning(
                f"Long response below minimum: {tokens} < {min_tokens} tokens"
            )
            return False
        return True

    @staticmethod
    def validate_structure(content: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Validate structured response against schema."""
        required_keys = schema.get("required", [])
        properties = schema.get("properties", {})
        
        # Check required fields
        for key in required_keys:
            if key not in content:
                raise ValidationError(
                    f"Missing required field in structure: {key}",
                    context={"required": required_keys, "present": list(content.keys())}
                )
        
        # Type validation (basic)
        for key, value in content.items():
            if key in properties:
                expected_type = properties[key].get("type")
                if expected_type and not OutputValidator._check_type(value, expected_type):
                    raise ValidationError(
                        f"Field '{key}' has wrong type",
                        context={"field": key, "expected": expected_type, "got": type(value).__name__}
                    )
        
        return True

    @staticmethod
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

    @staticmethod
    def validate_citations(content: str) -> List[str]:
        """Extract and validate citations in content."""
        # Look for common citation patterns
        patterns = [
            r'\(([A-Z][a-z]+(?:\s+&\s+[A-Z][a-z]+)*\s+\d{4})\)',  # (Author Year)
            r'\[(\d+)\]',  # [1]
            r'@(\w+)',  # @key
        ]
        
        citations = []
        for pattern in patterns:
            citations.extend(re.findall(pattern, content))
        
        return citations

    @staticmethod
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

    @staticmethod
    def validate_complete(
        content: str,
        mode: str = "standard",
        schema: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Comprehensive validation based on mode."""
        if not content or not content.strip():
            raise ValidationError("Empty response")
        
        # Basic formatting check
        if not OutputValidator.validate_formatting(content):
            logger.warning("Response has formatting issues")
        
        # Mode-specific validation
        if mode == "short":
            return OutputValidator.validate_short_response(content)
        elif mode == "long":
            return OutputValidator.validate_long_response(content)
        elif mode == "structured" and schema:
            try:
                data = OutputValidator.validate_json(content)
                return OutputValidator.validate_structure(data, schema)
            except json.JSONDecodeError as e:
                raise ValidationError(f"Invalid JSON for structured mode: {e}")
        
        return True

    @staticmethod
    def validate_no_repetition(
        content: str,
        max_allowed_ratio: float = 0.3,
    ) -> Tuple[bool, Dict[str, Any]]:
        """Validate that response doesn't contain excessive repetition.
        
        Detects when LLM output gets stuck in a loop repeating content.
        
        Args:
            content: The response text to validate
            max_allowed_ratio: Maximum ratio of repeated content (0.0-1.0)
                              0.3 means at most 30% of content can be repeated
        
        Returns:
            Tuple of (is_valid, details dict with repetition info)
        """
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

    @staticmethod
    def clean_repetitive_output(
        content: str,
        max_repetitions: int = 2,
    ) -> str:
        """Clean repetitive content from LLM output.
        
        Post-processing step to remove repeated sections/paragraphs.
        
        Args:
            content: The response text to clean
            max_repetitions: Maximum times a section can appear
            
        Returns:
            Cleaned text with repetitions removed
        """
        # Use balanced mode with lower content preservation threshold
        # since the purpose of this function is to aggressively clean repetition
        return deduplicate_sections(
            content, max_repetitions, mode="balanced", min_content_preservation=0.3
        )


# Note: Functions are imported at module level above for use in OutputValidator methods
__all__ = [
    # Core class
    'OutputValidator',
]
