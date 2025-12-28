# Integration Tests

End-to-end testing for the complete research pipeline, ensuring all components work together correctly from data generation through final manuscript production.

## Overview

Integration tests validate the **complete research workflow** using real data and real computations. These tests ensure that:

- Data generation produces valid outputs
- Figure creation works with generated data
- Manuscript sections are properly combined
- Cross-references are correctly resolved
- All file formats are generated correctly

## Test Coverage

| Test File | Purpose | Key Validations |
|-----------|---------|-----------------|
| `test_integration_pipeline.py` | Complete pipeline | Data → Figures → Manuscript → Validation |
| `test_generate_research_figures.py` | Figure pipeline | Data processing, visualization, file output |
| `test_example_figure.py` | Basic figures | Core plotting functionality, file formats |

## Running Tests

```bash
# Run all integration tests
pytest project/tests/integration/ -v

# Run with coverage
pytest project/tests/integration/ --cov=project.src --cov-report=term-missing

# Run specific test
pytest project/tests/integration/test_integration_pipeline.py::test_complete_research_pipeline -v
```

## Test Data

Tests use **deterministic, realistic research data**:

```python
# Generated test data includes:
data = {
    'iterations': np.arange(100),
    'objective_values': np.exp(-np.arange(100) / 20),  # Convergence
    'parameter_sets': np.random.randn(10, 5),          # Optimization
    'final_objectives': np.random.rand(10)             # Results
}
```

## Validation Checks

### Data Integrity
- ✅ Arrays have correct shapes and types
- ✅ Values are within expected ranges
- ✅ Relationships between data components are valid

### Figure Quality
- ✅ Files exist and are non-empty (>1KB)
- ✅ Images have reasonable dimensions (400x600+ pixels)
- ✅ Color content indicates meaningful plots (not blank)
- ✅ File formats are correct (PNG)

### Manuscript Structure
- ✅ Required sections present (Abstract, Introduction, Methods, Results, Discussion)
- ✅ Content length is substantial (>2000 characters)
- ✅ Word count meets minimum requirements (>500 words)
- ✅ Cross-references are properly formatted

### File System Operations
- ✅ Temporary directories are properly cleaned up
- ✅ File permissions allow reading/writing
- ✅ Path handling works across different environments

## Integration Points Tested

### Data Flow
```
Data Generation → Figure Creation → Manuscript Assembly → Validation
```

### Module Interactions
- **project.src** modules work together
- **infrastructure** components integrate properly
- **File I/O** operations are reliable
- **Error handling** prevents crashes

## Performance Validation

Tests include **performance checks**:

```python
# Pipeline completion within time limits
execution_time = end_time - start_time
assert execution_time < 30.0, f"Pipeline too slow: {execution_time:.2f}s"
```

## Error Scenarios

Tests validate **robust error handling**:

- Missing data components
- Invalid file formats
- Network failures (where applicable)
- Resource constraints

## Continuous Integration

Integration tests run in CI/CD pipeline:

```bash
# In run.sh pipeline
pytest project/tests/integration/ -q
```

## Debugging Failures

### Common Issues

**Figure Generation Failures:**
```python
# Check matplotlib backend
import matplotlib
print(f"Backend: {matplotlib.get_backend()}")

# Verify data validity
assert 'iterations' in data
assert 'objective_values' in data
```

**Manuscript Assembly Issues:**
```python
# Check section content
for section_name, content in sections.items():
    assert len(content.strip()) > 0, f"Empty section: {section_name}"
```

**File System Problems:**
```python
# Verify directory permissions
import os
assert os.access(output_dir, os.W_OK), "No write permission"
```

## Adding New Tests

### Test Template
```python
"""Test integration of [feature] with [other components]."""
import pytest
import numpy as np
from project.src import [relevant_modules]


def test_[feature]_integration(tmp_path):
    """Test [feature] works with [other components]."""

    # Setup test data
    data = generate_test_data()

    # Execute integration
    result = [feature_function](data, tmp_path)

    # Validate results
    assert result is not None
    assert [validation_checks]
```

### Best Practices
- Use `tmp_path` fixture for temporary files
- Test with realistic data sizes
- Include performance assertions
- Validate error conditions
- Clean up resources properly

## See Also

- [AGENTS.md](AGENTS.md) - Detailed test documentation
- [../unit/](../unit/) - Unit tests for individual functions
- [../../src/](../../src/) - Source code being tested
- [../../../tests/infrastructure/](../../../tests/infrastructure/) - Infrastructure tests