# Test Patterns Reference

Testing conventions and patterns for the `code_project` exemplar's zero-mock test suite.

## Zero-Mock Enforcement

The following are **strictly forbidden** in all test files:

```python
# ❌ FORBIDDEN
from unittest.mock import MagicMock, patch, Mock
import unittest.mock
mocker.patch(...)
type("FakeResult", (), {"converged": True})
```

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
    (0.05, True),
    (0.1, True),
    (1.5, False),  # Divergent step size
])
def test_convergence_by_step_size(self, step_size, expected_converged):
    """Test convergence across different step sizes."""
    result = gradient_descent(
        initial_point=np.array([5.0]),
        objective_func=quadratic_function,
        gradient_func=compute_gradient,
        step_size=step_size,
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
    with pytest.raises(ValueError, match="Dimension mismatch"):
        quadratic_function(x, A=A)
```

- Always use `match=` to verify the error message content
- Test every documented `Raises` clause in the docstring

## Coverage Verification

```bash
# Run with coverage (must achieve 100%)
pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=100

# Generate HTML report
pytest tests/ --cov=src --cov-report=html
```

Every line in `src/` must be executed by at least one test. The `pyproject.toml` enforces `fail_under = 90` as a minimum; this exemplar targets 100%.

## Determinism

- **No random seeds** in tests — algorithms are deterministic
- **No time-dependent assertions** — test mathematical properties, not wall-clock time
- **Fixed input data** — every test uses explicitly specified arrays

## See Also

- [AGENTS.md](AGENTS.md) — Test class listing and run commands
- [../src/STYLE.md](../src/STYLE.md) — How source code should be structured
- [../docs/testing_philosophy.md](../docs/testing_philosophy.md) — Zero-mock rationale
