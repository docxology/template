# Testing Philosophy: The Zero-Mock Standard

The Generalized Research Template strictly forbids mocking in scientific/mathematical validation.

## The 45-Test Exemplar Suite

The `code_project` implements a 45-test validation suite (`tests/test_optimizer.py`) that strictly adheres to this standard:

- **100% Test Coverage**: Enforced via `pyproject.toml`, ensuring no logic escapes validation.
- **Pure Computations**: Every test computes real gradients and performs actual gradient descent iterations.
- **Integration without Mocks**: Infrastructure integrations (like performance tracking) are tested via dependency injection, not mocks.

If a function is too complex to test without a mock, it is a structural smell indicating the function is not "pure" enough and belongs in a Thin Orchestrator (`scripts/`) rather than the core logic (`src/`).
