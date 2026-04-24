"""Tests for optimizer module.

Comprehensive tests covering functionality, edge cases, and numerical accuracy.

> **Template Exemplar Note**: This module enforces the Zero-Mock policy and targets
> high coverage on `src/` (≥90% gate in `pyproject.toml`; typically ~96% with the
> current suite).
"""

import functools
import json
import time
from pathlib import Path

import numpy as np
import pytest
from src.optimizer import (OptimizationResult, compute_gradient,
                           gradient_descent, make_quadratic_problem,
                           quadratic_function, simulate_trajectory)

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
        _A = np.array([[1.0]])
        _b = np.array([1.0])
        obj_func = functools.partial(quadratic_function, A=_A, b=_b)
        grad_func = functools.partial(compute_gradient, A=_A, b=_b)

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
        """Test that iteration cap is respected when tolerance is tighter than achievable.

        f(x) = x^2, optimum at x=0. With step_size=0.01 and only 10 iterations,
        the contraction factor is |1 - 2*0.01| = 0.98, so after 10 steps
        x ≈ 10 * 0.98^10 ≈ 8.17. The gradient norm (≈16.3) cannot meet 1e-10
        in 10 iterations, so the iteration cap triggers.
        """

        def obj_func(x):
            return x[0] ** 2

        def grad_func(x):
            return np.array([2.0 * x[0]])

        result = gradient_descent(
            initial_point=np.array([10.0]),
            objective_func=obj_func,
            gradient_func=grad_func,
            step_size=0.01,
            max_iterations=10,
            tolerance=1e-10,  # Tight tolerance unreachable in 10 steps
        )

        assert not result.converged
        assert result.iterations == 10
        assert result.solution[0] < 10.0  # Has moved toward optimum

    def test_already_converged(self):
        """Test when starting point is already at optimum."""

        # Optimum of f(x) = (1/2)x^2 - x is x = 1
        _A = np.array([[1.0]])
        _b = np.array([1.0])
        obj_func = functools.partial(quadratic_function, A=_A, b=_b)
        grad_func = functools.partial(compute_gradient, A=_A, b=_b)

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
        obj_func = functools.partial(quadratic_function, A=A, b=b)
        grad_func = functools.partial(compute_gradient, A=A, b=b)

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
        _A = np.array([[1.0]])
        _b = np.array([1.0])
        obj_func = functools.partial(quadratic_function, A=_A, b=_b)
        grad_func = functools.partial(compute_gradient, A=_A, b=_b)

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

        # For this unit-Hessian 1D problem the contraction factor is |1 - α|,
        # so α=0.2 (ρ=0.8) converges faster than α=0.1 (ρ=0.9) faster than α=0.01 (ρ=0.99).
        assert (
            results[0.2].iterations < results[0.1].iterations < results[0.01].iterations
        )

    def test_numerical_stability(self):
        """Test numerical stability with ill-conditioned problems."""
        # Create a well-conditioned but challenging problem
        # f(x) = (1/2) x^T A x - b^T x where A has eigenvalues [0.1, 10]
        A = np.array([[0.1, 0.0], [0.0, 10.0]])
        b = np.array([1.0, 1.0])
        obj_func = functools.partial(quadratic_function, A=A, b=b)
        grad_func = functools.partial(compute_gradient, A=A, b=b)

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

    def test_divergent_step_size(self):
        """Test that a step size exceeding the stability threshold causes non-convergence.

        For f(x) = (1/2)x^2 - x (unit Hessian, H=1), the gradient descent
        contraction factor is |1 - α|. When α > 2 the factor exceeds 1 and
        the iterates diverge. This verifies the algorithm terminates at
        max_iterations rather than looping forever.
        """
        _A = np.array([[1.0]])
        _b = np.array([1.0])
        obj_func = functools.partial(quadratic_function, A=_A, b=_b)
        grad_func = functools.partial(compute_gradient, A=_A, b=_b)

        result = gradient_descent(
            initial_point=np.array([0.5]),
            objective_func=obj_func,
            gradient_func=grad_func,
            step_size=2.5,  # |1 - 2.5| = 1.5 > 1 → diverges
            max_iterations=50,
            tolerance=1e-8,
        )

        assert not result.converged
        assert result.iterations == 50  # Hit the cap
        # Solution has moved away from the optimum (x=1)
        assert abs(result.solution[0] - 1.0) > abs(0.5 - 1.0)

    def test_verbose_logging_does_not_affect_result(self):
        """Test verbose=True path (covers the iteration % 100 log branch)."""
        import functools
        _A = np.array([[1.0]])
        _b = np.array([1.0])
        obj_func = functools.partial(quadratic_function, A=_A, b=_b)
        grad_func = functools.partial(compute_gradient, A=_A, b=_b)

        result = gradient_descent(
            initial_point=np.array([0.0]),
            objective_func=obj_func,
            gradient_func=grad_func,
            step_size=0.5,
            tolerance=1e-6,
            max_iterations=200,
            verbose=True,
        )
        assert result.converged
        assert np.isclose(result.solution[0], 1.0, atol=1e-5)


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

    def test_objective_history_populated(self):
        """Test that gradient_descent populates objective_history correctly.

        objective_history[0] is f(x0) (before any update) and the list grows
        by one entry per iteration, so len(history) == iterations + 1
        (initial value plus one value after each update step).
        """
        _A = np.array([[1.0]])
        _b = np.array([1.0])
        obj_func = functools.partial(quadratic_function, A=_A, b=_b)
        grad_func = functools.partial(compute_gradient, A=_A, b=_b)

        result = gradient_descent(
            initial_point=np.array([0.0]),
            objective_func=obj_func,
            gradient_func=grad_func,
            step_size=0.1,
            max_iterations=20,
            tolerance=1e-8,
        )

        assert result.objective_history is not None
        # History length = iterations taken + 1 (initial value)
        assert len(result.objective_history) == result.iterations + 1
        # First entry is f(x0) = f(0) = 0.5*(0)^2 - 1*0 = 0.0
        assert np.isclose(result.objective_history[0], 0.0)
        # Final entry matches reported objective_value
        assert np.isclose(result.objective_history[-1], result.objective_value)


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

            # Function evaluation should be fast (< 200ms for reasonable sizes)
            assert func_time < 0.2
            # Gradient evaluation should also be fast
            assert grad_time < 0.2


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
            pytest.fail("Stability analysis returned None")

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
                pytest.fail("Stability visualization returned None")
        else:
            pytest.fail("Stability analysis returned None")


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
            pytest.fail("Performance benchmarking returned None")

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
                pytest.fail("Performance visualization returned None")
        else:
            pytest.fail("Performance benchmarking returned None")


@pytest.mark.skipif(
    not INFRASTRUCTURE_AVAILABLE, reason="Infrastructure modules not available"
)
class TestAnalysisDashboard:
    """Test analysis dashboard generation."""

    def test_dashboard_generation(self, tmp_path):
        """Test that analysis dashboard is generated."""
        # Real OptimizationResult instances (zero-mock policy)
        test_results = {
            0.01: OptimizationResult(
                solution=np.array([0.2]), objective_value=-0.4,
                iterations=100, converged=False, gradient_norm=1e-3,
            ),
            0.05: OptimizationResult(
                solution=np.array([0.8]), objective_value=-0.45,
                iterations=50, converged=False, gradient_norm=5e-4,
            ),
            0.1: OptimizationResult(
                solution=np.array([1.0]), objective_value=-0.5,
                iterations=20, converged=True, gradient_norm=1e-8,
            ),
            0.2: OptimizationResult(
                solution=np.array([1.0]), objective_value=-0.5,
                iterations=10, converged=True, gradient_norm=1e-9,
            ),
        }

        # Generate dashboard
        dashboard_path = generate_analysis_dashboard(test_results)

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
            pytest.fail("Dashboard generation returned None")

    def test_dashboard_with_analysis_data(self, tmp_path):
        """Test dashboard generation with stability and benchmark data."""
        # Real OptimizationResult instances (zero-mock policy)
        test_results = {
            0.01: OptimizationResult(
                solution=np.array([0.2]), objective_value=-0.4,
                iterations=100, converged=False, gradient_norm=1e-3,
            ),
            0.05: OptimizationResult(
                solution=np.array([0.8]), objective_value=-0.45,
                iterations=50, converged=False, gradient_norm=5e-4,
            ),
            0.1: OptimizationResult(
                solution=np.array([1.0]), objective_value=-0.5,
                iterations=20, converged=True, gradient_norm=1e-8,
            ),
            0.2: OptimizationResult(
                solution=np.array([1.0]), objective_value=-0.5,
                iterations=10, converged=True, gradient_norm=1e-9,
            ),
        }

        # Try to get real analysis data
        stability_path = run_stability_analysis()
        benchmark_path = run_performance_benchmarking()

        # Generate dashboard with available data
        dashboard_path = generate_analysis_dashboard(
            test_results, stability_path, benchmark_path
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
            pytest.fail("Dashboard generation with analysis data returned None")


class TestMakeQuadraticProblem:
    """Tests for the make_quadratic_problem factory function."""

    def test_returns_callable_pair(self):
        """Factory returns two callables."""
        obj_func, grad_func = make_quadratic_problem(
            np.array([[1.0]]), np.array([1.0])
        )
        assert callable(obj_func)
        assert callable(grad_func)

    def test_objective_matches_quadratic_function(self):
        """Returned objective matches quadratic_function directly."""
        A, b = np.array([[2.0]]), np.array([1.0])
        obj_func, _ = make_quadratic_problem(A, b)
        x = np.array([0.5])
        assert abs(obj_func(x) - quadratic_function(x, A, b)) < 1e-10

    def test_gradient_matches_compute_gradient(self):
        """Returned gradient matches compute_gradient directly."""
        A, b = np.array([[2.0]]), np.array([1.0])
        _, grad_func = make_quadratic_problem(A, b)
        x = np.array([0.5])
        np.testing.assert_allclose(grad_func(x), compute_gradient(x, A, b))

    def test_factory_usable_with_gradient_descent(self):
        """Factory output passes cleanly into gradient_descent."""
        obj_func, grad_func = make_quadratic_problem(
            np.array([[1.0]]), np.array([1.0])
        )
        result = gradient_descent(
            initial_point=np.array([0.0]),
            objective_func=obj_func,
            gradient_func=grad_func,
            step_size=0.1,
            max_iterations=200,
            tolerance=1e-8,
        )
        assert result.converged
        np.testing.assert_allclose(result.solution, [1.0], atol=1e-5)

    def test_factory_with_default_params(self):
        """Factory with None params uses quadratic_function defaults."""
        obj_func, grad_func = make_quadratic_problem()
        x = np.array([1.0])
        # With A=I, b=ones, f(1) = 0.5 - 1 = -0.5
        assert abs(obj_func(x) - quadratic_function(x)) < 1e-10
        np.testing.assert_allclose(grad_func(x), compute_gradient(x))

    def test_factory_multidimensional(self):
        """Factory works for multi-dimensional problems."""
        A = np.eye(3)
        b = np.ones(3)
        obj_func, grad_func = make_quadratic_problem(A, b)
        x = np.array([0.5, 0.5, 0.5])
        assert abs(obj_func(x) - quadratic_function(x, A, b)) < 1e-10
        np.testing.assert_allclose(grad_func(x), compute_gradient(x, A, b))


class TestSimulateTrajectory:
    """Tests for simulate_trajectory — confirms delegation to gradient_descent."""

    def test_returns_dict_with_expected_keys(self):
        """Output dict has 'iterations' and 'objectives' keys."""
        result = simulate_trajectory(
            step_size=0.1, max_iter=20,
            A=np.array([[1.0]]), b=np.array([1.0])
        )
        assert "iterations" in result
        assert "objectives" in result

    def test_objectives_decrease_toward_optimum(self):
        """Trajectory converges — final objective below initial objective."""
        result = simulate_trajectory(
            step_size=0.1, max_iter=50,
            A=np.array([[1.0]]), b=np.array([1.0])
        )
        assert result["objectives"][-1] < result["objectives"][0]

    def test_iterations_and_objectives_same_length(self):
        """Iterations and objectives lists are parallel (same length)."""
        result = simulate_trajectory(
            step_size=0.05, max_iter=30,
            A=np.array([[1.0]]), b=np.array([1.0])
        )
        assert len(result["iterations"]) == len(result["objectives"])

    def test_iterations_are_sequential(self):
        """Iterations list is 0-based sequential integers."""
        result = simulate_trajectory(
            step_size=0.1, max_iter=10,
            A=np.array([[1.0]]), b=np.array([1.0])
        )
        iterations = result["iterations"]
        assert iterations[0] == 0
        for i in range(1, len(iterations)):
            assert iterations[i] == iterations[i - 1] + 1

    def test_default_params_produce_valid_trajectory(self):
        """Default A, b, initial_point produce a valid trajectory."""
        result = simulate_trajectory(step_size=0.1)
        assert len(result["iterations"]) > 0
        assert len(result["objectives"]) > 0
        assert isinstance(result["objectives"][0], float)
