# Style Guide

This document defines the coding and communication style for the `code_project` exemplar.

## 1. Zero-Mock Policy

The most critical style rule is the absolute prohibition of mocking (`unittest.mock`, `MagicMock`, `@patch`, etc.). All tests must run against real mathematical logic or local deterministic servers.

## 2. Infrastructure Delegation

Project code should **never** implement its own logging, PDF rendering, or basic data validation validation.

- `projects/code_project/src/` must not import `infrastructure.*`. `src/` is infrastructure-independent and may use stdlib logging (`logging.getLogger(__name__)`).
- Use `infrastructure.core.logging.utils` in `projects/code_project/scripts/` (and in the pipeline) for structured logging configuration.
- Use `infrastructure.core.progress.PipelineProgress` for CLI progress updates.

## 3. The Thin Orchestrator Pattern

Files in `scripts/` must be "thin orchestrators": they may run experiment loops and generate plots, but must not re-implement algorithms that belong in `projects/code_project/src/` (e.g., the gradient descent update rule). Scripts should compose `src/` functions and route cross-cutting concerns through `infrastructure/`.

## 4. Manuscript "Show, Not Tell"

When editing manuscript markdown (e.g. `02_methodology.md`), do not use vague terms like "the test suite". Use explicit, verifiable file paths:

- **BAD**: "Our testing framework verifies gradient calculations."
- **GOOD**: "The test suite in `projects/code_project/tests/test_optimizer.py` verifies gradient calculations without mocks."

## 5. Explicit Absolute File Paths

When AI agents or humans refer to files in logs, documentation, or implementation plans, always use the absolute file path relative to the repository root (e.g. `projects/code_project/src/optimizer.py`) to prevent ambiguity.
