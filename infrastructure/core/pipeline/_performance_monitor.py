"""PerformanceMonitor and related utilities for tracking resource usage.

Provides the PerformanceMonitor class, performance_context context manager,
and get_system_resources helper.
"""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from typing import Any, Iterator

from infrastructure.core._optional_deps import psutil
from infrastructure.core.exceptions import BuildError
from infrastructure.core.logging.helpers import format_duration
from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pipeline._monitor_types import (
    PerformanceMetrics,
    ResourceUsage,
)

logger = get_logger(__name__)


class PerformanceMonitor:
    """Resource-usage monitor tracking timing, memory, and operation counts."""

    def __init__(self):
        """Initialize performance monitor."""
        self.start_time: float | None = None
        self.start_memory: float | None = None
        self.peak_memory: float = 0.0
        self.operations_count: int = 0
        self.cache_hits: int = 0
        self.cache_misses: int = 0
        self.last_metrics: PerformanceMetrics | None = None

    def start(self) -> None:
        """Start a monitoring session."""
        self.start_time = time.time()
        self.start_memory = self._get_memory_usage()
        self.peak_memory = self.start_memory
        self.operations_count = 0
        self.cache_hits = 0
        self.cache_misses = 0

    def stop(self) -> PerformanceMetrics:
        """Stop monitoring and return metrics.

        Raises:
            BuildError: If stop() is called before start().
        """
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
        """Record a single operation execution."""
        self.operations_count += 1

    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        self.cache_hits += 1

    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        self.cache_misses += 1

    def update_memory(self) -> None:
        """Update peak memory usage."""
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
def performance_context(operation_name: str = "Operation") -> Iterator[PerformanceMonitor]:
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
