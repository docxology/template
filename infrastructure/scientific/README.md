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

### Performance Analysis
- `benchmark_function()` - Function performance measurement

### Documentation
- `generate_scientific_documentation()` - API documentation from docstrings

### Validation
- `validate_scientific_implementation()` - Complete implementation check
- `validate_scientific_best_practices()` - Best practices compliance

**Note**: Additional functions are available in `scientific_dev.py` but are not exported in the module's public API. Import directly from `infrastructure.scientific.scientific_dev` if needed.

## Usage Notes

The scientific module provides functions that can be called directly from Python. The `scientific_dev.py` module also has a `main()` function for standalone execution:

```bash
# Run scientific_dev.py directly
python3 infrastructure/scientific/scientific_dev.py
```

## Testing

```bash
pytest tests/infrastructure/test_scientific/
```

For detailed documentation, see [AGENTS.md](AGENTS.md).

