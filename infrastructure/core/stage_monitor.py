"""Stage-level performance monitoring (psutil-based, pipeline-level).

Provides PerformanceMonitor, StagePerformanceTracker, and related utilities
for tracking timing, memory, and CPU across pipeline stages.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Optional

from infrastructure.core._optional_deps import psutil
from infrastructure.core.exceptions import BuildError
from infrastructure.core.logging_helpers import format_duration
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

# Performance warning thresholds
_SLOW_STAGE_MULTIPLIER = 2  # warn when a stage takes > N× the pipeline average
_HIGH_MEMORY_MB = 1024  # warn when a stage RSS exceeds 1 GB
_HIGH_CPU_PERCENT = 90.0  # warn when CPU usage exceeds this percentage


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


class PerformanceMonitor:
    """Resource-usage monitor tracking timing, memory, and operation counts."""

    def __init__(self):
        self.start_time: Optional[float] = None
        self.start_memory: Optional[float] = None
        self.peak_memory: float = 0.0
        self.operations_count: int = 0
        self.cache_hits: int = 0
        self.cache_misses: int = 0
        self.last_metrics: Optional[PerformanceMetrics] = None

    def start(self) -> None:
        """Start a monitoring session."""
        self.start_time = time.time()
        self.start_memory = self._get_memory_usage()
        self.peak_memory = self.start_memory
        self.operations_count = 0
        self.cache_hits = 0
        self.cache_misses = 0

    def stop(self) -> PerformanceMetrics:
        """Stop monitoring and return metrics."""
        if self.start_time is None:
            raise BuildError("Monitor not started")

        duration = time.time() - self.start_time
        current_memory = self._get_memory_usage()

        resource_usage = ResourceUsage(
            cpu_percent=self._get_cpu_percent(),
            memory_mb=current_memory,
            peak_memory_mb=self.peak_memory,
        )

        return PerformanceMetrics(
            duration=duration,
            resource_usage=resource_usage,
            operations_count=self.operations_count,
            cache_hits=self.cache_hits,
            cache_misses=self.cache_misses,
        )

    def record_operation(self) -> None:
        self.operations_count += 1

    def record_cache_hit(self) -> None:
        self.cache_hits += 1

    def record_cache_miss(self) -> None:
        self.cache_misses += 1

    def update_memory(self) -> None:
        current = self._get_memory_usage()
        if current > self.peak_memory:
            self.peak_memory = current

    def _get_memory_usage(self) -> float:
        """Return current process memory usage in MB."""
        if psutil is None:
            return 0.0
        try:
            return float(psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024)
        except (OSError, AttributeError) as e:
            logger.debug(f"Failed to get memory usage: {e}")
            return 0.0

    def _get_cpu_percent(self) -> float:
        """Return current process CPU usage percentage."""
        if psutil is None:
            return 0.0
        try:
            return float(psutil.Process(os.getpid()).cpu_percent(interval=0.1))
        except (OSError, AttributeError) as e:
            logger.debug(f"Failed to get CPU percent: {e}")
            return 0.0


@contextmanager
def performance_context(operation_name: str = "Operation"):
    """Context manager for monitoring operation performance.

    Yields the started PerformanceMonitor. After the with-block, callers
    can read monitor.last_metrics for the final PerformanceMetrics.
    """
    monitor = PerformanceMonitor()
    monitor.start()
    try:
        yield monitor
    finally:
        try:
            metrics = monitor.stop()
            monitor.last_metrics = metrics
            logger.debug(f"{operation_name}: {format_duration(metrics.duration)}")
        except BuildError as e:
            logger.debug(f"performance_context stop failed for {operation_name}: {e}")


def get_system_resources() -> dict[str, Any]:
    """Return current system resource information."""
    if psutil is None:
        return {}
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info()

        return {
            "cpu_percent": cpu_percent,
            "memory_total_gb": memory.total / 1024 / 1024 / 1024,
            "memory_available_gb": memory.available / 1024 / 1024 / 1024,
            "memory_percent": memory.percent,
            "process_memory_mb": process_memory.rss / 1024 / 1024,
            "disk_total_gb": disk.total / 1024 / 1024 / 1024,
            "disk_free_gb": disk.free / 1024 / 1024 / 1024,
            "disk_percent": (disk.used / disk.total) * 100,
        }
    except (OSError, AttributeError) as e:
        logger.warning(f"Failed to get system resources: {e}")
        return {}


class StagePerformanceTracker:
    """Track performance metrics for pipeline stages."""

    def __init__(
        self,
        slow_stage_multiplier: float = _SLOW_STAGE_MULTIPLIER,
        high_memory_mb: float = _HIGH_MEMORY_MB,
        high_cpu_percent: float = _HIGH_CPU_PERCENT,
    ):
        self.stages: list[dict[str, Any]] = []
        self.start_time: Optional[float] = None
        self.start_memory: float = 0.0
        self.start_io: Optional[Any] = None
        self._slow_stage_multiplier = slow_stage_multiplier
        self._high_memory_mb = high_memory_mb
        self._high_cpu_percent = high_cpu_percent

    def start_stage(self, stage_name: str) -> None:
        """Start tracking a stage."""
        self.start_time = time.time()
        if psutil is None:
            self.start_memory = 0.0
            self.start_io = None
            return
        try:
            process = psutil.Process(os.getpid())
            self.start_memory = process.memory_info().rss / 1024 / 1024
            self.start_io = process.io_counters()
        except AttributeError:
            self.start_memory = 0.0
            self.start_io = None

    def end_stage(self, stage_name: str, exit_code: int) -> dict[str, Any]:
        """End tracking a stage and return metrics."""
        if self.start_time is None:
            raise BuildError(f"end_stage called without start_stage for {stage_name}")

        duration = time.time() - self.start_time

        memory_mb = 0.0
        cpu_percent = 0.0
        io_read_mb = 0.0
        io_write_mb = 0.0

        if psutil is not None:
            try:
                process = psutil.Process(os.getpid())
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_mb = current_memory
                cpu_percent = process.cpu_percent(interval=0.1)
                if self.start_io:
                    current_io = process.io_counters()
                    io_read_mb = (current_io.read_bytes - self.start_io.read_bytes) / 1024 / 1024
                    io_write_mb = (
                        current_io.write_bytes - self.start_io.write_bytes
                    ) / 1024 / 1024
            except AttributeError as e:
                logger.debug(f"psutil attribute not available on this platform: {e}")

        metrics = {
            "stage_name": stage_name,
            "duration": duration,
            "exit_code": exit_code,
            "memory_mb": memory_mb,
            "cpu_percent": cpu_percent,
            "io_read_mb": io_read_mb,
            "io_write_mb": io_write_mb,
        }

        self.stages.append(metrics)
        self.start_time = None

        return metrics

    def get_performance_warnings(self) -> list[dict[str, Any]]:
        """Return performance warnings for stages."""
        warnings: list[dict[str, Any]] = []

        if not self.stages:
            return warnings

        durations = [s["duration"] for s in self.stages]
        avg_duration = sum(durations) / len(durations)

        for stage in self.stages:
            if stage["duration"] > avg_duration * self._slow_stage_multiplier and avg_duration > 0:
                warnings.append(
                    {
                        "type": "slow_stage",
                        "stage": stage["stage_name"],
                        "duration": stage["duration"],
                        "average": avg_duration,
                        "message": f"Stage {stage['stage_name']} took {format_duration(stage['duration'])} ({self._slow_stage_multiplier}x average)",  # noqa: E501
                        "suggestion": "Consider optimizing this stage or running it in parallel",
                    }
                )
            if stage.get("memory_mb", 0) > self._high_memory_mb:
                warnings.append(
                    {
                        "type": "high_memory",
                        "stage": stage["stage_name"],
                        "memory_mb": stage["memory_mb"],
                        "message": f"Stage {stage['stage_name']} used {stage['memory_mb']:.0f} MB memory",  # noqa: E501
                        "suggestion": "Consider memory optimization or increasing available memory",
                    }
                )
            if stage.get("cpu_percent", 0) > self._high_cpu_percent:
                warnings.append(
                    {
                        "type": "high_cpu",
                        "stage": stage["stage_name"],
                        "cpu_percent": stage["cpu_percent"],
                        "message": f"Stage {stage['stage_name']} used {stage['cpu_percent']:.1f}% CPU",  # noqa: E501
                        "suggestion": "Consider parallelization or CPU optimization",
                    }
                )

        return warnings

    def get_summary(self) -> dict[str, Any]:
        """Return performance summary."""
        if not self.stages:
            return {}

        durations = [s["duration"] for s in self.stages]
        total_duration = sum(durations)

        return {
            "total_stages": len(self.stages),
            "total_duration": total_duration,
            "average_duration": total_duration / len(self.stages),
            "slowest_stage": max(self.stages, key=lambda s: s["duration"]),
            "fastest_stage": min(self.stages, key=lambda s: s["duration"]),
            "total_memory_mb": sum(s.get("memory_mb", 0) for s in self.stages),
            "peak_memory_mb": max((s.get("end_memory_mb", 0) for s in self.stages), default=0),
            "warnings": self.get_performance_warnings(),
        }
