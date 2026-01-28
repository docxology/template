"""Performance benchmarking for scientific functions.

Provides utilities for benchmarking function performance:
- Execution time measurement
- Memory usage tracking (when psutil available)
- Performance report generation with recommendations
- Multi-input benchmarking
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import numpy as np


@dataclass
class BenchmarkResult:
    """Container for benchmark results."""

    function_name: str
    execution_time: float
    memory_usage: Optional[float]
    iterations: int
    parameters: Dict[str, Any]
    result_summary: str
    timestamp: str


def benchmark_function(
    func: Callable, test_inputs: List[Any], iterations: int = 100
) -> BenchmarkResult:
    """Benchmark function performance across multiple inputs.

    Args:
        func: Function to benchmark
        test_inputs: List of input values to test
        iterations: Number of iterations per input

    Returns:
        BenchmarkResult with performance analysis
    """
    try:
        import psutil

        psutil_available = True
    except ImportError:
        psutil_available = False

    execution_times = []
    memory_usages = []

    for test_input in test_inputs:
        # Warm up
        for _ in range(10):
            try:
                _ = func(test_input)
            except:
                pass

        # Measure execution time
        start_time = time.perf_counter()

        for _ in range(iterations):
            try:
                result = func(test_input)
            except:
                result = None

        end_time = time.perf_counter()
        avg_time = (end_time - start_time) / iterations
        execution_times.append(avg_time)

        # Try to measure memory usage
        if psutil_available:
            try:
                process = psutil.Process(os.getpid())
                memory_info = process.memory_info()
                memory_usages.append(memory_info.rss / 1024 / 1024)  # MB
            except:
                memory_usages.append(None)
        else:
            memory_usages.append(None)

    avg_execution_time = np.mean(execution_times) if execution_times else 0.0
    valid_memory = [
        m
        for m in memory_usages
        if m is not None and not (isinstance(m, float) and np.isnan(m))
    ]
    avg_memory_usage = np.mean(valid_memory) if valid_memory else None

    # Create result summary
    result_summary = f"Avg time: {avg_execution_time:.6f}s"
    if avg_memory_usage:
        result_summary += f", Avg memory: {avg_memory_usage:.1f}MB"

    return BenchmarkResult(
        function_name=func.__name__,
        execution_time=avg_execution_time,
        memory_usage=avg_memory_usage,
        iterations=iterations,
        parameters={"input_count": len(test_inputs)},
        result_summary=result_summary,
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
    )


def generate_performance_report(benchmark_results: List[BenchmarkResult]) -> str:
    """Generate a performance analysis report.

    Args:
        benchmark_results: List of benchmark results to analyze

    Returns:
        Markdown formatted performance report
    """
    if not benchmark_results:
        return "No benchmark results to analyze."

    # Calculate summary statistics
    execution_times = [r.execution_time for r in benchmark_results]
    memory_usages = [
        r.memory_usage for r in benchmark_results if r.memory_usage is not None
    ]

    report = []
    report.append("# Performance Analysis Report")
    report.append("")

    report.append("## Summary Statistics")
    report.append(f"- **Functions tested**: {len(benchmark_results)}")
    report.append(f"- **Average execution time**: {np.mean(execution_times):.6f}s")
    report.append(f"- **Median execution time**: {np.median(execution_times):.6f}s")
    report.append(f"- **Min execution time**: {np.min(execution_times):.6f}s")
    report.append(f"- **Max execution time**: {np.max(execution_times):.6f}s")

    if memory_usages:
        report.append(f"- **Average memory usage**: {np.mean(memory_usages):.1f}MB")
        report.append(f"- **Median memory usage**: {np.median(memory_usages):.1f}MB")

    report.append("")

    report.append("## Detailed Results")
    report.append(
        "| Function | Exec Time (s) | Memory (MB) | Iterations | Parameters |"
    )
    report.append(
        "|----------|---------------|-------------|------------|------------|"
    )

    for result in sorted(
        benchmark_results, key=lambda x: x.execution_time, reverse=True
    ):
        memory_str = f"{result.memory_usage:.1f}" if result.memory_usage else "N/A"
        report.append(
            f"| `{result.function_name}` | {result.execution_time:.6f} | {memory_str} | {result.iterations} | {result.parameters} |"
        )

    report.append("")

    # Performance recommendations
    report.append("## Recommendations")
    slow_functions = [r for r in benchmark_results if r.execution_time > 0.1]
    if slow_functions:
        report.append("### Performance Optimization")
        for func in slow_functions[:3]:  # Top 3 slowest
            report.append(
                f"- Consider optimizing `{func.function_name}` (currently {func.execution_time:.6f}s)"
            )

    memory_intensive = [
        r for r in benchmark_results if r.memory_usage and r.memory_usage > 100
    ]
    if memory_intensive:
        report.append("### Memory Optimization")
        for func in memory_intensive[:3]:  # Top 3 memory intensive
            report.append(
                f"- Review memory usage in `{func.function_name}` (currently {func.memory_usage:.1f}MB)"
            )

    report.append("")

    return "\n".join(report)
