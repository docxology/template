# src/ - Minimal Source Code

## Overview

The `src/` directory contains minimal source code to satisfy the template's pipeline requirements. This project focuses on prose content rather than complex algorithms, so the source code is intentionally simple and exists primarily for test coverage compliance.

## Key Concepts

- **Pipeline compliance**: Minimal code to satisfy template requirements
- **Test coverage**: Simple functions designed for 100% test coverage
- **No domain logic**: Code exists for infrastructure compatibility only
- **Documentation**: Comprehensive documentation despite simple functionality

## Directory Structure

```
src/
├── __init__.py         # Package initialization
├── prose_smoke.py      # Simple utility functions
├── AGENTS.md          # This technical documentation
└── README.md          # Quick reference
```

## Installation/Setup

No special setup required. Uses standard Python with no external dependencies.

## Usage Examples

### Basic Function Usage

```python
from prose_smoke import identity, constant_value

# Identity function
result = identity("hello")
assert result == "hello"

# Constant value
value = constant_value()
assert value == 42
```

### Testing

```python
# Run tests to validate functionality
pytest ../tests/ -v

# Check coverage
pytest ../tests/ --cov=. --cov-report=term-missing
```

## Configuration

No configuration options. Functions are intentionally simple and deterministic.

## Testing

Functions are designed for complete test coverage:

```python
# All functions are tested for:
# - Basic functionality
# - Edge cases
# - Type preservation
# - Deterministic behavior
```

## API Reference

### prose_smoke.py

#### identity (function)
```python
def identity(x):
    """Return input unchanged.

    This trivial function exists solely to satisfy the pipeline's
    requirement for source code and test coverage. It performs
    no meaningful computation.

    Args:
        x: Any value

    Returns:
        The input value unchanged

    Examples:
        >>> identity(42)
        42
        >>> identity("hello")
        'hello'
    """
```

#### constant_value (function)
```python
def constant_value():
    """Return a constant value for testing.

    Returns:
        int: Always returns 42
    """
```

## Troubleshooting

### Common Issues

- **Import errors**: Ensure correct Python path
- **Test failures**: Functions are deterministic - check test setup

## Best Practices

- **Minimal complexity**: Keep functions simple for easy testing
- **Complete documentation**: Document even trivial functions thoroughly
- **Type hints**: Include type annotations for clarity
- **Examples**: Provide usage examples in docstrings

## See Also

- [README.md](README.md) - Quick reference
- [../tests/test_prose_smoke.py](../tests/test_prose_smoke.py) - Comprehensive tests