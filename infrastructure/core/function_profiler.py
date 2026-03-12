"""Function-level performance profiling (cProfile/tracemalloc-based).

Provides CodeProfiler, ProfilingMetrics, and related utilities for
fine-grained function call profiling and memory tracking.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

import cProfile
import functools
import pstats
import time
import tracemalloc
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class ProfilingMetrics:
    """Container for function-level performance measurement results.

    Memory fields store raw bytes from tracemalloc. to_dict() converts to MB.
    """

    operation_name: str
    execution_time: float
    memory_peak: int | None = None  # bytes from tracemalloc
    memory_current: int | None = None  # bytes from tracemalloc
    memory_delta: int | None = None  # bytes from tracemalloc
    cpu_time: float | None = None
    function_calls: int | None = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for reporting (memory values in MB)."""

        def _bytes_to_mb(b: int | None) -> float | None:
            return b / (1024 * 1024) if b is not None else None

        return {
            "operation": self.operation_name,
            "execution_time_seconds": round(self.execution_time, 3),
            "memory_peak_mb": _bytes_to_mb(self.memory_peak),
            "memory_current_mb": _bytes_to_mb(self.memory_current),
            "memory_delta_mb": _bytes_to_mb(self.memory_delta),
            "cpu_time_seconds": self.cpu_time,
            "function_calls": self.function_calls,
            "timestamp": self.timestamp,
        }


class CodeProfiler:
    """Comprehensive performance monitoring and profiling via cProfile/tracemalloc."""

    def __init__(self):
        """Initialize empty metrics history."""
        self.metrics_history: list[ProfilingMetrics] = []

    @contextmanager
    def monitor(self, operation_name: str, track_memory: bool = True):
        """Context manager for monitoring operation performance."""
        start_time = time.time()
        cpu_start = time.process_time()

        we_started_tracing = False
        if track_memory and not tracemalloc.is_tracing():
            tracemalloc.start()
            we_started_tracing = True

        try:
            yield
        finally:
            execution_time = time.time() - start_time
            cpu_time = time.process_time() - cpu_start

            metrics = ProfilingMetrics(
                operation_name=operation_name,
                execution_time=execution_time,
                cpu_time=cpu_time,
            )

            if track_memory:
                current, peak = tracemalloc.get_traced_memory()
                if we_started_tracing:
                    tracemalloc.stop()
                metrics.memory_current = current
                metrics.memory_peak = peak

            self.metrics_history.append(metrics)

            logger.debug(
                f"Performance: {operation_name} completed in {execution_time:.3f}s "
                f"(CPU: {cpu_time:.3f}s, Peak memory: {metrics.memory_peak or 'N/A'}MB)"
            )

    def profile_function(self, func: Callable, *args, **kwargs) -> Any:
        """Profile a function execution with detailed cProfile statistics."""
        profiler = cProfile.Profile()
        profiler.enable()

        try:
            result = func(*args, **kwargs)
            return result
        finally:
            profiler.disable()
            stats = pstats.Stats(profiler)
            stats.sort_stats("cumulative")
            logger.debug(f"Profile results for {func.__name__}:")
            stats.print_stats(10)

    def benchmark_function(
        self,
        func: Callable,
        *args,
        iterations: int = 5,
        warmup_iterations: int = 2,
        **kwargs,
    ) -> dict[str, float | list[float]]:
        """Benchmark function performance over multiple iterations."""
        for _ in range(warmup_iterations):
            func(*args, **kwargs)

        execution_times = []
        for i in range(iterations):
            start_time = time.perf_counter()
            func(*args, **kwargs)
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            execution_times.append(execution_time)
            logger.debug(f"Iteration {i + 1}: {execution_time:.4f}s")

        avg_time = sum(execution_times) / len(execution_times)
        min_time = min(execution_times)
        max_time = max(execution_times)
        std_dev = (sum((t - avg_time) ** 2 for t in execution_times) / len(execution_times)) ** 0.5

        result = {
            "function_name": func.__name__,
            "iterations": iterations,
            "average_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "std_dev": std_dev,
            "all_times": execution_times,
        }

        logger.info(f"Benchmark: {func.__name__} - avg: {avg_time:.4f}s, std: {std_dev:.4f}s")
        return result

    def get_recent_metrics(self, limit: int = 10) -> list[ProfilingMetrics]:
        """Return the most recent performance metrics."""
        return self.metrics_history[-limit:]

    def clear_metrics_history(self):
        """Clear the metrics history."""
        self.metrics_history.clear()

    def generate_performance_report(self) -> str:
        """Generate a comprehensive performance report."""
        if not self.metrics_history:
            return "No performance metrics available."

        report_lines = [
            "# Performance Report",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary Statistics",
            f"- Total operations monitored: {len(self.metrics_history)}",
        ]

        total_time = sum(m.execution_time for m in self.metrics_history)
        avg_time = total_time / len(self.metrics_history)
        max_memory = max(
            (m.memory_peak for m in self.metrics_history if m.memory_peak),
            default=None,
        )

        report_lines.extend(
            [
                f"- Total execution time: {total_time:.3f}s",
                f"- Average execution time: {avg_time:.3f}s",
                f"- Peak memory usage: {max_memory or 'N/A'} MB",
                "",
                "## Recent Operations",
                "| Operation | Time (s) | Peak Memory (MB) |",
                "|-----------|----------|------------------|",
            ]
        )

        for metric in self.metrics_history[-10:]:
            report_lines.append(
                f"| {metric.operation_name} | {metric.execution_time:.3f} | {metric.memory_peak or 'N/A'} |"  # noqa: E501
            )

        return "\n".join(report_lines)


_global_monitor: CodeProfiler | None = None


def get_performance_monitor() -> CodeProfiler:
    """Return the global CodeProfiler instance, creating it on first call."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = CodeProfiler()
    return _global_monitor


def monitor_performance(operation_name: str, track_memory: bool = True):
    """Decorator for monitoring function performance via the global CodeProfiler."""

    def decorator(func):
        """Decorator function wrapping the target function."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """Inner wrapper that executes with monitoring."""
            monitor = get_performance_monitor()
            op_name = operation_name or f"{func.__module__}.{func.__qualname__}"
            with monitor.monitor(op_name, track_memory):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def profile_memory_usage(func: Callable, *args, **kwargs) -> dict[str, Any]:
    """Profile memory usage of a function via CodeProfiler."""
    monitor = get_performance_monitor()
    result = None
    with monitor.monitor(func.__name__, track_memory=True):
        result = func(*args, **kwargs)
    if not monitor.metrics_history:
        return {"execution_time": 0.0, "memory_current": 0, "memory_peak": 0, "result": result}
    metrics = monitor.metrics_history[-1]
    return {
        "execution_time": metrics.execution_time,
        "memory_current": (metrics.memory_current or 0) // (1024 * 1024),
        "memory_peak": (metrics.memory_peak or 0) // (1024 * 1024),
        "result": result,
    }
