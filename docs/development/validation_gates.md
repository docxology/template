# Validation Gates

> Quality gates — checks that ensure contributions meet project standards before integration.

This document outlines the validation steps used to maintain code quality, correctness, and consistency in the Research Project Template.

## Overview

Before submitting a pull request or merging changes, contributors should ensure the following gates are passed:

| Gate | Purpose | How to Run | Status |
|------|---------|-------------|--------|
| **Unit & Integration Tests** | Verify correctness | `uv run pytest -m "not slow"` | Required |
| **Type Checking (MyPy)** | Catch type errors on public CI paths | `uv run python -m infrastructure.project.public_scope source-paths \| xargs uv run mypy` | Required (pre-commit + CI) |
| **Linting & Formatting (Ruff)** | Enforce style & fix common issues | `uv run python -m infrastructure.project.public_scope source-paths \| xargs uvx ruff check --fix` | Required (pre-commit + CI) |
| **Coverage Thresholds** | Ensure sufficient test coverage | `uv run pytest --cov=...` | Required |
| **No Mocks Policy** | Validate real-only testing | `uv run python scripts/verify_no_mocks.py` | Required (pre-push + CI) |

Type checking and linting are blocking in CI and in the default pre-commit hook stage when you install hooks locally.

## Pre-commit Hooks (Recommended)

Install hooks after `uv sync` so local runs mirror CI:

- **Commit stage** (`pre-commit`): Ruff + mypy on public CI source paths (blocking)
- **Pre-push stage** (`pre-push`): no-mocks check, short pytest smoke, Bandit (`bandit.yaml`), skills manifest + `__all__` export audit

### Setup

```bash
uv run python scripts/maintenance/setup_pre_commit.py
```

This script installs commit and pre-push hooks, validates configuration, and can dry-run hooks.

### Manual Execution

```bash
# Commit-stage linters on all files
pre-commit run --all-files --hook-stage pre-commit

# Pre-push gates on all files
pre-commit run --all-files --hook-stage pre-push
```

### Hook Details

See [`.pre-commit-config.yaml`](../../.pre-commit-config.yaml) for the authoritative hook list. Typical entries:

| Hook | Stage | Notes |
|------|-------|-------|
| `ruff` / `ruff-format` | pre-commit | Public CI source paths |
| `mypy` | pre-commit | Public CI source paths |
| `verify-no-mocks` | pre-push | Blocks mock imports in tests |
| `pre-push-quick` | pre-push | Short pytest smoke + tracked-project guards |
| `bandit` | pre-push | Security scan per `bandit.yaml` |
| `skills-check` / `all-exports-check` | pre-push | Manifest and re-export hygiene |

## Coverage Gates

All code changes must maintain or improve test coverage:

- **Infrastructure code**: ≥60% coverage
- **Project code**: ≥90% coverage
- **No coverage regression** allowed

Run coverage locally:

```bash
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-fail-under=60 -m "not requires_ollama"
uv run pytest projects/templates/template_code_project/tests/ --cov=projects/templates/template_code_project/src --cov-fail-under=90 -m "not requires_ollama"
```

## Testing Policy

- **No mocks**: Tests must use real numerical examples, not mocks.
- **Thin orchestrators**: Scripts in `scripts/` orchestrate; place logic in `infrastructure/` or project `src/`.
- **All new features require tests** (90% project, 60% infrastructure).

## Additional Checks

- **`verify_no_mocks.py`**: Ensures no mock usage in tests
- **`audit_filepaths.py`**: Validates file naming and placement conventions
- **`lint_docs.py`**: Markdown link, Mermaid, and consistency lint across docs
- **PDF rendering**: Full pipeline run (`./run.sh`) must complete without errors

## Related Documentation

- [Contributing Guide](contributing.md) — How to submit changes
- [Testing Guide](testing/testing-guide.md) — Writing effective tests
- [CI/CD Pipeline](../operational/build/ci-cd-integration.md) — Build and integration pipeline
- [No-Mocks Policy](../development/no-mocks-http-testing.md) — Real-only testing policy
- [Code of Conduct](code-of-conduct.md) — Community standards
