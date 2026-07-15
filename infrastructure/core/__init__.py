"""Lightweight compatibility exports for core infrastructure utilities.

New code should import leaf modules directly.  Package-level conveniences are
resolved lazily so importing an unrelated leaf such as ``pipeline.types`` does
not initialize performance or scientific dependencies.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_EXPORTS: dict[str, tuple[str, str]] = {
    "CheckpointManager": ("infrastructure.core.runtime.checkpoint", "CheckpointManager"),
    "SystemHealthChecker": ("infrastructure.core.runtime.health_check", "SystemHealthChecker"),
    "format_duration": ("infrastructure.core.logging.helpers", "format_duration"),
    "get_logger": ("infrastructure.core.logging.utils", "get_logger"),
    "log_operation": ("infrastructure.core.logging.utils", "log_operation"),
    "log_stage": ("infrastructure.core.logging.utils", "log_stage"),
    "log_success": ("infrastructure.core.logging.utils", "log_success"),
    "monitor_performance": ("infrastructure.core.runtime.function_profiler", "monitor_performance"),
    "ProgressBar": ("infrastructure.core.progress", "ProgressBar"),
    "TemplateError": ("infrastructure.core.exceptions", "TemplateError"),
}

__all__ = sorted(_EXPORTS)


def __getattr__(name: str) -> Any:
    """Resolve a legacy package-level export on first access."""
    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(name) from exc
    value = getattr(import_module(module_name), attribute)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Expose lazy compatibility names during introspection."""
    return sorted((*globals(), *__all__))
