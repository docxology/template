"""Tests for optimizer module.

Comprehensive tests covering functionality, edge cases, and numerical accuracy.

> **Template Exemplar Note**: This module enforces the Zero-Mock policy and targets
> high coverage on `src/` (≥90% gate in `pyproject.toml`; live percentage in
> `docs/_generated/COUNTS.md`).
"""

import functools
import numpy as np
import pytest
from src.optimizer import (
    OptimizationResult,
    compute_gradient,
    gradient_descent,
    make_quadratic_problem,
    quadratic_function,
    quadratic_optimum,
    simulate_trajectory,
)


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

    def test_non_vector_input_is_rejected(self):
        """Quadratic helpers require a one-dimensional optimization state."""
        with pytest.raises(ValueError, match="x must be a 1-D array"):
            quadratic_function(np.array([[1.0]]))

    def test_non_vector_b_is_rejected(self):
        """The linear term must be a vector, not a nested array."""
        with pytest.raises(ValueError, match="b must be length 1"):
            quadratic_function(np.array([1.0]), b=np.array([[1.0]]))

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


class TestQuadraticOptimum:
    """Tests for closed-form quadratic optimum."""

    def test_default_1d_optimum(self):
        A = np.array([[1.0]])
        b = np.array([1.0])
        x_star, f_star = quadratic_optimum(A, b)
        np.testing.assert_allclose(x_star, [1.0])
        assert np.isclose(f_star, -0.5)

    def test_non_default_optimum(self):
        A = np.array([[2.0]])
        b = np.array([4.0])
        x_star, f_star = quadratic_optimum(A, b)
        np.testing.assert_allclose(x_star, [2.0])
        assert f_star < 0


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

    def test_zero_input(self):
        """Gradient at x=0 with defaults equals -b = -1."""
        x = np.array([0.0])
        grad = compute_gradient(x)
        np.testing.assert_allclose(grad, np.array([-1.0]))

    def test_negative_input(self):
        """Gradient at x=-3 with defaults: A x - b = -3 - 1 = -4."""
        x = np.array([-3.0])
        grad = compute_gradient(x)
        np.testing.assert_allclose(grad, np.array([-4.0]))

    def test_dimension_mismatch_A(self):
        """Mismatched A shape raises ValueError via compute_gradient."""
        x = np.array([1.0, 2.0])
        A = np.array([[1.0]])  # Wrong size
        with pytest.raises(ValueError, match="A must be 2x2"):
            compute_gradient(x, A)

    def test_dimension_mismatch_b(self):
        """Mismatched b length raises ValueError via compute_gradient."""
        x = np.array([1.0, 2.0])
        b = np.array([1.0])  # Wrong size
        with pytest.raises(ValueError, match="b must be length 2"):
            compute_gradient(x, b=b)

    def test_nan_input_propagates(self):
        """NaN in x propagates to gradient (no silent masking)."""
        x = np.array([np.nan])
        grad = compute_gradient(x)
        # ∇f(NaN) = NaN - 1 = NaN; verify the algorithm does not silently
        # zero or filter NaN — the caller is responsible for sanitising input.
        assert np.isnan(grad).all()

    def test_inf_input_propagates(self):
        """+inf in x produces +inf gradient component."""
        x = np.array([np.inf])
        grad = compute_gradient(x)
        assert np.isinf(grad).all()
        assert grad[0] > 0  # +inf - 1 = +inf

    def test_quadratic_function_nan_input_propagates(self):
        """f(NaN) returns NaN — sanitisation is the caller's responsibility."""
        x = np.array([np.nan])
        result = quadratic_function(x)
        assert np.isnan(result)


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


class TestMakeQuadraticProblem:
    """Tests for the make_quadratic_problem factory function."""

    def test_returns_callable_pair(self):
        """Factory returns two callables."""
        obj_func, grad_func = make_quadratic_problem(np.array([[1.0]]), np.array([1.0]))
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
        obj_func, grad_func = make_quadratic_problem(np.array([[1.0]]), np.array([1.0]))
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
        result = simulate_trajectory(step_size=0.1, max_iter=20, A=np.array([[1.0]]), b=np.array([1.0]))
        assert "iterations" in result
        assert "objectives" in result

    def test_objectives_decrease_toward_optimum(self):
        """Trajectory converges — final objective below initial objective."""
        result = simulate_trajectory(step_size=0.1, max_iter=50, A=np.array([[1.0]]), b=np.array([1.0]))
        assert result["objectives"][-1] < result["objectives"][0]

    def test_iterations_and_objectives_same_length(self):
        """Iterations and objectives lists are parallel (same length)."""
        result = simulate_trajectory(step_size=0.05, max_iter=30, A=np.array([[1.0]]), b=np.array([1.0]))
        assert len(result["iterations"]) == len(result["objectives"])

    def test_iterations_are_sequential(self):
        """Iterations list is 0-based sequential integers."""
        result = simulate_trajectory(step_size=0.1, max_iter=10, A=np.array([[1.0]]), b=np.array([1.0]))
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
