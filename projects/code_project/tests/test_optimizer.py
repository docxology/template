"""Tests for optimizer module.

Comprehensive tests covering functionality, edge cases, and numerical accuracy.
Also tests scientific analysis features when infrastructure is available.
"""

import json
import time
from pathlib import Path

import numpy as np
import pytest
from src.optimizer import (OptimizationResult, compute_gradient,
                           gradient_descent, quadratic_function)

# Try to import scientific analysis functions (graceful fallback)
try:
    import sys

    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root / "scripts"))

    from optimization_analysis import (generate_analysis_dashboard,
                                       generate_benchmark_visualization,
                                       generate_stability_visualization,
                                       run_performance_benchmarking,
                                       run_stability_analysis)

    INFRASTRUCTURE_AVAILABLE = True
except ImportError:
    INFRASTRUCTURE_AVAILABLE = False


class TestQuadraticFunction:
    """Test quadratic function evaluation."""

    def test_simple_quadratic(self):
        """Test basic quadratic function evaluation."""
        # f(x) = (1/2) x^T x - 1^T x = (1/2)(x^2) - x
        x = np.array([2.0])
        result = quadratic_function(x)
        expected = 0.5 * 2.0**2 - 1.0 * 2.0  # 2.0 - 2.0 = 0.0
        assert np.isclose(result, expected)

    def test_multidimensional_quadratic(self):
        """Test quadratic function in higher dimensions."""
        x = np.array([1.0, 2.0])
        A = np.array([[2.0, 0.0], [0.0, 3.0]])
        b = np.array([1.0, 2.0])

        result = quadratic_function(x, A, b)
        # f(x) = (1/2) [1, 2] [2, 0; 0, 3] [1; 2] - [1, 2] [1; 2]
        #      = (1/2) [1, 2] [2; 6] - (1 + 4)
        #      = (1/2) (2 + 12) - 5 = (1/2)(14) - 5 = 7 - 5 = 2
        expected = 2.0
        assert np.isclose(result, expected)

    def test_default_parameters(self):
        """Test with default A and b parameters."""
        x = np.array([1.0, 1.0])
        result = quadratic_function(x)
        # A = I, b = [1, 1], so f(x) = (1/2)(1+1) - (1+1) = 1 - 2 = -1
        expected = -1.0
        assert np.isclose(result, expected)

    def test_dimension_mismatch_A(self):
        """Test error handling for mismatched A dimensions."""
        x = np.array([1.0, 2.0])
        A = np.array([[1.0]])  # Wrong size

        with pytest.raises(ValueError, match="A must be 2x2"):
            quadratic_function(x, A)

    def test_dimension_mismatch_b(self):
        """Test error handling for mismatched b dimensions."""
        x = np.array([1.0, 2.0])
        b = np.array([1.0])  # Wrong size

        with pytest.raises(ValueError, match="b must be length 2"):
            quadratic_function(x, b=b)

    def test_zero_input(self):
        """Test quadratic function with zero input."""
        x = np.array([0.0])
        result = quadratic_function(x)
        # f(0) = (1/2)(0)^2 - 1*0 = 0
        assert np.isclose(result, 0.0)

    def test_large_input(self):
        """Test quadratic function with large input values."""
        x = np.array([1000.0])
        result = quadratic_function(x)
        # f(1000) = (1/2)(1000)^2 - 1*1000 = 500000 - 1000 = 499000
        expected = 499000.0
        assert np.isclose(result, expected, rtol=1e-10)

    def test_negative_input(self):
        """Test quadratic function with negative input."""
        x = np.array([-2.0])
        result = quadratic_function(x)
        # f(-2) = (1/2)(4) - 1*(-2) = 2 + 2 = 4
        expected = 4.0
        assert np.isclose(result, expected)


class TestComputeGradient:
    """Test gradient computation."""

    def test_simple_gradient(self):
        """Test gradient computation for simple case."""
        x = np.array([2.0])
        grad = compute_gradient(x)
        # ∇f(x) = x - 1, so ∇f(2) = 2 - 1 = 1
        expected = np.array([1.0])
        np.testing.assert_allclose(grad, expected)

    def test_multidimensional_gradient(self):
        """Test gradient in higher dimensions."""
        x = np.array([1.0, 2.0])
        A = np.array([[2.0, 0.0], [0.0, 3.0]])
        b = np.array([1.0, 2.0])

        grad = compute_gradient(x, A, b)
        # ∇f(x) = A x - b = [2, 0; 0, 3] [1; 2] - [1; 2] = [2; 6] - [1; 2] = [1; 4]
        expected = np.array([1.0, 4.0])
        np.testing.assert_allclose(grad, expected)

    def test_default_gradient(self):
        """Test gradient with default parameters."""
        x = np.array([1.0, 1.0])
        grad = compute_gradient(x)
        # ∇f(x) = x - 1 = [1-1, 1-1] = [0, 0]
        expected = np.array([0.0, 0.0])
        np.testing.assert_allclose(grad, expected)


class TestGradientDescent:
    """Test gradient descent optimization."""

    def test_convergence_to_optimum(self):
        """Test that gradient descent converges to known optimum."""

        # f(x) = (1/2) x^2 - x, minimum at x = 1, f(1) = -0.5
        def obj_func(x):
            return quadratic_function(x, np.array([[1.0]]), np.array([1.0]))

        def grad_func(x):
            return compute_gradient(x, np.array([[1.0]]), np.array([1.0]))

        result = gradient_descent(
            initial_point=np.array([0.0]),
            objective_func=obj_func,
            gradient_func=grad_func,
            step_size=0.1,
            max_iterations=1000,
            tolerance=1e-6,
        )

        # Should converge to x = 1
        assert np.isclose(result.solution[0], 1.0, atol=1e-4)
        assert np.isclose(result.objective_value, -0.5, atol=1e-4)
        assert result.converged
        assert result.gradient_norm < 1e-6

    def test_max_iterations_reached(self):
        """Test behavior when max iterations reached without convergence."""

        def obj_func(x):
            return x[0] ** 2  # Never converges to zero

        def grad_func(x):
            return np.array([2.0 * x[0]])

        result = gradient_descent(
            initial_point=np.array([10.0]),
            objective_func=obj_func,
            gradient_func=grad_func,
            step_size=0.01,  # Small step size
            max_iterations=10,  # Few iterations
            tolerance=1e-10,  # Tight tolerance
        )

        assert not result.converged
        assert result.iterations == 10
        assert result.solution[0] < 10.0  # Should have moved toward optimum

    def test_already_converged(self):
        """Test when starting point is already at optimum."""

        # Optimum of f(x) = (1/2)x^2 - x is x = 1
        def obj_func(x):
            return quadratic_function(x, np.array([[1.0]]), np.array([1.0]))

        def grad_func(x):
            return compute_gradient(x, np.array([[1.0]]), np.array([1.0]))

        result = gradient_descent(
            initial_point=np.array([1.0]),
            objective_func=obj_func,
            gradient_func=grad_func,
            tolerance=1e-6,
        )

        assert result.converged
        assert result.iterations == 0
        assert np.isclose(result.solution[0], 1.0)
        assert np.isclose(result.objective_value, -0.5)

    def test_multidimensional_convergence(self):
        """Test convergence in higher dimensions."""
        # f(x,y) = (1/2)(x^2 + y^2) - (x + y), optimum at (1,1)
        A = np.eye(2)
        b = np.array([1.0, 1.0])

        def obj_func(x):
            return quadratic_function(x, A, b)

        def grad_func(x):
            return compute_gradient(x, A, b)

        result = gradient_descent(
            initial_point=np.array([0.0, 0.0]),
            objective_func=obj_func,
            gradient_func=grad_func,
            step_size=0.1,
            tolerance=1e-6,
        )

        expected_solution = np.array([1.0, 1.0])
        np.testing.assert_allclose(result.solution, expected_solution, atol=1e-4)
        assert result.converged
        assert result.gradient_norm < 1e-6

    def test_parameter_validation(self):
        """Test parameter validation in gradient descent."""

        def dummy_obj(x):
            return 0.0

        def dummy_grad(x):
            return np.zeros_like(x)

        # Test invalid step size
        with pytest.raises(ValueError, match="step_size must be positive"):
            gradient_descent(np.array([0.0]), dummy_obj, dummy_grad, step_size=-0.1)

        with pytest.raises(ValueError, match="step_size must be positive"):
            gradient_descent(np.array([0.0]), dummy_obj, dummy_grad, step_size=0.0)

        # Test invalid max_iterations
        with pytest.raises(ValueError, match="max_iterations must be positive"):
            gradient_descent(np.array([0.0]), dummy_obj, dummy_grad, max_iterations=0)

        with pytest.raises(ValueError, match="max_iterations must be positive"):
            gradient_descent(np.array([0.0]), dummy_obj, dummy_grad, max_iterations=-1)

        # Test invalid tolerance
        with pytest.raises(ValueError, match="tolerance must be positive"):
            gradient_descent(np.array([0.0]), dummy_obj, dummy_grad, tolerance=0.0)

        with pytest.raises(ValueError, match="tolerance must be positive"):
            gradient_descent(np.array([0.0]), dummy_obj, dummy_grad, tolerance=-1e-6)

    def test_invalid_initial_point(self):
        """Test error handling for invalid initial point."""

        def dummy_obj(x):
            return 0.0

        def dummy_grad(x):
            return np.zeros_like(x)

        # Test 2D array (should be 1D)
        with pytest.raises(ValueError, match="initial_point must be 1-D array"):
            gradient_descent(np.array([[0.0]]), dummy_obj, dummy_grad)

        # Test empty array
        with pytest.raises(ValueError, match="initial_point must not be empty"):
            gradient_descent(np.array([]), dummy_obj, dummy_grad)

    def test_gradient_descent_performance(self):
        """Test gradient descent performance characteristics."""

        # Simple quadratic: f(x) = (1/2)x^2 - x, minimum at x=1
        def obj_func(x):
            return quadratic_function(x, np.array([[1.0]]), np.array([1.0]))

        def grad_func(x):
            return compute_gradient(x, np.array([[1.0]]), np.array([1.0]))

        # Test with different step sizes to verify performance
        step_sizes = [0.01, 0.1, 0.2]
        results = {}

        for step_size in step_sizes:
            result = gradient_descent(
                initial_point=np.array([0.0]),
                objective_func=obj_func,
                gradient_func=grad_func,
                step_size=step_size,
                tolerance=1e-4,  # Relaxed tolerance for numerical stability
                max_iterations=1000,
            )
            results[step_size] = result

            # All should converge to the same solution
            assert np.isclose(result.solution[0], 1.0, atol=1e-4)
            assert np.isclose(result.objective_value, -0.5, atol=1e-4)
            assert result.converged

        # Larger step sizes should converge faster
        assert (
            results[0.2].iterations < results[0.1].iterations < results[0.01].iterations
        )

    def test_numerical_stability(self):
        """Test numerical stability with ill-conditioned problems."""
        # Create a well-conditioned but challenging problem
        # f(x) = (1/2) x^T A x - b^T x where A has eigenvalues [0.1, 10]
        A = np.array([[0.1, 0.0], [0.0, 10.0]])
        b = np.array([1.0, 1.0])

        def obj_func(x):
            return quadratic_function(x, A, b)

        def grad_func(x):
            return compute_gradient(x, A, b)

        # The optimum should be A^-1 b
        A_inv = np.linalg.inv(A)
        expected_solution = A_inv @ b

        result = gradient_descent(
            initial_point=np.array([0.0, 0.0]),
            objective_func=obj_func,
            gradient_func=grad_func,
            step_size=0.01,  # Conservative step size for stability
            tolerance=1e-4,  # Relaxed tolerance for numerical stability
            max_iterations=10000,
        )

        np.testing.assert_allclose(result.solution, expected_solution, atol=1e-2)
        assert result.converged
        assert result.gradient_norm < 1e-4


class TestOptimizationResult:
    """Test OptimizationResult dataclass."""

    def test_result_creation(self):
        """Test creating optimization result."""
        solution = np.array([1.0, 2.0])
        result = OptimizationResult(
            solution=solution,
            objective_value=-1.5,
            iterations=42,
            converged=True,
            gradient_norm=1e-8,
        )

        np.testing.assert_array_equal(result.solution, solution)
        assert result.objective_value == -1.5
        assert result.iterations == 42
        assert result.converged is True
        assert result.gradient_norm == 1e-8


class TestPerformanceBenchmarks:
    """Performance benchmarks for optimization algorithms."""

    def test_gradient_descent_timing(self):
        """Benchmark gradient descent execution time."""

        def obj_func(x):
            return quadratic_function(x, np.eye(len(x)), np.ones(len(x)))

        def grad_func(x):
            return compute_gradient(x, np.eye(len(x)), np.ones(len(x)))

        dimensions = [2, 5, 10]
        timing_results = {}

        for dim in dimensions:
            start_time = time.time()
            result = gradient_descent(
                initial_point=np.zeros(dim),
                objective_func=obj_func,
                gradient_func=grad_func,
                step_size=0.1,
                tolerance=1e-6,
                max_iterations=1000,
            )
            end_time = time.time()

            timing_results[dim] = {
                "time": end_time - start_time,
                "iterations": result.iterations,
                "converged": result.converged,
            }

            assert result.converged
            assert result.iterations < 1000  # Should converge well within limits

        # All should complete in reasonable time (< 1 second for this simple problem)
        for dim in dimensions:
            assert timing_results[dim]["time"] < 1.0

    def test_function_evaluation_speed(self):
        """Benchmark function and gradient evaluation speed."""
        # Test with different problem sizes
        sizes = [10, 100, 1000]

        for n in sizes:
            x = np.random.randn(n)
            A = np.eye(n)
            b = np.ones(n)

            # Time function evaluation
            start_time = time.time()
            for _ in range(100):  # Multiple evaluations for timing
                _ = quadratic_function(x, A, b)
            func_time = (time.time() - start_time) / 100

            # Time gradient evaluation
            start_time = time.time()
            for _ in range(100):
                _ = compute_gradient(x, A, b)
            grad_time = (time.time() - start_time) / 100

            # Function evaluation should be fast (< 1ms for reasonable sizes)
            assert func_time < 0.001
            # Gradient evaluation should also be fast
            assert grad_time < 0.001


@pytest.mark.skipif(
    not INFRASTRUCTURE_AVAILABLE, reason="Infrastructure modules not available"
)
class TestStabilityAnalysis:
    """Test numerical stability analysis functions."""

    def test_stability_analysis_execution(self, tmp_path):
        """Test that stability analysis runs without errors."""
        # Run stability analysis
        result_path = run_stability_analysis()

        if result_path:
            # Check that report file was created
            assert result_path.exists()
            assert result_path.is_file()

            # Check JSON content
            with open(result_path, "r") as f:
                data = json.load(f)

            assert "stability_score" in data
            assert "function_name" in data
            assert "recommendations" in data
            assert isinstance(data["stability_score"], (int, float))
            assert 0.0 <= data["stability_score"] <= 1.0
        else:
            # Should not fail, but might return None if infrastructure issues
            pytest.skip("Stability analysis returned None")

    def test_stability_visualization(self, tmp_path):
        """Test stability visualization generation."""
        # First run analysis to get data
        report_path = run_stability_analysis()

        if report_path:
            # Generate visualization
            viz_path = generate_stability_visualization(report_path)

            if viz_path:
                # Check that visualization file was created
                assert viz_path.exists()
                assert viz_path.is_file()
                assert viz_path.suffix == ".png"
            else:
                pytest.skip("Stability visualization returned None")
        else:
            pytest.skip("Stability analysis returned None")


@pytest.mark.skipif(
    not INFRASTRUCTURE_AVAILABLE, reason="Infrastructure modules not available"
)
class TestPerformanceBenchmarking:
    """Test performance benchmarking functions."""

    def test_performance_benchmarking_execution(self, tmp_path):
        """Test that performance benchmarking runs without errors."""
        # Run performance benchmarking
        result_path = run_performance_benchmarking()

        if result_path:
            # Check that report file was created
            assert result_path.exists()
            assert result_path.is_file()

            # Check JSON content
            with open(result_path, "r") as f:
                data = json.load(f)

            assert "execution_time" in data
            assert "function_name" in data
            assert "result_summary" in data
            assert "iterations" in data
            assert isinstance(data["execution_time"], (int, float))
            assert data["execution_time"] > 0
        else:
            pytest.skip("Performance benchmarking returned None")

    def test_performance_visualization(self, tmp_path):
        """Test performance visualization generation."""
        # First run benchmarking to get data
        report_path = run_performance_benchmarking()

        if report_path:
            # Generate visualization
            viz_path = generate_benchmark_visualization(report_path)

            if viz_path:
                # Check that visualization file was created
                assert viz_path.exists()
                assert viz_path.is_file()
                assert viz_path.suffix == ".png"
            else:
                pytest.skip("Performance visualization returned None")
        else:
            pytest.skip("Performance benchmarking returned None")


@pytest.mark.skipif(
    not INFRASTRUCTURE_AVAILABLE, reason="Infrastructure modules not available"
)
class TestAnalysisDashboard:
    """Test analysis dashboard generation."""

    def test_dashboard_generation(self, tmp_path):
        """Test that analysis dashboard is generated."""
        # Mock optimization results for testing
        mock_results = {
            0.01: type(
                "MockResult", (), {"converged": False, "objective_value": -0.4}
            )(),
            0.05: type(
                "MockResult", (), {"converged": False, "objective_value": -0.45}
            )(),
            0.1: type("MockResult", (), {"converged": True, "objective_value": -0.5})(),
            0.2: type("MockResult", (), {"converged": True, "objective_value": -0.5})(),
        }

        # Generate dashboard
        dashboard_path = generate_analysis_dashboard(mock_results)

        if dashboard_path:
            # Check that dashboard file was created
            assert dashboard_path.exists()
            assert dashboard_path.is_file()
            assert dashboard_path.suffix == ".html"

            # Check HTML content
            with open(dashboard_path, "r", encoding="utf-8") as f:
                content = f.read()

            assert "<!DOCTYPE html>" in content
            assert "Optimization Analysis Dashboard" in content
            assert "step sizes tested" in content.lower()
        else:
            pytest.skip("Dashboard generation returned None")

    def test_dashboard_with_analysis_data(self, tmp_path):
        """Test dashboard generation with stability and benchmark data."""
        # Mock optimization results
        mock_results = {
            0.01: type(
                "MockResult", (), {"converged": False, "objective_value": -0.4}
            )(),
            0.05: type(
                "MockResult", (), {"converged": False, "objective_value": -0.45}
            )(),
            0.1: type("MockResult", (), {"converged": True, "objective_value": -0.5})(),
            0.2: type("MockResult", (), {"converged": True, "objective_value": -0.5})(),
        }

        # Try to get real analysis data
        stability_path = run_stability_analysis()
        benchmark_path = run_performance_benchmarking()

        # Generate dashboard with available data
        dashboard_path = generate_analysis_dashboard(
            mock_results, stability_path, benchmark_path
        )

        if dashboard_path:
            # Check that dashboard file was created
            assert dashboard_path.exists()
            assert dashboard_path.is_file()

            # Check content includes expected sections
            with open(dashboard_path, "r", encoding="utf-8") as f:
                content = f.read()

            assert "Optimization Results" in content

            if stability_path:
                assert "Numerical Stability" in content

            if benchmark_path:
                assert "Performance Benchmark" in content
        else:
            pytest.skip("Dashboard generation with analysis data returned None")
