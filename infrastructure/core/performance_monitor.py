"""Performance monitoring and profiling utilities for research workflows.

This module provides comprehensive performance monitoring, benchmarking,
and profiling capabilities for research code execution.
"""

import cProfile
import functools
import io
import pstats
import time
import tracemalloc
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for performance measurement results."""

    operation_name: str
    execution_time: float
    memory_peak: Optional[int] = None
    memory_current: Optional[int] = None
    memory_delta: Optional[int] = None
    cpu_time: Optional[float] = None
    function_calls: Optional[int] = None
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        """Convert memory values to MB for readability."""
        if self.memory_peak:
            self.memory_peak = self.memory_peak // (1024 * 1024)
        if self.memory_current:
            self.memory_current = self.memory_current // (1024 * 1024)
        if self.memory_delta:
            self.memory_delta = self.memory_delta // (1024 * 1024)

    def to_dict(self) -> Dict[str, Union[str, float, int]]:
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


class PerformanceMonitor:
    """Comprehensive performance monitoring and profiling."""

    def __init__(self):
        self.metrics_history: List[PerformanceMetrics] = []

    @contextmanager
    def monitor(self, operation_name: str, track_memory: bool = True):
        """Context manager for monitoring operation performance.

        Args:
            operation_name: Name of the operation being monitored
            track_memory: Whether to track memory usage
        """
        start_time = time.time()
        cpu_start = time.process_time()

        if track_memory:
            tracemalloc.start()

        try:
            yield
        finally:
            execution_time = time.time() - start_time
            cpu_time = time.process_time() - cpu_start

            metrics = PerformanceMetrics(
                operation_name=operation_name,
                execution_time=execution_time,
                cpu_time=cpu_time,
            )

            if track_memory:
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                metrics.memory_current = current
                metrics.memory_peak = peak

            self.metrics_history.append(metrics)

            logger.info(
                f"Performance: {operation_name} completed in {execution_time:.3f}s "
                f"(CPU: {cpu_time:.3f}s, Peak memory: {metrics.memory_peak or 'N/A'}MB)"
            )

    def profile_function(self, func: Callable, *args, **kwargs) -> Any:
        """Profile a function execution with detailed statistics.

        Args:
            func: Function to profile
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Function result
        """
        profiler = cProfile.Profile()
        profiler.enable()

        try:
            result = func(*args, **kwargs)
            return result
        finally:
            profiler.disable()

            # Generate statistics
            stats = pstats.Stats(profiler)
            stats.sort_stats("cumulative")

            # Log top 10 most time-consuming functions
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
        """Benchmark function performance over multiple iterations.

        Args:
            func: Function to benchmark
            iterations: Number of benchmark iterations
            warmup_iterations: Number of warmup iterations (not measured)
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Dictionary with benchmark statistics
        """
        # Warmup runs
        for _ in range(warmup_iterations):
            func(*args, **kwargs)

        execution_times = []

        for i in range(iterations):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()

            execution_time = end_time - start_time
            execution_times.append(execution_time)
            logger.debug(f"Iteration {i + 1}: {execution_time:.4f}s")

        # Calculate statistics
        avg_time = sum(execution_times) / len(execution_times)
        min_time = min(execution_times)
        max_time = max(execution_times)
        std_dev = (
            sum((t - avg_time) ** 2 for t in execution_times) / len(execution_times)
        ) ** 0.5

        benchmark_results = {
            "function_name": func.__name__,
            "iterations": iterations,
            "average_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "std_dev": std_dev,
            "all_times": execution_times,
        }

        logger.info(
            f"Benchmark: {func.__name__} - "
            f"avg: {avg_time:.4f}s, "
            f"std: {std_dev:.4f}s"
        )

        return benchmark_results

    def get_recent_metrics(self, limit: int = 10) -> List[PerformanceMetrics]:
        """Get the most recent performance metrics.

        Args:
            limit: Maximum number of metrics to return

        Returns:
            List of recent performance metrics
        """
        return self.metrics_history[-limit:]

    def clear_metrics_history(self):
        """Clear the metrics history."""
        self.metrics_history.clear()

    def generate_performance_report(self) -> str:
        """Generate a comprehensive performance report.

        Returns:
            Formatted performance report
        """
        if not self.metrics_history:
            return "No performance metrics available."

        report_lines = [
            "# Performance Report",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary Statistics",
            f"- Total operations monitored: {len(self.metrics_history)}",
        ]

        if self.metrics_history:
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

            for metric in self.metrics_history[-10:]:  # Last 10 operations
                report_lines.append(
                    f"| {metric.operation_name} | {metric.execution_time:.3f} | {metric.memory_peak or 'N/A'} |"
                )

        return "\n".join(report_lines)


# Global performance monitor instance
_global_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance.

    Returns:
        Global PerformanceMonitor instance
    """
    return _global_monitor


def monitor_performance(operation_name: str, track_memory: bool = True):
    """Decorator for monitoring function performance.

    Args:
        operation_name: Name of the operation (if None, uses function name)
        track_memory: Whether to track memory usage

    Returns:
        Decorated function
    """

    def decorator(func):
        """Wrap the target function with performance monitoring.

        Args:
            func: The function to be decorated with monitoring.

        Returns:
            Callable: Wrapped function that monitors performance metrics.
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """Execute the wrapped function with performance monitoring.

            Monitors execution time, memory usage (if enabled), and logs
            performance metrics upon completion.

            Args:
                *args: Positional arguments passed to the wrapped function.
                **kwargs: Keyword arguments passed to the wrapped function.

            Returns:
                The return value from the wrapped function.
            """
            monitor = get_performance_monitor()
            op_name = operation_name or f"{func.__module__}.{func.__qualname__}"

            with monitor.monitor(op_name, track_memory):
                return func(*args, **kwargs)

        return wrapper

    return decorator


# Convenience functions for common use cases
def benchmark_llm_query(
    client, prompt: str, iterations: int = 3
) -> Dict[str, Union[float, List[float]]]:
    """Benchmark LLM query performance.

    Args:
        client: LLM client instance
        prompt: Query prompt
        iterations: Number of benchmark iterations

    Returns:
        Benchmark results dictionary
    """
    monitor = get_performance_monitor()
    return monitor.benchmark_function(client.query, prompt, iterations=iterations)


def profile_memory_usage(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """Profile memory usage of a function.

    Args:
        func: Function to profile
        *args: Function arguments
        **kwargs: Function keyword arguments

    Returns:
        Memory profiling results
    """
    tracemalloc.start()

    try:
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time

        current, peak = tracemalloc.get_traced_memory()

        return {
            "execution_time": execution_time,
            "memory_current": current // (1024 * 1024),  # MB
            "memory_peak": peak // (1024 * 1024),  # MB
            "result": result,
        }
    finally:
        tracemalloc.stop()


# CLI integration
def main():
    """CLI entry point for performance monitoring."""
    import argparse

    parser = argparse.ArgumentParser(description="Performance monitoring and profiling")
    parser.add_argument(
        "--report", action="store_true", help="Generate performance report"
    )
    parser.add_argument("--clear", action="store_true", help="Clear metrics history")

    args = parser.parse_args()

    monitor = get_performance_monitor()

    if args.clear:
        monitor.clear_metrics_history()
        print("Performance metrics history cleared.")

    if args.report:
        report = monitor.generate_performance_report()
        print(report)


def benchmark_function(
    func: Callable, *args, iterations: int = 5, **kwargs
) -> Dict[str, Union[float, List[float]]]:
    """
    Convenience function to benchmark a function using PerformanceMonitor.

    Args:
        func: The function to benchmark.
        *args: Positional arguments to pass to the function.
        iterations: Number of iterations to run.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        Dictionary containing benchmark results.
    """
    monitor = PerformanceMonitor()
    return monitor.benchmark_function(func, *args, iterations=iterations, **kwargs)


if __name__ == "__main__":
    main()
