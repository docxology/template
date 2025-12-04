# project/tests/ - Ways of Knowing Analysis Test Suite

## Purpose

The `project/tests/` directory contains comprehensive tests for the ways of knowing analysis code in `project/src/`. These tests validate the database operations, analysis algorithms, and statistical methods that form the core of the ways of knowing research project.

## Test Coverage Requirements

**70% minimum coverage** required for `project/src/` modules before PDF generation proceeds. This ensures all critical research code paths are validated.

## Directory Structure

```
project/tests/
├── conftest.py                    # Test configuration and fixtures
├── test_package_imports.py        # Import and packaging tests
├── test_sql_queries.py            # SQL query validation
├── test_ways_analysis.py          # Ways analysis framework validation
└── test_ways_statistics.py        # Ways statistical analysis tests
```

## Test Categories

### Unit Tests

Individual function and method validation:

- **`test_ways_analysis.py`** - Ways analysis framework validation (dataclasses, analyzer methods, characterization)
- **`test_ways_statistics.py`** - Ways statistical analysis and distributions
- **`test_sql_queries.py`** - SQL query construction and validation

### Specialized Tests

- **`test_package_imports.py`** - Ensures all ways modules can be imported correctly

## Testing Philosophy

### Real Database Analysis

**No mock methods** - all tests use actual database data and real computation:

```python
# ✅ GOOD: Real database analysis
def test_ways_characterization():
    analyzer = WaysAnalyzer()
    result = analyzer.characterize_ways()
    assert isinstance(result, WaysCharacterization)
    assert result.total_ways > 0

# ❌ BAD: Mock-based testing (not used)
def test_ways_characterization_mock(mocker):
    mock_analyzer = mocker.patch('WaysAnalyzer')
    mock_analyzer.characterize_ways.return_value = mock_characterization
    # ...
```

### Deterministic Results

Tests use controlled database state for reproducible results:

```python
def test_ways_analysis_deterministic():
    """Test that ways analysis is deterministic."""
    analyzer1 = WaysAnalyzer()
    result1 = analyzer1.characterize_ways()

    analyzer2 = WaysAnalyzer()
    result2 = analyzer2.characterize_ways()

    assert result1.total_ways == result2.total_ways
```

### Comprehensive Edge Case Coverage

Tests cover normal operation, edge cases, and error conditions:

```python
def test_ways_characterization_edge_cases():
    """Test ways characterization with various database states."""
    # Normal case with data
    analyzer = WaysAnalyzer()
    result = analyzer.characterize_ways()
    assert result.total_ways > 0

    # Edge cases
    # Test with empty database tables
    # Test with single way record
    # Test with missing relationships
```

## Running Tests

### All Project Tests

```bash
# With coverage (from repository root)
pytest project/tests/ --cov=project/src --cov-report=html --cov-fail-under=70

# Using uv
uv run pytest project/tests/ --cov=project/src --cov-report=term-missing
```

### Specific Test Categories

```bash
# Ways analysis tests
pytest project/tests/test_ways_analysis.py -v

# Ways statistics tests
pytest project/tests/test_ways_statistics.py -v

# SQL query tests
pytest project/tests/test_sql_queries.py -v

# Single test function
pytest project/tests/test_ways_analysis.py::TestWaysAnalyzer::test_characterize_ways -v
```

### Coverage Analysis

```bash
# Generate HTML coverage report
pytest project/tests/ --cov=project/src --cov-report=html
open htmlcov/index.html

# Show missing lines
pytest project/tests/ --cov=project/src --cov-report=term-missing

# Fail if below threshold
pytest project/tests/ --cov=project/src --cov-fail-under=70
```

## Test Configuration

### conftest.py

Shared test configuration and fixtures:

```python
import numpy as np
import pytest

@pytest.fixture
def sample_data():
    """Provide sample test data."""
    return np.array([1, 2, 3, 4, 5])

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary directory for file output tests."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
```

### Test Data Patterns

Common test data patterns used across tests:

- **Small datasets**: `[1, 2, 3, 4, 5]` for basic functionality
- **Edge cases**: Empty lists, single elements, extreme values
- **Realistic data**: Generated with known statistical properties
- **Invalid inputs**: None, wrong types, out-of-range values

## Coverage Status

Current coverage: **70% minimum** required for ways analysis modules

| Module | Coverage | Status |
|--------|----------|--------|
| `database.py` | TBD | ✅ |
| `sql_queries.py` | TBD | ✅ |
| `models.py` | TBD | ✅ |
| `ways_analysis.py` | TBD | ✅ |
| `house_of_knowledge.py` | TBD | ✅ |
| `network_analysis.py` | TBD | ✅ |
| `statistics.py` | TBD | ✅ |
| `metrics.py` | TBD | ✅ |

## Integration with Build System

### Automatic Execution

Project tests run automatically during the build pipeline:

```bash
# Stage 1: Run Tests
python3 scripts/01_run_tests.py
```

This executes both infrastructure and project tests with coverage validation.

### Pre-commit Validation

Before manuscript compilation, tests must pass:

```bash
# Required before PDF generation
pytest project/tests/ --cov=project/src --cov-fail-under=70
```

### CI/CD Integration

Tests are designed for automated execution:

- **No external dependencies** beyond project requirements
- **Deterministic results** with fixed seeds
- **Fast execution** (< 30 seconds for full suite)
- **Clear failure reporting** for debugging

## Writing New Tests

### Test File Template

```python
"""Tests for src/module_name.py"""
import pytest
from module_name import function_to_test


class TestFunctionName:
    """Test suite for function_to_test."""

    def test_basic_functionality(self):
        """Test normal operation."""
        result = function_to_test("input")
        assert result == "expected_output"

    def test_edge_cases(self):
        """Test boundary conditions."""
        assert function_to_test("") is None
        assert function_to_test(None) is None

    def test_error_handling(self):
        """Test error conditions."""
        with pytest.raises(ValueError):
            function_to_test("invalid_input")

    def test_integration(self):
        """Test integration with other modules."""
        # Test how function works with related modules
        pass
```

### Test Naming Conventions

- **Files**: `test_module_name.py` (matches `src/module_name.py`)
- **Classes**: `TestFunctionName` (describes function being tested)
- **Methods**: `test_descriptive_name` (clear test purpose)

### Fixtures for File I/O

```python
def test_figure_generation(tmp_path):
    """Test figure generation saves correct files."""
    output_dir = tmp_path / "figures"
    output_dir.mkdir()

    # Generate figure
    fig_path = generate_figure(output_dir)

    # Verify file exists and has content
    assert fig_path.exists()
    assert fig_path.stat().st_size > 1000  # Reasonable file size
```

## Debugging Test Failures

### Verbose Output

```bash
# Show test execution details
pytest project/tests/test_example.py -v

# Show print statements and logs
pytest project/tests/test_example.py -s

# Stop on first failure
pytest project/tests/test_example.py -x
```

### Coverage Analysis

```bash
# Show which lines are not covered
pytest project/tests/ --cov=project/src --cov-report=term-missing

# Generate detailed HTML report
pytest project/tests/ --cov=project/src --cov-report=html
```

### Re-running Failed Tests

```bash
# Run only previously failed tests
pytest project/tests/ --lf

# Run failed tests first, then others
pytest project/tests/ --ff
```

## Best Practices

### Do's ✅

- ✅ **Test real functionality** - use actual algorithms and data
- ✅ **Cover edge cases** - empty inputs, boundary values, error conditions
- ✅ **Use descriptive names** - clear test purpose and expectations
- ✅ **Keep tests fast** - avoid slow operations in unit tests
- ✅ **Use fixtures** - share common test data and setup
- ✅ **Test integration** - validate module interactions
- ✅ **Document test purpose** - clear docstrings explaining what is tested

### Don'ts ❌

- ❌ **Use mocks** - test actual behavior with real data
- ❌ **Skip error testing** - always test exception conditions
- ❌ **Hardcode paths** - use tmp_path fixtures for file operations
- ❌ **Test implementation details** - focus on behavior, not internals
- ❌ **Create slow tests** - keep unit tests under 1 second each
- ❌ **Duplicate test logic** - extract common assertions to helper functions
- ❌ **Leave untested code** - maintain 70%+ coverage requirement

## Module Test Details

### Ways Analysis Modules

**ways_analysis.py** (`test_ways_analysis.py`)
- WaysAnalyzer class initialization and methods
- WaysCharacterization dataclass validation
- Dialogue type analysis
- Room distribution analysis
- Partner analysis
- God relationship analysis
- Examples statistics

**ways_statistics.py** (`test_ways_statistics.py`)
- Ways distribution analysis
- Ways correlation computation
- Type-room independence testing
- Ways diversity metrics

**sql_queries.py** (`test_sql_queries.py`)
- SQL query construction
- Query parameter validation
- Database query execution
- Result set handling

**database.py** (tested via integration tests)
- Database ORM initialization
- Table creation and schema
- Connection management
- Transaction handling

## See Also

- [`README.md`](README.md) - Quick reference guide
- [`../src/`](../src/) - Ways analysis source code
- [`../../tests/AGENTS.md`](../../tests/AGENTS.md) - Infrastructure test documentation
- [`../AGENTS.md`](../AGENTS.md) - Project documentation
