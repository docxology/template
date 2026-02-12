"""Comprehensive tests for src/performance.py to ensure 100% coverage."""

import numpy as np
import pytest
from src.analysis.performance import (analyze_convergence, analyze_scalability,
                         benchmark_comparison, calculate_efficiency,
                         calculate_speedup)


class TestAnalyzeConvergence:
    """Test convergence analysis."""

    def test_convergence_with_target(self):
        """Test convergence analysis with target."""
        values = np.array([10, 8, 6, 4, 2, 1, 0.5, 0.1, 0.05, 0.01])
        convergence = analyze_convergence(values, target=0.0, tolerance=0.1)
        assert convergence.is_converged is True
        assert convergence.final_value == 0.01
        assert convergence.error < 0.1

    def test_convergence_metrics_to_dict(self):
        """Test ConvergenceMetrics.to_dict() method (line 27)."""
        values = np.array([10, 8, 6, 4, 2])
        convergence = analyze_convergence(values, target=0.0)
        metrics_dict = convergence.to_dict()
        assert "final_value" in metrics_dict
        assert "target_value" in metrics_dict
        assert "is_converged" in metrics_dict

    def test_convergence_without_target(self):
        """Test convergence analysis without target."""
        values = np.array([10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
        convergence = analyze_convergence(values, target=None)
        assert convergence.final_value == 1.0

    def test_no_convergence(self):
        """Test non-converging sequence."""
        values = np.array([10, 11, 12, 13, 14, 15])
        convergence = analyze_convergence(values, target=0.0, tolerance=0.1)
        assert convergence.is_converged is False


class TestAnalyzeScalability:
    """Test scalability analysis."""

    def test_scalability_analysis(self):
        """Test scalability analysis."""
        problem_sizes = [10, 50, 100, 500, 1000]
        execution_times = [0.1, 0.5, 1.0, 5.0, 10.0]
        scalability = analyze_scalability(problem_sizes, execution_times)
        assert scalability.time_complexity is not None
        assert len(scalability.speedup) == len(problem_sizes)

    def test_scalability_with_memory(self):
        """Test scalability with memory usage."""
        problem_sizes = [10, 50, 100]
        execution_times = [0.1, 0.5, 1.0]
        memory_usage = [10, 50, 100]
        scalability = analyze_scalability(problem_sizes, execution_times, memory_usage)
        assert scalability.memory_usage == memory_usage

    def test_scalability_metrics_to_dict(self):
        """Test ScalabilityMetrics.to_dict() method (line 117)."""
        problem_sizes = [10, 50, 100]
        execution_times = [0.1, 0.5, 1.0]
        scalability = analyze_scalability(problem_sizes, execution_times)
        metrics_dict = scalability.to_dict()
        assert "problem_sizes" in metrics_dict
        assert "execution_times" in metrics_dict
        assert "time_complexity" in metrics_dict

    def test_different_lengths(self):
        """Test error with different length arrays."""
        problem_sizes = [10, 50, 100]
        execution_times = [0.1, 0.5]
        with pytest.raises(ValueError):
            analyze_scalability(problem_sizes, execution_times)


class TestCalculateSpeedup:
    """Test speedup calculation."""

    def test_speedup(self):
        """Test speedup calculation."""
        baseline_time = 10.0
        optimized_times = [5.0, 2.0, 1.0]
        speedup = calculate_speedup(baseline_time, optimized_times)
        assert speedup == [2.0, 5.0, 10.0]


class TestCalculateEfficiency:
    """Test efficiency calculation."""

    def test_efficiency(self):
        """Test efficiency calculation."""
        speedup = [2.0, 4.0, 8.0]
        resource_ratios = [2.0, 4.0, 8.0]
        efficiency = calculate_efficiency(speedup, resource_ratios)
        assert efficiency == [1.0, 1.0, 1.0]

    def test_different_lengths(self):
        """Test error with different length arrays."""
        speedup = [2.0, 4.0]
        resource_ratios = [2.0]
        with pytest.raises(ValueError):
            calculate_efficiency(speedup, resource_ratios)


class TestBenchmarkComparison:
    """Test benchmark comparison."""

    def test_benchmark_comparison(self):
        """Test benchmark comparison."""
        methods = ["Method A", "Method B", "Method C"]
        metrics = {"execution_time": [10.0, 8.0, 12.0], "accuracy": [0.9, 0.95, 0.85]}
        comparison = benchmark_comparison(methods, metrics, "execution_time")
        assert comparison["best_method"] == "Method B"
        assert comparison["best_value"] == 8.0

    def test_missing_metric(self):
        """Test error with missing metric."""
        methods = ["Method A"]
        metrics = {"execution_time": [10.0]}
        with pytest.raises(ValueError):
            benchmark_comparison(methods, metrics, "missing_metric")


class TestStatisticalSignificance:
    """Test statistical significance testing."""

    def test_check_statistical_significance(self):
        """Test statistical significance."""
        from src.analysis.performance import check_statistical_significance

        group1 = np.array([1, 2, 3, 4, 5])
        group2 = np.array([2, 3, 4, 5, 6])
        result = check_statistical_significance(group1, group2, alpha=0.05)
        assert "p_value" in result
        assert "is_significant" in result
        assert "mean1" in result
        assert "mean2" in result

    def test_analyze_convergence_empty_array(self):
        """Test convergence analysis with empty array."""
        with pytest.raises(ValueError, match="empty"):
            analyze_convergence(np.array([]))

    def test_analyze_convergence_single_value(self):
        """Test convergence analysis with single value."""
        values = np.array([1.0])
        convergence = analyze_convergence(values, target=None)
        assert convergence.final_value == 1.0
        assert convergence.error == 0.0

    def test_analyze_convergence_with_window(self):
        """Test convergence analysis with window size."""
        values = np.array([10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0.5, 0.1])
        convergence = analyze_convergence(values, target=None, window_size=5)
        assert convergence.final_value == 0.1

    def test_analyze_convergence_errors_all_zero(self):
        """Test convergence when all errors are zero."""
        values = np.array([1.0, 1.0, 1.0, 1.0])
        convergence = analyze_convergence(values, target=1.0)
        # When errors are all zero, convergence_rate should be None
        assert convergence.is_converged is True

    def test_analyze_convergence_single_iteration(self):
        """Test convergence with single iteration."""
        values = np.array([1.0])
        convergence = analyze_convergence(values, target=1.0)
        assert convergence.convergence_rate is None

    def test_analyze_convergence_two_iterations(self):
        """Test convergence with exactly two iterations (branch 91->95)."""
        values = np.array([10.0, 5.0])
        convergence = analyze_convergence(values, target=0.0)
        # With only 2 iterations, len(iterations) > 1 is True, so should calculate convergence_rate
        assert convergence.final_value == 5.0

    def test_analyze_convergence_single_iteration_no_rate(self):
        """Test convergence with single iteration to cover branch 91->95 (False path)."""
        values = np.array([10.0])
        convergence = analyze_convergence(values, target=0.0)
        # With only 1 iteration, len(iterations) > 1 is False, so convergence_rate should be None
        assert convergence.final_value == 10.0
        assert convergence.convergence_rate is None

    def test_analyze_scalability_single_measurement(self):
        """Test scalability with single measurement."""
        problem_sizes = [10]
        execution_times = [0.1]
        scalability = analyze_scalability(problem_sizes, execution_times)
        assert scalability.speedup is None
        assert scalability.efficiency is None

    def test_analyze_scalability_no_memory(self):
        """Test scalability without memory usage."""
        problem_sizes = [10, 50, 100]
        execution_times = [0.1, 0.5, 1.0]
        scalability = analyze_scalability(problem_sizes, execution_times)
        assert scalability.memory_usage is None

    def test_estimate_complexity_single_size(self):
        """Test complexity estimation with single size."""
        from src.analysis.performance import _estimate_complexity

        complexity = _estimate_complexity([10], [0.1])
        assert complexity == "unknown"

    def test_estimate_complexity_linear(self):
        """Test complexity estimation for linear."""
        from src.analysis.performance import _estimate_complexity

        sizes = [10, 20, 30, 40, 50]
        times = [0.1, 0.2, 0.3, 0.4, 0.5]
        complexity = _estimate_complexity(sizes, times)
        assert "O(n" in complexity

    def test_estimate_complexity_quadratic(self):
        """Test complexity estimation for quadratic."""
        from src.analysis.performance import _estimate_complexity

        sizes = [10, 20, 30, 40, 50]
        times = [0.1, 0.4, 0.9, 1.6, 2.5]
        complexity = _estimate_complexity(sizes, times)
        assert "O(n" in complexity

    def test_estimate_complexity_constant(self):
        """Test complexity estimation for constant."""
        from src.analysis.performance import _estimate_complexity

        sizes = [10, 20, 30, 40, 50]
        times = [0.1, 0.1, 0.1, 0.1, 0.1]
        complexity = _estimate_complexity(sizes, times)
        assert "O(1)" in complexity

    def test_estimate_complexity_quadratic(self):
        """Test complexity estimation for quadratic O(n^2) (line 202)."""
        from src.analysis.performance import _estimate_complexity

        sizes = [10, 20, 30, 40, 50]
        times = [0.1, 0.4, 0.9, 1.6, 2.5]  # Quadratic: time ~ size^2
        complexity = _estimate_complexity(sizes, times)
        assert "O(n^2)" in complexity

    def test_estimate_complexity_cubic(self):
        """Test complexity estimation for cubic O(n^3) (line 203)."""
        from src.analysis.performance import _estimate_complexity

        sizes = [10, 20, 30, 40, 50]
        times = [0.1, 0.8, 2.7, 6.4, 12.5]  # Cubic: time ~ size^3
        complexity = _estimate_complexity(sizes, times)
        assert "O(n^3)" in complexity

    def test_estimate_complexity_nlogn(self):
        """Test complexity estimation for O(n log n) (line 205)."""
        import numpy as np
        from src.analysis.performance import _estimate_complexity

        sizes = [10, 20, 30, 40, 50]
        # The code checks if exponent is close to np.log(2) ≈ 0.693
        # So we need time ~ size^0.693 to trigger this branch
        times = [s ** np.log(2) / 10 for s in sizes]
        complexity = _estimate_complexity(sizes, times)
        assert "O(n log n)" in complexity

    def test_estimate_complexity_other(self):
        """Test complexity estimation for other exponent (line 207)."""
        from src.analysis.performance import _estimate_complexity

        sizes = [10, 20, 30, 40, 50]
        # Custom exponent (e.g., 1.5)
        times = [s**1.5 / 100 for s in sizes]
        complexity = _estimate_complexity(sizes, times)
        assert "O(n^" in complexity
        assert "1.5" in complexity or "1.50" in complexity

    def test_benchmark_comparison_empty_values(self):
        """Test benchmark comparison with empty values."""
        methods = ["Method A"]
        metrics = {"execution_time": []}
        # Empty values: best_idx becomes 0, so best_method is methods[0]
        comparison = benchmark_comparison(methods, metrics, "execution_time")
        assert comparison["best_value"] is None
        assert (
            comparison["best_method"] == "Method A"
        )  # best_idx=0 when values is empty

    def test_benchmark_comparison_zero_best_value(self):
        """Test benchmark comparison with zero best value."""
        methods = ["Method A", "Method B"]
        metrics = {"execution_time": [0.0, 1.0]}
        comparison = benchmark_comparison(methods, metrics, "execution_time")
        assert comparison["best_method"] == "Method A"
        assert comparison["best_value"] == 0.0
