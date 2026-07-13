"""Lazy compatibility exports for core logging utilities."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_EXPORTS = {
    "DiagnosticEvent": ("infrastructure.core.logging.diagnostic", "DiagnosticEvent"),
    "DiagnosticReporter": ("infrastructure.core.logging.diagnostic", "DiagnosticReporter"),
    "DiagnosticSeverity": ("infrastructure.core.logging.diagnostic", "DiagnosticSeverity"),
    "EMOJIS": ("infrastructure.core.logging.constants", "EMOJIS"),
    "get_emoji_enabled": ("infrastructure.core.logging.constants", "get_emoji_enabled"),
    "get_structured_logging_enabled": (
        "infrastructure.core.logging.constants",
        "get_structured_logging_enabled",
    ),
    "JSONFormatter": ("infrastructure.core.logging.formatters", "JSONFormatter"),
    "TemplateFormatter": ("infrastructure.core.logging.formatters", "TemplateFormatter"),
    "format_duration": ("infrastructure.core.logging.helpers", "format_duration"),
    "format_error_with_suggestions": (
        "infrastructure.core.logging.helpers",
        "format_error_with_suggestions",
    ),
    "Spinner": ("infrastructure.core.logging.progress", "Spinner"),
    "StreamingProgress": ("infrastructure.core.logging.progress", "StreamingProgress"),
    "log_progress_bar": ("infrastructure.core.logging.progress", "log_progress_bar"),
    "log_progress_streaming": ("infrastructure.core.logging.progress", "log_progress_streaming"),
    "log_stage_with_eta": ("infrastructure.core.logging.progress", "log_stage_with_eta"),
    "log_with_spinner": ("infrastructure.core.logging.progress", "log_with_spinner"),
    "get_logger": ("infrastructure.core.logging.utils", "get_logger"),
    "log_operation": ("infrastructure.core.logging.utils", "log_operation"),
    "log_stage": ("infrastructure.core.logging.utils", "log_stage"),
    "log_success": ("infrastructure.core.logging.utils", "log_success"),
    "setup_logger": ("infrastructure.core.logging.utils", "setup_logger"),
}

__all__ = sorted(_EXPORTS)


def __getattr__(name: str) -> Any:
    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(name) from exc
    value = getattr(import_module(module_name), attribute)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted((*globals(), *__all__))
