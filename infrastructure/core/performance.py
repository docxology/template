"""Backward-compatible re-export shim for the performance sub-modules.

The two sub-domains have been split into dedicated modules:
  infrastructure/core/stage_monitor.py     — psutil-based pipeline stage monitoring
  infrastructure/core/function_profiler.py — cProfile/tracemalloc function profiling

Import from those modules directly for new code. This shim exists so that
existing ``from infrastructure.core.performance import ...`` call sites
continue to work without modification.
"""

from __future__ import annotations

from infrastructure.core.function_profiler import (
    CodeProfiler,
    ProfilingMetrics,
    get_performance_monitor,
    monitor_performance,
    profile_memory_usage,
)
from infrastructure.core.stage_monitor import (
    PerformanceMetrics,
    PerformanceMonitor,
    ResourceUsage,
    StagePerformanceTracker,
    get_system_resources,
    performance_context,
)

__all__ = [
    # stage_monitor
    "ResourceUsage",
    "PerformanceMetrics",
    "PerformanceMonitor",
    "StagePerformanceTracker",
    "performance_context",
    "get_system_resources",
    # function_profiler
    "ProfilingMetrics",
    "CodeProfiler",
    "get_performance_monitor",
    "monitor_performance",
    "profile_memory_usage",
]
