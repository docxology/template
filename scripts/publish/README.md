# Publishing Scripts

This directory contains scripts for PyPI package publishing and installation verification.

## Files

- **test_pypi.py** — Builds the package, uploads to TestPyPI, and verifies installation in a clean venv.
- **verify_install.py** — Verifies the published package installs and runs correctly from PyPI (production).

## Prerequisites

- `uv` installed and available in PATH
- `twine` installed (automatically handled by test_pypi.py)
- For TestPyPI upload: `TEST_PYPI_API_TOKEN` environment variable set with an API token from https://test.pypi.org/manage/account/token/

## Workflow

### 1. TestPyPI Dry Run

Before publishing to production PyPI, do a full end-to-end test on TestPyPI:

```bash
export TEST_PYPI_API_TOKEN="pypi-xxxx..."
uv run python scripts/publish/test_pypi.py
```

What this does:
1. Runs `uv build` to create wheel and sdist in `dist/`
2. Uploads all distributions to TestPyPI via `twine`
3. Creates a fresh virtual environment
4. Installs the package from TestPyPI
5. Runs `template doctor` to verify the installation works
6. Reports success or failure

If this succeeds, your package is ready for production publish.

### 2. Production Publish

Upload to the real PyPI:

```bash
# Using twine directly (recommended after test passes)
twine upload dist/*

# Or use uv build + twine upload
uv build
twine upload dist/*
```

You will be prompted for your PyPI API token (or use `--username __token__ --password <token>`).

### 3. Post-Publish Verification

After the package is live on PyPI, verify it can be installed cleanly:

```bash
uv run python scripts/publish/verify_install.py
```

This creates a fresh venv, installs from https://pypi.org/simple/, and runs `template doctor` to confirm everything works.

### Optional Environment Variables

- `PACKAGE_NAME` — Override package name (default: `template`)
- `INDEX_URL` — Use a custom package index URL (default: `https://pypi.org/simple/`)
- `TEST_PYPI_API_TOKEN` — TestPyPI API token (required for test_pypi.py)

## Troubleshooting

### twine not found

`test_pypi.py` will attempt to install twine automatically if not present. If that fails, install manually:

```bash
pip install twine
```

### Build failures

Ensure pyproject.toml is valid and all version constraints are satisfied:

```bash
uv sync --all-groups  # check dependency resolution
```

### template doctor fails after install

This usually means a missing runtime dependency or import error. Check that all required dependencies are declared correctly in pyproject.toml `[project]` and `[project.optional-dependencies]`.

### TestPyPI upload rejects package

- Verify the package name is available on TestPyPI
- Check that version is unique (TestPyPI requires version bump for re-upload)
- Ensure `TEST_PYPI_API_TOKEN` has upload scope
