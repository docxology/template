# Testing Philosophy: The Zero-Mock Standard

The Generalized Research Template strictly forbids mocking in scientific/mathematical validation.

## The Validation Suite

The `code_project` implements a robust validation suite (`tests/`) that strictly adheres to these standards:

- **100% Test Coverage**: Enforced via `pyproject.toml`, ensuring no logic escapes validation. The `code_project` currently sustains a 45-test suite over the `optimizer.py` and reporting scripts.
- **Pure Computations**: Every test computes real gradients and performs actual gradient descent iterations.
- **Integration without Mocks**: Infrastructure integrations (like performance tracking) are tested via dependency injection, not mocks.

## Performance and Bounds Validation

The testing philosophy extends beyond correct return values. Using `infrastructure.scientific`, tests automatically map out the algorithm's performance across dimensions (e.g., $d=1$ to $d=50$) and condition variations. If algorithmic behavior violates the theoretical bounds ($O(n)$ time/space, stable convergence factors), the continuous integration pipeline marks the build as failed.

If a function is too complex to test without a mock, it is a structural smell indicating the function is not "pure" enough and belongs in a Thin Orchestrator (`scripts/`) rather than the core logic (`src/`).
