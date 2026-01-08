# API Design Standards and Guidelines

## Overview

Consistent API design ensures that all modules provide clear, intuitive, and maintainable interfaces. All public APIs must follow these design principles.

## API Design Principles

### 1. Consistency

- **Naming conventions** - Use consistent naming across all APIs
- **Parameter ordering** - Follow established parameter patterns
- **Return types** - Use consistent return type patterns
- **Error handling** - Uniform error handling approach

### 2. Clarity

- **Self-documenting** - APIs should be obvious in purpose
- **Minimal surprise** - Behavior should match expectations
- **Progressive disclosure** - Simple for basic use, advanced options available

### 3. Composability

- **Chainable operations** - Support method chaining where appropriate
- **Composable functions** - Functions work well together
- **Flexible inputs** - Accept various input types gracefully

## Function Design Patterns

### Function Signatures

```python
# ✅ GOOD: Clear, typed function signature
def process_data(
    data: list[dict],
    *,
    normalize: bool = True,
    validate: bool = True,
    timeout: float = 30.0
) -> dict[str, Any]:
    """Process a list of data dictionaries.

    Args:
        data: List of dictionaries to process
        normalize: Whether to normalize data values
        validate: Whether to validate input data
        timeout: Maximum processing time in seconds

    Returns:
        Dictionary with processed data and metadata

    Raises:
        ValidationError: If validation fails and validate=True
        TimeoutError: If processing exceeds timeout
    """
```

### Parameter Patterns

#### Required vs Optional

```python
# ✅ GOOD: Required parameters first, then optional
def create_user(name: str, email: str, age: int | None = None) -> User:
    """Create user with required name/email and optional age."""
    pass

# ❌ BAD: Optional parameters before required
def create_user(name: str = "Anonymous", email: str) -> User:  # email required but after optional
    pass
```

#### Keyword-Only Parameters

```python
# ✅ GOOD: Use * to separate positional from keyword-only
def configure_service(
    host: str,
    port: int = 8080,
    *,
    ssl_enabled: bool = True,
    max_connections: int = 100
) -> ServiceConfig:
    """Configure service with clear parameter separation."""
    pass

# This enforces clarity:
service = configure_service("localhost", 8080, ssl_enabled=False, max_connections=50)
```

#### Union Types for Flexibility

```python
# ✅ GOOD: Accept multiple input types
def load_config(config: str | Path | dict) -> dict:
    """Load configuration from various input types.

    Args:
        config: Configuration as file path, Path object, or dict

    Returns:
        Normalized configuration dictionary
    """
    if isinstance(config, (str, Path)):
        return load_from_file(config)
    elif isinstance(config, dict):
        return config.copy()
    else:
        raise TypeError(f"Unsupported config type: {type(config)}")
```

### Return Type Patterns

#### Consistent Return Structures

```python
# ✅ GOOD: Consistent return structure for similar operations
@dataclass
class ProcessResult:
    """Result of data processing operation."""
    success: bool
    data: list[dict] | None = None
    errors: list[str] | None = None
    metadata: dict[str, Any] | None = None

def process_batch(data: list[dict]) -> ProcessResult:
    """Process batch of data items."""
    # Always return ProcessResult, even for errors
    pass

# ❌ BAD: Inconsistent return types
def process_batch(data: list[dict]) -> list[dict]:  # Success case
    return processed_data

def process_batch(data: list[dict]) -> None:  # Error case - raises instead
    raise ProcessingError()
```

#### Result/Option Types

```python
# ✅ GOOD: Use result types for operations that can fail
from typing import Union

@dataclass
class Success:
    """Successful operation result."""
    value: Any

@dataclass
class Failure:
    """Failed operation result."""
    error: str
    context: dict | None = None

Result = Union[Success, Failure]

def safe_divide(a: float, b: float) -> Result:
    """Safely divide two numbers."""
    if b == 0:
        return Failure("Division by zero", {"a": a, "b": b})
    return Success(a / b)

# Usage
result = safe_divide(10, 2)
if isinstance(result, Success):
    print(f"Result: {result.value}")
else:
    print(f"Error: {result.error}")
```

## Class Design Patterns

### Class Structure

```python
# ✅ GOOD: Well-structured class
class DataProcessor:
    """Process and transform data."""

    def __init__(self, config: dict | None = None) -> None:
        """Initialize processor with configuration."""
        self.config = config or {}
        self._validate_config()

    def process(self, data: Any) -> Any:
        """Process input data."""
        self._validate_input(data)
        result = self._transform(data)
        self._log_processing(result)
        return result

    # Public methods
    def get_stats(self) -> dict[str, int]:
        """Get processing statistics."""
        pass

    # Private helper methods
    def _validate_config(self) -> None:
        """Validate configuration."""
        pass

    def _validate_input(self, data: Any) -> None:
        """Validate input data."""
        pass

    def _transform(self, data: Any) -> Any:
        """Transform data."""
        pass

    def _log_processing(self, result: Any) -> None:
        """Log processing results."""
        pass
```

### Property Patterns

```python
# ✅ GOOD: Use properties for computed attributes
class Dataset:
    """Dataset with computed properties."""

    def __init__(self, data: list[dict]) -> None:
        self._data = data.copy()

    @property
    def count(self) -> int:
        """Number of data items."""
        return len(self._data)

    @property
    def columns(self) -> list[str]:
        """Available columns in dataset."""
        if not self._data:
            return []
        return list(self._data[0].keys())

    @property
    def is_empty(self) -> bool:
        """Check if dataset is empty."""
        return self.count == 0
```

### Context Manager Pattern

```python
# ✅ GOOD: Context manager for resource management
class DatabaseConnection:
    """Database connection with context manager support."""

    def __init__(self, url: str) -> None:
        self.url = url
        self._connection = None

    def __enter__(self) -> "DatabaseConnection":
        """Enter context - establish connection."""
        self._connection = self._connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context - clean up connection."""
        if self._connection:
            self._connection.close()

    def query(self, sql: str) -> list[dict]:
        """Execute query."""
        if not self._connection:
            raise RuntimeError("Connection not established")
        return self._execute_query(sql)

    def _connect(self):
        """Establish database connection."""
        # Implementation
        pass

    def _execute_query(self, sql: str) -> list[dict]:
        """Execute SQL query."""
        # Implementation
        pass

# Usage
with DatabaseConnection("sqlite:///data.db") as db:
    results = db.query("SELECT * FROM users")
    # Connection automatically closed
```

## Module API Design

### Module Structure

```python
# infrastructure/example/__init__.py
"""Example module for demonstrating API design patterns."""

from .core import process_data, validate_input, ExampleProcessor
from .config import ExampleConfig, DEFAULT_SETTINGS
from .exceptions import ExampleError, ValidationError

__all__ = [
    # Core functionality
    "process_data",
    "validate_input",
    "ExampleProcessor",

    # Configuration
    "ExampleConfig",
    "DEFAULT_SETTINGS",

    # Exceptions
    "ExampleError",
    "ValidationError",
]
```

### Factory Functions

```python
# ✅ GOOD: Factory functions for complex object creation
def create_processor(config: dict | None = None) -> ExampleProcessor:
    """Create configured processor instance.

    Args:
        config: Optional configuration dictionary

    Returns:
        Configured ExampleProcessor instance
    """
    if config is None:
        config = DEFAULT_SETTINGS.copy()

    validated_config = validate_config(config)
    return ExampleProcessor(validated_config)

def create_processor_from_file(config_path: str | Path) -> ExampleProcessor:
    """Create processor from configuration file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configured ExampleProcessor instance
    """
    config = load_config_file(config_path)
    return create_processor(config)
```

### Builder Pattern

```python
# ✅ GOOD: Builder pattern for complex configuration
class ProcessorBuilder:
    """Builder for creating configured processors."""

    def __init__(self) -> None:
        self._config = DEFAULT_SETTINGS.copy()

    def with_timeout(self, timeout: float) -> "ProcessorBuilder":
        """Set processing timeout."""
        self._config["timeout"] = timeout
        return self

    def with_validation(self, enabled: bool) -> "ProcessorBuilder":
        """Enable or disable validation."""
        self._config["validation_enabled"] = enabled
        return self

    def with_parallel_processing(self, workers: int) -> "ProcessorBuilder":
        """Configure parallel processing."""
        self._config["parallel_workers"] = workers
        return self

    def build(self) -> ExampleProcessor:
        """Build configured processor."""
        return create_processor(self._config)

# Usage
processor = (
    ProcessorBuilder()
    .with_timeout(60.0)
    .with_validation(True)
    .with_parallel_processing(4)
    .build()
)
```

## Error Handling in APIs

### Custom Exceptions

```python
# ✅ GOOD: Module-specific exceptions
class ExampleError(Exception):
    """Base exception for example module."""
    pass

class ValidationError(ExampleError):
    """Input validation failed."""
    pass

class ProcessingError(ExampleError):
    """Data processing failed."""
    pass

class ConfigurationError(ExampleError):
    """Configuration is invalid."""
    pass
```

### Exception Context

```python
# ✅ GOOD: Exceptions with context
def validate_input(data: Any) -> None:
    """Validate input data.

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise ValidationError(
            "Input must be a dictionary",
            context={
                "received_type": type(data).__name__,
                "expected_type": "dict"
            }
        )

    if "required_field" not in data:
        raise ValidationError(
            "Missing required field: required_field",
            context={
                "available_fields": list(data.keys()),
                "missing_field": "required_field"
            }
        )
```

## Async API Design

### Async Function Patterns

```python
# ✅ GOOD: Async API design
import asyncio
from typing import AsyncIterator

async def process_data_async(data: list[dict]) -> dict[str, Any]:
    """Process data asynchronously.

    Args:
        data: Data to process

    Returns:
        Processing results
    """
    # Simulate async processing
    await asyncio.sleep(0.1)
    return {"processed": len(data)}

async def process_stream(data_stream: AsyncIterator[dict]) -> AsyncIterator[dict]:
    """Process streaming data asynchronously.

    Args:
        data_stream: Async iterator of data items

    Yields:
        Processed data items
    """
    async for item in data_stream:
        processed = await process_item_async(item)
        yield processed

# Usage
async def main():
    # Direct async call
    result = await process_data_async([{"id": 1}, {"id": 2}])

    # Streaming processing
    async def data_generator():
        for i in range(10):
            yield {"id": i}
            await asyncio.sleep(0.1)

    async for processed in process_stream(data_generator()):
        print(f"Processed: {processed}")
```

## API Versioning

### Version Indicators

```python
# ✅ GOOD: Version-aware APIs
def process_data_v1(data: list[dict]) -> dict:
    """Process data (version 1)."""
    # Legacy implementation
    pass

def process_data(data: list[dict], *, version: str = "v2") -> dict:
    """Process data with version support.

    Args:
        data: Data to process
        version: API version to use ("v1" or "v2")

    Returns:
        Processing results
    """
    if version == "v1":
        return process_data_v1(data)
    elif version == "v2":
        # Current implementation
        return process_data_v2(data)
    else:
        raise ValueError(f"Unsupported version: {version}")

# Usage
result = process_data(data, version="v1")  # Backward compatibility
result = process_data(data)  # Latest version (v2)
```

## API Documentation

### Docstrings

```python
# ✅ GOOD: API documentation
def analyze_dataset(
    dataset: "Dataset",
    *,
    method: str = "auto",
    parameters: dict[str, Any] | None = None,
    validate_results: bool = True,
    progress_callback: Callable[[float], None] | None = None
) -> AnalysisResult:
    """Analyze dataset using specified method.

    This function performs analysis on the input dataset,
    applying statistical methods, outlier detection, and trend analysis.
    Results include summary statistics, visualizations, and insights.

    Args:
        dataset: Dataset object to analyze. Must contain at least
            one numeric column and 10+ rows for meaningful analysis.
        method: Analysis method to use. Options:
            - "auto": Automatically select best method
            - "statistical": Basic statistical analysis
            - "ml": Machine learning-based analysis
            - "deep": Deep statistical analysis
        parameters: Method-specific parameters. If None, uses defaults
            for the selected method.
        validate_results: Whether to validate analysis results for
            statistical significance and data quality.
        progress_callback: Optional callback function called with
            progress percentage (0.0 to 1.0) during analysis.

    Returns:
        AnalysisResult containing:
        - summary_stats: Dict of statistical measures
        - visualizations: List of generated plot paths
        - insights: List of key findings and recommendations
        - quality_score: Float between 0-1 indicating result quality
        - warnings: List of warnings about data or analysis

    Raises:
        ValueError: If dataset is invalid or method unsupported
        AnalysisError: If analysis fails due to data issues
        TimeoutError: If analysis exceeds time limits

    Examples:
        Basic analysis:

        >>> result = analyze_dataset(my_dataset)
        >>> print(f"Quality: {result.quality_score:.2f}")

        Advanced analysis with progress:

        >>> def progress(pct):
        ...     print(f"Progress: {pct:.1%}")
        >>> result = analyze_dataset(
        ...     dataset=my_dataset,
        ...     method="ml",
        ...     progress_callback=progress
        ... )

    Note:
        Large datasets (>10k rows) may take several minutes to analyze.
        Consider using method="auto" for optimal performance.

    See Also:
        validate_dataset: For dataset validation before analysis
        export_analysis: For saving analysis results
    """
```

## API Testing Patterns

### API Contract Tests

```python
# ✅ GOOD: Test API contracts
def test_process_data_api_contract():
    """Test process_data API contract."""
    # Test with minimal valid input
    result = process_data([{"id": 1}])

    # Verify return type
    assert isinstance(result, dict)

    # Verify expected keys exist
    assert "processed_count" in result
    assert "errors" in result

    # Verify types
    assert isinstance(result["processed_count"], int)
    assert isinstance(result["errors"], list)

def test_process_data_error_contract():
    """Test process_data error handling contract."""
    # Test with invalid input
    with pytest.raises(ValidationError) as exc_info:
        process_data("invalid input")

    # Verify exception type and message
    error = exc_info.value
    assert "invalid" in str(error).lower()

    # Verify context is provided
    assert hasattr(error, 'context')
    assert error.context is not None
```

### Integration Tests

```python
# ✅ GOOD: Test API integration
def test_api_composition():
    """Test that APIs work well together."""
    # Create data
    data = create_sample_data()

    # Process through multiple APIs
    validated = validate_data(data)
    processed = process_data(validated)
    analyzed = analyze_results(processed)

    # Verify the chain works
    assert analyzed["success"] is True
    assert analyzed["chain_length"] == 3
```

## API Evolution Guidelines

### Backward Compatibility

```python
# ✅ GOOD: Maintain backward compatibility
def process_data_v2(data: list[dict], *, enhanced: bool = False) -> dict:
    """Process data with features (v2).

    Args:
        data: Data to process (same as v1)
        enhanced: Enable processing features

    Returns:
        Same structure as v1, with additional fields when enhanced=True
    """
    # Implementation that maintains v1 behavior by default
    pass

# Provide backward-compatible wrapper
def process_data(data: list[dict]) -> dict:
    """Process data (maintains v1 API)."""
    return process_data_v2(data, enhanced=False)
```

### Deprecation Notices

```python
# ✅ GOOD: Deprecate gracefully
import warnings

def old_function_name(param: str) -> str:
    """Old function name (deprecated).

    .. deprecated:: 2.0.0
        Use :func:`new_function_name` instead.
    """
    warnings.warn(
        "old_function_name is deprecated, use new_function_name instead",
        DeprecationWarning,
        stacklevel=2
    )
    return new_function_name(param)

def new_function_name(parameter: str) -> str:
    """New function with improved API."""
    return parameter.upper()
```

## Best Practices Summary

### Do's ✅

- ✅ **Use descriptive names** that clearly indicate purpose
- ✅ **Provide type hints** for all parameters and returns
- ✅ **Use keyword-only parameters** for optional/advanced settings
- ✅ **Document exceptions** in docstrings with context
- ✅ **Maintain backward compatibility** when possible
- ✅ **Use consistent patterns** across similar APIs
- ✅ **Provide examples** in docstrings for complex APIs
- ✅ **Use builder/factory patterns** for complex object creation
- ✅ **Implement context managers** for resource management
- ✅ **Version APIs** when breaking changes are necessary

### Don'ts ❌

- ❌ **Use positional-only parameters** unnecessarily
- ❌ **Mix positional and keyword arguments** in confusing ways
- ❌ **Change return types** between versions without clear migration
- ❌ **Use generic exceptions** like ValueError for API errors
- ❌ **Require complex setup** for simple operations
- ❌ **Expose internal implementation** details in public APIs
- ❌ **Use abbreviations** that aren't widely understood
- ❌ **Make APIs too rigid** - allow reasonable flexibility
- ❌ **Forget to document** edge cases and error conditions

## See Also

- [type_hints_standards.md](type_hints_standards.md) - Type annotation patterns
- [error_handling.md](error_handling.md) - Exception handling in APIs
- [testing_standards.md](testing_standards.md) - Testing API contracts
- [infrastructure_modules.md](infrastructure_modules.md) - Module API design
- [../docs/reference/API_REFERENCE.md](../docs/reference/API_REFERENCE.md) - API documentation
- [../docs/core/ARCHITECTURE.md](../docs/core/ARCHITECTURE.md) - API architecture design
