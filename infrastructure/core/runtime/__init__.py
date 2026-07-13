"""Lazy compatibility exports for runtime infrastructure."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_EXPORTS = {
    "CheckpointManager": ("infrastructure.core.runtime.checkpoint", "CheckpointManager"),
    "StageResult": ("infrastructure.core.runtime.checkpoint", "StageResult"),
    "check_python_version": ("infrastructure.core.runtime.environment", "check_python_version"),
    "get_python_command": ("infrastructure.core.runtime.environment", "get_python_command"),
    "get_subprocess_env": ("infrastructure.core.runtime.environment", "get_subprocess_env"),
    "setup_directories": ("infrastructure.core.runtime.environment", "setup_directories"),
    "ETAEstimate": ("infrastructure.core.runtime.eta", "ETAEstimate"),
    "calculate_eta": ("infrastructure.core.runtime.eta", "calculate_eta"),
    "CodeProfiler": ("infrastructure.core.runtime.function_profiler", "CodeProfiler"),
    "ProfilingMetrics": ("infrastructure.core.runtime.function_profiler", "ProfilingMetrics"),
    "monitor_performance": ("infrastructure.core.runtime.function_profiler", "monitor_performance"),
    "SystemHealthChecker": ("infrastructure.core.runtime.health_check", "SystemHealthChecker"),
    "retry_with_backoff": ("infrastructure.core.runtime.retry", "retry_with_backoff"),
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
