# Code Project API Reference

This document provides API reference for the code project's optimization algorithms.

## Classes

### OptimizationResult

Container for optimization algorithm results.

**Attributes:**
- `solution`: Final solution point as numpy array
- `objective_value`: Objective function value at the solution
- `iterations`: Number of iterations performed
- `converged`: True if gradient norm fell below tolerance
- `gradient_norm`: Final L2 norm of the gradient vector
- `objective_history`: List of objective function values during optimization
- `termination_reason`: One of `converged`, `max_iterations`, or `non_finite`

## Functions

### quadratic_function(x, A=None, b=None)

Evaluate quadratic objective function f(x) = (1/2) x^T A x - b^T x.

### compute_gradient(x, A=None, b=None)

Compute analytical gradient of quadratic function ∇f(x) = A x - b.

### gradient_descent(initial_point, objective_func, gradient_func, ...)

Perform gradient descent optimization with fixed step size. Non-finite
candidate states are rejected and reported as `termination_reason="non_finite"`.
