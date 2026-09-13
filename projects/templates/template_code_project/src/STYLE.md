# Source Code Style Guide

Code style and design conventions for `src/` modules in the `template_code_project` exemplar.

## Pure Function Design

All functions in `src/` must be **side-effect-free**:

```python
# ✅ CORRECT: Pure function — takes input, returns output
def quadratic_function(x: np.ndarray, A: np.ndarray, b: np.ndarray) -> float:
    return 0.5 * x @ A @ x - b @ x

# ❌ WRONG: Side-effect function — writes files, prints, logs
def quadratic_function(x, A, b):
    print(f"Computing f({x})")     # Side effect: I/O
    result = 0.5 * x @ A @ x - b @ x
    Path("result.txt").write_text(str(result))  # Side effect: file write
    return result
```

File I/O, logging, and visualisation belong in `scripts/`, not `src/`.

## Type Hints

Every public function must have complete type annotations:

```python
from typing import Optional, Callable
import numpy as np

def gradient_descent(
    initial_point: np.ndarray,
    objective_func: Callable[[np.ndarray], float],
    gradient_func: Callable[[np.ndarray], np.ndarray],
    max_iterations: int = 1000,
    tolerance: float = 1e-6,
    step_size: float = 0.01,
    verbose: bool = False,
) -> OptimizationResult:
```

- Use `np.ndarray` for array types (not `list` or `array`)
- Use `Optional[T]` when `None` is a valid value
- Use `Callable[[ArgsType], ReturnType]` for function parameters
- Use `@dataclass` for structured return types

## Docstring Format

Google-style docstrings with Args/Returns/Raises:

```python
def compute_gradient(
    x: np.ndarray,
    A: Optional[np.ndarray] = None,
    b: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Compute analytical gradient ∇f(x) = Ax - b.

    Args:
        x: Input point (n-dimensional vector).
        A: Positive definite matrix (n×n). Defaults to identity.
        b: Linear term (n-dimensional). Defaults to ones.

    Returns:
        Gradient vector at x.

    Raises:
        ValueError: If dimensions of A, b, and x are incompatible.
    """
```

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Functions | `snake_case` | `compute_gradient` |
| Classes | `PascalCase` | `OptimizationResult` |
| Constants | `UPPER_SNAKE` | `MAX_ITERATIONS` |
| Private | `_leading_underscore` | `_validate_dimensions` |
| Parameters | descriptive `snake_case` | `initial_point`, `step_size` |

## NumPy Idioms

```python
# ✅ Use vectorized operations
result = A @ x - b

# ❌ Avoid loops over array elements
result = np.zeros_like(b)
for i in range(len(x)):
    result[i] = sum(A[i, j] * x[j] for j in range(len(x))) - b[i]
```

- Prefer `@` operator over `np.dot()` for matrix multiplication
- Use `np.linalg.norm()` for norm computations
- Use `np.allclose()` for floating-point comparisons in validation

## Error Handling

```python
def quadratic_function(x: np.ndarray, A: np.ndarray, b: np.ndarray) -> float:
    if A.shape[0] != A.shape[1]:
        raise ValueError(f"A must be square, got shape {A.shape}")
    if A.shape[0] != len(x):
        raise ValueError(
            f"Dimension mismatch: A is {A.shape[0]}×{A.shape[1]} "
            f"but x has length {len(x)}"
        )
    return 0.5 * x @ A @ x - b @ x
```

- Validate inputs at function entry
- Use `ValueError` for dimension/type mismatches
- Include actual values in error messages for debuggability
- Never catch and silently swallow exceptions

## Module Exports

`src/__init__.py` is a namespace shim only — it performs no re-exports:

```python
"""Namespace shim — the real template_code_project package lives at src/template_code_project/ (TEST-ISOLATION-SYSPATH-1)."""
```

The public API lives in the `src/template_code_project/` subpackages and is
accessed through deep imports such as:

```python
from template_code_project.core.optimizer import gradient_descent
from template_code_project.core.invariants import all_invariants
from template_code_project.figures import generate_convergence_plot
from template_code_project.core.experiment_config import load_experiment_config
```

`src/template_code_project/analysis/`, `src/template_code_project/dashboard/`,
`src/template_code_project/figures/`, `src/template_code_project/core/experiment_config.py`,
and `src/template_code_project/core/manuscript_variables.py`
expose their public callables directly via these deep imports; they are part
of the orchestration layer, not the pure-math API, so nothing from them is
re-exported at package level. `core/experiment_config.py` is the config
single source of truth shared by analysis, figures, dashboard, and
manuscript_variables.

## See Also

- [AGENTS.md](template_code_project/AGENTS.md) — Full API reference and infrastructure integration
- [../tests/PATTERNS.md](../tests/PATTERNS.md) — How to test code written here
- [../scripts/CONVENTIONS.md](../scripts/CONVENTIONS.md) — How scripts use this code
