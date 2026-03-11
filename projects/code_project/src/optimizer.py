"""Numerical optimization utilities.

Implements gradient descent and supporting utilities. Integrates with
infrastructure.scientific for stability analysis and benchmarking.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class OptimizationResult:
    """Result container from gradient_descent."""

    solution: np.ndarray
    objective_value: float
    iterations: int
    converged: bool
    gradient_norm: float
    objective_history: Optional[list[float]] = None


def quadratic_function(
    x: np.ndarray, A: Optional[np.ndarray] = None, b: Optional[np.ndarray] = None
) -> float:
    """Evaluate f(x) = (1/2) x^T A x - b^T x. A defaults to identity, b to ones."""
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


def compute_gradient(
    x: np.ndarray, A: Optional[np.ndarray] = None, b: Optional[np.ndarray] = None
) -> np.ndarray:
    """Compute ∇f(x) = A x - b for the quadratic objective. A defaults to identity, b to ones."""
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
    verbose: bool = False,
) -> OptimizationResult:
    """Run gradient descent: x_{k+1} = x_k - α ∇f(x_k) until convergence or max_iterations.

    Args:
        initial_point: Starting point (1-D numpy array)
        objective_func: f(x) → float
        gradient_func: ∇f(x) → np.ndarray
        max_iterations: Iteration cap (default: 1000)
        tolerance: Gradient norm convergence threshold (default: 1e-6)
        step_size: Fixed step size α > 0 (default: 0.01)
        verbose: Log progress every 100 iterations (default: False)

    Returns:
        OptimizationResult with solution, objective_value, iterations, converged, gradient_norm

    Raises:
        ValueError: If step_size, max_iterations, or tolerance are non-positive, or
                    if initial_point is not a 1-D array
    """
    # Input validation
    if step_size <= 0:
        raise ValueError(f"step_size must be positive, got {step_size}")
    if max_iterations <= 0:
        raise ValueError(f"max_iterations must be positive, got {max_iterations}")
    if tolerance <= 0:
        raise ValueError(f"tolerance must be positive, got {tolerance}")

    x = np.asarray(initial_point, dtype=float)
    if x.ndim != 1:
        raise ValueError(f"initial_point must be 1-D array, got shape {x.shape}")
    if x.size == 0:
        raise ValueError("initial_point must not be empty")

    iteration = 0
    converged = False
    objective_history = [objective_func(x)]  # Track initial objective value

    logger.debug(f"Starting gradient descent with x0={x}, step_size={step_size}")

    while iteration < max_iterations:
        grad = gradient_func(x)
        grad_norm = np.linalg.norm(grad)

        if verbose and iteration % 100 == 0:
            obj_val = objective_func(x)
            logger.info(f"Iteration {iteration}: x={x}, f(x)={obj_val:.6f}, ||∇f||={grad_norm:.6f}")

        if grad_norm < tolerance:
            converged = True
            logger.debug(f"Converged at iteration {iteration} with ||∇f||={grad_norm:.2e}")
            break

        # Update: x = x - step_size * ∇f(x)
        x = x - step_size * grad
        iteration += 1

        # Track objective value after each update
        objective_history.append(objective_func(x))

    final_obj_value = objective_func(x)
    final_grad_norm = np.linalg.norm(gradient_func(x))

    if converged:
        logger.info(
            f"Gradient descent converged in {iteration} iterations, final f(x)={final_obj_value:.6f}"  # noqa: E501
        )
    else:
        logger.warning(
            f"Gradient descent did not converge within {max_iterations} iterations, final f(x)={final_obj_value:.6f}"  # noqa: E501
        )

    return OptimizationResult(
        solution=x,
        objective_value=final_obj_value,
        iterations=iteration,
        converged=converged,
        gradient_norm=final_grad_norm,
        objective_history=objective_history,
    )


def make_quadratic_problem(
    A: Optional[np.ndarray] = None,
    b: Optional[np.ndarray] = None,
) -> tuple[Callable[[np.ndarray], float], Callable[[np.ndarray], np.ndarray]]:
    """Create paired (objective, gradient) callables for a quadratic problem.

    Returns a tuple of (obj_func, grad_func) parametrized by A and b,
    suitable for passing directly to gradient_descent().

    Args:
        A: Optional symmetric positive definite matrix (default: identity)
        b: Optional target vector (default: vector of ones, same dim as x)

    Returns:
        Tuple of (objective_function, gradient_function)

    Example:
        >>> obj_func, grad_func = make_quadratic_problem(
        ...     np.array([[1.0]]), np.array([1.0])
        ... )
        >>> result = gradient_descent(np.array([0.0]), obj_func, grad_func, step_size=0.1)
    """

    def obj_func(x: np.ndarray) -> float:
        return quadratic_function(x, A, b)

    def grad_func(x: np.ndarray) -> np.ndarray:
        return compute_gradient(x, A, b)

    return obj_func, grad_func


def simulate_trajectory(
    step_size: float,
    max_iter: int = 50,
    A: Optional[np.ndarray] = None,
    b: Optional[np.ndarray] = None,
    initial_point: Optional[np.ndarray] = None,
) -> dict[str, list]:
    """Run gradient descent and return iteration/objective history.

    Uses gradient_descent() from this module — no reimplementation of the
    update loop. Returns a dict with 'iterations' and 'objectives' lists
    for downstream plotting.

    Args:
        step_size: Fixed step size for gradient descent.
        max_iter: Maximum iterations (default: 50).
        A: Optional quadratic coefficient matrix (default: identity).
        b: Optional linear coefficient vector (default: ones).
        initial_point: Starting point (default: [0.0]).

    Returns:
        Dict with keys 'iterations' (list[int]) and 'objectives' (list[float]).

    Example:
        >>> traj = simulate_trajectory(step_size=0.1, max_iter=20,
        ...                           A=np.array([[1.0]]), b=np.array([1.0]))
        >>> print(len(traj['iterations']), len(traj['objectives']))
    """
    if initial_point is None:
        initial_point = np.array([0.0])

    obj_func, grad_func = make_quadratic_problem(A, b)
    result = gradient_descent(
        initial_point=initial_point,
        objective_func=obj_func,
        gradient_func=grad_func,
        step_size=step_size,
        max_iterations=max_iter,
        tolerance=1e-8,
        verbose=False,
    )
    return {
        "iterations": list(range(len(result.objective_history))),
        "objectives": result.objective_history,
    }
