"""Infrastructure availability probe for analysis modules."""

from __future__ import annotations

import logging

INFRASTRUCTURE_AVAILABLE = False
ScriptExecutionError: type[Exception]
TemplateError: type[Exception]
ValidationError: type[Exception]

try:
    from infrastructure.core import ProgressBar, SystemHealthChecker, get_logger
    from infrastructure.core.exceptions import (
        ScriptExecutionError as _ScriptExecutionError,
        TemplateError as _TemplateError,
        ValidationError as _ValidationError,
    )
    from infrastructure.scientific import benchmark_function, check_numerical_stability
    from infrastructure.validation import verify_output_integrity

    ScriptExecutionError = _ScriptExecutionError
    TemplateError = _TemplateError
    ValidationError = _ValidationError
    INFRASTRUCTURE_AVAILABLE = True
except ImportError as e:
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
    ProgressBar = None  # type: ignore[misc, assignment]
    SystemHealthChecker = None  # type: ignore[misc, assignment]
    get_logger = None  # type: ignore[assignment]
    benchmark_function = None  # type: ignore[assignment]
    check_numerical_stability = None  # type: ignore[assignment]
    verify_output_integrity = None  # type: ignore[assignment]

__all__ = [
    "INFRASTRUCTURE_AVAILABLE",
    "ProgressBar",
    "ScriptExecutionError",
    "SystemHealthChecker",
    "TemplateError",
    "ValidationError",
    "benchmark_function",
    "check_numerical_stability",
    "get_logger",
    "verify_output_integrity",
]
