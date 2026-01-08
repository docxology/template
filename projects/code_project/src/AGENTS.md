# src/ - Core Optimization Algorithms

## Overview

The `src/` directory contains the core mathematical optimization algorithms and data structures used in the research project. This module implements gradient-based optimization methods with reproducible results.

## Key Concepts

- **Mathematical optimization** algorithms for parameter tuning
- **Reproducible research** with fixed random seeds
- **Numerical stability** and convergence analysis
- **Type safety** with type hints

## Directory Structure

```
src/
├── __init__.py           # Module exports and initialization
├── optimizer.py          # Core optimization algorithms
├── AGENTS.md            # This technical documentation
└── README.md            # Quick reference
```

## Installation/Setup

This module uses standard scientific Python libraries:

- `numpy` - Numerical computations and arrays
- `scipy` - Scientific computing utilities
- `matplotlib` - Plotting and visualization

## Infrastructure Integration

This module integrates seamlessly with the repository's infrastructure modules for analysis, logging, and validation.

### Available Infrastructure Capabilities

- **Scientific Analysis**: `infrastructure.scientific` - Numerical stability and performance benchmarking
- **Logging**: `infrastructure.core.logging_utils` - Structured logging with context
- **Validation**: `infrastructure.validation` - Output integrity and quality checks
- **Rendering**: `infrastructure.rendering` - Multi-format output generation
- **Publishing**: `infrastructure.publishing` - Academic publishing workflows

### Integration Examples

#### Scientific Analysis Integration

```python
from optimizer import gradient_descent
from infrastructure.scientific import check_numerical_stability, benchmark_function
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

# Define test problem
def objective(x): return (x[0] - 1)**2 + (x[1] - 2)**2
def gradient(x): return np.array([2*(x[0] - 1), 2*(x[1] - 2)])

# Run optimization
result = gradient_descent(np.array([0.0, 0.0]), objective, gradient)

# Analyze numerical stability
stability = check_numerical_stability(
    func=objective,
    test_inputs=[np.array([0.0, 0.0]), result.solution]
)
logger.info(f"Stability score: {stability['overall_stable']}")

# Benchmark performance
benchmark = benchmark_function(
    func=lambda x: gradient_descent(x, objective, gradient).iterations,
    test_inputs=[np.array([0.0, 0.0])]
)
logger.info(f"Average iterations: {benchmark['mean_time']:.1f}")
```

#### Validation Integration

```python
from infrastructure.validation import verify_output_integrity

# After generating optimization results
output_dir = Path("output")
integrity_report = verify_output_integrity(output_dir)

if integrity_report.issues:
    logger.warning(f"Found {len(integrity_report.issues)} integrity issues")
else:
    logger.info("Output integrity validation passed")
```

## Usage Examples

### Basic Optimization

```python
from optimizer import gradient_descent, quadratic_function, compute_gradient

# Define objective function
def objective(x):
    return quadratic_function(x, A=np.eye(len(x)), b=np.ones(len(x)))

def gradient(x):
    return compute_gradient(x, A=np.eye(len(x)), b=np.ones(len(x)))

# Run optimization
result = gradient_descent(
    initial_point=np.array([0.0, 0.0]),
    objective_func=objective,
    gradient_func=gradient,
    step_size=0.1
)

print(f"Optimal point: {result.solution}")
print(f"Objective value: {result.objective_value}")
```

### Custom Optimization Problems

```python
# Define custom objective and gradient
def custom_objective(x):
    return (x[0] - 1)**2 + (x[1] - 2)**2

def custom_gradient(x):
    return np.array([2*(x[0] - 1), 2*(x[1] - 2)])

result = gradient_descent(
    initial_point=np.array([5.0, 5.0]),
    objective_func=custom_objective,
    gradient_func=custom_gradient
)
```

## Configuration

The optimization algorithms support configuration through function parameters:

- **step_size**: Learning rate for gradient descent (default: 0.01)
- **max_iterations**: Maximum iterations before termination (default: 1000)
- **tolerance**: Convergence tolerance for gradient norm (default: 1e-6)
- **verbose**: Enable progress printing (default: False)

## Testing

```bash
# Run all tests for this module
pytest ../tests/ -v

# Run specific test classes
pytest ../tests/ -k "TestQuadraticFunction"

# Run with coverage
pytest ../tests/ --cov=. --cov-report=html
```

## API Reference

### optimizer.py

#### OptimizationResult (dataclass)
```python
@dataclass
class OptimizationResult:
    """Result of an optimization run.

    Attributes:
        solution: np.ndarray - Final solution point
        objective_value: float - Objective function value at solution
        iterations: int - Number of iterations performed
        converged: bool - Whether convergence criteria were met
        gradient_norm: float - Final gradient norm
    """
```

#### quadratic_function (function)
```python
def quadratic_function(
    x: np.ndarray,
    A: Optional[np.ndarray] = None,
    b: Optional[np.ndarray] = None
) -> float:
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
```

#### compute_gradient (function)
```python
def compute_gradient(
    x: np.ndarray,
    A: Optional[np.ndarray] = None,
    b: Optional[np.ndarray] = None
) -> np.ndarray:
    """Compute gradient of quadratic function.

    Args:
        x: Input point
        A: Quadratic term matrix
        b: Linear term vector

    Returns:
        Gradient vector at x
    """
```

#### gradient_descent (function)
```python
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
```

## Troubleshooting

### Common Issues

- **Dimension mismatches**: Ensure A, b, and x have compatible dimensions
- **Non-convergence**: Try smaller step sizes or different initial points
- **Numerical instability**: Check condition number of matrix A

### Debug Tips

Enable verbose output to monitor optimization progress:
```python
result = gradient_descent(..., verbose=True)
```

## Best Practices

- **Scale variables** to similar magnitudes for better convergence
- **Choose appropriate step sizes** through experimentation
- **Monitor convergence** using gradient norms
- **Use multiple starting points** for global optimization problems

## See Also

- [README.md](README.md) - Quick reference
- [../scripts/optimization_analysis.py](../scripts/optimization_analysis.py) - Example usage
- [../tests/test_optimizer.py](../tests/test_optimizer.py) - tests