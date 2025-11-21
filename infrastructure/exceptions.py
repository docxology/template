"""Custom exception hierarchy for the Research Project Template.

This module defines a hierarchical exception structure for consistent error handling
across all template components. All exceptions inherit from a base TemplateError class
for easy catching and handling.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Sequence


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
        context: Optional[dict[str, Any]] = None
    ) -> None:
        """Initialize template error with message and optional context.
        
        Args:
            message: Human-readable error description
            context: Additional information about the error (file paths, line numbers, etc.)
        """
        self.message = message
        self.context = context or {}
        
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
    """Raised when configuration is invalid or missing.
    
    This includes errors in:
    - YAML configuration files
    - Environment variables
    - Command-line arguments
    - Project structure
    
    Example:
        >>> raise ConfigurationError(
        ...     "Invalid YAML syntax in config file",
        ...     context={"file": "config.yaml", "line": 10}
        ... )
    """
    pass


class MissingConfigurationError(ConfigurationError):
    """Raised when required configuration is missing.
    
    Example:
        >>> raise MissingConfigurationError(
        ...     "Required configuration key 'author' not found",
        ...     context={"file": "config.yaml"}
        ... )
    """
    pass


class InvalidConfigurationError(ConfigurationError):
    """Raised when configuration values are invalid.
    
    Example:
        >>> raise InvalidConfigurationError(
        ...     "Invalid email format",
        ...     context={"field": "author_email", "value": "invalid-email"}
        ... )
    """
    pass


# =============================================================================
# VALIDATION ERRORS
# =============================================================================

class ValidationError(TemplateError):
    """Raised when validation fails.
    
    This includes errors in:
    - Markdown validation
    - PDF validation
    - Data validation
    - Output verification
    
    Example:
        >>> raise ValidationError(
        ...     "Unresolved figure reference",
        ...     context={"reference": "fig:results", "file": "results.md"}
        ... )
    """
    pass


class MarkdownValidationError(ValidationError):
    """Raised when markdown validation fails.
    
    Example:
        >>> raise MarkdownValidationError(
        ...     "Image file not found",
        ...     context={"image": "figure.png", "referenced_in": "intro.md", "line": 42}
        ... )
    """
    pass


class PDFValidationError(ValidationError):
    """Raised when PDF validation fails.
    
    Example:
        >>> raise PDFValidationError(
        ...     "Unresolved references found in PDF",
        ...     context={"pdf": "manuscript.pdf", "unresolved_count": 3}
        ... )
    """
    pass


class DataValidationError(ValidationError):
    """Raised when data validation fails.
    
    Example:
        >>> raise DataValidationError(
        ...     "Data contains NaN values",
        ...     context={"column": "temperature", "count": 5}
        ... )
    """
    pass


# =============================================================================
# BUILD ERRORS
# =============================================================================

class BuildError(TemplateError):
    """Raised when build process fails.
    
    This includes errors in:
    - PDF generation
    - LaTeX compilation
    - Script execution
    - Pipeline orchestration
    
    Example:
        >>> raise BuildError(
        ...     "LaTeX compilation failed",
        ...     context={"file": "manuscript.tex", "exit_code": 1}
        ... )
    """
    pass


class CompilationError(BuildError):
    """Raised when compilation (LaTeX, etc.) fails.
    
    Example:
        >>> raise CompilationError(
        ...     "xelatex exited with error",
        ...     context={"file": "manuscript.tex", "exit_code": 1, "log": "compile.log"}
        ... )
    """
    pass


class ScriptExecutionError(BuildError):
    """Raised when script execution fails.
    
    Example:
        >>> raise ScriptExecutionError(
        ...     "Analysis script failed",
        ...     context={"script": "analysis_pipeline.py", "exit_code": 1}
        ... )
    """
    pass


class PipelineError(BuildError):
    """Raised when pipeline orchestration fails.
    
    Example:
        >>> raise PipelineError(
        ...     "Stage 2 failed",
        ...     context={"stage": "02_run_analysis", "failed_scripts": ["script1.py"]}
        ... )
    """
    pass


# =============================================================================
# FILE/IO ERRORS
# =============================================================================

class FileOperationError(TemplateError):
    """Raised when file operations fail.
    
    This includes errors in:
    - File reading/writing
    - Directory operations
    - Path resolution
    - Permission issues
    
    Example:
        >>> raise FileOperationError(
        ...     "Failed to write output file",
        ...     context={"file": "output.pdf", "reason": "Permission denied"}
        ... )
    """
    pass


class FileNotFoundError(FileOperationError):
    """Raised when a required file is not found.
    
    Note: This shadows Python's built-in FileNotFoundError, but provides
    better context for template-specific file errors.
    
    Example:
        >>> raise FileNotFoundError(
        ...     "Manuscript file not found",
        ...     context={"file": "manuscript.md", "searched_in": "/path/to/project"}
        ... )
    """
    pass


class InvalidFileFormatError(FileOperationError):
    """Raised when file format is invalid or unexpected.
    
    Example:
        >>> raise InvalidFileFormatError(
        ...     "Expected PDF file, got text file",
        ...     context={"file": "output.pdf", "detected_type": "text/plain"}
        ... )
    """
    pass


# =============================================================================
# DEPENDENCY ERRORS
# =============================================================================

class DependencyError(TemplateError):
    """Raised when dependencies are missing or invalid.
    
    This includes errors in:
    - Missing Python packages
    - Missing system tools (pandoc, xelatex)
    - Version mismatches
    - Environment setup
    
    Example:
        >>> raise DependencyError(
        ...     "Required tool not found",
        ...     context={"tool": "pandoc", "install_cmd": "apt-get install pandoc"}
        ... )
    """
    pass


class MissingDependencyError(DependencyError):
    """Raised when a required dependency is missing.
    
    Example:
        >>> raise MissingDependencyError(
        ...     "pandoc not found in PATH",
        ...     context={"dependency": "pandoc", "min_version": "3.1.9"}
        ... )
    """
    pass


class VersionMismatchError(DependencyError):
    """Raised when dependency version is incompatible.
    
    Example:
        >>> raise VersionMismatchError(
        ...     "pandoc version too old",
        ...     context={"dependency": "pandoc", "found": "2.5", "required": ">=3.1.9"}
        ... )
    """
    pass


# =============================================================================
# TEST ERRORS
# =============================================================================

class TestError(TemplateError):
    """Raised when test execution or validation fails.
    
    This includes errors in:
    - Test execution
    - Coverage validation
    - Test configuration
    - Test data setup
    
    Example:
        >>> raise TestError(
        ...     "Test coverage below threshold",
        ...     context={"coverage": 85, "required": 100, "module": "data_processing"}
        ... )
    """
    pass


class InsufficientCoverageError(TestError):
    """Raised when test coverage is insufficient.
    
    Example:
        >>> raise InsufficientCoverageError(
        ...     "Coverage below required threshold",
        ...     context={"actual": 85.5, "required": 100.0, "missing_lines": [10, 15, 20]}
        ... )
    """
    pass


# =============================================================================
# INTEGRATION ERRORS
# =============================================================================

class IntegrationError(TemplateError):
    """Raised when component integration fails.
    
    This includes errors in:
    - Cross-module communication
    - API mismatches
    - Data format incompatibilities
    - Protocol violations
    
    Example:
        >>> raise IntegrationError(
        ...     "Script failed to import from src/",
        ...     context={"script": "analysis.py", "module": "data_generator"}
        ... )
    """
    pass


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def raise_with_context(
    exception_class: type[TemplateError],
    message: str,
    **context: Any
) -> None:
    """Raise an exception with context information.
    
    This is a convenience function for raising exceptions with keyword arguments
    as context.
    
    Args:
        exception_class: Exception class to raise
        message: Error message
        **context: Context information as keyword arguments
        
    Raises:
        exception_class: The specified exception with context
        
    Example:
        >>> raise_with_context(
        ...     ValidationError,
        ...     "Validation failed",
        ...     file="data.csv",
        ...     line=10,
        ...     column="temperature"
        ... )
    """
    raise exception_class(message, context=context)


def format_file_context(file_path: Path | str, line: Optional[int] = None) -> dict[str, Any]:
    """Format file path and optional line number as error context.
    
    Args:
        file_path: Path to file
        line: Optional line number
        
    Returns:
        Context dictionary with file and line information
        
    Example:
        >>> context = format_file_context("data.csv", line=10)
        >>> context
        {'file': 'data.csv', 'line': 10}
    """
    context: dict[str, Any] = {"file": str(file_path)}
    if line is not None:
        context["line"] = line
    return context


def chain_exceptions(
    new_exception: TemplateError,
    original: Exception
) -> TemplateError:
    """Chain a new exception with the original exception's context.
    
    This preserves the original exception while wrapping it in a more
    specific template exception.
    
    Args:
        new_exception: New exception to raise
        original: Original exception that was caught
        
    Returns:
        New exception with chained context
        
    Example:
        >>> try:
        ...     risky_operation()
        ... except ValueError as e:
        ...     raise chain_exceptions(
        ...         ValidationError("Invalid value"),
        ...         e
        ...     )
    """
    # Add original exception info to context
    if not new_exception.context:
        new_exception.context = {}
    new_exception.context["original_error"] = str(original)
    new_exception.context["original_type"] = type(original).__name__
    
    # Use exception chaining
    new_exception.__cause__ = original
    return new_exception

