# project/tests/ - Project Test Suite

test suite ensuring 90%+ coverage of `project/src/` scientific code.

## Quick Start

### Run All Tests

```bash
# With coverage report
pytest tests/ --cov=src --cov-report=html

# Require 90% coverage
pytest tests/ --cov=src --cov-fail-under=90
```

### Run Specific Tests

```bash
# Unit tests only
pytest tests/ -k "not integration"

# Integration tests
pytest tests/integration/

# Single test file
pytest tests/test_example.py -v
```

## Coverage Requirements

- **90% minimum** for project/src/ modules
- Currently achieving **100%** coverage (coverage!)
- Tests must pass before PDF generation

## Test Categories

### Unit Tests
- `test_example.py` - Core utility functions
- `test_data_generator.py` - Data generation algorithms
- `test_data_processing.py` - Data preprocessing
- `test_metrics.py` - Performance metrics
- `test_statistics.py` - Statistical analysis
- `test_parameters.py` - Parameter management
- `test_validation.py` - Result validation

### Integration Tests
- `test_integration_pipeline.py` - analysis workflow
- `test_example_figure.py` - Figure generation
- `test_generate_research_figures.py` - Multi-figure pipeline

## Testing Philosophy

- **data analysis** - no mocks, actual computation
- **Deterministic results** - fixed seeds for reproducibility
- **Edge case coverage** - empty inputs, boundary values, errors

## See Also

- [`AGENTS.md`](AGENTS.md) - documentation
- [`../src/README.md`](../src/README.md) - Source code overview
