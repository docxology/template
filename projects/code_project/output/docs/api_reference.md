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

## Functions

### quadratic_function(x, A=None, b=None)

Evaluate quadratic objective function f(x) = (1/2) x^T A x - b^T x.

**Parameters:**
- `x`: Input point as numpy array (n-dimensional vector)
- `A`: Symmetric positive definite matrix (n x n). Defaults to identity.
- `b`: Linear coefficient vector (n-dimensional). Defaults to vector of ones.

**Returns:** Function value as float

### compute_gradient(x, A=None, b=None)

Compute analytical gradient of quadratic function ∇f(x) = A x - b.

**Parameters:**
- `x`: Input point as numpy array (n-dimensional vector)
- `A`: Symmetric positive definite matrix (n x n). Defaults to identity.
- `b`: Linear coefficient vector (n-dimensional). Defaults to vector of ones.

**Returns:** Gradient vector as numpy array

### gradient_descent(initial_point, objective_func, gradient_func, ...)

Perform gradient descent optimization with fixed step size.

**Parameters:**
- `initial_point`: Starting point for optimization as numpy array
- `objective_func`: Callable that takes x and returns f(x)
- `gradient_func`: Callable that takes x and returns ∇f(x)
- `max_iterations`: Maximum number of iterations (default: 1000)
- `tolerance`: Convergence tolerance for gradient norm (default: 1e-6)
- `step_size`: Fixed step size α > 0 (default: 0.01)
- `verbose`: If True, print progress (default: False)

**Returns:** OptimizationResult containing solution and convergence diagnostics

## Examples

```python
import numpy as np
from optimizer import gradient_descent, quadratic_function, compute_gradient

# Define optimization problem
def obj_func(x):
    return quadratic_function(x, np.eye(len(x)), np.ones(len(x)))

def grad_func(x):
    return compute_gradient(x, np.eye(len(x)), np.ones(len(x)))

# Run optimization
initial_point = np.array([0.0, 0.0])
result = gradient_descent(initial_point, obj_func, grad_func, step_size=0.1)

if result.converged:
    print(f"Converged in {{result.iterations}} iterations")
    print(f"Solution: {{result.solution}}")
    print(f"Objective: {{result.objective_value:.6f}}")
else:
    print(f"Did not converge within {{result.iterations}} iterations")
```
