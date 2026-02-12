# Environment Setup Troubleshooting

> **Systematic solutions** for environment-related issues

**Quick Reference:** [Main Troubleshooting](../troubleshooting-guide.md) | [Build Tools](build-tools.md) | [Configuration](../configuration.md)

## Diagnostic Commands

```bash
# System information
python --version
uv --version
pandoc --version
xelatex --version

# Environment variables
env | grep -E "AUTHOR|PROJECT|DOI"

# Dependency status
uv tree
uv pip list
```

---

## Python Environment Issues

### Missing `patch` Import in Tests

**Symptom:** `NameError: name 'patch' is not defined`

**Cause:** This template **absolutely prohibits** mocks. All tests must use real data.

**Solution:**

```python
# ✅ CORRECT: Use real data
def test_function_with_real_data():
    real_data = load_test_dataset("sample.csv")
    result = process_data(real_data)
    assert result is not None

# ❌ FORBIDDEN: Never use mocks
```

---

### Optional `python-dotenv` Dependency

**Symptom:** `ModuleNotFoundError: No module named 'dotenv'`

**Solution:** System uses conditional import with graceful fallback. Install optionally:

```bash
pip install python-dotenv  # or: uv add python-dotenv
```

---

### Missing `infrastructure.build` Modules

**Symptom:** `ModuleNotFoundError: No module named 'infrastructure.build'`

**Solution:** Scripts use graceful fallback with stub functions. No action needed.

---

## uv Package Manager Issues

### uv sync Failures

**Symptom:** `uv sync failed (exit code 1): error: Failed to download and build Python`

**Solutions:**

```bash
# Use system Python instead of building
export UV_PYTHON_PREFERENCE=system

# Install system build tools if needed
# Ubuntu/Debian:
sudo apt-get install -y build-essential cargo pkg-config

# macOS:
xcode-select --install

# Clean and retry
uv cache clean
uv sync
```

---

### uv Not Found in PATH

**Symptom:** `uv not found in PATH`

**Solution:**

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH
export PATH="$HOME/.cargo/bin:$PATH"

# Verify
uv --version
```

---

## Matplotlib Configuration Issues

**Symptom:** `Exit code 134 (SIGABRT)` or `/Users/.../.matplotlib is not a writable directory`

**Solution:**

```bash
export MPLBACKEND=Agg
export MPLCONFIGDIR=/tmp/matplotlib
python3 scripts/02_run_analysis.py
```

---

## VIRTUAL_ENV Warning Messages

**Symptom:** `warning: VIRTUAL_ENV=... does not match the project environment path`

**Status:** Harmless warning. The system automatically handles this.

---

## Environment Variables Reference

| Variable | Default | Purpose |
|----------|---------|---------|
| `MAX_TEST_FAILURES` | `0` | Maximum allowed test failures |
| `MPLBACKEND` | (system) | Matplotlib backend |
| `MPLCONFIGDIR` | `~/.matplotlib` | Matplotlib config directory |
| `LOG_LEVEL` | `1` | Logging verbosity (0=DEBUG, 1=INFO) |
| `AUTHOR_NAME` | `"Project Author"` | Primary author name |
| `AUTHOR_ORCID` | `"0000-0000-0000-0000"` | Author ORCID |
| `PROJECT_TITLE` | `"Project Title"` | Project title |
| `DOI` | `""` | Digital Object Identifier |

---

## Quick Diagnostics

```bash
# Show all template-related variables
env | grep -E "MAX_TEST|MPL|LOG_LEVEL|AUTHOR|PROJECT|DOI"

# Test matplotlib configuration
python3 -c "import matplotlib; print(matplotlib.get_backend())"

# Verify LaTeX installation
which xelatex && echo "LaTeX OK" || echo "LaTeX missing"

# Check Python imports
python3 -c "from infrastructure.core import credentials; print('Imports OK')"
```

---

**Related:** [Build Tools](build-tools.md) | [Test Failures](test-failures.md) | [Main Guide](../troubleshooting-guide.md)
