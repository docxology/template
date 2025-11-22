# Scientific Module - Quick Reference

Utilities for scientific computing and research software development.

## Quick Start

```python
from infrastructure.scientific import (
    check_numerical_stability,
    benchmark_function,
    validate_scientific_best_practices
)

# Check numerical stability
stability = check_numerical_stability(
    your_algorithm,
    [test_input_1, test_input_2]
)

# Benchmark performance
benchmark = benchmark_function(
    your_algorithm,
    [test_input_1, test_input_2],
    iterations=100
)

# Validate scientific implementation
report = validate_scientific_best_practices(your_module)
```

## Modules

- **scientific_dev** - Scientific computing utilities and best practices

## Key Functions

### Numerical Stability
- `check_numerical_stability()` - Test algorithm stability
- `test_edge_cases()` - Edge case validation

### Performance Analysis
- `benchmark_function()` - Function performance measurement
- `generate_performance_report()` - Comprehensive performance analysis

### Documentation
- `generate_scientific_documentation()` - API documentation from docstrings
- `generate_api_documentation()` - Detailed API reference

### Validation
- `validate_scientific_implementation()` - Complete implementation check
- `validate_scientific_best_practices()` - Best practices compliance
- `check_research_compliance()` - Research standards compliance

### Templates
- `create_scientific_test_suite()` - Test template generation
- `create_scientific_module_template()` - Module template generation
- `create_scientific_workflow_template()` - Workflow template generation

## CLI

```bash
# Check numerical stability
python3 -m infrastructure.scientific check-stability module.function

# Benchmark function
python3 -m infrastructure.scientific benchmark module.function

# Validate implementation
python3 -m infrastructure.scientific validate module

# Generate documentation
python3 -m infrastructure.scientific generate-docs module
```

## Testing

```bash
pytest tests/infrastructure/test_scientific/
```

For detailed documentation, see [AGENTS.md](AGENTS.md).

