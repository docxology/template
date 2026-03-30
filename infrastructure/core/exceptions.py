"""Raiseable exception hierarchy for the Research Project Template.

All exceptions inherit from TemplateError for easy broad catching.

Boundary rule:
  exceptions.py → raiseable exception classes (raise and catch)
  errors.py     → log message constants (format and print, never raise)

Implementation split:
  _exceptions_core.py    — TemplateError base + config/validation/build/file/dep/test/integration
  _exceptions_domains.py — literature/LLM/security/rendering/publishing exceptions
  exceptions.py          — utility functions + backwards-compat re-exports

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Re-export core exceptions
from infrastructure.core._exceptions_core import (  # noqa: F401
    BuildError,
    CompilationError,
    ConfigurationError,
    DataValidationError,
    DependencyError,
    FileNotFoundError,
    FileOperationError,
    InsufficientCoverageError,
    IntegrationError,
    InvalidConfigurationError,
    InvalidFileFormatError,
    MarkdownValidationError,
    MissingConfigurationError,
    MissingDependencyError,
    NotADirectoryError,
    PDFValidationError,
    PipelineError,
    ScriptExecutionError,
    TemplateError,
    TestError,
    ValidationError,
    VersionMismatchError,
)

# Re-export domain exceptions
from infrastructure.core._exceptions_domains import (  # noqa: F401
    APIRateLimitError,
    ContextLimitError,
    FormatError,
    InvalidQueryError,
    LiteratureSearchError,
    LLMConnectionError,
    LLMError,
    LLMTemplateError,
    MetadataError,
    PublishingError,
    RenderingError,
    SecurityError,
    SecurityViolation,
    TemplateRenderingError,
    UploadError,
)


# UTILITY FUNCTIONS
# =============================================================================


def raise_with_context(exception_class: type[TemplateError], message: str, **context: Any) -> None:
    """Raise exception_class(message) with the given keyword arguments as context."""
    raise exception_class(message, context=context)


def format_file_context(file_path: Path | str, line: int | None = None) -> dict[str, Any]:
    """Return a context dict with 'file' and optionally 'line' keys."""
    context: dict[str, Any] = {"file": str(file_path)}
    if line is not None:
        context["line"] = line
    return context


def chain_exceptions(new_exception: TemplateError, original: Exception) -> TemplateError:
    """Set new_exception.__cause__ = original, store original info in context, and return it."""
    # Add original exception info to context
    if not new_exception.context:
        new_exception.context = {}
    new_exception.context["original_error"] = str(original)
    new_exception.context["original_type"] = type(original).__name__

    # Use exception chaining
    new_exception.__cause__ = original
    return new_exception
