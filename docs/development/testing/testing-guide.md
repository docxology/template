# Testing Guide

> **Test-driven development** with coverage requirements

**Quick Reference:** [Logging Guide](../../operational/logging/) | [Error Handling Guide](../../operational/error-handling-guide.md)

**For detailed testing standards and patterns, see:**
- **[Testing Standards](../../rules/testing_standards.md)** - testing patterns, coverage requirements, and best practices
- **[Testing and Reproducibility](../../guides/testing-and-reproducibility.md)** - Test-driven development (TDD) workflow guide

## Quick Start

```bash
# Run the selected project pipeline test contract:
# focused infrastructure smoke + project coverage suite
uv run python scripts/pipeline/stage_01_test.py --project template_code_project

# Run tests with verbose output (shows all test names)
uv run python scripts/pipeline/stage_01_test.py --project template_code_project --verbose

# Run the full coverage-bearing infrastructure gate
uv run python scripts/pipeline/stage_01_test.py --infra-only --infra-scope full

# Run only the focused infrastructure smoke contract used by project pipelines
uv run python scripts/pipeline/stage_01_test.py --infra-only --infra-scope pipeline-smoke

# Run including slow tests
uv run python scripts/pipeline/stage_01_test.py --include-slow --project template_code_project

# Run specific test suite
uv run pytest tests/infra_tests/ -v

# Run with coverage report
uv run pytest tests/ --cov=src --cov-report=html

# Run only slow tests (requires Ollama for LLM tests)
uv run pytest -m slow
```

`pipeline-smoke` is intentionally small but real: it exercises the declarative
DAG, advisory HITL controls, evidence registry, domain profiles, benchmark
harness, documentation invariant, and tracked-artifact guard. It is the right
default inside `./run.sh --pipeline` because project pipelines already run the
selected project's full coverage suite and then render/validate real outputs.

## Slow Test Handling

### Overview

Tests are categorized by execution speed:
- **Fast tests**: Unit tests, configuration tests, validation tests (< 1 second)
- **Slow tests**: Integration tests using `ollama_test_server` (network calls, LLM queries)

### Default Test Selection

By default, pytest deselects slow, benchmark, private-project, and external-fixture tests to keep the maintained public gate deterministic:

```bash
# Normal test run
uv run python scripts/pipeline/stage_01_test.py

# pytest directly uses the same marker selection from pyproject.toml
uv run pytest tests/
```

### Typed Test Profiles

The orchestrators share one additive profile registry:

- `quick` is the deterministic unit/contract loop; it excludes slow,
  long-running, network, service, and benchmark lanes.
- `release` includes deterministic slow tests and existing coverage floors, but
  excludes long-running and live-service lanes.
- `exhaustive` adds long-running tests; live services and benchmarks remain
  explicit opt-ins.

```bash
uv run python scripts/pipeline/stage_01_test.py --profile quick
uv run python scripts/pipeline/stage_01_test.py --project-only --profile release
uv run python scripts/pipeline/stage_01_test.py --project-only --profile exhaustive
```

Legacy `--include-slow`, `--include-long-running`, `--include-ollama-tests`,
and `--include-bench` flags remain additive for compatibility.

### Running Slow Tests

To include slow tests when needed:

```bash
# Include slow tests in orchestrator
uv run python scripts/pipeline/stage_01_test.py --include-slow

# Run only slow tests (useful for LLM testing)
uv run pytest -m slow

# Run slow tests with verbose output
uv run pytest -m slow -v
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

The test orchestrator (`scripts/pipeline/stage_01_test.py`) generates structured reports:

- **JSON Report**: `projects/{name}/output/reports/test_results.json`
  - Test counts (passed/failed/skipped)
  - Coverage metrics per module
  - Execution time per test file
  - Failure details with stack traces

- **Markdown Report**: `projects/{name}/output/reports/test_results.md`
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

- **90% minimum** for projects/{name}/src/ (see [COUNTS.md](../../_generated/COUNTS.md) for current %)
- **60% minimum** for infrastructure/ (see [coverage-gaps.md](../coverage-gaps.md) for current %)
- **ABSOLUTE PROHIBITION**: Never use mock methods - use data only
- Test all error paths

```bash
# Generate coverage report
uv run pytest tests/ --cov=src --cov-report=html
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

- [Logging Guide](../../operational/logging/)
- [Error Handling Guide](../../operational/error-handling-guide.md)
