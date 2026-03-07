"""Pipeline-stage and function-level performance monitoring.

Provides:
- PerformanceMonitor: psutil-based resource snapshots (start/stop)
- StagePerformanceTracker: per-stage pipeline metrics
- performance_context: context manager wrapping PerformanceMonitor
- CodeProfiler: cProfile + tracemalloc function-level profiling
- monitor_performance: decorator for monitoring function performance
- benchmark_function: convenience function-level benchmarking
"""

from __future__ import annotations

import cProfile
import functools
import os
import pstats
import time
import tracemalloc
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

import psutil

from infrastructure.core.logging_utils import format_duration, get_logger

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
        """Return current process memory usage in MB."""
        try:
            return float(psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024)
        except Exception:
            return 0.0

    def _get_cpu_percent(self) -> float:
        """Return current process CPU usage percentage."""
        try:
            return float(psutil.Process(os.getpid()).cpu_percent(interval=0.1))
        except Exception:
            return 0.0


@contextmanager
def performance_context(operation_name: str = "Operation"):
    """Context manager for monitoring operation performance.

    Yields the PerformanceMonitor so callers can record operations.
    The context manager logs duration on exit; call monitor.stop()
    explicitly if you need the final PerformanceMetrics object.

    Example:
        >>> with performance_context("Data processing") as monitor:
        ...     process_data()
        ...     monitor.record_operation()
    """
    monitor = PerformanceMonitor()
    monitor.start()
    _start = time.time()
    try:
        yield monitor
    finally:
        _duration = time.time() - _start
        logger.debug(f"{operation_name}: {format_duration(_duration)}")


def get_system_resources() -> dict[str, Any]:
    """Return current system resource information."""
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
    except Exception as e:
        logger.warning(f"Failed to get system resources: {e}")
        return {}


class StagePerformanceTracker:
    """Track performance metrics for pipeline stages."""

    def __init__(self):
        self.stages: list[dict[str, Any]] = []
        self.start_time: Optional[float] = None

    def start_stage(self, stage_name: str) -> None:
        """Start tracking a stage."""
        self.start_time = time.time()
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
            return {}

        duration = time.time() - self.start_time

        metrics = {
            "stage_name": stage_name,
            "duration": duration,
            "exit_code": exit_code,
            "memory_mb": 0.0,
            "peak_memory_mb": 0.0,
            "cpu_percent": 0.0,
            "io_read_mb": 0.0,
            "io_write_mb": 0.0,
        }

        try:
            process = psutil.Process(os.getpid())
            current_memory = process.memory_info().rss / 1024 / 1024
            metrics["memory_mb"] = current_memory
            metrics["peak_memory_mb"] = current_memory
            metrics["cpu_percent"] = process.cpu_percent(interval=0.1)

            if self.start_io:
                current_io = process.io_counters()
                metrics["io_read_mb"] = (
                    (current_io.read_bytes - self.start_io.read_bytes) / 1024 / 1024
                )
                metrics["io_write_mb"] = (
                    (current_io.write_bytes - self.start_io.write_bytes) / 1024 / 1024
                )
        except AttributeError as e:
            logger.debug(f"psutil attribute not available on this platform: {e}")

        self.stages.append(metrics)
        self.start_time = None

        return metrics

    def get_performance_warnings(self) -> list[dict[str, Any]]:
        """Return performance warnings for stages."""
        warnings: list[dict[str, Any]] = []

        if not self.stages:
            return warnings

        durations = [s["duration"] for s in self.stages]
        avg_duration = sum(durations) / len(durations) if durations else 0

        for stage in self.stages:
            if stage["duration"] > avg_duration * 2 and avg_duration > 0:
                warnings.append(
                    {
                        "type": "slow_stage",
                        "stage": stage["stage_name"],
                        "duration": stage["duration"],
                        "average": avg_duration,
                        "message": f"Stage {stage['stage_name']} took {format_duration(stage['duration'])} (2x average)",  # noqa: E501
                        "suggestion": "Consider optimizing this stage or running it in parallel",
                    }
                )

        for stage in self.stages:
            if stage.get("peak_memory_mb", 0) > 1024:
                warnings.append(
                    {
                        "type": "high_memory",
                        "stage": stage["stage_name"],
                        "memory_mb": stage["peak_memory_mb"],
                        "message": f"Stage {stage['stage_name']} used {stage['peak_memory_mb']:.0f} MB memory",  # noqa: E501
                        "suggestion": "Consider memory optimization or increasing available memory",
                    }
                )

        for stage in self.stages:
            if stage.get("cpu_percent", 0) > 90:
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
            "average_duration": total_duration / len(self.stages) if self.stages else 0,
            "slowest_stage": (
                max(self.stages, key=lambda s: s["duration"]) if self.stages else None
            ),
            "fastest_stage": (
                min(self.stages, key=lambda s: s["duration"]) if self.stages else None
            ),
            "total_memory_mb": sum(s.get("memory_mb", 0) for s in self.stages),
            "peak_memory_mb": max((s.get("peak_memory_mb", 0) for s in self.stages), default=0),
            "warnings": self.get_performance_warnings(),
        }


# ── Function-level profiling (CodeProfiler) ─────────────────────────────────


@dataclass
class ProfilingMetrics:
    """Container for function-level performance measurement results."""

    operation_name: str
    execution_time: float
    memory_peak: Optional[int] = None
    memory_current: Optional[int] = None
    memory_delta: Optional[int] = None
    cpu_time: Optional[float] = None
    function_calls: Optional[int] = None
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        """Convert memory values to MB."""
        if self.memory_peak:
            self.memory_peak = self.memory_peak // (1024 * 1024)
        if self.memory_current:
            self.memory_current = self.memory_current // (1024 * 1024)
        if self.memory_delta:
            self.memory_delta = self.memory_delta // (1024 * 1024)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting."""
        return {
            "operation": self.operation_name,
            "execution_time_seconds": round(self.execution_time, 3),
            "memory_peak_mb": self.memory_peak,
            "memory_current_mb": self.memory_current,
            "memory_delta_mb": self.memory_delta,
            "cpu_time_seconds": self.cpu_time,
            "function_calls": self.function_calls,
            "timestamp": self.timestamp,
        }


class CodeProfiler:
    """Comprehensive performance monitoring and profiling via cProfile/tracemalloc."""

    def __init__(self):
        self.metrics_history: List[ProfilingMetrics] = []

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

            logger.info(
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
            logger.info(f"Profile results for {func.__name__}:")
            stats.print_stats(10)

    def benchmark_function(
        self,
        func: Callable,
        *args,
        iterations: int = 5,
        warmup_iterations: int = 2,
        **kwargs,
    ) -> Dict[str, Union[float, List[float]]]:
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

    def get_recent_metrics(self, limit: int = 10) -> List[ProfilingMetrics]:
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


_global_monitor = CodeProfiler()


def get_performance_monitor() -> CodeProfiler:
    """Return the global CodeProfiler instance."""
    return _global_monitor


def monitor_performance(operation_name: str, track_memory: bool = True):
    """Decorator for monitoring function performance.

    Args:
        operation_name: Label for the monitored operation
        track_memory: Whether to track memory usage
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            op_name = operation_name or f"{func.__module__}.{func.__qualname__}"
            with monitor.monitor(op_name, track_memory):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def benchmark_llm_query(
    client, prompt: str, iterations: int = 3
) -> Dict[str, Union[float, List[float]]]:
    """Benchmark LLM query performance."""
    monitor = get_performance_monitor()
    return monitor.benchmark_function(client.query, prompt, iterations=iterations)


def profile_memory_usage(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """Profile memory usage of a function."""
    tracemalloc.start()

    try:
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        current, peak = tracemalloc.get_traced_memory()

        return {
            "execution_time": execution_time,
            "memory_current": current // (1024 * 1024),
            "memory_peak": peak // (1024 * 1024),
            "result": result,
        }
    finally:
        tracemalloc.stop()


def benchmark_function(
    func: Callable, *args, iterations: int = 5, **kwargs
) -> Dict[str, Union[float, List[float]]]:
    """Benchmark a function using CodeProfiler."""
    return CodeProfiler().benchmark_function(func, *args, iterations=iterations, **kwargs)


def main():
    """CLI entry point for performance monitoring."""
    import argparse

    parser = argparse.ArgumentParser(description="Performance monitoring and profiling")
    parser.add_argument("--report", action="store_true", help="Generate performance report")
    parser.add_argument("--clear", action="store_true", help="Clear metrics history")

    args = parser.parse_args()
    monitor = get_performance_monitor()

    if args.clear:
        monitor.clear_metrics_history()
        print("Performance metrics history cleared.")

    if args.report:
        print(monitor.generate_performance_report())


if __name__ == "__main__":
    main()
