# Testing Guide

> **Test-driven development** with coverage requirements

**Quick Reference:** [Logging Guide](../operational/LOGGING_GUIDE.md) | [Error Handling Guide](../operational/ERROR_HANDLING_GUIDE.md)

**For detailed testing standards and patterns, see:**
- **[Testing Standards](../../.cursorrules/testing_standards.md)** - testing patterns, coverage requirements, and best practices
- **[Testing and Reproducibility](../guides/TESTING_AND_REPRODUCIBILITY.md)** - Test-driven development (TDD) workflow guide

## Quick Start

```bash
# Run all tests with coverage (quiet mode by default, skips slow tests)
python3 scripts/01_run_tests.py

# Run tests with verbose output (shows all test names)
python3 scripts/01_run_tests.py --verbose

# Run including slow tests (LLM integration tests)
python3 scripts/01_run_tests.py --include-slow

# Run specific test suite
pytest tests/infra_tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Run only slow tests (requires Ollama for LLM tests)
pytest -m slow
```

## Slow Test Handling

### Overview

Tests are categorized by execution speed:
- **Fast tests**: Unit tests, configuration tests, validation tests (< 1 second)
- **Slow tests**: Integration tests using `ollama_test_server` (network calls, LLM queries)

### Automatic Slow Test Skipping

By default, slow tests are **automatically skipped** to ensure fast test runs:

```bash
# Normal test run (skips slow tests)
python3 scripts/01_run_tests.py

# pytest directly (also skips slow tests due to addopts)
pytest tests/
```

### Running Slow Tests

To include slow tests when needed:

```bash
# Include slow tests in orchestrator
python3 scripts/01_run_tests.py --include-slow

# Run only slow tests (useful for LLM testing)
pytest -m slow

# Run slow tests with verbose output
pytest -m slow -v
```

### Test Timeout Protection

All tests are protected by a **10-second timeout** to prevent hanging:

```python
# pytest-timeout plugin automatically kills tests after 10 seconds
@pytest.mark.timeout(10)  # Applied globally via pyproject.toml

def test_llm_query(ollama_test_server):
    """Test that times out after 10 seconds if it hangs."""
    # Test implementation
```

**Timeout Behavior:**
- Tests that exceed 10 seconds are automatically terminated
- Prevents infinite hangs from network issues or bugs
- Can be adjusted per-test with `@pytest.mark.timeout(seconds)`

## Test Reporting

The test orchestrator (`scripts/01_run_tests.py`) generates structured reports:

- **JSON Report**: `project/output/reports/test_results.json`
  - Test counts (passed/failed/skipped)
  - Coverage metrics per module
  - Execution time per test file
  - Failure details with stack traces

- **Markdown Report**: `project/output/reports/test_results.md`
  - Human-readable summary
  - Test statistics
  - Coverage summary

- **HTML Coverage**: `htmlcov/index.html`
  - Interactive coverage report
  - Line-by-line coverage details

## Test Structure

```python
"""Tests for module_name.py"""
import pytest
from module_name import function_to_test

class TestFunctionName:
    """Test suite for function_to_test."""
    
    def test_basic_functionality(self):
        """Test basic usage."""
        result = function_to_test("input")
        assert result == "expected"
    
    def test_error_handling(self):
        """Test error conditions."""
        with pytest.raises(ValueError):
            function_to_test(invalid_input)
```

## Testing with Logging

```python
def test_logging_output(caplog):
    """Test function logs correctly."""
    logger = get_logger("test")
    
    with caplog.at_level(logging.INFO):
        function_that_logs()
    
    messages = [rec.message for rec in caplog.records]
    assert any("Expected message" in msg for msg in messages)
```

## Testing with Exceptions

```python
def test_raises_specific_exception():
    """Test function raises correct exception."""
    with pytest.raises(ValidationError) as exc_info:
        validate_invalid_data()
    
    error = exc_info.value
    assert "expected message" in error.message
    assert error.context["file"] == "data.csv"
```

## Fixtures

```python
@pytest.fixture
def temp_data_file(tmp_path):
    """Create temporary data file."""
    data_file = tmp_path / "data.csv"
    data_file.write_text("col1,col2\n1,2\n")
    return data_file

def test_with_fixture(temp_data_file):
    """Test using fixture."""
    data = load_data(temp_data_file)
    assert len(data) == 1
```

## Coverage Requirements

- **90% minimum** for project/src/ (currently achieving 100% - coverage!)
- **60% minimum** for infrastructure/ (currently achieving 83.33% - exceeds stretch goal!)
- **ABSOLUTE PROHIBITION**: Never use mock methods - use data only
- Test all error paths

```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

## Best Practices

### Do's ✅
- Write tests first (TDD)
- Use data, no mocks
- Test error paths
- Use descriptive names
- One assertion per concept

### Don'ts ❌
- **ABSOLUTELY FORBIDDEN**: Never use mock methods, MagicMock, mocker.patch, or any mocking
- Don't skip tests
- Don't test implementation details
- Don't ignore coverage gaps

## See Also

- [Logging Guide](../operational/LOGGING_GUIDE.md)
- [Error Handling Guide](../operational/ERROR_HANDLING_GUIDE.md)






