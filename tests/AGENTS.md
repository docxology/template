# tests/ - Test Suite

## Purpose

The `tests/` directory ensures **100% test coverage** for all `src/` modules. Tests validate that core business logic works correctly using real data and real computations.

## Testing Philosophy

### Test-Driven Development (TDD)
1. Write tests first
2. Implement functionality in `src/`
3. Run tests until they pass
4. Refactor with confidence

### No Mocks Policy
- **Always use real data** and real computations
- **No mock methods** - test actual behavior
- Create temporary directories/files for testing
- Use deterministic seeds for reproducibility
- Test real integration between components

### 100% Coverage Requirement
- All `src/` modules must have 100% test coverage
- Tests must pass before PDF generation proceeds
- Coverage validated by `.coveragerc` configuration
- No code ships without tests

## Test Organization

Tests are organized to mirror `src/` structure:

```
tests/
├── conftest.py              # Test configuration (adds src/ to path)
├── test_example.py          # Tests for src/example.py
├── test_glossary_gen.py     # Tests for src/glossary_gen.py
├── test_pdf_validator.py    # Tests for src/pdf_validator.py
├── test_build_verifier.py   # Tests for src/build_verifier.py
├── test_integrity.py        # Tests for src/integrity.py
├── test_quality_checker.py  # Tests for src/quality_checker.py
├── test_reproducibility.py  # Tests for src/reproducibility.py
├── test_publishing.py       # Tests for src/publishing.py
├── test_scientific_dev.py   # Tests for src/scientific_dev.py
├── test_example_figure.py   # Integration: scripts/example_figure.py
├── test_generate_research_figures.py  # Integration: scripts/generate_research_figures.py
├── test_repo_utilities.py   # Tests for repo_utilities/*.py
└── test_integration_pipeline.py  # Full pipeline integration tests
```

## conftest.py

Configures test environment:
```python
import os
import sys

# Force headless backend for matplotlib
os.environ.setdefault("MPLBACKEND", "Agg")

# Add src/ to path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)
```

This allows tests to import directly:
```python
from example import add_numbers  # Works immediately
```

## Test Categories

### Unit Tests
Test individual functions in `src/` modules:
- `test_example.py` - 121 lines, tests basic operations
- `test_glossary_gen.py` - 189 lines, tests API extraction
- `test_pdf_validator.py` - 328 lines, tests PDF validation
- `test_build_verifier.py` - 400 lines, tests build verification
- `test_integrity.py` - 496 lines, tests integrity checking
- `test_quality_checker.py` - 463 lines, tests quality analysis
- `test_reproducibility.py` - 427 lines, tests reproducibility
- `test_publishing.py` - 427 lines, tests publishing tools
- `test_scientific_dev.py` - 339 lines, tests scientific dev

### Integration Tests
Test component interactions:
- `test_integration_pipeline.py` - 821 lines
  - End-to-end pipeline validation
  - Script execution integration
  - Build system validation
  - Output verification

### Script Integration Tests
Verify scripts properly use `src/` modules:
- `test_example_figure.py` - 452 lines
  - Tests example_figure.py integration
  - Validates import patterns
  - Checks output generation
  
- `test_generate_research_figures.py` - 588 lines
  - Tests generate_research_figures.py integration
  - Validates complex figure generation
  - Checks data processing

### Repository Utilities Tests
Validate build utilities:
- `test_repo_utilities.py` - 1318 lines
  - Tests generate_glossary.py (100+ tests)
  - Tests validate_markdown.py (comprehensive)
  - Tests validate_pdf_output.py (full coverage)

## Running Tests

### All Tests with Coverage
```bash
# Using pytest directly
pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

# Using uv
uv run pytest tests/ --cov=src --cov-report=html

# Require 100% coverage
pytest tests/ --cov=src --cov-fail-under=100
```

### Specific Tests
```bash
# Single test file
pytest tests/test_example.py -v

# Single test function
pytest tests/test_example.py::test_add_numbers -v

# By pattern
pytest tests/ -k "test_add" -v
```

### Coverage Reports
```bash
# Terminal report with missing lines
pytest tests/ --cov=src --cov-report=term-missing

# HTML report (opens in browser)
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

## Writing Tests

### Test Structure
```python
"""Tests for src/module_name.py"""
import pytest
from module_name import function_to_test

class TestFunctionName:
    """Test suite for function_to_test."""
    
    def test_basic_functionality(self):
        """Test basic usage."""
        result = function_to_test("input")
        assert result == "expected_output"
    
    def test_edge_case(self):
        """Test edge case."""
        result = function_to_test("")
        assert result is None
    
    def test_error_handling(self):
        """Test error conditions."""
        with pytest.raises(ValueError):
            function_to_test(invalid_input)
```

### Fixtures for Temporary Files
```python
def test_with_temp_file(tmp_path):
    """Use pytest's tmp_path fixture."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    
    # Test your function
    result = process_file(test_file)
    
    assert result == expected
    # tmp_path automatically cleaned up
```

### Parametrized Tests
```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    """Test doubling with multiple inputs."""
    assert double(input) == expected
```

## Test Coverage Details

### Current Coverage: 100%
All `src/` modules have complete test coverage:
- example.py: 100%
- glossary_gen.py: 100%
- pdf_validator.py: 100%
- build_verifier.py: 100%
- integrity.py: 100%
- quality_checker.py: 100%
- reproducibility.py: 100%
- publishing.py: 100%
- scientific_dev.py: 100%

### Coverage Configuration
`.coveragerc` enforces coverage rules:
```ini
[run]
source = src
omit = 
    */tests/*
    */test_*.py

[report]
precision = 2
show_missing = True
```

## Debugging Test Failures

### Verbose Output
```bash
pytest tests/ -v  # Verbose test names
pytest tests/ -vv  # Very verbose with diffs
pytest tests/ -s  # Show print statements
```

### Stop on First Failure
```bash
pytest tests/ -x  # Stop on first failure
pytest tests/ --maxfail=3  # Stop after 3 failures
```

### Run Failed Tests Only
```bash
pytest tests/ --lf  # Run last failed
pytest tests/ --ff  # Run failed first, then others
```

### Debugging with PDB
```python
def test_something():
    """Test with debugging."""
    result = function()
    import pdb; pdb.set_trace()  # Breakpoint
    assert result == expected
```

## Best Practices

### Do's
- ✅ Test all public APIs
- ✅ Use real data and computations
- ✅ Test edge cases and error conditions
- ✅ Use descriptive test names
- ✅ Test one thing per test function
- ✅ Use fixtures for setup/teardown
- ✅ Document what each test validates

### Don'ts
- ❌ Use mock methods (test real behavior)
- ❌ Skip tests to fix coverage
- ❌ Test implementation details
- ❌ Use hardcoded file paths
- ❌ Leave commented-out tests
- ❌ Write tests that depend on order
- ❌ Test multiple things in one function

## Integration with Build System

### Automatic Execution
`render_pdf.sh` automatically:
1. **Runs all tests** with 100% coverage requirement
2. **Fails build** if tests don't pass
3. **Generates coverage report** (htmlcov/)
4. **Validates integration** between components

### Pre-commit Checks
Before committing code:
```bash
# Run tests
pytest tests/ --cov=src --cov-fail-under=100

# Check coverage report
open htmlcov/index.html
```

## Adding New Tests

### Checklist
1. Create test file matching src/ module name
2. Import functions to test from src/
3. Write comprehensive test cases
4. Ensure 100% coverage of new module
5. Run full test suite to verify
6. Update this documentation if needed

### Template
```python
"""Tests for src/new_module.py"""
import pytest
from new_module import new_function


class TestNewFunction:
    """Test suite for new_function."""
    
    def test_basic_usage(self):
        """Test basic functionality."""
        result = new_function("input")
        assert result == "expected"
    
    def test_edge_cases(self):
        """Test edge case handling."""
        assert new_function("") is None
        assert new_function(None) is None
    
    def test_error_conditions(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            new_function("invalid")


def test_integration_with_other_modules():
    """Test integration between modules."""
    # Test how new_function works with other src/ modules
    pass
```

## See Also

- [`conftest.py`](conftest.py) - Test configuration
- [`../src/AGENTS.md`](../src/AGENTS.md) - Module documentation
- [`../AGENTS.md`](../AGENTS.md) - System documentation
- [`../docs/WORKFLOW.md`](../docs/WORKFLOW.md) - Development workflow



