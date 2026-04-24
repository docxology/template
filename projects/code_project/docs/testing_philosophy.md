# Testing Philosophy: The Zero-Mock Standard

The Generalized Research Template strictly forbids mocking in scientific/mathematical validation.

## Why Zero Mocks?

The core insight is architectural: if a function requires a mock to be tested, it is doing I/O, calling external systems, or producing side-effects — which means it belongs in `scripts/` (as a thin orchestrator), not in `src/` (as pure logic). The purity of `src/optimizer.py` is what makes zero-mock testing achievable. Every function in `src/` is deterministic and side-effect-free, so tests simply call functions with real numpy arrays and verify real mathematical outputs.

If you ever feel the urge to mock something in a test for `src/`, treat it as a signal: move that code to `scripts/` and test the `src/` boundary directly.

## The Validation Suite

File: `projects/code_project/tests/test_optimizer.py` (749 lines)
Configuration: `projects/code_project/pyproject.toml` (`fail_under = 90`)
Conftest: `projects/code_project/tests/conftest.py` (sets `MPLBACKEND=Agg`, adds `src/` to `sys.path`)

The suite currently collects **42** tests covering `optimizer.py` and, via conditional imports, thin orchestration in `scripts/optimization_analysis.py`. Line/branch coverage on `src/` typically lands at ~96%, well above the 90% gate.

## Test Class Inventory

| Class | Tests | Covers |
|---|---|---|
| `TestQuadraticFunction` | 7 | `quadratic_function()` evaluation, dimension mismatch errors, zero/large/negative inputs |
| `TestComputeGradient` | 3 | `compute_gradient()` accuracy at 1D and nD, default parameter handling |
| `TestGradientDescent` | 10 | Convergence to optimum, iteration cap, already-at-optimum, multidimensional, parameter validation, divergent step size (α > 2), verbose path |
| `TestOptimizationResult` | 2 | Dataclass construction; `objective_history` population and length invariant |
| `TestPerformanceBenchmarks` | 2 | Execution time across dimensions, function evaluation speed (real timing) |
| `TestMakeQuadraticProblem` | 6 | Factory returns callables, objective matches `quadratic_function`, gradient matches `compute_gradient`, factory usable with `gradient_descent` |
| `TestSimulateTrajectory` | 5 | Return structure, objectives decrease toward optimum, parallel list lengths, sequential iterations, default params |
| `TestStabilityAnalysis` | 2 | Infrastructure-dependent; skipped if `infrastructure.scientific` unavailable |
| `TestPerformanceBenchmarking` | 2 | Infrastructure-dependent; skipped if `infrastructure.scientific` unavailable |
| `TestAnalysisDashboard` | 2 | Infrastructure-dependent; skipped if `infrastructure.reporting` unavailable |

**Total: 42 collected tests**

## Coverage Mechanics

`pyproject.toml` settings relevant to coverage:

```toml
[tool.coverage.run]
source = ["src"]
branch = true          # Branch coverage, not just line coverage
omit = ["tests/*", "*/__init__.py", "*/test_*.py"]

[tool.coverage.report]
fail_under = 90        # CI fails if src/ drops below 90%
precision = 2
exclude_lines = [
    "pragma: no cover",
    "if __name__ == .__main__.:",
    "raise NotImplementedError",
]
```

Run with full coverage report:

```bash
uv run pytest projects/code_project/tests/ \
    --cov=projects/code_project/src \
    --cov-report=term-missing \
    --cov-fail-under=90
```

## Zero-Mock Checklist

Before submitting any test, verify all boxes are checked:

- [ ] Test uses real `numpy` arrays as inputs
- [ ] Test calls `src/optimizer.py` functions directly with real data
- [ ] Test asserts mathematical properties (convergence, gradient accuracy, dimension shapes), not call counts
- [ ] No `unittest.mock`, `MagicMock`, `create_autospec`, `@patch`, or `monkeypatch` used as a mock factory
- [ ] Infrastructure-dependent tests use `@pytest.mark.skipif(not INFRASTRUCTURE_AVAILABLE, ...)` — real infrastructure or graceful skip, never a fake
- [ ] Any timing assertion uses bounds (`< 5.0`) not exact values, and the test docstring explains why timing is the right property to check

## Infrastructure-Dependent Test Pattern

Three test classes (`TestStabilityAnalysis`, `TestPerformanceBenchmarking`, `TestAnalysisDashboard`) call functions from `scripts/optimization_analysis.py` that in turn call `infrastructure.scientific` and `infrastructure.reporting`. These tests use the following pattern:

```python
try:
    from projects.code_project.scripts.optimization_analysis import run_stability_analysis
    INFRASTRUCTURE_AVAILABLE = True
except ImportError:
    INFRASTRUCTURE_AVAILABLE = False

@pytest.mark.skipif(not INFRASTRUCTURE_AVAILABLE, reason="infrastructure not available")
def test_stability_analysis_execution(tmp_path):
    result = run_stability_analysis()
    assert result is not None
```

This is **not a mock**. When `infrastructure` is importable (CI, local with `uv sync`), the test runs the real code end-to-end and validates real output. When infrastructure is absent, it skips cleanly. The distinction matters: a mock would substitute a fake for infrastructure; a skip simply does not run the test in that environment.

## Performance and Bounds Validation

The testing philosophy extends beyond correct return values. Using `infrastructure.scientific`, tests automatically map out the algorithm's performance across dimensions (e.g., $d=1$ to $d=50$) and condition variations. If algorithmic behavior violates the theoretical bounds ($O(n)$ time/space, stable convergence factors), the continuous integration pipeline marks the build as failed.

## Structural Rule: If You Need a Mock, Move the Code

The zero-mock constraint is self-enforcing when the architecture is correct. The rule is simple:

- **`src/optimizer.py`** — Pure functions, no I/O, no infrastructure imports → testable with real data
- **`scripts/*.py`** — Orchestrators that do I/O → test via integration, skip when infrastructure unavailable

If you find yourself wanting to mock `open()`, a logger, or an infrastructure module inside a test for `src/`, stop. That call does not belong in `src/`. Move it to `scripts/` and test the mathematical output from `src/` directly.
