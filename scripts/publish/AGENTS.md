# Publishing Scripts — Agent Guide

This document describes how autonomous agents (Hermes, CI/CD systems) should interact with the `scripts/publish/` tooling.

## Purpose

The scripts in this directory automate PyPI release validation and post-publish verification. They are designed to be **non-interactive** and **fully automated** — suitable for CI/CD pipelines, agent workflows, and pre-commit hooks.

## Conventions

### Importability

All scripts are intended to be executed with:

```bash
uv run python scripts/publish/<script>.py
```

This ensures the runtime environment matches the project's dependency resolution via `uv sync`.

### Environment Variables

| Variable | Purpose | Required |
|---|---|---|
| `TEST_PYPI_API_TOKEN` | TestPyPI upload token (for `test_pypi.py`) | Yes |
| `PACKAGE_NAME` | Override package name (default: `template`) | No |
| `INDEX_URL` | Custom package index URL (default: `https://pypi.org/simple/`) | No |

### Exit Codes

- `0` — Success
- non-zero — Failure (build error, upload failure, or verification failure)

### Output

Scripts are verbose by design, printing each command executed and streaming subprocess output. This makes logs self-documenting for agent audit trails.

## Scripts

### test_pypi.py

**Workflow:** Build → Upload → Fresh venv install → `template doctor`

**Usage:**

```bash
export TEST_PYPI_API_TOKEN="pypi-..."
uv run python scripts/publish/test_pypi.py
```

**Expected sequence:**

1. Clean `dist/` directory (remove old builds)
2. `uv build` → produces `dist/*.whl` and `dist/*.tar.gz`
3. `twine upload --repository testpypi ...` → pushes to TestPyPI
4. Create temp virtual environment
5. `pip install <package> --index-url https://test.pypi.org/simple/`
6. Run `<venv>/bin/template doctor`
7. Exit 0 if doctor succeeds; else exit 1

**Agent notes:**

- Run this **before** any production PyPI upload as a gate.
- The script performs a full dependency resolution on TestPyPI; this catches missing dependencies that may not appear in local development.
- Requires `twine` to be available or pip-installable (the script attempts `pip install twine` if module not found).
- The fresh venv approach mimics a real user installation.

### verify_install.py

**Workflow:** Fresh venv → Install from index → Import check → `template doctor`

**Usage:**

```bash
# Against production PyPI (default)
uv run python scripts/publish/verify_install.py

# Against a specific package/index
PACKAGE_NAME=template INDEX_URL=https://test.pypi.org/simple/ uv run python scripts/publish/verify_install.py
```

**Expected sequence:**

1. Create temp virtual environment
2. `pip install <package>` from `INDEX_URL`
3. Import check: `python -c "import template; print(template.__version__)"`
4. Run `template doctor`
5. Exit 0 if both steps succeed; else exit 1

**Agent notes:**

- Run this **after** a production PyPI release to confirm deploy success.
- Also useful as a health check in monitoring (periodic re-verification that the package remains installable).
- If the package name changed (e.g., monorepo with multiple packages), set `PACKAGE_NAME` accordingly.

## Integration with Pre-Commit or CI

Example GitHub Actions step:

```yaml
- name: TestPyPI dry-run
  env:
    TEST_PYPI_API_TOKEN: ${{ secrets.TEST_PYPI_API_TOKEN }}
  run: uv run python scripts/publish/test_pypi.py

- name: Upload to PyPI
  if: success() && github.ref == 'refs/tags/v*'
  run: |
    uv build
    twine upload dist/*
```

## File Locations

- `scripts/publish/test_pypi.py` — TestPyPI integration test
- `scripts/publish/verify_install.py` — Post-publish verification
- `scripts/publish/README.md` — Human-readable usage guide

## Related

- Root-level `AGENTS.md` — Repository-wide agent conventions
- `pyproject.toml` — Package metadata, optional dependencies, and extras definition
- `README.md` — Public-facing installation and usage documentation
