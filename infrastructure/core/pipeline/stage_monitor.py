"""Stage-level performance monitoring (psutil-based, pipeline-level).

Provides PerformanceMonitor, StagePerformanceTracker, and related utilities
for tracking timing, memory, and CPU across pipeline stages.

Part of the infrastructure layer (Layer 1) - reusable across all projects.

Implementation split across submodules:
    _monitor_types          - Data types (ResourceUsage, PerformanceMetrics, StageMetricsDict)
    _performance_monitor    - PerformanceMonitor, performance_context, get_system_resources
    _stage_tracker          - StagePerformanceTracker
"""

from __future__ import annotations

from infrastructure.core.pipeline._monitor_types import (
    PerformanceMetrics,
    ResourceUsage,
    StageMetricsDict,
)
from infrastructure.core.pipeline._performance_monitor import (
    PerformanceMonitor,
    get_system_resources,
    performance_context,
)
from infrastructure.core.pipeline._stage_tracker import StagePerformanceTracker

__all__ = [
    "PerformanceMetrics",
    "PerformanceMonitor",
    "ResourceUsage",
    "StageMetricsDict",
    "StagePerformanceTracker",
    "get_system_resources",
    "performance_context",
]
