# Testing Philosophy: The Zero-Mock Standard

The Generalized Research Template strictly forbids mocking in scientific/mathematical validation.

## The Validation Suite

The `code_project` implements a robust validation suite (`tests/`) that strictly adheres to these standards:

- **Coverage gate**: `projects/code_project/pyproject.toml` enforces ≥90% on `src/` during pytest runs. The suite currently collects **39** tests covering `optimizer.py` and, via imports, thin orchestration in `scripts/optimization_analysis.py`.
- **Pure Computations**: Every test computes real gradients and performs actual gradient descent iterations.
- **Integration without Mocks**: Infrastructure integrations (like performance tracking) are tested via dependency injection, not mocks.

## Performance and Bounds Validation

The testing philosophy extends beyond correct return values. Using `infrastructure.scientific`, tests automatically map out the algorithm's performance across dimensions (e.g., $d=1$ to $d=50$) and condition variations. If algorithmic behavior violates the theoretical bounds ($O(n)$ time/space, stable convergence factors), the continuous integration pipeline marks the build as failed.

If a function is too complex to test without a mock, it is a structural smell indicating the function is not "pure" enough and belongs in a Thin Orchestrator (`scripts/`) rather than the core logic (`src/`).
