# Testing Guide

> **Test-driven development** with 100% coverage requirement

**Quick Reference:** [Logging Guide](LOGGING_GUIDE.md) | [Error Handling Guide](ERROR_HANDLING_GUIDE.md)

## Quick Start

```bash
# Run all tests with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/test_example.py -v

# Run with new logging/exceptions
pytest tests/infrastructure/test_logging_utils.py -v
pytest tests/infrastructure/test_exceptions.py -v
```

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

- 100% coverage for project/src/
- 100% coverage for infrastructure/
- No mock methods - use real data
- Test all error paths

```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

## Best Practices

### Do's ✅
- Write tests first (TDD)
- Use real data, no mocks
- Test error paths
- Use descriptive names
- One assertion per concept

### Don'ts ❌
- Don't use mock methods
- Don't skip tests
- Don't test implementation details
- Don't ignore coverage gaps

## See Also

- [Logging Guide](LOGGING_GUIDE.md)
- [Error Handling Guide](ERROR_HANDLING_GUIDE.md)



