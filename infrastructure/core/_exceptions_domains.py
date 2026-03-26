"""Domain-specific exception classes: literature, LLM, security, rendering, publishing.

Extracted from exceptions.py for single-responsibility. Import via exceptions.py
for backwards compatibility.
"""

from __future__ import annotations

from infrastructure.core._exceptions_core import TemplateError


# LITERATURE SEARCH ERRORS
# =============================================================================


class LiteratureSearchError(TemplateError):
    """Raised when literature search operations fail."""

    pass


class APIRateLimitError(LiteratureSearchError):
    """Raised when API rate limits are exceeded."""

    pass


class InvalidQueryError(LiteratureSearchError):
    """Raised when search query is invalid."""

    pass


# LLM ERRORS
# =============================================================================


class LLMError(TemplateError):
    """Base exception for LLM operations."""

    pass


class LLMConnectionError(LLMError):
    """Raised when connecting to LLM provider fails."""

    pass


class LLMTemplateError(LLMError):
    """Raised when template processing fails."""

    pass


class ContextLimitError(LLMError):
    """Raised when token limit is exceeded."""

    pass


# SECURITY ERRORS
# =============================================================================


class SecurityViolation(TemplateError):
    """Raised when a security constraint is violated."""

    pass


class SecurityError(SecurityViolation):
    """Security violation in LLM input sanitization.

    Subclass of SecurityViolation kept for backwards compatibility with call
    sites that catch SecurityError specifically. Prefer catching SecurityViolation
    at higher layers.
    """

    pass


# RENDERING ERRORS
# =============================================================================


class RenderingError(TemplateError):
    """Base exception for rendering operations."""

    pass


class FormatError(RenderingError):
    """Raised when output format is invalid or unsupported."""

    pass


class TemplateRenderingError(RenderingError):
    """Raised when rendering a template fails."""

    pass


# PUBLISHING ERRORS
# =============================================================================


class PublishingError(TemplateError):
    """Base exception for publishing operations."""

    pass


class UploadError(PublishingError):
    """Raised when file upload fails."""

    pass


class MetadataError(PublishingError):
    """Raised when metadata validation fails."""

    pass
