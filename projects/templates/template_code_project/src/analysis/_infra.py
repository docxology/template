"""Infrastructure availability probe for analysis modules."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

INFRASTRUCTURE_AVAILABLE = False
_INFRASTRUCTURE_OVERRIDE: ContextVar[bool | None] = ContextVar("template_code_infrastructure_available", default=None)
ScriptExecutionError: type[Exception]
TemplateError: type[Exception]
ValidationError: type[Exception]

try:
    from infrastructure.core import ProgressBar, SystemHealthChecker, get_logger, log_success
    from infrastructure.core.exceptions import (
        ScriptExecutionError as _ScriptExecutionError,
        TemplateError as _TemplateError,
        ValidationError as _ValidationError,
    )
    from infrastructure.documentation.figure_manager import FigureManager
    from infrastructure.documentation.glossary_gen import build_api_index, generate_markdown_table
    from infrastructure.publishing import generate_citation_apa, generate_citation_bibtex, generate_citation_mla
    from infrastructure.publishing.models import PublicationMetadata
    from infrastructure.reporting.interactive_dashboard import InteractiveDashboard, Invariant, Panel
    from infrastructure.scientific import benchmark_function, check_numerical_stability
    from infrastructure.validation import verify_output_integrity

    ScriptExecutionError = _ScriptExecutionError
    TemplateError = _TemplateError
    ValidationError = _ValidationError
    INFRASTRUCTURE_AVAILABLE = True
except ImportError as e:  # pragma: no cover — fallback when infrastructure is unavailable
    _fallback_logger = logging.getLogger("template_code_project.optimization_analysis")
    if not _fallback_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        _fallback_logger.addHandler(handler)
        _fallback_logger.setLevel(logging.INFO)
    _fallback_logger.warning("Infrastructure modules not available: %s", e)

    class _FallbackScriptExecutionError(Exception):
        """Fallback script execution error when infrastructure is unavailable."""

    class _FallbackTemplateError(Exception):
        """Fallback template error when infrastructure is unavailable."""

    class _FallbackValidationError(Exception):
        """Fallback validation error when infrastructure is unavailable."""

    ScriptExecutionError = _FallbackScriptExecutionError
    TemplateError = _FallbackTemplateError
    ValidationError = _FallbackValidationError
    ProgressBar = None
    SystemHealthChecker = None
    get_logger = None
    benchmark_function = None  # type: ignore[assignment]
    check_numerical_stability = None  # type: ignore[assignment]
    verify_output_integrity = None  # type: ignore[assignment]
    FigureManager = None  # type: ignore[misc, assignment]
    build_api_index = None  # type: ignore[assignment]
    generate_markdown_table = None  # type: ignore[assignment]
    generate_citation_apa = None  # type: ignore[assignment]
    generate_citation_bibtex = None  # type: ignore[assignment]
    generate_citation_mla = None  # type: ignore[assignment]
    PublicationMetadata = None  # type: ignore[misc, assignment]
    InteractiveDashboard = None  # type: ignore[misc, assignment]
    Invariant = None  # type: ignore[misc, assignment]
    Panel = None  # type: ignore[misc, assignment]
    log_success = None


def infrastructure_available() -> bool:
    """Return whether infrastructure modules are available, honoring any context-local override."""
    override = _INFRASTRUCTURE_OVERRIDE.get()
    return INFRASTRUCTURE_AVAILABLE if override is None else override


@contextmanager
def infrastructure_context(available: bool) -> Iterator[None]:
    """Context manager that temporarily overrides infrastructure availability.

    Args:
        available: The override value to set within the context block.

    Yields:
        None while the override is active; restores the previous value on exit.
    """
    token = _INFRASTRUCTURE_OVERRIDE.set(available)
    try:
        yield
    finally:
        _INFRASTRUCTURE_OVERRIDE.reset(token)


__all__ = [
    "INFRASTRUCTURE_AVAILABLE",
    "FigureManager",
    "InteractiveDashboard",
    "Invariant",
    "Panel",
    "ProgressBar",
    "PublicationMetadata",
    "ScriptExecutionError",
    "SystemHealthChecker",
    "TemplateError",
    "ValidationError",
    "benchmark_function",
    "build_api_index",
    "check_numerical_stability",
    "generate_citation_apa",
    "generate_citation_bibtex",
    "generate_citation_mla",
    "generate_markdown_table",
    "get_logger",
    "log_success",
    "verify_output_integrity",
    "infrastructure_available",
    "infrastructure_context",
]
