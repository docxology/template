"""Small code project - numerical optimization utilities.

This project demonstrates a small, fully-tested codebase implementing
basic numerical optimization algorithms with comprehensive testing
and analysis capabilities.
"""

from .optimizer import (
    OptimizationResult,
    compute_gradient,
    gradient_descent,
    make_quadratic_problem,
    quadratic_function,
    simulate_trajectory,
)

__all__ = [
    "quadratic_function",
    "gradient_descent",
    "compute_gradient",
    "make_quadratic_problem",
    "simulate_trajectory",
    "OptimizationResult",
]
