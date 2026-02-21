"""Performance analysis for Ento-Linguistic pipelines.

This module provides tools for analyzing the scalability and convergence properties
of terminology extraction and discourse mapping algorithms.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

__all__ = [
    "ConvergenceMetrics",
    "analyze_convergence",
    "ScalabilityMetrics",
    "analyze_scalability",
    "calculate_speedup",
    "calculate_efficiency",
    "benchmark_comparison",
    "check_statistical_significance",
]


@dataclass
class ConvergenceMetrics:
    """Metrics for convergence analysis."""

    final_value: float
    target_value: Optional[float]
    error: float
    convergence_rate: Optional[float]
    iterations_to_convergence: Optional[int]
    is_converged: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "final_value": self.final_value,
            "target_value": self.target_value,
            "error": self.error,
            "convergence_rate": self.convergence_rate,
            "iterations_to_convergence": self.iterations_to_convergence,
            "is_converged": self.is_converged,
        }


def analyze_convergence(
    values: np.ndarray,
    target: Optional[float] = None,
    tolerance: float = 1e-6,
    window_size: int = 10,
) -> ConvergenceMetrics:
    """Analyze convergence of a sequence.

    Args:
        values: Sequence of values
        target: Target value (if known)
        tolerance: Convergence tolerance
        window_size: Window size for convergence detection

    Returns:
        ConvergenceMetrics object
    """
    if len(values) == 0:
        raise ValueError("Values array is empty")

    final_value = float(values[-1])

    # Calculate error if target provided
    if target is not None:
        error = abs(final_value - target)
    else:
        # Use relative change
        if len(values) > window_size:
            recent_mean = np.mean(values[-window_size:])
            earlier_mean = np.mean(values[-2 * window_size : -window_size])
            error = abs(recent_mean - earlier_mean) / (abs(earlier_mean) + 1e-10)
        else:
            error = abs(values[-1] - values[0]) if len(values) > 1 else 0.0

    # Check convergence
    is_converged = error < tolerance

    # Find iteration to convergence
    iterations_to_convergence = None
    if target is not None:
        for i, val in enumerate(values):
            if abs(val - target) < tolerance:
                iterations_to_convergence = i
                break

    # Calculate convergence rate (exponential fit to error)
    convergence_rate = None
    if len(values) > 1 and target is not None:
        errors = np.abs(values - target)
        # Fit exponential: error = a * exp(-r * iteration)
        if np.all(errors > 0):
            log_errors = np.log(errors)
            iterations = np.arange(len(errors))
            # Linear fit to log errors
            if len(iterations) > 1:
                coeffs = np.polyfit(iterations, log_errors, 1)
                convergence_rate = -coeffs[0]  # Negative slope

    return ConvergenceMetrics(
        final_value=final_value,
        target_value=target,
        error=float(error),
        convergence_rate=convergence_rate,
        iterations_to_convergence=iterations_to_convergence,
        is_converged=is_converged,
    )


@dataclass
class ScalabilityMetrics:
    """Metrics for scalability analysis."""

    problem_sizes: List[int]
    execution_times: List[float]
    memory_usage: Optional[List[float]]
    time_complexity: Optional[str]
    speedup: Optional[List[float]]
    efficiency: Optional[List[float]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "problem_sizes": self.problem_sizes,
            "execution_times": self.execution_times,
            "memory_usage": self.memory_usage,
            "time_complexity": self.time_complexity,
            "speedup": self.speedup,
            "efficiency": self.efficiency,
        }


def analyze_scalability(
    problem_sizes: List[int],
    execution_times: List[float],
    memory_usage: Optional[List[float]] = None,
) -> ScalabilityMetrics:
    """Analyze scalability of an algorithm.

    Args:
        problem_sizes: List of problem sizes
        execution_times: Corresponding execution times
        memory_usage: Optional memory usage measurements

    Returns:
        ScalabilityMetrics object
    """
    if len(problem_sizes) != len(execution_times):
        raise ValueError("problem_sizes and execution_times must have same length")

    # Estimate time complexity
    time_complexity = _estimate_complexity(problem_sizes, execution_times)

    # Calculate speedup (relative to first measurement)
    speedup = None
    if len(execution_times) > 1:
        baseline_time = execution_times[0]
        speedup = [baseline_time / t for t in execution_times]

    # Calculate efficiency (speedup / problem_size_ratio)
    efficiency = None
    if speedup and len(problem_sizes) > 1:
        baseline_size = problem_sizes[0]
        size_ratios = [s / baseline_size for s in problem_sizes]
        efficiency = [s / r for s, r in zip(speedup, size_ratios)]

    return ScalabilityMetrics(
        problem_sizes=problem_sizes,
        execution_times=execution_times,
        memory_usage=memory_usage,
        time_complexity=time_complexity,
        speedup=speedup,
        efficiency=efficiency,
    )


def _estimate_complexity(sizes: List[int], times: List[float]) -> str:
    """Estimate time complexity from measurements.

    Args:
        sizes: Problem sizes
        times: Execution times

    Returns:
        Estimated complexity (O(1), O(n), O(n^2), etc.)
    """
    if len(sizes) < 2:
        return "unknown"

    # Log-log fit to estimate exponent
    log_sizes = np.log(sizes)
    log_times = np.log(times)

    # Linear fit
    coeffs = np.polyfit(log_sizes, log_times, 1)
    exponent = coeffs[0]

    # Classify based on exponent
    if abs(exponent) < 0.1:
        return "O(1)"
    elif abs(exponent - 1) < 0.2:
        return "O(n)"
    elif abs(exponent - 2) < 0.2:
        return "O(n^2)"
    elif abs(exponent - 3) < 0.2:
        return "O(n^3)"
    elif abs(exponent - np.log(2)) < 0.2:
        return "O(n log n)"
    else:
        return f"O(n^{exponent:.2f})"


def calculate_speedup(
    baseline_time: float, optimized_times: List[float]
) -> List[float]:
    """Calculate speedup relative to baseline.

    Args:
        baseline_time: Baseline execution time
        optimized_times: Optimized execution times

    Returns:
        List of speedup values
    """
    return [baseline_time / t for t in optimized_times]


def calculate_efficiency(
    speedup: List[float], resource_ratios: List[float]
) -> List[float]:
    """Calculate efficiency (speedup / resource_ratio).

    Args:
        speedup: Speedup values
        resource_ratios: Resource usage ratios (e.g., number of processors)

    Returns:
        List of efficiency values
    """
    if len(speedup) != len(resource_ratios):
        raise ValueError("speedup and resource_ratios must have same length")

    return [s / r for s, r in zip(speedup, resource_ratios)]


def benchmark_comparison(
    methods: List[str],
    metrics: Dict[str, List[float]],
    metric_name: str = "execution_time",
) -> Dict[str, Any]:
    """Compare multiple methods on benchmarks.

    Args:
        methods: List of method names
        metrics: Dictionary mapping method names to metric values
        metric_name: Name of the metric being compared

    Returns:
        Dictionary with comparison results
    """
    if metric_name not in metrics:
        raise ValueError(f"Metric '{metric_name}' not found in metrics")

    values = metrics[metric_name]

    # Calculate statistics
    best_idx = np.argmin(values) if values else 0
    best_method = methods[best_idx] if best_idx < len(methods) else None
    best_value = values[best_idx] if values else None

    # Calculate relative performance
    if best_value and best_value > 0:
        relative_performance = [best_value / v for v in values]
    else:
        relative_performance = [1.0] * len(values)

    return {
        "methods": methods,
        "values": values,
        "best_method": best_method,
        "best_value": best_value,
        "relative_performance": relative_performance,
        "metric_name": metric_name,
    }


def check_statistical_significance(
    group1: np.ndarray, group2: np.ndarray, alpha: float = 0.05
) -> Dict[str, Any]:
    """Test statistical significance between two groups.

    Args:
        group1: First group of measurements
        group2: Second group of measurements
        alpha: Significance level

    Returns:
        Dictionary with test results
    """
    from .statistics import t_test

    # Perform t-test
    test_result = t_test(group1, group2)
    p_value = test_result["p_value"]

    is_significant = p_value < alpha

    return {
        "p_value": p_value,
        "alpha": alpha,
        "is_significant": is_significant,
        "mean1": float(np.mean(group1)),
        "mean2": float(np.mean(group2)),
        "std1": float(np.std(group1)),
        "std2": float(np.std(group2)),
    }
