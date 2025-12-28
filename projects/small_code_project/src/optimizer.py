"""Numerical optimization utilities.

This module implements basic optimization algorithms for testing and demonstration.
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class OptimizationResult:
    """Result of an optimization run.

    Attributes:
        solution: Final solution point
        objective_value: Objective function value at solution
        iterations: Number of iterations performed
        converged: Whether convergence criteria were met
        gradient_norm: Final gradient norm
    """
    solution: np.ndarray
    objective_value: float
    iterations: int
    converged: bool
    gradient_norm: float


def quadratic_function(x: np.ndarray, A: Optional[np.ndarray] = None, b: Optional[np.ndarray] = None) -> float:
    """Evaluate quadratic function f(x) = (1/2) x^T A x - b^T x.

    Args:
        x: Input point (n-dimensional vector)
        A: Positive definite matrix (n x n), defaults to identity
        b: Linear term vector (n-dimensional), defaults to ones

    Returns:
        Function value at x

    Raises:
        ValueError: If dimensions don't match
    """
    x = np.asarray(x, dtype=float)
    n = len(x)

    if A is None:
        A = np.eye(n)
    else:
        A = np.asarray(A, dtype=float)
        if A.shape != (n, n):
            raise ValueError(f"A must be {n}x{n}, got {A.shape}")

    if b is None:
        b = np.ones(n)
    else:
        b = np.asarray(b, dtype=float)
        if len(b) != n:
            raise ValueError(f"b must be length {n}, got {len(b)}")

    # f(x) = (1/2) x^T A x - b^T x
    quadratic_term = 0.5 * x.T @ A @ x
    linear_term = b.T @ x

    return quadratic_term - linear_term


def compute_gradient(x: np.ndarray, A: Optional[np.ndarray] = None, b: Optional[np.ndarray] = None) -> np.ndarray:
    """Compute gradient of quadratic function.

    Args:
        x: Input point
        A: Quadratic term matrix
        b: Linear term vector

    Returns:
        Gradient vector at x
    """
    x = np.asarray(x, dtype=float)
    n = len(x)

    if A is None:
        A = np.eye(n)
    else:
        A = np.asarray(A, dtype=float)

    if b is None:
        b = np.ones(n)
    else:
        b = np.asarray(b, dtype=float)

    # ∇f(x) = A x - b
    return A @ x - b


def gradient_descent(
    initial_point: np.ndarray,
    objective_func: Callable[[np.ndarray], float],
    gradient_func: Callable[[np.ndarray], np.ndarray],
    max_iterations: int = 1000,
    tolerance: float = 1e-6,
    step_size: float = 0.01,
    verbose: bool = False
) -> OptimizationResult:
    """Perform gradient descent optimization.

    Args:
        initial_point: Starting point for optimization
        objective_func: Function to minimize
        gradient_func: Gradient function
        max_iterations: Maximum number of iterations
        tolerance: Convergence tolerance for gradient norm
        step_size: Fixed step size for updates
        verbose: Whether to print progress

    Returns:
        OptimizationResult with final solution and statistics
    """
    x = np.asarray(initial_point, dtype=float)
    iteration = 0
    converged = False

    while iteration < max_iterations:
        grad = gradient_func(x)
        grad_norm = np.linalg.norm(grad)

        if verbose and iteration % 100 == 0:
            obj_val = objective_func(x)
            print(f"Iteration {iteration}: x={x}, f(x)={obj_val:.6f}, ||∇f||={grad_norm:.6f}")

        if grad_norm < tolerance:
            converged = True
            break

        # Update: x = x - step_size * ∇f(x)
        x = x - step_size * grad
        iteration += 1

    final_obj_value = objective_func(x)
    final_grad_norm = np.linalg.norm(gradient_func(x))

    return OptimizationResult(
        solution=x,
        objective_value=final_obj_value,
        iterations=iteration,
        converged=converged,
        gradient_norm=final_grad_norm
    )