# Testing Standards and Patterns

## Overview

All code in this repository requires **comprehensive test coverage** with **real data only** (no mocks). Tests must be fast, deterministic, and self-documenting.

## Coverage Requirements

### Mandatory Standards

- **Infrastructure modules**: 49% minimum coverage (currently achieving 55.89%)
- **Project code**: 70% minimum coverage (currently achieving 99.88%)
- **Integration tests**: All critical workflows covered
- **Edge cases**: All error paths tested

### Coverage Verification

```bash
# Run tests with coverage report
python3 -m pytest tests/ --cov=infrastructure --cov=project/src --cov-report=html

# View coverage report
open htmlcov/index.html

# Verify coverage meets requirements
python3 -m pytest tests/ --cov=infrastructure --cov-fail-under=49
python3 -m pytest project/tests/ --cov=project/src --cov-fail-under=70
```

## Test Organization

### Directory Structure

```
tests/
├── __init__.py                      # Makes tests a package
├── conftest.py                      # Shared fixtures
├── infrastructure/                  # Infrastructure module tests
│   ├── test_core/                  # Core functionality tests
│   │   ├── __init__.py
│   │   ├── conftest.py             # Module-specific fixtures
│   │   ├── test_basic.py           # Basic functionality
│   │   ├── test_edge_cases.py      # Edge cases and errors
│   │   └── test_integration.py     # End-to-end workflows
│   └── validation/                 # Example module
│       ├── __init__.py
│       └── test_*.py
├── scientific/                      # Scientific code tests
│   └── test_*.py
└── integration/                     # End-to-end tests
    └── test_*.py
```

### Module Test Organization

For each infrastructure module:

```
tests/infrastructure/test_<module>/
├── __init__.py
├── conftest.py                  # Fixtures: sample data, temp files
├── test_core.py                 # Core functionality
├── test_cli.py                  # CLI interface (if applicable)
├── test_errors.py               # Error conditions
└── test_integration.py          # End-to-end workflows
```

## Testing Principles

### 1. No Mocks - Use Real Data

**CRITICAL**: Never use `MagicMock`, `mocker.patch`, `unittest.mock`, or any mocking framework.

```python
# ✅ GOOD: Test with real data
def test_validation_passes():
    data = {"name": "Alice", "age": 30}
    assert validate_data(data) is True

# ❌ BAD: Using mock data
def test_validation_passes():
    mock_data = MagicMock()  # NEVER use MagicMock
    mock_data.name = "Alice"
    assert validate_data(mock_data) is True

# ❌ BAD: Using mocker.patch
def test_with_mock(mocker):
    mocker.patch("module.function")  # NEVER use mocker.patch
```

### Network-Dependent Modules

For modules requiring external services (LLM, Literature, Publishing APIs):

1. **Pure Logic Tests**: Test configuration, validation, data handling without network
2. **Integration Tests**: Mark with `@pytest.mark.requires_ollama` (or similar marker)
3. **Skip Gracefully**: Tests auto-skip when service unavailable

```python
# ✅ GOOD: Pure logic test (no network needed)
def test_config_from_env(clean_llm_env):
    os.environ["OLLAMA_HOST"] = "http://test:11434"
    config = LLMConfig.from_env()
    assert config.base_url == "http://test:11434"

# ✅ GOOD: Integration test with marker
@pytest.mark.requires_ollama
class TestLLMIntegration:
    @pytest.fixture(autouse=True)
    def check_ollama(self):
        client = LLMClient()
        if not client.check_connection():
            pytest.skip("Ollama server not available")
    
    def test_query(self):
        client = LLMClient()
        response = client.query("Hello")
        assert response is not None

# Run commands:
# pytest -m "not requires_ollama"  # Skip network tests
# pytest -m requires_ollama        # Only network tests
```

### 2. Test Behavior, Not Implementation

```python
# ✅ GOOD: Test the observable behavior
def test_sort_returns_sorted_list():
    result = sort_numbers([3, 1, 2])
    assert result == [1, 2, 3]

# ❌ BAD: Testing implementation details
def test_sort_uses_sorted_builtin():
    with patch('builtins.sorted') as mock:
        sort_numbers([3, 1, 2])
        mock.assert_called_once()
```

### 3. Clear, Self-Documenting Names

```python
# ✅ GOOD: Name clearly describes what's tested
def test_validation_fails_when_email_is_missing():
    data = {"name": "Alice"}  # No email
    with pytest.raises(ValidationError):
        validate_user_data(data)

# ❌ BAD: Unclear what's tested
def test_validation_error():
    data = {}
    with pytest.raises(ValidationError):
        validate_user_data(data)
```

### 4. Fast Execution

```python
# ✅ GOOD: Unit tests < 1 second
def test_format_string():
    result = format_date(datetime(2025, 1, 1))
    assert result == "2025-01-01"

# ❌ BAD: Slow integration tests in unit test suite
def test_format_string():
    # Writes to file, reads from API, etc.
    # Takes 10 seconds
```

### 5. Isolated Tests

```python
# ✅ GOOD: Each test is independent
def test_add():
    assert add(2, 2) == 4

def test_subtract():
    assert subtract(4, 2) == 2

# ❌ BAD: Tests depend on each other
def test_initialization():
    global calculator
    calculator = Calculator()

def test_add():
    global calculator
    assert calculator.add(2, 2) == 4
```

## Test Patterns

### Arrange-Act-Assert (AAA)

```python
def test_user_creation():
    # Arrange: Set up test data
    user_data = {"name": "Alice", "email": "alice@example.com"}
    
    # Act: Perform the action
    user = create_user(**user_data)
    
    # Assert: Verify the result
    assert user.name == "Alice"
    assert user.email == "alice@example.com"
```

### Testing Error Conditions

```python
def test_validation_error_has_context():
    """Test that validation errors include helpful context."""
    try:
        validate_email("invalid-email")
    except ValidationError as e:
        assert "email" in str(e).lower()
        assert "invalid" in str(e).lower()
    else:
        pytest.fail("ValidationError not raised")

# Or using pytest.raises
def test_validation_error_with_pytest_raises():
    """Cleaner approach using pytest.raises."""
    with pytest.raises(ValidationError) as exc_info:
        validate_email("invalid-email")
    
    assert "invalid" in str(exc_info.value).lower()
```

### Testing with Fixtures

```python
# conftest.py - Shared fixtures
import pytest

@pytest.fixture
def sample_data():
    """Provide sample test data."""
    return {
        "name": "Alice",
        "email": "alice@example.com",
        "age": 30
    }

@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file."""
    file = tmp_path / "test.txt"
    file.write_text("test content")
    return file

# test_module.py - Use fixtures
def test_user_creation(sample_data):
    """Test using fixture."""
    user = create_user(**sample_data)
    assert user.name == sample_data["name"]

def test_file_reading(temp_file):
    """Test using temporary file."""
    content = read_file(temp_file)
    assert content == "test content"
```

### Parameterized Tests

```python
import pytest

@pytest.mark.parametrize("input,expected", [
    ("123", 123),
    ("456", 456),
    ("0", 0),
    ("-123", -123),
])
def test_parse_integer(input, expected):
    """Test parsing various integer strings."""
    assert parse_integer(input) == expected

@pytest.mark.parametrize("invalid_input", [
    "abc",      # Not a number
    "12.34",    # Float, not int
    "",         # Empty
])
def test_parse_integer_invalid(invalid_input):
    """Test that invalid inputs raise errors."""
    with pytest.raises(ValueError):
        parse_integer(invalid_input)
```

### Testing Logging

```python
def test_operation_is_logged(caplog):
    """Test that operation is properly logged."""
    import logging
    caplog.set_level(logging.INFO)
    
    perform_operation()
    
    assert "Operation started" in caplog.text
    assert "Operation completed" in caplog.text
```

## Integration Testing

### End-to-End Workflows

```python
# tests/integration/test_validation_pipeline.py
def test_full_validation_pipeline():
    """Test complete validation workflow."""
    # 1. Load data from file
    data = load_test_data("sample.csv")
    
    # 2. Validate all records
    results = validate_all(data)
    
    # 3. Check results
    assert results.valid_count == 95
    assert results.error_count == 5
    
    # 4. Generate report
    report = generate_report(results)
    assert "95 valid" in report
```

### Testing Script Execution

```python
# tests/integration/test_script_execution.py
def test_analysis_script_generates_output(tmp_path):
    """Test that analysis script produces expected output."""
    import subprocess
    
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Run script
    result = subprocess.run(
        ["python3", "scripts/example_figure.py", str(output_dir)],
        capture_output=True,
        text=True
    )
    
    # Check execution
    assert result.returncode == 0
    
    # Check output files
    assert (output_dir / "figure.png").exists()
```

## Common Fixtures

### conftest.py - Project-Wide Fixtures

```python
import pytest
from pathlib import Path
import tempfile

@pytest.fixture
def test_data_dir():
    """Path to test data directory."""
    return Path(__file__).parent / "data"

@pytest.fixture
def sample_data():
    """Load sample test data."""
    return {
        "count": 100,
        "items": list(range(100))
    }

@pytest.fixture
def temp_dir():
    """Create temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def logger_mock(caplog):
    """Mock logger for testing logging."""
    import logging
    caplog.set_level(logging.DEBUG)
    return caplog
```

## Running Tests

### Basic Commands

```bash
# Run all tests
python3 -m pytest tests/

# Run specific test file
python3 -m pytest tests/infrastructure/test_core/test_basic.py

# Run specific test function
python3 -m pytest tests/infrastructure/test_core/test_basic.py::test_validation_passes

# Run with verbose output
python3 -m pytest tests/ -v

# Run with coverage
python3 -m pytest tests/ --cov=infrastructure --cov=project/src

# Run with coverage and HTML report
python3 -m pytest tests/ --cov=infrastructure --cov-report=html

# Stop at first failure
python3 -m pytest tests/ -x

# Show print statements
python3 -m pytest tests/ -s
```

### Filtering Tests

```bash
# Run only tests matching a pattern
python3 -m pytest tests/ -k "validation"

# Run all error tests
python3 -m pytest tests/ -k "error"

# Run excluding certain tests
python3 -m pytest tests/ --ignore=tests/integration/
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: "3.11"
      
      - name: Install dependencies
        run: |
          python3 -m pip install -r requirements.txt
          python3 -m pip install pytest pytest-cov
      
      - name: Run tests
        run: python3 -m pytest tests/ --cov=infrastructure --cov=project/src --cov-fail-under=100
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Debugging Tests

### Print Debugging

```bash
# Show print statements in passing tests
python3 -m pytest tests/ -s

# Show print statements only for failures
python3 -m pytest tests/ --tb=short
```

### Interactive Debugging

```bash
# Use pdb (Python debugger)
python3 -m pytest tests/ --pdb

# Drop to debugger on failure
python3 -m pytest tests/ --pdb --lf
```

### Viewing Test Output

```bash
# Show full traceback
python3 -m pytest tests/ --tb=long

# Short traceback
python3 -m pytest tests/ --tb=short

# No traceback
python3 -m pytest tests/ --tb=no
```

## Quality Checklist

Before committing tests:

- [ ] Coverage requirements met (49% infra, 70% project) verified
- [ ] All tests pass (`pytest tests/`)
- [ ] No skipped tests (`-k "not skip"`)
- [ ] Tests run in < 30 seconds total
- [ ] Test names are clear and descriptive
- [ ] No mocks or patches used
- [ ] Real data used in all tests
- [ ] Edge cases tested
- [ ] Error conditions tested
- [ ] Documentation added to AGENTS.md and README.md

## See Also

- [error_handling.md](error_handling.md) - Exception patterns for tests
- [documentation_standards.md](documentation_standards.md) - Documenting tests
- [../docs/ADVANCED_USAGE.md](../docs/ADVANCED_USAGE.md) - Test-driven development guide
- [../docs/TEST_IMPROVEMENTS_SUMMARY.md](../docs/TEST_IMPROVEMENTS_SUMMARY.md) - Test enhancements
- [../docs/TESTING_GUIDE.md](../docs/TESTING_GUIDE.md) - Testing best practices
- [../tests/AGENTS.md](../tests/AGENTS.md) - Test framework setup
- [pytest Documentation](https://docs.pytest.org/)




