# 🛡️ Validation Gates

> **Quality gates** — checks that ensure contributions meet project standards before integration.

This document outlines the validation steps used to maintain code quality, correctness, and consistency in the Research Project Template.

## 📋 Overview

Before submitting a pull request or merging changes, contributors should ensure the following gates are passed:

| Gate | Purpose | How to Run | Status |
|------|---------|-------------|--------|
| **Unit & Integration Tests** | Verify correctness | `uv run pytest -m "not slow"` | ✅ Required |
| **Type Checking (MyPy)** | Catch type errors | `uv run mypy infrastructure/ projects/*/src/` | ⚠️ Optional |
| **Linting & Formatting (Ruff)** | Enforce style & fix common issues | `uvx ruff check infrastructure/ projects/*/src/ --fix && uvx ruff format infrastructure/ projects/*/src/` | ⚠️ Optional |
| **Coverage Thresholds** | Ensure sufficient test coverage | `uv run pytest --cov=...` | ✅ Required |
| **No Mocks Policy** | Validate real-only testing | `uv run python scripts/verify_no_mocks.py` | ✅ Required |

*Note: Type checking and linting can be automated locally via pre-commit hooks (see below).*

## 🔧 Pre-commit Hooks (Optional but Recommended)

To streamline local development, you can install pre-commit hooks that automatically run checks before each commit or push:

- **Pre-commit stage** (`pre-commit`): ruff auto-fixes + mypy type-check on staged Python files
- **Pre-push stage** (`pre-push`): runs unit tests on changed files (with `--maxfail=1`)

### Setup

Run once to install the git hooks:

```bash
uv run python scripts/setup_pre_commit.py
```

This script:
- Installs the `pre-commit` hook
- Installs the `pre-push` hook
- Validates the configuration
- Performs a dry-run of all hooks on all files (manual stage) to verify they work

### Manual Execution

You can also run the hooks manually at any time:

```bash
# Run only pre-commit stage hooks (linters) on all files
pre-commit run --all-files --hook-stage pre-commit

# Run only pre-push stage hooks (unit tests) on all files
pre-commit run --all-files --hook-stage pre-push

# Run all hooks manually
pre-commit run --all-files --hook-stage manual
```

### Hook Details

| Hook | Files | Arguments | Notes |
|------|-------|-----------|-------|
| `ruff` | `infrastructure/ projects/*/src/` | `--fix` | Auto-fixes formatting & lint issues (CI scope) |
| `mypy` | `infrastructure/ projects/*/src/` | (pyproject.toml config) | Uses project type hints (CI scope) |
| `pytest-unit` | Changed `.py` files | `-m unit --maxfail=1` | Stops after first failure |

These hooks respect `.pre-commit-config.yaml` at the repository root.

## 📊 Coverage Gates

All code changes must maintain or improve test coverage:

- **Infrastructure code**: ≥60% coverage
- **Project code**: ≥90% coverage
- **No coverage regression** allowed

Run coverage locally:

```bash
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-fail-under=60 -m "not requires_ollama"
uv run pytest projects/template_code_project/tests/ --cov=projects/template_code_project/src --cov-fail-under=90 -m "not requires_ollama"
```

## 🧪 Testing Policy

- **No mocks**: Tests must use real numerical examples, not mocks.
- **Thin orchestrators**: Scripts in `scripts/` orchestrate; place logic in `infrastructure/` or project `src/`.
- **All new features require tests** (90% project, 60% infrastructure).

## 🔍 Additional Checks

- **`verify_no_mocks.py`**: Ensures no mock usage in tests
- **`audit_filepaths.py`**: Validates file naming and placement conventions
- **PDF rendering**: Full pipeline run (`./run.sh`) must complete without errors

## 📚 Related Documentation

- [Contributing Guide](contributing.md) — How to submit changes
- [Testing Guide](testing/testing-guide.md) — Writing effective tests
- [CI/CD Pipeline](../operational/build/ci-cd-integration.md) — Build and integration pipeline
- [No-Mocks Policy](../development/no-mocks-http-testing.md) — Real-only testing policy
- [Code of Conduct](code-of-conduct.md) — Community standards
