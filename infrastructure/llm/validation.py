"""Output validation for LLM responses."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional, Type, List

from infrastructure.core.exceptions import ValidationError
from infrastructure.core.logging_utils import get_logger

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

