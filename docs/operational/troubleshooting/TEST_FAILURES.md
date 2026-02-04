# Test Failures Troubleshooting

> **Solutions** for pytest, coverage, and testing issues

**Quick Reference:** [Main Troubleshooting](../TROUBLESHOOTING_GUIDE.md) | [Testing Guide](../../development/TESTING_GUIDE.md)

---

## Quick Diagnosis

```bash
# Run single test
uv run pytest tests/test_example.py::test_add_numbers -v

# Check imports
python -c "from example import add_numbers; print('OK')"

# Verify test data
ls -la tests/test_data/
```

---

## Common Test Errors

### ImportError: No module named

**Symptom:** `ImportError: No module named 'module_name'`

**Solutions:**

```bash
# Check if module is installed
uv pip list | grep module_name

# Install missing module
uv add module_name

# Add to Python path if local module
export PYTHONPATH="${PYTHONPATH}:path/to"

# Check Python path
python -c "import sys; print(sys.path)"
```

---

### AssertionError

**Symptom:** `AssertionError: Expected value but got other`

**Diagnosis:**

```bash
# Run test with verbose output
uv run pytest tests/test_file.py -vv

# Run specific test
uv run pytest tests/test_file.py::test_function -v

# Check test data
cat tests/test_data.json
```

**Debug steps:**

1. Run test in isolation
2. Add debug output (print intermediate values)
3. Check test data
4. Review test logic

---

### Coverage Below Threshold

**Symptom:** `Coverage: 65% (below 90% requirement)`

**Diagnosis:**

```bash
# Generate coverage report
uv run pytest tests/ --cov=src --cov-report=term-missing

# View HTML report
open htmlcov/index.html

# Find missing lines
uv run pytest tests/ --cov=src --cov-report=term-missing | grep ">>>>>"
```

**Solutions:**

1. Identify gaps in coverage report
2. Add tests for uncovered code paths
3. Test edge cases and boundary conditions
4. Test error paths and exception handling

---

## Test Failure Tolerance

**Feature:** Configure maximum allowed test failures.

```bash
export MAX_TEST_FAILURES=5  # Allow up to 5 failures
```

**Default:** `0` (strict - any failure halts pipeline)

**When to use:**

- ✅ Development - work on features with some tests broken
- ✅ Migration - gradual fixing of test suites
- ❌ Production - should always be 0
- ❌ Releases - all tests must pass

---

## Subprocess Execution Issues

**Symptom:** pytest fails with subprocess errors

**Solution:** Tests include skip logic:

```python
@pytest.mark.integration
def test_uv_sync_when_available(tmp_path):
    if not shutil.which('uv'):
        pytest.skip("uv not installed")
    # Real uv sync execution...
```

**Run tests selectively:**

```bash
# Skip integration tests
pytest tests/ -m "not integration"

# Run only integration tests
pytest tests/ -m integration
```

---

## All Tests Fail

**Checklist:**

- [ ] Python version correct
- [ ] Dependencies installed (`uv sync`)
- [ ] Test data exists and readable
- [ ] Import paths configured
- [ ] pytest configuration correct

**Diagnostic:**

```bash
uv run pytest tests/test_example.py::test_add_numbers -v
python -c "from example import add_numbers; print('OK')"
ls -la tests/test_data/
```

---

## Debug Commands

```bash
# Run with debugger
uv run pytest tests/test_file.py::test_function --pdb

# Run with verbose output
uv run pytest tests/test_file.py::test_function -vv -s

# Check specific module coverage
uv run pytest tests/test_file.py --cov=src.module_name --cov-report=term-missing

# Parallel execution
uv run pytest tests/ -n auto
```

---

**Related:** [Environment Setup](ENVIRONMENT_SETUP.md) | [Testing Guide](../../development/TESTING_GUIDE.md) | [Main Guide](../TROUBLESHOOTING_GUIDE.md)
