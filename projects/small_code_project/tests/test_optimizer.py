"""Tests for optimizer module.

Comprehensive tests covering functionality, edge cases, and numerical accuracy.
"""
import numpy as np
import pytest

from src.optimizer import (
    quadratic_function,
    compute_gradient,
    gradient_descent,
    OptimizationResult,
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
            tolerance=1e-6
        )

        # Should converge to x = 1
        assert np.isclose(result.solution[0], 1.0, atol=1e-4)
        assert np.isclose(result.objective_value, -0.5, atol=1e-4)
        assert result.converged
        assert result.gradient_norm < 1e-6

    def test_max_iterations_reached(self):
        """Test behavior when max iterations reached without convergence."""
        def obj_func(x):
            return x[0]**2  # Never converges to zero

        def grad_func(x):
            return np.array([2.0 * x[0]])

        result = gradient_descent(
            initial_point=np.array([10.0]),
            objective_func=obj_func,
            gradient_func=grad_func,
            step_size=0.01,  # Small step size
            max_iterations=10,  # Few iterations
            tolerance=1e-10  # Tight tolerance
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
            tolerance=1e-6
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
            tolerance=1e-6
        )

        expected_solution = np.array([1.0, 1.0])
        np.testing.assert_allclose(result.solution, expected_solution, atol=1e-4)
        assert result.converged
        assert result.gradient_norm < 1e-6


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
            gradient_norm=1e-8
        )

        np.testing.assert_array_equal(result.solution, solution)
        assert result.objective_value == -1.5
        assert result.iterations == 42
        assert result.converged is True
        assert result.gradient_norm == 1e-8