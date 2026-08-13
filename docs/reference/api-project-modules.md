# API reference — project modules

> Source-grounded entry point for Layer 2 APIs under
> `projects/<qualified-name>/src/`.

**Quick reference:** [Infrastructure API](api-reference.md) |
[public project roster](../_generated/active_projects.md) |
[control-positive source](../../projects/templates/template_code_project/src/README.md)

Project APIs are deliberately project-specific; there is no universal
`example.py`, `statistics.py`, or `visualization.py` surface. Treat the source,
tests, and each project's `src/README.md`/`src/AGENTS.md` as authoritative. The
examples below use the public control-positive exemplar and should be checked
against source when its API changes.

## Import context

From the repository root, the public exemplar can be imported by its full
namespace:

```python
from projects.templates.template_code_project.src.optimizer import (
    compute_gradient,
    gradient_descent,
    make_quadratic_problem,
    quadratic_function,
)
```

Project scripts commonly add their own project root to `sys.path` and then use
`from src.optimizer import ...`; follow the convention exercised by that
project's tests and scripts. The obsolete namespace
`projects.template_code_project` is not valid for the typed `projects/`
layout.

## `optimizer.py`

Source: [`optimizer.py`](../../projects/templates/template_code_project/src/optimizer.py)

Behavior tests: [`test_optimizer.py`](../../projects/templates/template_code_project/tests/test_optimizer.py)

### `OptimizationResult`

```python
@dataclass
class OptimizationResult:
    solution: np.ndarray
    objective_value: float
    iterations: int
    converged: bool
    gradient_norm: float
    objective_history: list[float] | None = None
    termination_reason: str = "unknown"
```

`termination_reason` distinguishes convergence, the iteration cap, and a
non-finite state. The optimizer retains the last finite iterate when an update
would become non-finite.

### Core functions

```python
quadratic_function(x, A=None, b=None) -> float
compute_gradient(x, A=None, b=None) -> np.ndarray
quadratic_optimum(A=None, b=None) -> tuple[np.ndarray, float]
make_quadratic_problem(A=None, b=None) -> tuple[Callable, Callable]
gradient_descent(
    initial_point,
    objective_func,
    gradient_func,
    max_iterations=1000,
    tolerance=1e-6,
    step_size=0.01,
    verbose=False,
) -> OptimizationResult
```

The default objective is
$f(x)=\tfrac{1}{2}x^\mathsf{T}Ax-b^\mathsf{T}x$, with identity `A` and an
all-ones `b`. Inputs must be finite, one-dimensional, and shape-compatible;
`gradient_descent()` also requires positive finite tolerance and step size and
a positive integer iteration cap.

```python
import numpy as np

objective, gradient = make_quadratic_problem()
result = gradient_descent(
    initial_point=np.array([5.0]),
    objective_func=objective,
    gradient_func=gradient,
    step_size=0.1,
    tolerance=1e-6,
)

assert result.termination_reason in {"converged", "max_iterations", "non_finite"}
```

`simulate_trajectory(...)` is the figure/diagnostic convenience surface; see
its source docstring for the current return mapping and defaults.

## `invariants.py`

Source: [`invariants.py`](../../projects/templates/template_code_project/src/invariants.py)

Behavior tests: [`test_invariants.py`](../../projects/templates/template_code_project/tests/test_invariants.py)

The invariant surface evaluates real numerical behavior without infrastructure
imports or I/O:

- `InvariantResult` — typed witness record with comparison kind, actual and
  expected values, tolerance, description, and extra metadata.
- `OptimizerSweepConfig` — immutable matrix/vector, initial-point, step-size,
  iteration, and tolerance configuration.
- `convergence_invariants(config)` — stable-step convergence, objective, and
  monotonicity checks.
- `gradient_consistency_invariants(config, eps=..., seed=...)` — analytical vs
  finite-difference gradient agreement.
- `trajectory_invariants(config, max_iter=...)` — trajectory behavior for
  stable step sizes.
- `all_invariants(config)` — aggregate project invariant set.

## Figure and manuscript APIs are infrastructure services

`FigureManager` is an infrastructure utility, not a project module, and it
emits legacy raw-LaTeX blocks. New manuscript pipelines should use Pandoc image
syntax plus the deterministic generated-figure registry. See the
[Visualization Guide](../usage/visualization-guide.md) and
[Manuscript Semantics](../guides/manuscript-semantics.md).

For infrastructure exports, use the generated
[Infrastructure API Reference](api-reference.md). For another project's Layer
2 API, inspect that project's own `src/` documentation and tests rather than
assuming the control-positive optimizer surface applies.
