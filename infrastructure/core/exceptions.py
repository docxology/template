"""Raiseable exception hierarchy for the Research Project Template.

All exceptions inherit from TemplateError for easy broad catching.

Boundary rule:
  exceptions.py → raiseable exception classes (raise and catch)
  errors.py     → log message constants (format and print, never raise)

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

import builtins
from pathlib import Path
from typing import Any

# =============================================================================
# BASE EXCEPTION
# =============================================================================

class TemplateError(Exception):
    """Base exception for all template-related errors.

    All custom exceptions in the template inherit from this class, allowing
    code to catch all template-specific errors with a single except clause.

    Attributes:
        message: Human-readable error description
        context: Additional context about the error
        suggestions: List of actionable recovery suggestions
        recovery_commands: List of command-line commands to fix the issue

    Example:
        >>> try:
        ...     raise TemplateError("Something went wrong", context={"file": "data.csv"})
        ... except TemplateError as e:
        ...     print(f"Error: {e.message}")
        ...     print(f"Context: {e.context}")
    """

    def __init__(
        self,
        message: str,
        context: dict[str, Any | None] = None,
        suggestions: list[str | None] = None,
        recovery_commands: list[str | None] = None,
    ) -> None:
        """Initialize template error with message, optional context, recovery suggestions, and commands.

        Args:
            message: Human-readable error description
            context: Additional information about the error (file paths, line numbers, etc.)
            suggestions: List of actionable recovery suggestions
            recovery_commands: List of command-line commands to fix the issue
        """
        self.message = message
        self.context = context or {}
        self.suggestions = suggestions or []
        self.recovery_commands = recovery_commands or []

        # Build full message with context
        full_message = message
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            full_message = f"{message} ({context_str})"

        super().__init__(full_message)

# =============================================================================
# CONFIGURATION ERRORS
# =============================================================================

class ConfigurationError(TemplateError):
    """Raised when configuration is invalid or missing."""

    pass

class MissingConfigurationError(ConfigurationError):
    """Raised when required configuration is missing."""

    pass

class InvalidConfigurationError(ConfigurationError):
    """Raised when configuration values are invalid."""

    pass

# =============================================================================
# VALIDATION ERRORS
# =============================================================================

class ValidationError(TemplateError):
    """Raised when validation fails."""

    pass

class MarkdownValidationError(ValidationError):
    """Raised when markdown validation fails."""

    pass

class PDFValidationError(ValidationError):
    """Raised when PDF validation fails."""

    pass

class DataValidationError(ValidationError):
    """Raised when data validation fails."""

    pass

# =============================================================================
# BUILD ERRORS
# =============================================================================

class BuildError(TemplateError):
    """Raised when build process fails."""

    pass

class CompilationError(BuildError):
    """Raised when compilation (LaTeX, etc.) fails."""

    pass

class ScriptExecutionError(BuildError):
    """Raised when script execution fails."""

    pass

class PipelineError(BuildError):
    """Raised when pipeline orchestration fails."""

    pass

# =============================================================================
# FILE/IO ERRORS
# =============================================================================

class FileOperationError(TemplateError):
    """Raised when file operations fail."""

    pass

class FileNotFoundError(FileOperationError, builtins.FileNotFoundError):
    """Raised when a required file is not found.

    Inherits from both custom FileOperationError and built-in FileNotFoundError
    for compatibility with standard Python exception handling while providing
    better context for template-specific file errors.

    Automatically generates recovery commands based on file path.

    Example:
        >>> raise FileNotFoundError(
        ...     "Manuscript file not found",
        ...     context={"file": "manuscript.md", "searched_in": "/path/to/project"}
        ... )
    """

    def __init__(
        self,
        message: str,
        context: dict[str, Any | None] = None,
        suggestions: list[str | None] = None,
        recovery_commands: list[str | None] = None,
    ) -> None:
        context = context or {}
        file_path = context.get("file", "")

        # Auto-generate suggestions if not provided
        if suggestions is None:
            suggestions = [
                f"Verify the file exists: {file_path}",
                "Check the file path is correct",
                "Ensure you're running from the correct directory",
            ]
            if "searched_in" in context:
                suggestions.append(f"File should be in: {context['searched_in']}")

        # Auto-generate recovery commands if not provided
        if recovery_commands is None and file_path:
            recovery_commands = [
                f"ls -la {file_path}",
                f"find . -name '{Path(file_path).name}'",
            ]
            if "searched_in" in context:
                recovery_commands.append(f"ls -la {context['searched_in']}")

        super().__init__(message, context, suggestions, recovery_commands)

class NotADirectoryError(FileOperationError, builtins.NotADirectoryError):
    """Raised when a path is not a directory when a directory is expected."""

class InvalidFileFormatError(FileOperationError):
    """Raised when file format is invalid or unexpected."""

    pass

# =============================================================================
# DEPENDENCY ERRORS
# =============================================================================

class DependencyError(TemplateError):
    """Raised when dependencies are missing or invalid."""

    pass

class MissingDependencyError(DependencyError):
    """Raised when a required dependency is missing.

    Automatically generates installation commands based on dependency name.

    Example:
        >>> raise MissingDependencyError(
        ...     "pandoc not found in PATH",
        ...     context={"dependency": "pandoc", "min_version": "3.1.9"}
        ... )
    """

    def __init__(
        self,
        message: str,
        context: dict[str, Any | None] = None,
        suggestions: list[str | None] = None,
        recovery_commands: list[str | None] = None,
    ) -> None:
        context = context or {}
        dependency = context.get("dependency", "")

        # Auto-generate suggestions if not provided
        if suggestions is None:
            suggestions = [
                f"Install {dependency} using your system's package manager",
                f"Verify {dependency} is in your PATH",
            ]
            if "min_version" in context:
                suggestions.append(f"Ensure version >= {context['min_version']}")

        # Auto-generate installation commands based on common package managers
        if recovery_commands is None and dependency:
            from infrastructure.core.environment import build_install_commands
            recovery_commands = build_install_commands(dependency)

        super().__init__(message, context, suggestions, recovery_commands)

class VersionMismatchError(DependencyError):
    """Raised when dependency version is incompatible."""

    pass

# =============================================================================
# TEST ERRORS
# =============================================================================

class TestError(TemplateError):
    """Raised when test execution or validation fails."""

    pass

class InsufficientCoverageError(TestError):
    """Raised when test coverage is insufficient."""

    pass

# =============================================================================
# INTEGRATION ERRORS
# =============================================================================

class IntegrationError(TemplateError):
    """Raised when component integration fails."""

    pass

# =============================================================================
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

# =============================================================================
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

# =============================================================================
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

# =============================================================================
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

# =============================================================================
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
