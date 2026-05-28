"""Infrastructure availability probe for analysis modules."""

from __future__ import annotations

import logging

INFRASTRUCTURE_AVAILABLE = False

try:
    from infrastructure.core import ProgressBar, SystemHealthChecker, get_logger
    from infrastructure.core.exceptions import ScriptExecutionError, TemplateError, ValidationError
    from infrastructure.scientific import benchmark_function, check_numerical_stability
    from infrastructure.validation import verify_output_integrity

    INFRASTRUCTURE_AVAILABLE = True
except ImportError as e:
    _fallback_logger = logging.getLogger("template_code_project.optimization_analysis")
    if not _fallback_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        _fallback_logger.addHandler(handler)
        _fallback_logger.setLevel(logging.INFO)
    _fallback_logger.warning("Infrastructure modules not available: %s", e)
    ProgressBar = None  # type: ignore[misc, assignment]
    SystemHealthChecker = None  # type: ignore[misc, assignment]
    get_logger = None  # type: ignore[assignment]
    ScriptExecutionError = Exception  # type: ignore[misc, assignment]
    TemplateError = Exception  # type: ignore[misc, assignment]
    ValidationError = Exception  # type: ignore[misc, assignment]
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
