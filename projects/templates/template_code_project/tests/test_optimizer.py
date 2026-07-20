"""Tests for optimizer module.

Comprehensive tests covering functionality, edge cases, and numerical accuracy.

> **Template Exemplar Note**: This module enforces the Zero-Mock policy and targets
> high coverage on `src/` (≥90% gate in `pyproject.toml`; live percentage in
> `docs/_generated/COUNTS.md`).
"""

import functools
import time

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

        with pytest.raises(ValueError, match="step_size must be positive"):
            gradient_descent(np.array([0.0]), dummy_obj, dummy_grad, step_size=np.inf)

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

        with pytest.raises(ValueError, match="tolerance must be positive"):
            gradient_descent(np.array([0.0]), dummy_obj, dummy_grad, tolerance=np.nan)

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

        with pytest.raises(ValueError, match="initial_point must contain only finite values"):
            gradient_descent(np.array([np.nan]), dummy_obj, dummy_grad)

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
        assert results[0.2].iterations < results[0.1].iterations < results[0.01].iterations

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

    def test_zero_gradient_function_converges_immediately(self):
        """If gradient_func returns zero everywhere, converge at iteration 0."""

        def obj_func(x):
            return float(np.sum(x))

        def grad_func(x):
            return np.zeros_like(x)

        result = gradient_descent(
            initial_point=np.array([7.0, -3.0, 0.5]),
            objective_func=obj_func,
            gradient_func=grad_func,
            step_size=0.1,
            tolerance=1e-6,
            max_iterations=100,
        )
        assert result.converged
        assert result.iterations == 0
        # Solution unchanged
        np.testing.assert_allclose(result.solution, [7.0, -3.0, 0.5])
        assert result.gradient_norm == 0.0

    def test_max_iterations_boundary_exactly_one(self):
        """max_iterations=1 runs exactly one update before stopping."""

        def obj_func(x):
            return float(x[0] ** 2)

        def grad_func(x):
            return np.array([2.0 * x[0]])

        result = gradient_descent(
            initial_point=np.array([1.0]),
            objective_func=obj_func,
            gradient_func=grad_func,
            step_size=0.1,
            max_iterations=1,
            tolerance=1e-12,  # unattainable in 1 step
        )
        assert not result.converged
        assert result.iterations == 1
        # x = 1 - 0.1 * 2 * 1 = 0.8 after one update
        np.testing.assert_allclose(result.solution, [0.8])

    def test_nan_gradient_terminates_at_cap(self):
        """A non-finite gradient produces an explicit non-convergent result."""

        def obj_func(x):
            return 0.0

        def grad_func(x):
            return np.array([np.nan])

        result = gradient_descent(
            initial_point=np.array([0.0]),
            objective_func=obj_func,
            gradient_func=grad_func,
            step_size=0.1,
            max_iterations=5,
            tolerance=1e-6,
        )
        assert not result.converged
        assert result.iterations == 0
        assert result.termination_reason == "non_finite"
        assert np.isinf(result.gradient_norm)
        assert np.isfinite(result.solution[0])
        assert result.objective_history == [0.0]

    def test_gradient_shape_mismatch_is_rejected(self):
        """Gradient callbacks must preserve the shape of the optimization state."""

        def obj_func(_x):
            return 0.0

        def grad_func(_x):
            return np.array([0.0, 0.0])

        with pytest.raises(ValueError, match=r"gradient_func must return shape \(1,\), got \(2,\)"):
            gradient_descent(np.array([0.0]), obj_func, grad_func)

    def test_non_finite_objective_stops_before_recording_bad_state(self):
        """An overflowing candidate is not written into the objective history."""

        def obj_func(x):
            return 0.0 if x[0] >= 0.0 else np.inf

        def grad_func(_x):
            return np.array([1.0])

        result = gradient_descent(
            np.array([0.0]),
            obj_func,
            grad_func,
            step_size=2.0,
            max_iterations=5,
        )

        assert result.termination_reason == "non_finite"
        assert result.iterations == 0
        assert result.objective_history == [0.0]
        assert np.isfinite(result.objective_value)

    def test_overflowing_divergence_is_bounded_and_reported(self):
        """Divergence ends at the last finite iterate instead of serializing inf."""
        obj_func, grad_func = make_quadratic_problem(np.array([[1.0]]), np.array([1.0]))

        result = gradient_descent(
            np.array([0.5]),
            obj_func,
            grad_func,
            step_size=2.5,
            max_iterations=1000,
            tolerance=1e-8,
        )

        assert not result.converged
        assert result.termination_reason == "non_finite"
        assert result.iterations < 1000
        assert np.all(np.isfinite(result.solution))
        assert np.isfinite(result.objective_value)
        assert all(np.isfinite(value) for value in result.objective_history or [])

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
        """Benchmark function and gradient evaluation speed.

        Timing tests check that BLAS-backed numpy arithmetic stays under a
        reasonable per-call ceiling for the array sizes a typical quadratic
        problem reaches in this template (n ≤ 1000). The assertion is on
        a bound (`< 0.2s`), not on an exact value, so wall-clock jitter
        on a loaded CI worker is fine. Inputs are seeded for reproducibility
        per Rule 5 of `docs/agent_instructions.md`; the timing properties
        being asserted do not depend on the specific random values.
        """
        rng = np.random.default_rng(seed=20260520)
        sizes = [10, 100, 1000]

        for n in sizes:
            x = rng.standard_normal(n)
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
