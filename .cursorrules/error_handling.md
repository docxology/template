# Error Handling Standards

## Exception Hierarchy

All custom exceptions inherit from `TemplateError` in `infrastructure/core/exceptions.py`.

### Import Pattern

```python
from infrastructure.core.exceptions import (
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

## Exception Hierarchy Details

### Base Exception

```python
class TemplateError(Exception):
    """Base exception for all template errors."""
    
    def __init__(self, message: str, context: dict | None = None):
        """Initialize exception.
        
        Args:
            message: Error message
            context: Additional context information
        """
        self.message = message
        self.context = context or {}
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Format message with context."""
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} ({context_str})"
        return self.message
```

### Derived Exceptions

```python
# Configuration errors
class ConfigurationError(TemplateError):
    """Configuration or setup failed."""
    pass

class MissingConfigurationError(ConfigurationError):
    """Required configuration is missing."""
    pass

# Validation errors
class ValidationError(TemplateError):
    """Data validation failed."""
    pass

class DataValidationError(ValidationError):
    """Data format/content invalid."""
    pass

# Build/Processing errors
class BuildError(TemplateError):
    """Build or rendering process failed."""
    pass

class CompilationError(BuildError):
    """LaTeX or code compilation failed."""
    pass

# File operation errors
class FileOperationError(TemplateError):
    """File I/O operation failed."""
    pass

class FileNotFoundError(FileOperationError):
    """Required file not found."""
    pass

# Dependency errors
class DependencyError(TemplateError):
    """External dependency missing or invalid."""
    pass

class MissingDependencyError(DependencyError):
    """Required package or tool not installed."""
    pass

# Test errors
class TestError(TemplateError):
    """Test execution or assertion failed."""
    pass

# Integration errors
class IntegrationError(TemplateError):
    """System integration failed."""
    pass
```

## Advanced Patterns

### Exception Context Pattern

```python
from infrastructure.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

def process_user_data(data: dict) -> None:
    """Process user data with context in exceptions.
    
    Args:
        data: User data dictionary
        
    Raises:
        ValidationError: If data is invalid
    """
    try:
        if "email" not in data:
            raise ValueError("email field required")
        if "@" not in data["email"]:
            raise ValueError("invalid email format")
    except ValueError as e:
        logger.error(f"Validation failed: {e}")
        raise ValidationError(
            "Invalid user data",
            context={
                "email": data.get("email", "MISSING"),
                "data": str(data)
            }
        ) from e
```

### Exception Recovery Pattern

```python
def load_config_with_fallback(primary_path: str, fallback_path: str) -> dict:
    """Load config with fallback.
    
    Args:
        primary_path: Primary config file path
        fallback_path: Fallback config file path
        
    Returns:
        Configuration dictionary
        
    Raises:
        ConfigurationError: If both paths fail
    """
    errors = []
    
    # Try primary path
    try:
        return load_config(primary_path)
    except FileOperationError as e:
        logger.warning(f"Primary config failed: {e}")
        errors.append(e)
    
    # Try fallback path
    try:
        return load_config(fallback_path)
    except FileOperationError as e:
        logger.warning(f"Fallback config failed: {e}")
        errors.append(e)
    
    # Both failed
    logger.error(f"Both config paths failed: {errors}")
    raise ConfigurationError(
        "Failed to load configuration from any path",
        context={
            "primary": primary_path,
            "fallback": fallback_path,
            "errors": [str(e) for e in errors]
        }
    ) from errors[-1]
```

### Exception Translation Pattern

```python
def safe_api_call(url: str) -> dict:
    """Call API with exception translation.
    
    Args:
        url: API endpoint URL
        
    Returns:
        API response
        
    Raises:
        IntegrationError: If API call fails
    """
    import requests
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.ConnectionError as e:
        raise IntegrationError("API connection failed") from e
    except requests.Timeout as e:
        raise IntegrationError("API request timeout") from e
    except requests.HTTPError as e:
        raise IntegrationError(f"API returned error: {e.response.status_code}") from e
    except ValueError as e:
        raise IntegrationError("Invalid JSON response") from e
```

### Validation Error Collection Pattern

```python
def validate_user_registration(data: dict) -> None:
    """Validate user registration data.
    
    Collects all validation errors before raising.
    
    Args:
        data: User registration data
        
    Raises:
        ValidationError: If any validation fails
    """
    errors: list[str] = []
    
    # Check all fields
    if not data.get("username"):
        errors.append("username is required")
    elif len(data["username"]) < 3:
        errors.append("username must be at least 3 characters")
    
    if not data.get("email"):
        errors.append("email is required")
    elif "@" not in data["email"]:
        errors.append("email format invalid")
    
    if not data.get("password"):
        errors.append("password is required")
    elif len(data["password"]) < 8:
        errors.append("password must be at least 8 characters")
    
    # Raise with all errors
    if errors:
        raise ValidationError(
            "User registration validation failed",
            context={
                "errors": errors,
                "error_count": len(errors)
            }
        )
```

## Testing Exception Handling

### Testing Exception Raising

```python
import pytest
from infrastructure.core.exceptions import ValidationError

def test_validation_error_raised():
    """Test that validation error is raised."""
    with pytest.raises(ValidationError) as exc_info:
        validate_email("invalid")
    
    # Verify error message
    assert "invalid" in str(exc_info.value).lower()

def test_validation_error_context():
    """Test that error includes context."""
    with pytest.raises(ValidationError) as exc_info:
        validate_email("invalid")
    
    error = exc_info.value
    assert error.context.get("invalid_value") == "invalid"

def test_exception_chaining():
    """Test that exceptions are properly chained."""
    with pytest.raises(ValidationError) as exc_info:
        validate_email("invalid")
    
    # Check that original exception is preserved
    assert exc_info.value.__cause__ is not None
```

## Best Practices

- Use specific exception types (not generic `Exception`)
- Always chain exceptions to preserve traceback (`raise ... from e`)
- Include context information in exceptions
- Log errors before raising (for debugging)
- Use meaningful error messages
- Document exceptions in docstrings
- Test both success and failure paths
- Provide recovery paths when possible

## See Also

- [Error Handling Guide](../docs/operational/ERROR_HANDLING_GUIDE.md) - Comprehensive error handling patterns
- [Logging](python_logging.md) - Logging standards
- [testing_standards.md](testing_standards.md) - Testing error conditions
- [documentation_standards.md](documentation_standards.md) - Documenting exceptions



