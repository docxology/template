"""Small code project - numerical optimization utilities.

This project demonstrates a small, fully-tested codebase implementing
basic numerical optimization algorithms with comprehensive testing
and analysis capabilities.
"""
from .optimizer import (
    quadratic_function,
    gradient_descent,
    compute_gradient,
    OptimizationResult,
)

__all__ = [
    "quadratic_function",
    "gradient_descent",
    "compute_gradient",
    "OptimizationResult",
]