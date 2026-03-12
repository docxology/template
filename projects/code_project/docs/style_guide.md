# Style Guide

This document defines the coding and communication style for the `code_project` exemplar.

## 1. Zero-Mock Policy

The most critical style rule is the absolute prohibition of mocking (`unittest.mock`, `MagicMock`, `@patch`, etc.). All tests must run against real mathematical logic or local deterministic servers.

## 2. Infrastructure Delegation

Project code should **never** implement its own logging, PDF rendering, or basic data validation validation.

- Use `infrastructure.core.logging_utils.ProjectLogger` for logging.
- Use `infrastructure.core.progress.PipelineProgress` for CLI progress updates.

## 3. The Thin Orchestrator Pattern

Files in `scripts/` must be "thin orchestrators". They must not contain any `for` loops computing math, or implementation-heavy logic. They simply connect `src/` to `infrastructure/`.

## 4. Manuscript "Show, Not Tell"

When editing manuscript markdown (e.g. `02_methodology.md`), do not use vague terms like "the test suite". Use explicit, verifiable file paths:

- **BAD**: "Our testing framework verifies gradient calculations."
- **GOOD**: "The test suite in `projects/code_project/tests/test_optimizer.py` verifies gradient calculations without mocks."

## 5. Explicit Absolute File Paths

When AI agents or humans refer to files in logs, documentation, or implementation plans, always use the absolute file path relative to the repository root (e.g. `projects/code_project/src/optimizer.py`) to prevent ambiguity.
