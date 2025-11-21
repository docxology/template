# Testing Standards

## Core Requirement: 100% Coverage

All code in `src/` must have 100% test coverage.

### Why No Mocks?
- **Mocks hide bugs**: Real integration failures discovered
- **Tests stay valid**: Don't test implementation details  
- **Better confidence**: Real behavior verified
- **Cleaner code**: Simpler, more readable tests

### Real Data Testing

Use real data and actual computations:

```python
# ✅ GOOD - Real data
def test_mean_calculation():
    data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    assert compute_mean(data) == 3.0

# ❌ BAD - Mock
def test_mean_calculation():
    mock_data = MagicMock()
    mock_data.__len__.return_value = 5
    assert compute_mean(mock_data) == 3.0
```

### Test Categories

#### Unit Tests
- Individual function behavior
- Use real input data
- Test all code paths
- Deterministic (fixed seeds)

#### Integration Tests
- Multiple components together
- Scripts with src/ modules
- Real file I/O where needed
- Validate pipeline coherence

#### Validation Tests
- Output quality checks
- Data integrity verification
- Format correctness
- Cross-reference resolution

## Test Coverage Requirements

### Minimum Coverage
- **src/**: 100% code coverage (including package-level imports)
- **tests/**: All functionality covered
- **scripts/**: Tested through src/ integration
- **repo_utilities/**: Comprehensive testing

### Achievement Status
As of latest build:
- **Coverage**: 100% for all project/src/ modules
- **Tests**: 343 tests passing (100% pass rate)
- **Integration**: Full pipeline validated
- **Package API**: Package-level imports tested via `test_package_imports.py`

### Coverage Calculation

```bash
# Run tests with coverage report
python3 -m pytest tests/ --cov=src --cov-report=term-missing

# Generate HTML report
python3 -m pytest tests/ --cov=src --cov-report=html
```

### Enforcing Coverage

From `.coveragerc`:
```ini
[run]
branch = True
source = src

[report]
precision = 2
show_missing = True
fail_under = 100
```

## Test Structure

### Test File Organization

```
tests/
├── conftest.py                  # Shared fixtures
├── test_example.py              # Tests for src/example.py
├── test_integration_pipeline.py # Integration tests
└── test_repo_utilities.py       # Utility tests
```

### Fixture Pattern

```python
# tests/conftest.py

import pytest
import numpy as np
from pathlib import Path
import tempfile

@pytest.fixture
def sample_data():
    """Generate deterministic sample data."""
    np.random.seed(42)
    return np.random.randn(100)

@pytest.fixture
def temp_output_dir():
    """Temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
```

### Test Example

```python
# tests/test_example.py

import numpy as np
from src.example import add_numbers, process_data

class TestBasicFunctions:
    """Test basic arithmetic operations."""
    
    def test_add_numbers(self):
        """Test integer addition."""
        assert add_numbers(2, 3) == 5
        assert add_numbers(-1, 1) == 0
        assert add_numbers(0, 0) == 0
    
    def test_add_numbers_float(self):
        """Test floating point addition."""
        assert add_numbers(1.5, 2.5) == 4.0
        assert abs(add_numbers(0.1, 0.2) - 0.3) < 1e-10

def test_process_data():
    """Test data processing with real data."""
    # Use real test data (no mocks)
    data = np.array([1, 2, 3, 4, 5])
    result = process_data(data)
    
    assert result is not None
    assert len(result) == len(data)
    assert np.all(np.isfinite(result))
```

## Test Best Practices

### 1. Use Deterministic Seeds
```python
@pytest.fixture(autouse=True)
def seed_random():
    """Set seed for reproducible tests."""
    np.random.seed(42)
    random.seed(42)
    yield
```

### 2. Test Edge Cases
```python
def test_edge_cases():
    """Test boundary conditions."""
    # Empty
    assert process_data([]) == []
    
    # Single element
    assert process_data([1]) == [1]
    
    # Large values
    assert process_data([1e10, 1e10]) is not None
    
    # Negative values
    assert process_data([-1, -2, -3]) is not None
```

### 3. Test Error Conditions
```python
def test_invalid_input():
    """Test error handling."""
    with pytest.raises(ValueError):
        process_data(None)
    
    with pytest.raises(TypeError):
        process_data("not_an_array")
```

### 4. Document Test Purpose
```python
def test_algorithm_convergence():
    """
    Verify algorithm converges within expected iterations.
    
    This test ensures the optimization algorithm reaches
    a solution within the maximum iteration limit.
    """
    result = run_algorithm(max_iterations=100)
    assert result['converged']
    assert result['iterations'] < 100
```

## Running Tests

### Full Test Suite
```bash
# Run all tests with coverage
python3 -m pytest tests/ --cov=src --cov-report=term-missing

# Verbose output
python3 -m pytest tests/ -v

# Specific test file
python3 -m pytest tests/test_example.py -v

# Specific test
python3 -m pytest tests/test_example.py::test_add_numbers -v
```

### Watch Mode
```bash
# Run on file changes
ptw tests/ -- --cov=src
```

### CI/CD Integration
```bash
# Used in build pipeline
python3 -m pytest tests/ \
    --cov=src \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-fail-under=70 \
    --junitxml=results.xml
```

## Test Organization Example

```python
# tests/test_data_processing.py

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile

from src.data_processing import (
    load_data,
    clean_data,
    normalize_data,
    validate_data
)

class TestDataLoading:
    """Tests for data loading functionality."""
    
    def test_load_csv(self, temp_output_dir):
        """Load CSV file successfully."""
        # Create test CSV
        csv_path = temp_output_dir / 'test_data.csv'
        pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]}).to_csv(csv_path)
        
        data = load_data(csv_path)
        assert len(data) == 3
        assert list(data.columns) == ['a', 'b']
    
    def test_load_missing_file(self):
        """Handle missing file gracefully."""
        with pytest.raises(FileNotFoundError):
            load_data('/nonexistent/path.csv')

class TestDataCleaning:
    """Tests for data cleaning functionality."""
    
    def test_remove_outliers(self):
        """Remove statistical outliers."""
        # Normal data
        data = np.array([1, 2, 3, 4, 5])
        # Add outlier
        data = np.append(data, 100)
        
        cleaned = clean_data(data)
        assert 100 not in cleaned
        assert len(cleaned) < len(data)

class TestNormalization:
    """Tests for data normalization."""
    
    def test_normalize_zero_mean(self):
        """Normalize to zero mean."""
        data = np.array([0, 1, 2, 3, 4])
        normalized = normalize_data(data)
        
        assert abs(np.mean(normalized)) < 1e-10
        assert abs(np.std(normalized) - 1.0) < 1e-10
```

## Performance Tests

Include performance benchmarks:

```python
def test_performance_data_loading(benchmark):
    """Benchmark data loading performance."""
    # Create test data
    test_data = np.random.randn(10000, 100)
    
    # Benchmark function
    result = benchmark(load_data, test_data)
    assert result is not None
```

## Test Maintenance

### Keep Tests Updated
- Update tests when requirements change
- Add tests for new features
- Remove obsolete tests
- Refactor as codebase evolves

### Monitor Coverage
- Check coverage report regularly
- Identify untested code paths
- Add tests for gaps
- Maintain 100% coverage

## Comprehensive Documentation

For complete testing guidance and best practices, see:

- [`docs/TEST_IMPROVEMENTS_SUMMARY.md`](../docs/TEST_IMPROVEMENTS_SUMMARY.md) - Testing enhancements overview
- [`docs/BEST_PRACTICES.md`](../docs/BEST_PRACTICES.md) - Testing best practices section
- [`docs/BUILD_SYSTEM.md`](../docs/BUILD_SYSTEM.md) - Coverage metrics and build integration

## See Also

- [core_architecture.md](core_architecture.md) - System design
- [thin_orchestrator.md](thin_orchestrator.md) - Script testing patterns
- [../tests/AGENTS.md](../tests/AGENTS.md) - Test suite documentation
- [../AGENTS.md](../AGENTS.md) - System documentation

