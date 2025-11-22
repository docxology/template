# Error Handling Standards

## Exception Hierarchy

All custom exceptions inherit from `TemplateError` in `infrastructure/exceptions.py`.

### Import Pattern

```python
from exceptions import (
    ValidationError,
    ConfigurationError,
    BuildError,
    raise_with_context
)
```

## Exception Types

- **ConfigurationError** - Config issues
- **ValidationError** - Validation failures
- **BuildError** - Build/compilation failures
- **FileOperationError** - File I/O issues
- **DependencyError** - Missing dependencies
- **TestError** - Test failures
- **IntegrationError** - Integration issues

## Usage Patterns

### Raise with Context

```python
raise_with_context(
    ValidationError,
    "Validation failed",
    file="data.csv",
    line=42
)
```

### Chain Exceptions

```python
try:
    risky_operation()
except ValueError as e:
    new_error = ValidationError("Wrapped error")
    raise chain_exceptions(new_error, e)
```

### Catch Specific First

```python
try:
    operation()
except MissingConfigurationError:
    # Handle specific
    pass
except ConfigurationError:
    # Handle category
    pass
except TemplateError:
    # Handle all template errors
    pass
```

## Best Practices

- Use specific exception types
- Include context (file, line, values)
- Chain exceptions to preserve history
- Log with `exc_info=True`
- Catch specific before general

## See Also

- [Error Handling Guide](../docs/ERROR_HANDLING_GUIDE.md)
- [Logging](python_logging.md)

