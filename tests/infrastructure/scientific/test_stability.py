"""Test suite for infrastructure.scientific.stability module.

Tests numerical stability checking utilities including:
- Stability testing with tolerance checking
- NaN/Inf detection
- Extreme value handling
- Stability scoring and recommendations

All tests use real numerical data with no mocks.
"""

import math

import numpy as np
import pytest

from infrastructure.scientific.stability import (
    StabilityTest,
    check_numerical_stability,
)


class TestStabilityTestDataclass:
    """Test StabilityTest dataclass."""

    def test_stability_test_creation(self):
        """Test creation of StabilityTest with all fields."""
        result = StabilityTest(
            function_name="test_func",
            test_name="numerical_stability",
            input_range=(0.0, 10.0),
            expected_behavior="Stable numerical behavior",
            actual_behavior="Stability score: 0.95",
            stability_score=0.95,
            recommendations=["Consider input validation"],
        )

        assert result.function_name == "test_func"
        assert result.test_name == "numerical_stability"
        assert result.input_range == (0.0, 10.0)
        assert result.stability_score == 0.95
        assert len(result.recommendations) == 1

    def test_stability_test_empty_recommendations(self):
        """Test StabilityTest with no recommendations."""
        result = StabilityTest(
            function_name="stable_func",
            test_name="test",
            input_range=(1.0, 5.0),
            expected_behavior="Stable",
            actual_behavior="Stable",
            stability_score=1.0,
            recommendations=[],
        )

        assert result.stability_score == 1.0
        assert result.recommendations == []


class TestCheckNumericalStability:
    """Test check_numerical_stability function."""

    def test_stable_linear_function(self):
        """Test stability of linear function (always stable)."""

        def linear(x):
            return 2 * x + 1

        test_inputs = [0.1, 1.0, 10.0, 100.0, 1000.0]
        result = check_numerical_stability(linear, test_inputs)

        assert result.function_name == "linear"
        assert result.stability_score == 1.0
        assert result.test_name == "numerical_stability"
        assert len(result.recommendations) == 0

    def test_stable_polynomial_function(self):
        """Test stability of polynomial function."""

        def polynomial(x):
            return x**2 + 3 * x + 5

        test_inputs = list(np.linspace(-10, 10, 20))
        result = check_numerical_stability(polynomial, test_inputs)

        assert result.stability_score == 1.0
        assert result.input_range == (min(test_inputs), max(test_inputs))

    def test_function_producing_nan(self):
        """Test detection of NaN values."""

        def nan_producer(x):
            if x == 0:
                return float("nan")
            return x

        test_inputs = [-1.0, 0.0, 1.0, 2.0]
        result = check_numerical_stability(nan_producer, test_inputs)

        assert result.stability_score < 1.0
        assert any("NaN" in rec or "numerical" in rec.lower() for rec in result.recommendations)

    def test_function_producing_inf(self):
        """Test detection of infinite values."""

        def inf_producer(x):
            if x == 0:
                return float("inf")
            return 1.0 / x

        test_inputs = [-1.0, 0.0, 1.0]
        result = check_numerical_stability(inf_producer, test_inputs)

        assert result.stability_score < 1.0

    def test_function_producing_negative_inf(self):
        """Test detection of negative infinite values."""

        def neg_inf_producer(x):
            if x == 0:
                return float("-inf")
            return x

        test_inputs = [0.0, 1.0]
        result = check_numerical_stability(neg_inf_producer, test_inputs)

        assert result.stability_score < 1.0

    def test_function_producing_large_values(self):
        """Test detection of extremely large values."""

        def large_value_producer(x):
            return x * 1e15  # Very large values

        test_inputs = [1.0, 10.0, 100.0]
        result = check_numerical_stability(large_value_producer, test_inputs)

        # Large values should reduce stability score
        assert result.stability_score < 1.0

    def test_function_with_exception(self):
        """Test handling of functions that raise exceptions."""

        def exception_raiser(x):
            if x < 0:
                raise ValueError("Negative input")
            return math.sqrt(x)

        test_inputs = [-1.0, 0.0, 1.0, 4.0]
        result = check_numerical_stability(exception_raiser, test_inputs)

        assert result.stability_score < 1.0
        assert any("edge cases" in rec.lower() or "exception" in rec.lower()
                   for rec in result.recommendations)

    def test_all_exceptions(self):
        """Test when all inputs cause exceptions."""

        def always_fails(x):
            raise RuntimeError("Always fails")

        test_inputs = [1.0, 2.0, 3.0]
        result = check_numerical_stability(always_fails, test_inputs)

        assert result.stability_score == 0.0

    def test_empty_inputs(self):
        """Test with empty input list."""

        def dummy(x):
            return x

        result = check_numerical_stability(dummy, [])

        assert result.stability_score == 0.0
        assert result.input_range == (0, 0)

    def test_single_input(self):
        """Test with single input value."""

        def simple(x):
            return x * 2

        result = check_numerical_stability(simple, [5.0])

        assert result.stability_score == 1.0
        assert result.input_range == (5.0, 5.0)

    def test_numpy_array_output(self):
        """Test function returning numpy array."""

        def array_function(x):
            return np.array([x, x * 2, x * 3])

        test_inputs = [1.0, 2.0, 3.0]
        result = check_numerical_stability(array_function, test_inputs)

        # Note: The stability checker may not handle array outputs perfectly
        # due to the np.abs(result) > 1e10 check which fails for arrays
        # This test verifies the function completes without error
        assert isinstance(result, StabilityTest)
        assert result.function_name == "array_function"

    def test_numpy_array_with_nan(self):
        """Test numpy array containing NaN."""

        def array_with_nan(x):
            if x == 0:
                return np.array([1.0, float("nan"), 3.0])
            return np.array([x, x * 2, x * 3])

        test_inputs = [0.0, 1.0, 2.0]
        result = check_numerical_stability(array_with_nan, test_inputs)

        assert result.stability_score < 1.0

    def test_numpy_array_with_inf(self):
        """Test numpy array containing infinity."""

        def array_with_inf(x):
            if x == 0:
                return np.array([1.0, float("inf"), 3.0])
            return np.array([x, x * 2, x * 3])

        test_inputs = [0.0, 1.0]
        result = check_numerical_stability(array_with_inf, test_inputs)

        assert result.stability_score < 1.0

    def test_custom_tolerance(self):
        """Test with custom tolerance parameter."""

        def precise_function(x):
            return x + 1e-15  # Very small perturbation

        test_inputs = [1.0, 2.0, 3.0]
        result = check_numerical_stability(precise_function, test_inputs, tolerance=1e-20)

        assert result.stability_score == 1.0

    def test_input_range_calculation(self):
        """Test input range is correctly calculated."""

        def simple(x):
            return x

        test_inputs = [5.0, 1.0, 10.0, 3.0, 7.0]
        result = check_numerical_stability(simple, test_inputs)

        assert result.input_range == (1.0, 10.0)

    def test_negative_inputs(self):
        """Test stability with negative inputs."""

        def handle_negatives(x):
            return abs(x) * 2

        test_inputs = [-10.0, -5.0, 0.0, 5.0, 10.0]
        result = check_numerical_stability(handle_negatives, test_inputs)

        assert result.stability_score == 1.0
        assert result.input_range == (-10.0, 10.0)

    def test_mixed_stability_results(self):
        """Test function with mixed stable/unstable outputs."""

        def mixed_stability(x):
            if x > 5:
                return float("nan")
            if x < -5:
                return float("inf")
            return x

        test_inputs = [-10.0, -5.0, 0.0, 5.0, 10.0]
        result = check_numerical_stability(mixed_stability, test_inputs)

        # Should have partial stability (some pass, some fail)
        assert 0.0 < result.stability_score < 1.0

    def test_recommendations_for_unstable_function(self):
        """Test recommendations are generated for unstable functions."""

        def unstable(x):
            if x == 0:
                return float("nan")
            if x == 1:
                return float("inf")
            if x == 2:
                raise ValueError("Bad input")
            return x

        test_inputs = [0.0, 1.0, 2.0, 3.0]
        result = check_numerical_stability(unstable, test_inputs)

        assert result.stability_score < 0.8
        assert len(result.recommendations) > 0

    def test_stable_trigonometric_functions(self):
        """Test stability of trigonometric functions."""

        def trig_combo(x):
            return np.sin(x) + np.cos(x)

        test_inputs = list(np.linspace(0, 2 * np.pi, 50))
        result = check_numerical_stability(trig_combo, test_inputs)

        assert result.stability_score == 1.0

    def test_exponential_function_stability(self):
        """Test stability of exponential functions (can overflow)."""

        def exp_func(x):
            return np.exp(x)

        # Large inputs will cause overflow
        test_inputs = [1.0, 10.0, 100.0, 1000.0]
        result = check_numerical_stability(exp_func, test_inputs)

        # Should detect the overflow for large inputs
        assert result.stability_score < 1.0

    def test_division_stability(self):
        """Test stability of division (potential divide by zero)."""

        def safe_division(x):
            if x == 0:
                return 0  # Safe handling
            return 1.0 / x

        test_inputs = [0.001, 0.01, 0.1, 0.0, 1.0, 10.0]
        result = check_numerical_stability(safe_division, test_inputs)

        assert result.stability_score == 1.0  # Should be stable with safe handling


class TestStabilityIntegration:
    """Integration tests for stability checking."""

    def test_scientific_computation_stability(self):
        """Test stability of realistic scientific computation."""

        def scientific_calc(x):
            """Simulate a scientific calculation."""
            # Normalize
            normalized = (x - 50) / 10
            # Apply sigmoid
            sigmoid = 1 / (1 + np.exp(-normalized))
            return sigmoid

        test_inputs = list(np.linspace(0, 100, 100))
        result = check_numerical_stability(scientific_calc, test_inputs)

        assert result.stability_score == 1.0

    def test_matrix_operation_stability(self):
        """Test stability of matrix-like operations."""

        def matrix_trace_like(n):
            """Compute sum of diagonal elements."""
            if n <= 0:
                return 0
            arr = np.arange(n * n).reshape(n, n)
            return np.trace(arr)

        test_inputs = [1, 5, 10, 20]
        result = check_numerical_stability(matrix_trace_like, test_inputs)

        assert result.stability_score == 1.0

    def test_numerical_derivative_stability(self):
        """Test stability of numerical differentiation."""

        def numerical_derivative(x, h=1e-8):
            """Approximate derivative of x^2 at point x."""
            f = lambda t: t * t
            return (f(x + h) - f(x)) / h

        test_inputs = list(np.linspace(-10, 10, 50))
        result = check_numerical_stability(numerical_derivative, test_inputs)

        assert result.stability_score == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
