"""Numerical optimization utilities.

This module implements basic optimization algorithms for testing and demonstration.
Integrates with infrastructure modules for comprehensive analysis:

- **Logging**: Uses infrastructure.core.logging_utils for structured logging
- **Stability Analysis**: Compatible with infrastructure.scientific.check_numerical_stability
- **Benchmarking**: Compatible with infrastructure.scientific.benchmark_function
- **Validation**: Results can be validated using infrastructure.validation modules

Example infrastructure integration:
    ```python
    from infrastructure.scientific import check_numerical_stability, benchmark_function
    from infrastructure.core.logging_utils import get_logger

    # Create logger for structured output
    logger = get_logger(__name__)

    # Run optimization
    result = gradient_descent(initial_point, objective_func, gradient_func)

    # Analyze numerical stability
    stability = check_numerical_stability(
        func=objective_func,
        test_inputs=[initial_point, result.solution]
    )

    # Benchmark performance
    benchmark = benchmark_function(
        func=lambda x: gradient_descent(x, objective_func, gradient_func).iterations,
        test_inputs=[initial_point]
    )

    logger.info(f"Stability score: {stability['overall_stable']}")
    logger.info(f"Benchmark: {benchmark['mean_time']:.4f}s avg")
    ```
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np

# Add logging support
try:
    from infrastructure.core.logging_utils import get_logger

    logger = get_logger(__name__)
    LOGGING_AVAILABLE = True
except ImportError:
    LOGGING_AVAILABLE = False


@dataclass
class OptimizationResult:
    """Container for optimization algorithm results.

    This dataclass encapsulates the complete output of an optimization run,
    providing both the solution and convergence diagnostics.

    Attributes:
        solution: Final solution point as numpy array
        objective_value: Objective function value at the solution
        iterations: Number of iterations performed (0-based, so max_iterations means failure to converge)
        converged: True if gradient norm fell below tolerance, False if max iterations reached
        gradient_norm: Final L2 norm of the gradient vector
        objective_history: List of objective function values during optimization (optional)

    Example:
        >>> result = gradient_descent(initial_point, objective, gradient)
        >>> if result.converged:
        ...     print(f"Converged in {result.iterations} iterations")
        ...     print(f"Solution: {result.solution}")
        ...     print(f"Objective: {result.objective_value:.6f}")
        ...     if result.objective_history:
        ...         print(f"Initial objective: {result.objective_history[0]:.6f}")
    """

    solution: np.ndarray
    objective_value: float
    iterations: int
    converged: bool
    gradient_norm: float
    objective_history: Optional[list[float]] = None


def quadratic_function(
    x: np.ndarray, A: Optional[np.ndarray] = None, b: Optional[np.ndarray] = None
) -> float:
    """Evaluate quadratic objective function f(x) = (1/2) x^T A x - b^T x.

    This function implements a general quadratic minimization problem where A is the
    quadratic coefficient matrix and b defines the linear term. The function is convex
    when A is positive definite.

    Args:
        x: Input point as numpy array (n-dimensional vector). Must be 1-D array.
        A: Symmetric positive definite matrix (n x n). Defaults to identity matrix.
            Must be square and same dimension as x.
        b: Linear coefficient vector (n-dimensional). Defaults to vector of ones.
            Must have same length as x.

    Returns:
        Function value as float: f(x) = 0.5 * x^T A x - b^T x

    Raises:
        ValueError: If array dimensions are incompatible
        TypeError: If inputs are not numpy arrays or cannot be converted

    Example:
        >>> import numpy as np
        >>> x = np.array([1.0, 2.0])
        >>> A = np.eye(2)
        >>> b = np.ones(2)
        >>> result = quadratic_function(x, A, b)
        >>> print(f"f([1, 2]) = {result}")
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


def compute_gradient(
    x: np.ndarray, A: Optional[np.ndarray] = None, b: Optional[np.ndarray] = None
) -> np.ndarray:
    """Compute analytical gradient of quadratic function ∇f(x) = A x - b.

    For the quadratic function f(x) = (1/2) x^T A x - b^T x, the gradient is
    ∇f(x) = A x - b, which is computed efficiently using matrix multiplication.

    Args:
        x: Input point as numpy array (n-dimensional vector)
        A: Quadratic coefficient matrix (n x n). Defaults to identity matrix.
        b: Linear coefficient vector (n-dimensional). Defaults to vector of ones.

    Returns:
        Gradient vector ∇f(x) as numpy array with same shape as x

    Raises:
        ValueError: If array dimensions are incompatible

    Example:
        >>> x = np.array([1.0, 2.0])
        >>> grad = compute_gradient(x)
        >>> print(f"∇f([1, 2]) = {grad}")  # Should be [0, 1] for default A=I, b=ones
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
    verbose: bool = False,
) -> OptimizationResult:
    """Perform gradient descent optimization with fixed step size.

    Implements the classic gradient descent algorithm for unconstrained minimization:
    x_{k+1} = x_k - α ∇f(x_k), where α is the step size and ∇f is the gradient.

    The algorithm terminates when either:
    1. The gradient norm falls below the tolerance: ||∇f(x)|| < tolerance
    2. Maximum iterations are reached: iteration >= max_iterations

    Args:
        initial_point: Starting point for optimization as numpy array (n-dimensional)
        objective_func: Callable that takes x (np.ndarray) and returns f(x) (float)
        gradient_func: Callable that takes x (np.ndarray) and returns ∇f(x) (np.ndarray)
        max_iterations: Maximum number of iterations before termination (default: 1000)
        tolerance: Convergence tolerance for L2 norm of gradient (default: 1e-6)
        step_size: Fixed step size α > 0 for gradient updates (default: 0.01)
        verbose: If True, print progress every 100 iterations (default: False)

    Returns:
        OptimizationResult containing:
        - solution: Final iterate x
        - objective_value: f(solution)
        - iterations: Number of iterations performed (0-based)
        - converged: True if ||∇f(x)|| < tolerance, False if max_iterations reached
        - gradient_norm: Final ||∇f(x)||_2

    Raises:
        ValueError: If step_size <= 0, max_iterations <= 0, or tolerance <= 0
        TypeError: If initial_point is not array-like

    Example:
        >>> def f(x): return (x[0] - 1)**2 + (x[1] - 2)**2
        >>> def grad(x): return np.array([2*(x[0] - 1), 2*(x[1] - 2)])
        >>> result = gradient_descent(np.array([0.0, 0.0]), f, grad, step_size=0.1)
        >>> print(f"Converged: {result.converged}, Solution: {result.solution}")

    Infrastructure Integration:
        This function integrates seamlessly with infrastructure modules:

        >>> from infrastructure.scientific import check_numerical_stability, benchmark_function
        >>> from infrastructure.core.logging_utils import get_logger
        >>>
        >>> # Enable structured logging
        >>> logger = get_logger(__name__)
        >>>
        >>> # Run optimization
        >>> result = gradient_descent(np.array([0.0, 0.0]), f, grad, step_size=0.1)
        >>>
        >>> # Analyze numerical stability
        >>> stability = check_numerical_stability(f, [np.array([0.0, 0.0]), result.solution])
        >>> logger.info(f"Stability score: {stability['overall_stable']}")
        >>>
        >>> # Benchmark performance
        >>> benchmark = benchmark_function(lambda x: gradient_descent(x, f, grad).iterations,
        ...                               [np.array([0.0, 0.0])])
        >>> logger.info(f"Avg iterations: {benchmark['mean_time']:.1f}")
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

    if LOGGING_AVAILABLE and logger:
        logger.debug(f"Starting gradient descent with x0={x}, step_size={step_size}")

    while iteration < max_iterations:
        grad = gradient_func(x)
        grad_norm = np.linalg.norm(grad)

        if verbose and iteration % 100 == 0:
            obj_val = objective_func(x)
            if LOGGING_AVAILABLE and logger:
                logger.info(
                    f"Iteration {iteration}: x={x}, f(x)={obj_val:.6f}, ||∇f||={grad_norm:.6f}"
                )

        if grad_norm < tolerance:
            converged = True
            if LOGGING_AVAILABLE and logger:
                logger.debug(
                    f"Converged at iteration {iteration} with ||∇f||={grad_norm:.2e}"
                )
            break

        # Update: x = x - step_size * ∇f(x)
        x = x - step_size * grad
        iteration += 1

        # Track objective value after each update
        objective_history.append(objective_func(x))

    final_obj_value = objective_func(x)
    final_grad_norm = np.linalg.norm(gradient_func(x))

    if LOGGING_AVAILABLE and logger:
        if converged:
            logger.info(
                f"Gradient descent converged in {iteration} iterations, final f(x)={final_obj_value:.6f}"
            )
        else:
            logger.warning(
                f"Gradient descent did not converge within {max_iterations} iterations, final f(x)={final_obj_value:.6f}"
            )

    return OptimizationResult(
        solution=x,
        objective_value=final_obj_value,
        iterations=iteration,
        converged=converged,
        gradient_norm=final_grad_norm,
        objective_history=objective_history,
    )
