"""Performance monitoring and resource tracking utilities.

This module provides utilities for tracking resource usage (CPU, memory),
performance metrics, and bottleneck identification during pipeline execution.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""
from __future__ import annotations

import os
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from infrastructure.core.logging_utils import get_logger, format_duration

logger = get_logger(__name__)


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
            'cpu_percent': self.cpu_percent,
            'memory_mb': self.memory_mb,
            'peak_memory_mb': self.peak_memory_mb,
            'io_read_mb': self.io_read_mb,
            'io_write_mb': self.io_write_mb,
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
            'duration': self.duration,
            'resource_usage': self.resource_usage.to_dict(),
            'operations_count': self.operations_count,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
        }


class PerformanceMonitor:
    """Monitor performance metrics for operations."""
    
    def __init__(self):
        """Initialize performance monitor."""
        self.start_time: Optional[float] = None
        self.start_memory: Optional[float] = None
        self.peak_memory: float = 0.0
        self.operations_count: int = 0
        self.cache_hits: int = 0
        self.cache_misses: int = 0
    
    def start(self) -> None:
        """Start monitoring."""
        self.start_time = time.time()
        self.start_memory = self._get_memory_usage()
        self.peak_memory = self.start_memory
        self.operations_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
    
    def stop(self) -> PerformanceMetrics:
        """Stop monitoring and return metrics.
        
        Returns:
            PerformanceMetrics with collected data
        """
        if self.start_time is None:
            raise RuntimeError("Monitor not started")
        
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
        """Record an operation."""
        self.operations_count += 1
    
    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        self.cache_hits += 1
    
    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        self.cache_misses += 1
    
    def update_memory(self) -> None:
        """Update peak memory tracking."""
        current = self._get_memory_usage()
        if current > self.peak_memory:
            self.peak_memory = current
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB.
        
        Returns:
            Memory usage in megabytes
        """
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except ImportError:
            # Fallback if psutil not available
            return 0.0
        except Exception:
            return 0.0
    
    def _get_cpu_percent(self) -> float:
        """Get CPU usage percentage.
        
        Returns:
            CPU usage percentage (0-100)
        """
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.cpu_percent(interval=0.1)
        except ImportError:
            return 0.0
        except Exception:
            return 0.0


@contextmanager
def monitor_performance(operation_name: str = "Operation"):
    """Context manager for monitoring operation performance.
    
    Args:
        operation_name: Name of the operation being monitored
        
    Yields:
        PerformanceMonitor instance
        
    Example:
        >>> with monitor_performance("Data processing") as monitor:
        ...     process_data()
        ...     monitor.record_operation()
        ... metrics = monitor.stop()
        >>> print(f"Duration: {metrics.duration:.2f}s")
    """
    monitor = PerformanceMonitor()
    monitor.start()
    
    try:
        yield monitor
    finally:
        metrics = monitor.stop()
        logger.debug(
            f"{operation_name}: {format_duration(metrics.duration)}, "
            f"Memory: {metrics.resource_usage.memory_mb:.1f}MB, "
            f"Peak: {metrics.resource_usage.peak_memory_mb:.1f}MB"
        )


def get_system_resources() -> dict[str, Any]:
    """Get current system resource information.
    
    Returns:
        Dictionary with system resource information
    """
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_percent': cpu_percent,
            'memory_total_gb': memory.total / 1024 / 1024 / 1024,
            'memory_available_gb': memory.available / 1024 / 1024 / 1024,
            'memory_percent': memory.percent,
            'disk_total_gb': disk.total / 1024 / 1024 / 1024,
            'disk_free_gb': disk.free / 1024 / 1024 / 1024,
            'disk_percent': (disk.used / disk.total) * 100,
        }
    except ImportError:
        logger.warning("psutil not available - resource tracking disabled")
        return {}
    except Exception as e:
        logger.warning(f"Failed to get system resources: {e}")
        return {}


