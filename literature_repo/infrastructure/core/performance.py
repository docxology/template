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
        
        # Get process-specific resources
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info()
        
        return {
            'cpu_percent': cpu_percent,
            'memory_total_gb': memory.total / 1024 / 1024 / 1024,
            'memory_available_gb': memory.available / 1024 / 1024 / 1024,
            'memory_percent': memory.percent,
            'process_memory_mb': process_memory.rss / 1024 / 1024,
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


class StagePerformanceTracker:
    """Track performance metrics for pipeline stages."""
    
    def __init__(self):
        """Initialize stage performance tracker."""
        self.stages: list[dict[str, Any]] = []
        self.start_time: Optional[float] = None
    
    def start_stage(self, stage_name: str) -> None:
        """Start tracking a stage.
        
        Args:
            stage_name: Name of the stage
        """
        self.start_time = time.time()
        try:
            import psutil
            process = psutil.Process(os.getpid())
            self.start_memory = process.memory_info().rss / 1024 / 1024  # MB
            self.start_io = process.io_counters()
        except (ImportError, AttributeError):
            self.start_memory = 0.0
            self.start_io = None
    
    def end_stage(self, stage_name: str, exit_code: int) -> dict[str, Any]:
        """End tracking a stage and return metrics.
        
        Args:
            stage_name: Name of the stage
            exit_code: Exit code from the stage
            
        Returns:
            Dictionary with stage performance metrics
        """
        if self.start_time is None:
            return {}
        
        duration = time.time() - self.start_time
        
        metrics = {
            'stage_name': stage_name,
            'duration': duration,
            'exit_code': exit_code,
            'memory_mb': 0.0,
            'peak_memory_mb': 0.0,
            'cpu_percent': 0.0,
            'io_read_mb': 0.0,
            'io_write_mb': 0.0,
        }
        
        try:
            import psutil
            process = psutil.Process(os.getpid())
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            metrics['memory_mb'] = current_memory
            metrics['peak_memory_mb'] = current_memory  # Simplified - could track peak during stage
            metrics['cpu_percent'] = process.cpu_percent(interval=0.1)
            
            if self.start_io:
                current_io = process.io_counters()
                metrics['io_read_mb'] = (current_io.read_bytes - self.start_io.read_bytes) / 1024 / 1024
                metrics['io_write_mb'] = (current_io.write_bytes - self.start_io.write_bytes) / 1024 / 1024
        except (ImportError, AttributeError):
            pass
        
        self.stages.append(metrics)
        self.start_time = None
        
        return metrics
    
    def get_performance_warnings(self) -> list[dict[str, Any]]:
        """Get performance warnings for stages.
        
        Returns:
            List of warning dictionaries
        """
        warnings = []
        
        if not self.stages:
            return warnings
        
        # Calculate average duration
        durations = [s['duration'] for s in self.stages]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Check for unusually slow stages (> 2x average)
        for stage in self.stages:
            if stage['duration'] > avg_duration * 2 and avg_duration > 0:
                warnings.append({
                    'type': 'slow_stage',
                    'stage': stage['stage_name'],
                    'duration': stage['duration'],
                    'average': avg_duration,
                    'message': f"Stage {stage['stage_name']} took {format_duration(stage['duration'])} (2x average)",
                    'suggestion': 'Consider optimizing this stage or running it in parallel',
                })
        
        # Check for high memory usage (> 1GB)
        for stage in self.stages:
            if stage.get('peak_memory_mb', 0) > 1024:
                warnings.append({
                    'type': 'high_memory',
                    'stage': stage['stage_name'],
                    'memory_mb': stage['peak_memory_mb'],
                    'message': f"Stage {stage['stage_name']} used {stage['peak_memory_mb']:.0f} MB memory",
                    'suggestion': 'Consider memory optimization or increasing available memory',
                })
        
        # Check for high CPU usage (> 90%)
        for stage in self.stages:
            if stage.get('cpu_percent', 0) > 90:
                warnings.append({
                    'type': 'high_cpu',
                    'stage': stage['stage_name'],
                    'cpu_percent': stage['cpu_percent'],
                    'message': f"Stage {stage['stage_name']} used {stage['cpu_percent']:.1f}% CPU",
                    'suggestion': 'Consider parallelization or CPU optimization',
                })
        
        return warnings
    
    def get_summary(self) -> dict[str, Any]:
        """Get performance summary.
        
        Returns:
            Dictionary with performance summary
        """
        if not self.stages:
            return {}
        
        durations = [s['duration'] for s in self.stages]
        total_duration = sum(durations)
        
        return {
            'total_stages': len(self.stages),
            'total_duration': total_duration,
            'average_duration': total_duration / len(self.stages) if self.stages else 0,
            'slowest_stage': max(self.stages, key=lambda s: s['duration']) if self.stages else None,
            'fastest_stage': min(self.stages, key=lambda s: s['duration']) if self.stages else None,
            'total_memory_mb': sum(s.get('memory_mb', 0) for s in self.stages),
            'peak_memory_mb': max((s.get('peak_memory_mb', 0) for s in self.stages), default=0),
            'warnings': self.get_performance_warnings(),
        }


