"""Comprehensive tests for the example module to ensure 100% coverage."""

import pytest
from src.core.example import (add_numbers, calculate_average, find_maximum,
                     find_minimum, is_even, is_odd, multiply_numbers)


class TestBasicOperations:
    """Test basic arithmetic operations."""

    def test_add_numbers(self):
        """Test addition of numbers."""
        assert add_numbers(2, 3) == 5
        assert add_numbers(-1, 1) == 0
        assert add_numbers(0, 0) == 0
        assert add_numbers(1.5, 2.5) == 4.0

    def test_multiply_numbers(self):
        """Test multiplication of numbers."""
        assert multiply_numbers(2, 3) == 6
        assert multiply_numbers(-2, 3) == -6
        assert multiply_numbers(0, 5) == 0
        assert multiply_numbers(1.5, 2.0) == 3.0


class TestListOperations:
    """Test operations on lists of numbers."""

    def test_calculate_average(self):
        """Test average calculation."""
        assert calculate_average([1, 2, 3, 4, 5]) == 3.0
        assert calculate_average([0, 0, 0]) == 0.0
        assert calculate_average([1.5, 2.5]) == 2.0
        assert calculate_average([]) is None

    def test_find_maximum(self):
        """Test maximum finding."""
        assert find_maximum([1, 2, 3, 4, 5]) == 5
        assert find_maximum([-5, -3, -1]) == -1
        assert find_maximum([0]) == 0
        assert find_maximum([]) is None

    def test_find_minimum(self):
        """Test minimum finding."""
        assert find_minimum([1, 2, 3, 4, 5]) == 1
        assert find_minimum([-5, -3, -1]) == -5
        assert find_minimum([0]) == 0
        assert find_minimum([]) is None


class TestNumberProperties:
    """Test even/odd number detection."""

    def test_is_even(self):
        """Test even number detection."""
        assert is_even(0) is True
        assert is_even(2) is True
        assert is_even(-2) is True
        assert is_even(1) is False
        assert is_even(-1) is False

    def test_is_odd(self):
        """Test odd number detection."""
        assert is_odd(1) is True
        assert is_odd(-1) is True
        assert is_odd(0) is False
        assert is_odd(2) is False
        assert is_odd(-2) is False


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_lists(self):
        """Test operations on empty lists."""
        assert calculate_average([]) is None
        assert find_maximum([]) is None
        assert find_minimum([]) is None

    def test_single_element_lists(self):
        """Test operations on single-element lists."""
        assert calculate_average([42]) == 42.0
        assert find_maximum([42]) == 42
        assert find_minimum([42]) == 42

    def test_negative_numbers(self):
        """Test operations with negative numbers."""
        assert add_numbers(-5, -3) == -8
        assert multiply_numbers(-2, -3) == 6
        assert calculate_average([-1, -2, -3]) == -2.0
        assert find_maximum([-1, -2, -3]) == -1
        assert find_minimum([-1, -2, -3]) == -3

    def test_zero_values(self):
        """Test operations with zero values."""
        assert add_numbers(0, 0) == 0
        assert multiply_numbers(0, 5) == 0
        assert calculate_average([0, 0, 0]) == 0.0
        assert find_maximum([0, 0, 0]) == 0
        assert find_minimum([0, 0, 0]) == 0


class TestFloatPrecision:
    """Test floating point precision handling."""

    def test_float_operations(self):
        """Test operations with floating point numbers."""
        assert add_numbers(0.1, 0.2) == pytest.approx(0.3, rel=1e-10)
        assert multiply_numbers(0.1, 0.2) == pytest.approx(0.02, rel=1e-10)
        assert calculate_average([0.1, 0.2, 0.3]) == pytest.approx(0.2, rel=1e-10)


if __name__ == "__main__":
    pytest.main([__file__])
