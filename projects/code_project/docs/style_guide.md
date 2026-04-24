# Style Guide

This document defines the coding and communication style for the `code_project` exemplar. Every rule here has a concrete consequence for test correctness, reproducibility, or manuscript accuracy.

---

## 1. Zero-Mock Policy

The most critical style rule is the absolute prohibition of mocking. The following are **forbidden** anywhere inside `projects/code_project/tests/`:

- `import unittest.mock`
- `from unittest.mock import MagicMock, patch, create_autospec, Mock, AsyncMock`
- `@patch(...)` decorators
- `monkeypatch.setattr(...)` when used to substitute a real function with a fake callable

**Why**: `src/optimizer.py` contains pure functions. You can always test them with real numpy arrays and real mathematical results. A test that requires a mock is a test for the wrong thing — it tests that one function calls another (call-count assertion), not that the algorithm is correct.

**Forbidden pattern**:
```python
# BAD — tests call behavior, not correctness
from unittest.mock import MagicMock
mock_grad = MagicMock(return_value=np.array([0.0]))
result = gradient_descent(x0, obj_func, mock_grad, step_size=0.1)
assert mock_grad.call_count > 0
```

**Correct pattern** (from `tests/test_optimizer.py`):
```python
# GOOD — tests real mathematical output
obj, grad = make_quadratic_problem(A=np.array([[2.0]]), b=np.array([4.0]))
result = gradient_descent(np.array([0.0]), obj, grad, step_size=0.1)
assert result.converged
assert abs(result.final_point[0] - 2.0) < 1e-4  # x* = A^-1 b = 2.0
```

**Verify cleanliness**:
```bash
grep -r "unittest.mock\|MagicMock\|@patch" projects/code_project/tests/ || echo "Clean"
```

---

## 2. Infrastructure Delegation

Project code must delegate cross-cutting concerns to `infrastructure/`. The delegation table is:

| File | May Import | Must NOT Import |
|---|---|---|
| `src/optimizer.py` | `numpy`, `dataclasses`, `logging` (stdlib), `typing` | **Anything from `infrastructure.*`** |
| `scripts/optimization_analysis.py` | `src/optimizer`, `infrastructure.core.logging.utils`, `infrastructure.scientific.*`, `infrastructure.reporting.*`, `infrastructure.validation.*`, `infrastructure.core.progress` | Business logic (math, gradient update rules) |
| `scripts/generate_api_docs.py` | `src/optimizer`, `infrastructure.core.logging.utils` | Math |
| `scripts/z_generate_manuscript_variables.py` | `src/optimizer` (for computing analytical optimum), `infrastructure.core.logging.utils` | Infrastructure modules that write files |
| `tests/test_optimizer.py` | `src/optimizer`, `scripts/optimization_analysis` (via `INFRASTRUCTURE_AVAILABLE` guard) | `unittest.mock.*`, `infrastructure.*` directly |

**Verify `src/` is clean**:
```bash
grep -r "from infrastructure\|import infrastructure" projects/code_project/src/ || echo "Clean"
```

---

## 3. The Thin Orchestrator Pattern

Files in `scripts/` must be "thin orchestrators": they may run experiment loops and generate plots, but must not re-implement algorithms that belong in `src/`.

**Forbidden** — gradient update rule re-implemented in `scripts/`:
```python
# BAD — math belongs in src/optimizer.py, not in optimization_analysis.py
def run_experiment(alpha, x0):
    x = x0
    for i in range(1000):
        grad = x - 1.0   # BAD: hardcoded math
        x = x - alpha * grad
    return x
```

**Correct** — `scripts/` calls `src/` for the math:
```python
# GOOD — import and call the tested function
from projects.code_project.src.optimizer import gradient_descent, make_quadratic_problem

def run_experiment(alpha, A, b, x0):
    obj, grad = make_quadratic_problem(A=A, b=b)
    return gradient_descent(x0, obj, grad, step_size=alpha)
```

**Decision rule**: If a line of code in `scripts/` contains a mathematical operation that determines the algorithm's output (not just its visualization), move that line to `src/` and write a test for it.

---

## 4. Manuscript "Show, Not Tell"

When editing manuscript markdown (e.g., `02_methodology.md`), use explicit, verifiable file paths instead of vague descriptions. Reviewers and future agents must be able to find the referenced code.

**Forbidden (vague)**:
```markdown
Our testing framework verifies gradient calculations using standard numerical methods.
The infrastructure handles PDF rendering automatically.
```

**Correct (concrete, from `01_introduction.md`)**:
```markdown
The test suite in `projects/code_project/tests/test_optimizer.py` verifies gradient
calculations without mocks, using `numpy` arrays with known analytical solutions.
PDF rendering is handled by `infrastructure/rendering/pdf_renderer.py` via Pandoc and LaTeX.
```

Two additional BAD/GOOD pairs:

| BAD (vague) | GOOD (concrete) |
|---|---|
| "The optimizer converges for most step sizes." | "For $\alpha \in \{0.01, 0.1, 0.5, 1.0\}$, `gradient_descent()` in `src/optimizer.py` meets the gradient tolerance $\|\nabla f\| < 10^{-8}$ within `max_iterations=1000`." |
| "We validated numerical stability." | "`check_numerical_stability()` from `infrastructure.scientific.stability` was called with {{CONFIG_NUM_STABILITY_STARTS}} starting points and {{CONFIG_NUM_STABILITY_STEPS}} step sizes, producing {{CONFIG_STABILITY_CELLS}} total evaluations." |

---

## 5. Explicit Absolute File Paths

When AI agents or humans refer to files in logs, documentation, comments, or implementation plans, always use the path relative to the **repository root** (`template/`). This prevents ambiguity when the same filename appears in multiple directories.

**Repository-root anchors** for this project:

| Short Name | Absolute Path (from repo root) |
|---|---|
| optimizer | `projects/code_project/src/optimizer.py` |
| test suite | `projects/code_project/tests/test_optimizer.py` |
| conftest | `projects/code_project/tests/conftest.py` |
| analysis script | `projects/code_project/scripts/optimization_analysis.py` |
| variable hydration | `projects/code_project/scripts/z_generate_manuscript_variables.py` |
| config | `projects/code_project/manuscript/config.yaml` |
| results CSV | `projects/code_project/output/data/optimization_results.csv` |
| final PDF | `output/code_project/pdf/code_project_combined.pdf` |

**Forbidden (relative / ambiguous)**:
```
optimizer.py       # Which optimizer? Which project?
output/figures/    # Relative to what?
../src/optimizer   # Only valid from one directory
```

**Correct (absolute from repo root)**:
```
projects/code_project/src/optimizer.py
projects/code_project/output/figures/convergence_plot.png
```

---

## 6. Dataclass and Type Hint Standards

Follow the patterns established in `src/optimizer.py`:

- Use Python 3.10+ union syntax: `list[float] | None`, not `Optional[List[float]]`
- Use `np.ndarray` for array type hints, not `npt.NDArray[np.float64]` (consistency with existing code)
- All public functions must have complete type annotations on all parameters and return values
- `@dataclass` fields use the same union syntax: `trajectory: list[np.ndarray] | None = None`

**Example** (following `OptimizationResult` in `src/optimizer.py`):
```python
@dataclass
class NewResult:
    converged: bool
    iterations: int
    history: list[float] | None = None
    metadata: dict[str, float] | None = None
```

---

## 7. Error Message Format

All `ValueError` and `TypeError` raises must include the actual problematic value so that users can diagnose the issue without reading source code.

**Forbidden (no diagnostic value)**:
```python
raise ValueError("Dimension mismatch")
raise ValueError("Invalid step size")
```

**Correct** (following the pattern in `src/optimizer.py`):
```python
raise ValueError(f"A must be {n}x{n}, got {A.shape}")
raise ValueError(f"step_size must be positive, got {step_size}")
raise ValueError(f"initial_point must be 1D array of length {n}, got shape {x0.shape}")
```
