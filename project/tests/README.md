# project/tests/ - Project Test Suite

Comprehensive test suite ensuring 70%+ coverage of `project/src/` scientific code.

## Quick Start

### Run All Tests

```bash
# With coverage report
pytest tests/ --cov=src --cov-report=html

# Require 70% coverage
pytest tests/ --cov=src --cov-fail-under=70
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

- **70% minimum** for project/src/ modules
- Currently achieving **99.88%** coverage
- Tests must pass before PDF generation

## Test Categories

### Unit Tests
- `test_database.py` - Database ORM and queries
- `test_models.py` - Data models (Way, Room, Question)
- `test_sql_queries.py` - SQL query execution
- `test_ways_analysis.py` - Ways analysis framework
- `test_network_analysis.py` - Network analysis algorithms
- `test_house_of_knowledge.py` - House of Knowledge framework
- `test_ways_statistics.py` - Statistical analysis functions
- `test_comprehensive_analysis.py` - Comprehensive analysis script (10 tests)
- `test_generate_figures.py` - Figure generation script (8 tests)

### Integration Tests
- `test_package_imports.py` - Package import validation
- Database integration tests in `test_database.py`
- Network analysis integration in `test_network_analysis.py`

## Testing Philosophy

- **Real data analysis** - no mocks, actual computation
- **Deterministic results** - fixed seeds for reproducibility
- **Edge case coverage** - empty inputs, boundary values, errors

## See Also

- [`AGENTS.md`](AGENTS.md) - Complete documentation
- [`../src/README.md`](../src/README.md) - Source code overview


