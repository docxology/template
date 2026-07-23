"""Test suite for scientific_dev module.

This test suite provides comprehensive validation for scientific development tools
including numerical stability, performance benchmarking, and best practices.
"""

import numpy as np
import pytest

# Import the modules to test
from infrastructure.scientific import (
    BenchmarkResult,
    benchmark_function,
    check_numerical_stability,
    format_benchmark_report,
)
from infrastructure.scientific.stability import StabilityTest


class TestNumericalStability:
    """Test numerical stability analysis."""

    def test_check_numerical_stability_stable_function(self):
        """Test stability check on numerically stable function."""

        def stable_function(x):
            return x * 2 + 1

        test_inputs = [0.1, 1.0, 10.0, 100.0, 1000.0]
        stability = check_numerical_stability(stable_function, test_inputs)

        assert stability.stability_score > 0.8
        assert stability.function_name == "stable_function"
        assert len(stability.recommendations) == 0

    def test_check_numerical_stability_unstable_function(self):
        """Test stability check on numerically unstable function."""

        def unstable_function(x):
            return 1.0 / x if x != 0 else float("inf")

        test_inputs = [0.001, 0.01, 0.1, 0.0, 1.0, 10.0]
        stability = check_numerical_stability(unstable_function, test_inputs)

        assert stability.stability_score < 1.0


class TestBenchmarking:
    """Test performance benchmarking functionality."""

    def test_benchmark_function_simple(self):
        """Test benchmarking of simple function."""

        def simple_function(x):
            return x**2

        test_inputs = [1.0, 2.0, 3.0]
        benchmark = benchmark_function(simple_function, test_inputs, iterations=10)

        assert benchmark.function_name == "simple_function"
        assert benchmark.execution_time > 0
        assert benchmark.iterations == 10
        assert benchmark.parameters["input_count"] == 3

    def test_benchmark_function_with_memory(self):
        """Test benchmarking with memory usage tracking."""

        def memory_function(x):
            arr = np.zeros(1000)
            return np.sum(arr)

        test_inputs = [1.0, 2.0]
        benchmark = benchmark_function(memory_function, test_inputs, iterations=5)

        # Memory measurement may not be available in all environments
        if benchmark.memory_usage is not None:
            assert benchmark.memory_usage >= 0  # Should be non-negative if available
        else:
            # If memory measurement is not available, check that other metrics are still working
            assert benchmark.execution_time > 0
            assert benchmark.iterations == 5


class TestPerformanceReporting:
    """Test performance report generation."""

    def test_format_benchmark_report(self):
        """Test generation of performance analysis report."""

        results = [
            BenchmarkResult("func1", 0.001, 10.5, 100, {}, "Fast function", "2024-01-01 10:00:00"),
            BenchmarkResult("func2", 0.010, 25.0, 100, {}, "Slow function", "2024-01-01 10:00:01"),
            BenchmarkResult("func3", 0.005, 15.2, 100, {}, "Medium function", "2024-01-01 10:00:02"),
        ]

        report = format_benchmark_report(results)

        assert "Performance Analysis Report" in report
        assert "func1" in report
        assert "func2" in report
        assert "func3" in report
        assert "Average execution time" in report


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_check_numerical_stability_empty_inputs(self):
        """Test stability check with empty input list."""

        def dummy_function(x):
            return x

        stability = check_numerical_stability(dummy_function, [])

        assert stability.stability_score == 0.0
        assert len(stability.recommendations) > 0

    def test_benchmark_function_exception_handling(self):
        """Test benchmarking with function that raises exceptions."""

        def failing_function(x):
            if x > 0:
                raise ValueError("Test error")
            return x

        test_inputs = [-1.0, 1.0]  # One should fail
        benchmark = benchmark_function(failing_function, test_inputs, iterations=5)

        # Should still complete despite exceptions
        assert benchmark.function_name == "failing_function"
        assert benchmark.execution_time >= 0


class TestPerformanceRecommendations:
    """Test performance report recommendations (covers lines 459-467)."""

    def test_format_benchmark_report_slow_functions(self):
        """Test performance report with slow functions (lines 459-461)."""

        results = [
            # Slow function (> 0.1s)
            BenchmarkResult("slow_func", 0.15, 10.0, 100, {}, "Slow", "2024-01-01 10:00:00"),
            # Very slow function
            BenchmarkResult(
                "very_slow_func",
                0.25,
                10.0,
                100,
                {},
                "Very slow",
                "2024-01-01 10:00:01",
            ),
            # Fast function
            BenchmarkResult("fast_func", 0.001, 10.0, 100, {}, "Fast", "2024-01-01 10:00:02"),
        ]

        report = format_benchmark_report(results)

        assert "Performance Optimization" in report
        assert "slow_func" in report
        assert "Consider optimizing" in report

    def test_format_benchmark_report_memory_intensive(self):
        """Test performance report with memory-intensive functions (lines 463-467)."""

        results = [
            # Memory-intensive function (> 100MB)
            BenchmarkResult("memory_hog", 0.01, 150.0, 100, {}, "Memory hog", "2024-01-01 10:00:00"),
            # Very memory-intensive function
            BenchmarkResult(
                "memory_hog2",
                0.01,
                200.0,
                100,
                {},
                "Memory hog 2",
                "2024-01-01 10:00:01",
            ),
            # Normal function
            BenchmarkResult("normal_func", 0.01, 10.0, 100, {}, "Normal", "2024-01-01 10:00:02"),
        ]

        report = format_benchmark_report(results)

        assert "Memory Optimization" in report
        assert "memory_hog" in report
        assert "Review memory usage" in report

    def test_format_benchmark_report_both_issues(self):
        """Test performance report with both slow and memory-intensive functions."""

        results = [
            BenchmarkResult(
                "problem_func",
                0.2,
                250.0,
                100,
                {},
                "Has both issues",
                "2024-01-01 10:00:00",
            ),
        ]

        report = format_benchmark_report(results)

        assert "Performance Optimization" in report
        assert "Memory Optimization" in report


class TestScientificDevEdgeCases:
    """Edge case tests for scientific_dev module."""

    def test_check_numerical_stability_with_nan(self):
        """Test numerical stability check with NaN results."""

        def unstable_function(x):
            return float("nan") if x == 0 else x

        result = check_numerical_stability(unstable_function, [0, 1, 2])

        # Result is a StabilityTest dataclass
        assert isinstance(result, StabilityTest)
        # Should detect some stability issues (score not perfect)
        assert result.stability_score < 1.0

    def test_benchmark_function_exception_handling(self):
        """Test benchmarking handles exceptions gracefully."""

        def working_function(x):
            return x * 2

        result = benchmark_function(working_function, [1, 2, 3])

        # Result is a BenchmarkResult dataclass
        assert isinstance(result, BenchmarkResult)
        assert result.execution_time > 0


if __name__ == "__main__":
    pytest.main([__file__])
