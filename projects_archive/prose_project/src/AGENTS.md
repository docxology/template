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

## Infrastructure Integration

Despite minimal functionality, this module demonstrates comprehensive infrastructure integration for research projects.

### Available Infrastructure Capabilities

- **Logging**: `infrastructure.core.logging_utils` - Structured logging with context
- **Validation**: `infrastructure.validation` - Output integrity and quality checks
- **Rendering**: `infrastructure.rendering` - Multi-format output generation
- **Scientific Analysis**: `infrastructure.scientific` - Numerical analysis tools
- **Publishing**: `infrastructure.publishing` - Academic publishing workflows

### Integration Examples

#### Comprehensive Pipeline Integration

```python
from prose_smoke import identity, constant_value
from infrastructure.core.logging_utils import get_logger
from infrastructure.scientific import check_numerical_stability
from infrastructure.validation import verify_output_integrity
from pathlib import Path

logger = get_logger(__name__)

# Run basic functions
result1 = identity("test_input")
result2 = constant_value()

logger.info(f"Identity result: {result1}")
logger.info(f"Constant result: {result2}")

# Demonstrate scientific analysis integration
def test_func(x):
    return identity(x)  # Simple function for analysis

# Analyze numerical stability
stability = check_numerical_stability(
    func=test_func,
    test_inputs=["input1", "input2", "input3"]
)
logger.info(f"Function stability: {stability['overall_stable']}")

# Validate outputs
output_dir = Path("output")
integrity_report = verify_output_integrity(output_dir)
if integrity_report.issues:
    logger.warning(f"Found {len(integrity_report.issues)} integrity issues")
else:
    logger.info("Output integrity validation passed")
```

#### Error Handling with Infrastructure

```python
from infrastructure.core.exceptions import ValidationError, TemplateError

try:
    # Run functions with potential validation
    result = identity("input")
    if not isinstance(result, str):
        raise ValidationError("Identity function must return string")
except ValidationError as e:
    logger.error(f"Validation error: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

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