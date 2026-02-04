"""Test suite for infrastructure.scientific.benchmarking module.

Tests performance benchmarking utilities including:
- Execution time measurement
- Memory usage tracking
- Performance report generation
- Multi-input benchmarking
- Edge cases and error handling

All tests use real numerical data with no mocks.
"""

import time

import numpy as np
import pytest

from infrastructure.scientific.benchmarking import (
    BenchmarkResult,
    benchmark_function,
    generate_performance_report,
)


class TestBenchmarkResult:
    """Test BenchmarkResult dataclass."""

    def test_benchmark_result_creation(self):
        """Test creation of BenchmarkResult with all fields."""
        result = BenchmarkResult(
            function_name="test_func",
            execution_time=0.001,
            memory_usage=50.5,
            iterations=100,
            parameters={"input_count": 5},
            result_summary="Avg time: 0.001s",
            timestamp="2024-01-15 10:00:00",
        )

        assert result.function_name == "test_func"
        assert result.execution_time == 0.001
        assert result.memory_usage == 50.5
        assert result.iterations == 100
        assert result.parameters == {"input_count": 5}
        assert "Avg time" in result.result_summary
        assert result.timestamp == "2024-01-15 10:00:00"

    def test_benchmark_result_without_memory(self):
        """Test BenchmarkResult with None memory usage."""
        result = BenchmarkResult(
            function_name="test_func",
            execution_time=0.002,
            memory_usage=None,
            iterations=50,
            parameters={},
            result_summary="Test",
            timestamp="2024-01-15 10:00:00",
        )

        assert result.memory_usage is None
        assert result.execution_time == 0.002


class TestBenchmarkFunction:
    """Test benchmark_function utility."""

    def test_benchmark_simple_function(self):
        """Test benchmarking a simple mathematical function."""

        def simple_add(x):
            return x + 1

        test_inputs = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = benchmark_function(simple_add, test_inputs, iterations=50)

        assert result.function_name == "simple_add"
        assert result.execution_time > 0
        assert result.execution_time < 1.0  # Should be fast
        assert result.iterations == 50
        assert result.parameters["input_count"] == 5
        assert "Avg time" in result.result_summary

    def test_benchmark_numpy_function(self):
        """Test benchmarking function with numpy operations."""

        def numpy_sum(x):
            arr = np.arange(x)
            return np.sum(arr)

        test_inputs = [10, 100, 1000]
        result = benchmark_function(numpy_sum, test_inputs, iterations=20)

        assert result.function_name == "numpy_sum"
        assert result.execution_time > 0
        assert result.iterations == 20

    def test_benchmark_with_exception_handling(self):
        """Test benchmarking handles exceptions gracefully."""

        def failing_function(x):
            if x > 5:
                raise ValueError("Input too large")
            return x * 2

        test_inputs = [1.0, 3.0, 7.0, 10.0]  # Last two will fail
        result = benchmark_function(failing_function, test_inputs, iterations=10)

        # Should still complete despite exceptions
        assert result.function_name == "failing_function"
        assert result.execution_time >= 0
        assert result.iterations == 10

    def test_benchmark_all_inputs_fail(self):
        """Test benchmarking when all inputs cause exceptions."""

        def always_fails(x):
            raise RuntimeError("Always fails")

        test_inputs = [1.0, 2.0, 3.0]
        result = benchmark_function(always_fails, test_inputs, iterations=5)

        # Should still complete
        assert result.function_name == "always_fails"
        assert result.execution_time >= 0

    def test_benchmark_single_input(self):
        """Test benchmarking with single input."""

        def square(x):
            return x * x

        test_inputs = [5.0]
        result = benchmark_function(square, test_inputs, iterations=100)

        assert result.parameters["input_count"] == 1
        assert result.execution_time > 0

    def test_benchmark_empty_inputs(self):
        """Test benchmarking with empty input list."""

        def dummy(x):
            return x

        result = benchmark_function(dummy, [], iterations=10)

        assert result.execution_time == 0.0
        assert result.parameters["input_count"] == 0

    def test_benchmark_large_iterations(self):
        """Test benchmarking with many iterations."""

        def fast_function(x):
            return x

        test_inputs = [1.0]
        result = benchmark_function(fast_function, test_inputs, iterations=1000)

        assert result.iterations == 1000
        assert result.execution_time > 0

    def test_benchmark_result_summary_format(self):
        """Test result summary contains expected information."""

        def test_func(x):
            return x + 1

        result = benchmark_function(test_func, [1.0, 2.0], iterations=10)

        assert "Avg time:" in result.result_summary
        # Memory might be present if psutil is available
        if result.memory_usage is not None:
            assert "Avg memory:" in result.result_summary

    def test_benchmark_timestamp_format(self):
        """Test timestamp is in expected format."""

        def test_func(x):
            return x

        result = benchmark_function(test_func, [1.0], iterations=5)

        # Timestamp should be in YYYY-MM-DD HH:MM:SS format
        assert len(result.timestamp) == 19
        assert result.timestamp[4] == "-"
        assert result.timestamp[10] == " "

    def test_benchmark_memory_with_large_arrays(self):
        """Test memory tracking with memory-intensive operations."""

        def create_large_array(size):
            return np.zeros(size * 1000)

        test_inputs = [10, 50, 100]
        result = benchmark_function(create_large_array, test_inputs, iterations=5)

        # Memory tracking may or may not be available
        assert result.function_name == "create_large_array"
        assert result.execution_time > 0


class TestGeneratePerformanceReport:
    """Test generate_performance_report function."""

    def test_generate_report_empty_results(self):
        """Test report generation with empty results list."""
        report = generate_performance_report([])

        assert report == "No benchmark results to analyze."

    def test_generate_report_single_result(self):
        """Test report generation with single result."""
        results = [
            BenchmarkResult(
                function_name="func1",
                execution_time=0.005,
                memory_usage=25.0,
                iterations=100,
                parameters={"input_count": 3},
                result_summary="Test",
                timestamp="2024-01-15 10:00:00",
            )
        ]

        report = generate_performance_report(results)

        assert "Performance Analysis Report" in report
        assert "Summary Statistics" in report
        assert "func1" in report
        assert "Functions tested**: 1" in report

    def test_generate_report_multiple_results(self):
        """Test report generation with multiple results."""
        results = [
            BenchmarkResult(
                "func1", 0.001, 10.0, 100, {}, "Fast", "2024-01-15 10:00:00"
            ),
            BenchmarkResult(
                "func2", 0.010, 25.0, 100, {}, "Medium", "2024-01-15 10:00:01"
            ),
            BenchmarkResult(
                "func3", 0.100, 50.0, 100, {}, "Slow", "2024-01-15 10:00:02"
            ),
        ]

        report = generate_performance_report(results)

        assert "func1" in report
        assert "func2" in report
        assert "func3" in report
        assert "Average execution time" in report
        assert "Median execution time" in report
        assert "Min execution time" in report
        assert "Max execution time" in report

    def test_generate_report_with_slow_functions(self):
        """Test recommendations for slow functions (> 0.1s)."""
        results = [
            BenchmarkResult(
                "slow_func", 0.150, 10.0, 100, {}, "Slow", "2024-01-15 10:00:00"
            ),
            BenchmarkResult(
                "very_slow_func", 0.300, 10.0, 100, {}, "Very slow", "2024-01-15 10:00:01"
            ),
        ]

        report = generate_performance_report(results)

        assert "Performance Optimization" in report
        assert "Consider optimizing" in report
        assert "slow_func" in report or "very_slow_func" in report

    def test_generate_report_with_memory_intensive_functions(self):
        """Test recommendations for memory-intensive functions (> 100MB)."""
        results = [
            BenchmarkResult(
                "memory_hog", 0.01, 150.0, 100, {}, "Memory intensive", "2024-01-15 10:00:00"
            ),
            BenchmarkResult(
                "bigger_hog", 0.01, 250.0, 100, {}, "More memory", "2024-01-15 10:00:01"
            ),
        ]

        report = generate_performance_report(results)

        assert "Memory Optimization" in report
        assert "Review memory usage" in report

    def test_generate_report_no_memory_data(self):
        """Test report generation when memory data is None."""
        results = [
            BenchmarkResult(
                "func1", 0.001, None, 100, {}, "No memory", "2024-01-15 10:00:00"
            ),
            BenchmarkResult(
                "func2", 0.002, None, 100, {}, "No memory", "2024-01-15 10:00:01"
            ),
        ]

        report = generate_performance_report(results)

        assert "Performance Analysis Report" in report
        assert "N/A" in report  # Memory should show N/A

    def test_generate_report_mixed_memory_data(self):
        """Test report with some results having memory, some not."""
        results = [
            BenchmarkResult(
                "with_memory", 0.001, 30.0, 100, {}, "Has memory", "2024-01-15 10:00:00"
            ),
            BenchmarkResult(
                "no_memory", 0.002, None, 100, {}, "No memory", "2024-01-15 10:00:01"
            ),
        ]

        report = generate_performance_report(results)

        assert "30.0" in report or "30" in report
        assert "N/A" in report

    def test_generate_report_table_format(self):
        """Test report contains properly formatted table."""
        results = [
            BenchmarkResult(
                "test_func", 0.005, 25.0, 50, {"key": "value"}, "Test", "2024-01-15 10:00:00"
            )
        ]

        report = generate_performance_report(results)

        assert "| Function |" in report
        assert "| Exec Time (s) |" in report
        assert "| Memory (MB) |" in report
        assert "| Iterations |" in report
        assert "|----------|" in report

    def test_generate_report_recommendations_section(self):
        """Test recommendations section is always present."""
        results = [
            BenchmarkResult(
                "fast_func", 0.001, 10.0, 100, {}, "Fast", "2024-01-15 10:00:00"
            )
        ]

        report = generate_performance_report(results)

        assert "## Recommendations" in report

    def test_generate_report_sorted_by_execution_time(self):
        """Test results are sorted by execution time (slowest first)."""
        results = [
            BenchmarkResult(
                "fast", 0.001, 10.0, 100, {}, "Fast", "2024-01-15 10:00:00"
            ),
            BenchmarkResult(
                "slow", 0.100, 10.0, 100, {}, "Slow", "2024-01-15 10:00:01"
            ),
            BenchmarkResult(
                "medium", 0.050, 10.0, 100, {}, "Medium", "2024-01-15 10:00:02"
            ),
        ]

        report = generate_performance_report(results)

        # Slow should appear before fast in the table
        slow_pos = report.find("`slow`")
        fast_pos = report.find("`fast`")
        assert slow_pos < fast_pos

    def test_generate_report_top_3_slow_recommendation(self):
        """Test only top 3 slowest functions are recommended for optimization."""
        results = [
            BenchmarkResult(f"slow_func_{i}", 0.15 + i * 0.01, 10.0, 100, {}, "Slow", "2024-01-15")
            for i in range(5)
        ]

        report = generate_performance_report(results)

        # Count "Consider optimizing" occurrences - should be at most 3
        optimize_count = report.count("Consider optimizing")
        assert optimize_count <= 3


class TestBenchmarkIntegration:
    """Integration tests for benchmarking functionality."""

    def test_benchmark_and_report_workflow(self):
        """Test complete benchmark and report workflow."""

        def func1(x):
            return x * 2

        def func2(x):
            return sum(range(int(x)))

        results = []
        for func in [func1, func2]:
            result = benchmark_function(func, [10.0, 50.0, 100.0], iterations=20)
            results.append(result)

        report = generate_performance_report(results)

        assert "func1" in report
        assert "func2" in report
        assert "Performance Analysis Report" in report

    def test_benchmark_deterministic_timing(self):
        """Test that benchmark timing is reasonably consistent."""

        def consistent_func(x):
            total = 0
            for i in range(100):
                total += i * x
            return total

        # Run benchmark twice
        result1 = benchmark_function(consistent_func, [1.0], iterations=100)
        result2 = benchmark_function(consistent_func, [1.0], iterations=100)

        # Times should be within same order of magnitude
        ratio = result1.execution_time / result2.execution_time if result2.execution_time > 0 else 1
        assert 0.1 < ratio < 10  # Within 10x


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
