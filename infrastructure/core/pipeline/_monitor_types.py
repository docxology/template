"""Data types for stage-level performance monitoring.

Provides ResourceUsage, PerformanceMetrics, and StageMetricsDict used
by PerformanceMonitor and StagePerformanceTracker.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypedDict


class StageMetricsDict(TypedDict, total=False):
    """Typed dict for per-stage performance metrics collected by StagePerformanceTracker."""

    stage_name: str
    duration: float
    exit_code: int
    memory_mb: float
    cpu_percent: float
    io_read_mb: float
    io_write_mb: float


# Performance warning thresholds
SLOW_STAGE_MULTIPLIER = 2  # warn when a stage takes > N x the pipeline average
HIGH_MEMORY_MB = 1024  # warn when a stage RSS exceeds 1 GB
HIGH_CPU_PERCENT = 90.0  # warn when CPU usage exceeds this percentage


@dataclass
class ResourceUsage:
    """Resource usage metrics for a stage or operation."""

    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    peak_memory_mb: float = 0.0
    io_read_mb: float = 0.0
    io_write_mb: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "peak_memory_mb": self.peak_memory_mb,
            "io_read_mb": self.io_read_mb,
            "io_write_mb": self.io_write_mb,
        }


@dataclass
class PerformanceMetrics:
    """Performance metrics for a stage or operation."""

    duration: float
    resource_usage: ResourceUsage = field(default_factory=ResourceUsage)
    operations_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "duration": self.duration,
            "resource_usage": self.resource_usage.to_dict(),
            "operations_count": self.operations_count,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
        }
