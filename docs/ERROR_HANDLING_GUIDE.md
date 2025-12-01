# Error Handling Guide

> **Custom exception hierarchy** for consistent error handling

**Quick Reference:** [Logging Guide](LOGGING_GUIDE.md) | [Testing Guide](TESTING_GUIDE.md)

## Quick Start

```python
from exceptions import ValidationError, raise_with_context
from logging_utils import get_logger

logger = get_logger(__name__)

# Raise with context
raise_with_context(
    ValidationError,
    "Data validation failed",
    file="data.csv",
    line=42,
    column="temperature"
)

# Catch specific errors
try:
    process_data()
except ValidationError as e:
    logger.error(f"Validation error: {e}", exc_info=True)
    return 1
```

## Exception Hierarchy

```
TemplateError (base)
├── ConfigurationError
│   ├── MissingConfigurationError
│   └── InvalidConfigurationError
├── ValidationError
│   ├── MarkdownValidationError
│   ├── PDFValidationError
│   └── DataValidationError
├── BuildError
│   ├── CompilationError
│   ├── ScriptExecutionError
│   └── PipelineError
├── FileOperationError
│   ├── FileNotFoundError
│   └── InvalidFileFormatError
├── DependencyError
│   ├── MissingDependencyError
│   └── VersionMismatchError
├── TestError
│   └── InsufficientCoverageError
└── IntegrationError
```

## Usage Patterns

### Basic Exception

```python
from exceptions import ValidationError

if not is_valid(data):
    raise ValidationError("Validation failed")
```

### With Context

```python
from exceptions import raise_with_context, FileNotFoundError

if not path.exists():
    raise_with_context(
        FileNotFoundError,
        "Required file not found",
        file=str(path),
        searched_in=str(Path.cwd())
    )
```

### Chain Exceptions

```python
from exceptions import chain_exceptions, BuildError

try:
    compile_latex()
except subprocess.CalledProcessError as e:
    new_error = BuildError("Compilation failed")
    raise chain_exceptions(new_error, e)
```

### Catch Hierarchy

```python
# Catch specific
try:
    operation()
except MissingConfigurationError as e:
    logger.error(f"Config missing: {e}")

# Catch category
try:
    operation()
except ConfigurationError as e:
    logger.error(f"Config error: {e}")

# Catch all template errors
try:
    operation()
except TemplateError as e:
    logger.error(f"Template error: {e}")
```

## Exception Types

### Configuration Errors

```python
from exceptions import ConfigurationError, MissingConfigurationError

# Missing configuration
raise MissingConfigurationError(
    "Required key not found",
    context={"key": "author", "file": "config.yaml"}
)

# Invalid configuration
raise InvalidConfigurationError(
    "Invalid email format",
    context={"field": "email", "value": "invalid"}
)
```

### Validation Errors

```python
from exceptions import ValidationError, MarkdownValidationError

# Markdown validation
raise MarkdownValidationError(
    "Image file not found",
    context={"image": "figure.png", "file": "intro.md", "line": 42}
)

# Data validation
raise DataValidationError(
    "NaN values detected",
    context={"column": "temperature", "count": 5}
)
```

### Build Errors

```python
from exceptions import BuildError, CompilationError

# Compilation failure
raise CompilationError(
    "LaTeX compilation failed",
    context={"file": "manuscript.tex", "exit_code": 1}
)

# Script failure
raise ScriptExecutionError(
    "Analysis script failed",
    context={"script": "analysis.py", "exit_code": 1}
)
```

## Integration with Logging

```python
from logging_utils import get_logger
from exceptions import ValidationError

logger = get_logger(__name__)

try:
    validate_data(data)
except ValidationError as e:
    logger.error(f"Validation failed: {e}", exc_info=True)
    # exc_info=True includes stack trace
    raise
```

## Best Practices

### Do's ✅
- Use specific exception types
- Include context information
- Chain exceptions to preserve history
- Log exceptions with exc_info=True
- Catch specific exceptions first

### Don'ts ❌
- Don't use bare except clauses
- Don't lose exception context
- Don't catch Exception without good reason
- Don't raise generic Exception
- Don't ignore exceptions silently

## Common Patterns

### Validation with Context

```python
def validate_file(path: Path) -> None:
    if not path.exists():
        raise_with_context(
            FileNotFoundError,
            "File not found",
            file=str(path),
            expected_location=str(path.parent)
        )
    
    if not path.suffix == '.csv':
        raise_with_context(
            InvalidFileFormatError,
            "Expected CSV file",
            file=str(path),
            detected_type=path.suffix
        )
```

### Pipeline Error Handling

```python
def run_pipeline() -> int:
    try:
        with log_operation("Run pipeline", logger):
            for stage in stages:
                run_stage(stage)
        return 0
    except ScriptExecutionError as e:
        logger.error(f"Script failed: {e}", exc_info=True)
        return 1
    except PipelineError as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        return 1
    except TemplateError as e:
        logger.error(f"Template error: {e}", exc_info=True)
        return 1
```

### Utility Functions

```python
from exceptions import format_file_context

# Format file context
context = format_file_context("data.csv", line=42)
raise ValidationError("Error at line", context=context)
```

## See Also

- [Logging Guide](LOGGING_GUIDE.md)
- [Testing Guide](TESTING_GUIDE.md)
- [API Reference](API_REFERENCE.md)






