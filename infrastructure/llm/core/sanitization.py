"""Input sanitization and security utilities for LLM operations.

Validates and sanitizes LLM prompts before generation: strips dangerous
patterns, normalizes whitespace, and enforces length limits. Called by
LLMClient before each outbound request.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

# SecurityError is a subclass of SecurityViolation (see infrastructure/core/exceptions.py).
# Both names are valid here; SecurityError is used for backwards compatibility with
# call sites that catch SecurityError specifically.
from infrastructure.core.exceptions import SecurityError
from infrastructure.core.logging_utils import get_logger
from infrastructure.core.security import get_security_validator

logger = get_logger(__name__)

class InputSanitizer:
    """Comprehensive input sanitization for LLM operations."""

    # LLM-specific patterns extending the core SecurityValidator patterns.
    _LLM_EXTRA_PATTERNS: tuple[str, ...] = (
        # Dangerous LaTeX commands — \{ anchors prevent matching \readability etc.
        r"\\input\s*\{|\\include\s*\{|\\usepackage\s*[\[{]|\\newcommand\s*\{",
        r"\\write\s*\d|\\read\s*\d|\\openout\s*\d|\\openin\s*\d",
    )

    def __init__(self) -> None:
        # Delegate core pattern detection to the shared SecurityValidator; add LLM-specific patterns.
        core_patterns = get_security_validator().dangerous_patterns
        self.dangerous_patterns = core_patterns + list(self._LLM_EXTRA_PATTERNS)

    def sanitize_prompt(self, prompt: str, context: dict[str, Any] | None = None) -> str:
        """Sanitize LLM prompt for security.

        Args:
            prompt: Raw prompt text
            context: Additional context for validation

        Returns:
            Sanitized prompt text

        Raises:
            SecurityError: If prompt contains dangerous content
        """
        if not isinstance(prompt, str):
            raise SecurityError("Prompt must be a string")

        # Remove null bytes and other control characters
        prompt = self._remove_control_characters(prompt)

        # Check for dangerous patterns
        self._check_dangerous_patterns(prompt)

        # Sanitize HTML entities
        prompt = self._escape_html_entities(prompt)

        # Remove excessive whitespace
        prompt = self._normalize_whitespace(prompt)

        # Limit prompt length
        prompt = self._limit_length(prompt)

        logger.debug(f"Sanitized prompt: {len(prompt)} characters")
        return prompt

    def validate_file_input(
        self, file_path: Path, allowed_extensions: list[str] | None = None
    ) -> None:
        """Validate file input for security.

        Args:
            file_path: Path to file
            allowed_extensions: List of allowed file extensions

        Raises:
            SecurityError: If file input is unsafe
        """
        # LLM-provided paths must be relative: absolute paths from untrusted input
        # risk referencing arbitrary system locations (e.g. /etc/passwd).
        # Note: SecurityValidator.validate_file_path() allows absolute paths because
        # it validates infrastructure-owned paths (output dirs, config files) which
        # are trusted and always absolute. These are different threat models.
        if file_path.is_absolute():
            raise SecurityError("Absolute paths not allowed in LLM input")

        # Resolve path to prevent traversal attacks
        try:
            resolved = file_path.resolve()
        except (OSError, RuntimeError) as e:
            raise SecurityError("Invalid file path") from e

        # Check for directory traversal attempts
        if ".." in str(file_path) or not resolved.exists():
            raise SecurityError("Invalid file path")

        # Check file extension
        if allowed_extensions:
            if resolved.suffix.lower() not in [ext.lower() for ext in allowed_extensions]:
                raise SecurityError(f"File extension not allowed: {resolved.suffix}")

        # Check file size (prevent DoS)
        max_size = 50 * 1024 * 1024  # 50MB limit
        file_stat = resolved.stat()
        if file_stat.st_size > max_size:
            raise SecurityError(f"File too large: {file_stat.st_size} bytes")


    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file operations.

        Args:
            filename: Raw filename

        Returns:
            Sanitized filename safe for file operations
        """
        if not filename or not isinstance(filename, str):
            raise SecurityError("Invalid filename")

        # Remove path separators
        filename = re.sub(r"[\/\\]", "_", filename)

        # Remove dangerous characters
        filename = re.sub(r'[<>:"|?*]', "_", filename)

        # Remove control characters
        filename = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", filename)

        # Limit length
        filename = filename[:255]

        # Ensure not empty after sanitization
        if not filename.strip():
            filename = "unnamed_file"

        return filename

    def _remove_control_characters(self, text: str) -> str:
        """Remove control characters from text."""
        # Remove null bytes and other dangerous control characters
        # Keep newlines, tabs, and spaces
        return re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]", "", text)

    def _check_dangerous_patterns(self, text: str) -> None:
        """Check for dangerous patterns in text."""
        for pattern in self.dangerous_patterns:
            if re.search(pattern, text):  # patterns use inline (?i) flags; re.IGNORECASE is redundant
                logger.warning(f"Dangerous pattern detected: {pattern}")
                raise SecurityError("Dangerous content detected in input")

    def _escape_html_entities(self, text: str) -> str:
        """Escape HTML entities for safety."""
        return html.escape(text, quote=True)

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize excessive whitespace."""
        # Replace multiple spaces with single space
        text = re.sub(r" +", " ", text)
        # Replace multiple newlines with double newline
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        return text.strip()

    def _limit_length(self, text: str, max_length: int = 100000) -> str:
        """Limit text length to prevent resource exhaustion."""
        if len(text) > max_length:
            logger.warning(f"Text truncated from {len(text)} to {max_length} characters")
            return text[:max_length] + "...[truncated]"
        return text

# SecurityError is defined in infrastructure.core.exceptions and imported above.
# Global instance (lazy initialization — avoids import-time side effects)
_input_sanitizer: InputSanitizer | None = None

def get_input_sanitizer() -> InputSanitizer:
    """Get the global input sanitizer instance."""
    global _input_sanitizer
    if _input_sanitizer is None:
        _input_sanitizer = InputSanitizer()
    return _input_sanitizer

def sanitize_llm_input(prompt: str) -> str:
    """Convenience function for LLM input sanitization."""
    return get_input_sanitizer().sanitize_prompt(prompt)
