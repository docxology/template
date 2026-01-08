# project/tests/ - Project Test Suite

## Purpose

The `project/tests/` directory contains tests for the project-specific scientific code in `project/src/`. These tests validate the research algorithms, data processing pipelines, and analysis methods that form the core of the research project.

## Test Coverage Requirements

**90% minimum coverage** required for `project/src/` modules before PDF generation proceeds. This ensures all critical research code paths are validated.

## Directory Structure

```
project/tests/
├── conftest.py                    # Test configuration and fixtures
├── integration/                   # Integration tests across modules
│   ├── conftest.py
│   ├── test_example_figure.py     # Figure generation integration
│   ├── test_generate_research_figures.py  # Research figure pipeline
│   └── test_integration_pipeline.py  # Full analysis pipeline
├── test_data_generator.py         # Data generation validation
├── test_data_processing.py        # Data preprocessing tests
├── test_example.py                # Core example functionality
├── test_metrics.py                # Performance metrics validation
├── test_package_imports.py        # Import and packaging tests
├── test_parameters.py             # Parameter management tests
├── test_performance.py            # Performance analysis tests
├── test_plots.py                  # Plotting function tests
├── test_reporting.py              # Report generation tests
├── test_simulation_coverage.py    # Simulation framework coverage
├── test_simulation.py             # Simulation engine tests
├── test_statistics.py             # Statistical analysis tests
├── test_validation.py             # Result validation tests
└── test_visualization.py          # Visualization tests
```

## Test Categories

### Unit Tests

Individual function and method validation:

- **`test_example.py`** - Core utility functions (add_numbers, calculate_average, etc.)
- **`test_data_generator.py`** - Synthetic data generation algorithms
- **`test_data_processing.py`** - Data cleaning and preprocessing pipelines
- **`test_metrics.py`** - Performance measurement and evaluation metrics
- **`test_statistics.py`** - Statistical analysis and hypothesis testing
- **`test_parameters.py`** - Parameter validation and management
- **`test_validation.py`** - Result validation and anomaly detection

### Integration Tests (`integration/`)

Cross-module workflow validation:

- **`test_integration_pipeline.py`** - analysis pipeline from data generation to reporting
- **`test_example_figure.py`** - Figure generation and file output integration
- **`test_generate_research_figures.py`** - Multi-figure research visualization pipeline

### Specialized Tests

- **`test_package_imports.py`** - Ensures all modules can be imported correctly
- **`test_simulation_coverage.py`** - Additional coverage for simulation framework edge cases
- **`test_performance.py`** - Performance benchmarking and scalability analysis
- **`test_plots.py`** - Visualization function correctness
- **`test_reporting.py`** - Automated report generation validation

## Testing Philosophy

### Data Analysis

**No mock methods** - all tests use actual data and computation:

```python
# ✅ GOOD: data analysis
def test_calculate_average():
    data = [1, 2, 3, 4, 5]
    result = calculate_average(data)
    assert result == 3.0

# ❌ BAD: Mock-based testing (not used)
def test_calculate_average_mock(mocker):
    mock_func = mocker.patch('calculate_average')
    mock_func.return_value = 3.0
    # ...
```

### Deterministic Results

Tests use fixed seeds and controlled inputs for reproducible results:

```python
def test_data_generation_reproducible():
    """Test that data generation is deterministic with fixed seed."""
    generator = DataGenerator(seed=42)
    data1 = generator.generate(n_samples=100)
    data2 = generator.generate(n_samples=100)
    assert np.array_equal(data1, data2)
```

### Edge Case Coverage

Tests cover normal operation, edge cases, and error conditions:

```python
def test_calculate_average_edge_cases():
    """Test average calculation with various inputs."""
    # Normal case
    assert calculate_average([1, 2, 3]) == 2.0

    # Edge cases
    assert calculate_average([]) is None  # Empty list
    assert calculate_average([5]) == 5.0  # Single element
    assert calculate_average([1.5, 2.5]) == 2.0  # Floats
```

## Running Tests

### All Project Tests

```bash
# With coverage (from repository root)
pytest project/tests/ --cov=project/src --cov-report=html --cov-fail-under=90

# Using uv
uv run pytest project/tests/ --cov=project/src --cov-report=term-missing
```

### Specific Test Categories

```bash
# Unit tests only
pytest project/tests/ -k "not integration"

# Integration tests only
pytest project/tests/integration/

# Single test file
pytest project/tests/test_example.py -v

# Single test function
pytest project/tests/test_example.py::test_add_numbers -v
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

Current coverage: **100%** (coverage - exceeds 90% requirement!)

| Module | Coverage | Status |
|--------|----------|--------|
| `example.py` | 100% | ✅ |
| `data_generator.py` | 99% | ✅ |
| `data_processing.py` | 100% | ✅ |
| `metrics.py` | 100% | ✅ |
| `statistics.py` | 100% | ✅ |
| `parameters.py` | 100% | ✅ |
| `performance.py` | 100% | ✅ |
| `plots.py` | 100% | ✅ |
| `reporting.py` | 100% | ✅ |
| `simulation.py` | 100% | ✅ |
| `validation.py` | 100% | ✅ |
| `visualization.py` | 100% | ✅ |

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
pytest project/tests/ --cov=project/src --cov-fail-under=90
```

### CI/CD Integration

Tests are designed for automated execution:

- **No external dependencies** beyond project requirements
- **Deterministic results** with fixed seeds
- **Fast execution** (< 30 seconds for full suite)
- **Clear failure reporting** for debugging

## Writing Tests

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

- ❌ **Use mocks** - test actual behavior with data
- ❌ **Skip error testing** - always test exception conditions
- ❌ **Hardcode paths** - use tmp_path fixtures for file operations
- ❌ **Test implementation details** - focus on behavior, not internals
- ❌ **Create slow tests** - keep unit tests under 1 second each
- ❌ **Duplicate test logic** - extract common assertions to helper functions
- ❌ **Leave untested code** - maintain 90%+ coverage requirement

## Module Test Details

### Core Modules

**example.py** (`test_example.py`)
- Basic arithmetic operations (add_numbers, multiply_numbers)
- Statistical calculations (calculate_average, find_maximum/find_minimum)
- Validation functions (is_even, is_odd)
- Error handling for invalid inputs

**data_generator.py** (`test_data_generator.py`)
- Synthetic data generation algorithms
- Random seed reproducibility
- Statistical property validation
- Parameter validation and error handling

**data_processing.py** (`test_data_processing.py`)
- Data cleaning and preprocessing pipelines
- Outlier detection algorithms
- Normalization and transformation functions
- Missing data handling

### Analysis Modules

**metrics.py** (`test_metrics.py`)
- Classification metrics (accuracy, precision, recall, F1)
- Regression metrics (MSE, MAE, R²)
- Statistical significance testing
- Confidence interval calculations

**statistics.py** (`test_statistics.py`)
- Descriptive statistics (mean, median, variance, skewness)
- Hypothesis testing (t-tests, ANOVA, chi-square)
- Correlation analysis (Pearson, Spearman)
- Distribution fitting and testing

**performance.py** (`test_performance.py`)
- Algorithm timing and benchmarking
- Scalability analysis with increasing data sizes
- Memory usage profiling
- Performance regression detection

### Simulation Framework

**simulation.py** (`test_simulation.py`, `test_simulation_coverage.py`)
- Simulation engine initialization and configuration
- Time series generation and validation
- Parameter sweep functionality
- Result reproducibility with seeds

**parameters.py** (`test_parameters.py`)
- Parameter set validation and type checking
- Parameter sweep configuration
- Constraint validation and error handling
- Serialization and deserialization

### Visualization and Reporting

**plots.py** (`test_plots.py`)
- Plot generation for different chart types
- Figure saving and format validation
- Axis labeling and title verification
- Data visualization correctness

**visualization.py** (`test_visualization.py`)
- Complex multi-panel figure generation
- Figure layout and arrangement
- Color scheme and styling validation
- Interactive visualization components

**reporting.py** (`test_reporting.py`)
- Automated report generation
- Markdown and HTML output validation
- Table and figure integration
- Report structure and completeness

## See Also

- [`README.md`](README.md) - Quick reference guide
- [`../src/AGENTS.md`](../src/AGENTS.md) - Source code documentation
- [`../../tests/AGENTS.md`](../../tests/AGENTS.md) - Infrastructure test documentation
- [`../../docs/TESTING_GUIDE.md`](../../docs/TESTING_GUIDE.md) - Testing best practices
- [`../../tests/integration/AGENTS.md`](../../tests/integration/AGENTS.md) - Integration test details
