# Test Patterns Reference

Testing conventions and patterns for the `code_project` exemplar's zero-mock test suite.

## Zero-Mock Enforcement

The following are **strictly forbidden** anywhere in the `code_project` exemplar:

- Any mocking framework usage (including built-in mocking libraries and third-party monkeypatch helpers)
- Any test strategy that fakes objects/attributes to avoid executing real code paths
- Any "synthetic result objects" created solely to satisfy a type shape without executing the algorithm

Every test must exercise real algorithms with real data.

## Fixture Patterns

### Shared fixtures live in `conftest.py`

```python
# conftest.py
import pytest
import numpy as np

@pytest.fixture
def simple_problem():
    """Standard 1D quadratic test problem."""
    return {
        "A": np.array([[2.0]]),
        "b": np.array([1.0]),
        "x0": np.array([5.0]),
        "solution": np.array([0.5]),
    }
```

### Use fixtures for reusable problem definitions, not for mocking infrastructure

## Tolerance Constants

```python
# Standard tolerances for floating-point comparisons
ATOL = 1e-4   # Absolute tolerance
RTOL = 1e-6   # Relative tolerance

# Use in assertions
np.testing.assert_allclose(result.solution, expected, atol=ATOL)
```

- **ATOL=1e-4**: Acceptable for optimization convergence checks
- **RTOL=1e-6**: Acceptable for gradient accuracy checks
- Use `np.testing.assert_allclose` over `pytest.approx` for NumPy arrays

## Test Class Organisation

```python
class TestQuadraticFunction:
    """Tests for quadratic_function()."""

    def test_simple_evaluation(self):
        """Test basic function evaluation with identity matrix."""

    def test_multidimensional(self):
        """Test N-dimensional quadratic with custom A, b."""

    def test_default_parameters(self):
        """Test fallback when A=None, b=None."""

    def test_dimension_mismatch(self):
        """Test ValueError on incompatible dimensions."""
```

- One test class per public function or class
- Class name: `Test{FunctionOrClassName}`
- Method names: `test_{what_is_being_tested}`
- Each test method must have a docstring

## Parametrize Usage

```python
@pytest.mark.parametrize("step_size,expected_converged", [
    (0.01, True),
    (0.1,  True),
    (1.0,  True),   # |1 - 1.0| = 0.0 → single-step convergence for unit Hessian
    (2.5,  False),  # |1 - 2.5| = 1.5 > 1 → diverges for unit Hessian
])
def test_convergence_by_step_size(self, step_size, expected_converged):
    """Test convergence across different step sizes.

    For f(x) = (1/2)x^T A x - b^T x with unit Hessian (A = I), the
    contraction factor is |1 - α|. Stability requires |1 - α| < 1, i.e.
    0 < α < 2. Step sizes ≥ 2 cause divergence.
    """
    obj_func, grad_func = make_quadratic_problem(
        np.array([[1.0]]), np.array([1.0])
    )
    result = gradient_descent(
        initial_point=np.array([0.5]),
        objective_func=obj_func,
        gradient_func=grad_func,
        step_size=step_size,
        max_iterations=200,
        tolerance=1e-6,
    )
    assert result.converged == expected_converged
```

Use `parametrize` when testing the same behaviour across multiple inputs. Don't use it for fundamentally different test scenarios.

## Error-Path Testing

```python
def test_dimension_mismatch_A(self):
    """Test that mismatched A dimensions raise ValueError."""
    x = np.array([1.0, 2.0])
    A = np.array([[1.0]])  # 1×1, but x is 2D
    with pytest.raises(ValueError, match="A must be 2x2"):
        quadratic_function(x, A=A)
```

- Always use `match=` to verify the error message content
- The actual message format is `f"A must be {n}x{n}, got {A.shape}"` (see `src/optimizer.py::_validate_quadratic_inputs`)
- Test every documented `Raises` clause in the docstring

## Coverage Verification

```bash
# Run with coverage (gate is 90% enforced by pyproject.toml)
uv run pytest projects/code_project/tests/ \
    --cov=projects/code_project/src \
    --cov-report=term-missing \
    --cov-fail-under=90

# Generate HTML report
uv run pytest projects/code_project/tests/ \
    --cov=projects/code_project/src \
    --cov-report=html
```

The `pyproject.toml` enforces `fail_under = 90` as the CI gate. The current suite typically achieves ~96%, providing a comfortable buffer. Do not delete tests to make a coverage number work — fix the gap.

## Determinism

- **Fixed inputs preferred** — algorithms are deterministic; use explicit arrays
- **RNG acceptable only for timing tests** — `np.random.randn` is acceptable in `TestPerformanceBenchmarks` because those tests assert timing bounds, not exact mathematical values
- **No time-dependent mathematical assertions** — test correctness properties, not wall-clock values

## See Also

- [AGENTS.md](AGENTS.md) — Test class listing and run commands
- [../src/STYLE.md](../src/STYLE.md) — How source code should be structured
- [../docs/testing_philosophy.md](../docs/testing_philosophy.md) — Zero-mock rationale
