# Infrastructure Module Development Rules

## Overview

The `infrastructure/` directory contains **reusable, generic build and validation tools** that apply to any research project. All new infrastructure modules must follow these standards.

## Module Structure Standards

### Subfolder Organization

```
infrastructure/<module>/
├── __init__.py           # Public API exports
├── AGENTS.md            # Comprehensive documentation
├── README.md            # Quick reference
├── core.py              # Core functionality
├── api.py               # External API integrations (if needed)
├── config.py            # Configuration management
└── utils.py             # Utilities (if needed)
```

### Module Requirements

1. **Generic First**: Reusable across all projects
2. **Domain-Independent**: No research-specific assumptions
3. **Well-Tested**: 60% minimum coverage with real data (currently 83.33% achieved - exceeds stretch goal!)
4. **Well-Documented**: Complete AGENTS.md and README.md
5. **Type-Hinted**: All public APIs have type annotations

## Testing Standards

### Test Organization

```
tests/infrastructure/test_<module>/
├── __init__.py
├── conftest.py          # Shared fixtures
├── test_core.py         # Core functionality tests
├── test_api.py          # API integration tests
├── test_integration.py  # End-to-end workflows
```

### Coverage Requirements

- **60% minimum coverage** required for infrastructure code (currently 83.33% achieved - exceeds stretch goal!)
- **No mock methods** - test with real data
- **Integration tests** demonstrating complete workflows
- **Edge cases** and error conditions tested

## Import Standards

### From Infrastructure

```python
# Good: Import from infrastructure package
from infrastructure.literature import LiteratureSearch
from infrastructure.llm import LLMClient
from infrastructure.rendering import RenderManager
from infrastructure.reporting import generate_pipeline_report, get_error_aggregator

# Bad: Relative imports outside package
from ..literature import LiteratureSearch  # DON'T
```

### Exception Handling

```python
# Good: Use infrastructure exceptions
from infrastructure.core.exceptions import (
    LiteratureSearchError, 
    LLMConnectionError,
    RenderingError
)

# Good: Raise with context
raise LiteratureSearchError(
    "API request failed",
    context={"source": "arxiv", "query": query}
)
```

### Logging

```python
# Good: Use infrastructure logging
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)
logger.info(f"Processing {count} items")

# See python_logging.md for full guidelines
```

## Module-Specific Guidelines

### Literature Module

- **Multi-source**: Support multiple academic databases
- **Rate limiting**: Respect API rate limits automatically
- **Caching**: Cache responses where possible
- **Deduplication**: Merge results from multiple sources

### LLM Module

- **Local-first**: Prefer local models (Ollama)
- **Privacy**: No data sent to external services by default
- **Fallback**: Graceful degradation when models unavailable
- **Templates**: Reusable prompts for common tasks

### Rendering Module

- **Format-agnostic**: Support multiple output formats
- **Quality checks**: Validate all generated outputs
- **Incremental**: Support incremental builds
- **Caching**: Cache intermediate results

### Publishing Module

- **Platform-independent**: Support multiple publishing platforms
- **Metadata-rich**: Complete metadata for all outputs
- **Compliance**: Check platform-specific requirements
- **Automation**: Minimize manual intervention

### Reporting Module

- **Multi-format**: Generate reports in JSON, HTML, and Markdown
- **Actionable**: Include specific recommendations and fixes
- **Integrated**: Automatically integrated into pipeline stages
- **Error aggregation**: Categorize and prioritize errors
- **Performance tracking**: Monitor resource usage and bottlenecks

## Configuration Management

### Environment Variables

- Prefix with module name: `LITERATURE_API_KEY`
- Document in module README.md
- Provide sensible defaults

### Config Files

- Use `<module>/config.py` for configuration classes
- Support loading from environment variables
- Use dataclasses for type safety

```python
@dataclass
class ModuleConfig:
    setting: str = "default"
    
    @classmethod
    def from_env(cls) -> ModuleConfig:
        return cls(
            setting=os.getenv("MODULE_SETTING", "default")
        )
```

## API Design

### Public API

- Export in `__init__.py`
- Document with comprehensive docstrings
- Type-hint all parameters and returns
- Use descriptive names

### Private Implementation

- Prefix with `_` for internal functions
- Keep in separate modules if complex
- Document for maintainers

## Error Handling

### Use Specific Exceptions

```python
# Good
raise LiteratureSearchError("Query failed")

# Bad
raise Exception("Query failed")
```

### Chain Exceptions

```python
try:
    api_call()
except RequestException as e:
    raise LiteratureSearchError("API failed") from e
```

## Documentation Requirements

### AGENTS.md

- **Purpose**: What the module does
- **Architecture**: How it's organized
- **Usage**: Code examples
- **Configuration**: All options documented
- **Testing**: How to run tests

### README.md

- **Quick Start**: Minimal example
- **Features**: Key capabilities
- **Installation**: Dependencies (if any)

### Code Documentation

```python
def function_name(arg: str) -> str:
    """One-line summary.
    
    Detailed description of what the function does,
    including any important behavior or edge cases.
    
    Args:
        arg: Description of argument
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: When this happens
        
    Example:
        >>> function_name("input")
        'output'
    """
```

## Integration with Build System

### Scripts Integration

Infrastructure modules are integrated into the build pipeline through:

1. **Setup** (`scripts/00_setup_environment.py`) - Environment validation
2. **Testing** (`scripts/01_run_tests.py`) - Infrastructure and project tests
3. **Analysis** (`scripts/02_run_analysis.py`) - Project script discovery and execution
4. **PDF Rendering** (`scripts/03_render_pdf.py`) - Document generation
5. **Validation** (`scripts/04_validate_output.py`) - Quality assurance

**Pipeline Entry Points**: Two orchestrators available:
- `./run.sh --pipeline`: 10 stages (0-9) with optional LLM stages (stage 0 cleanup, stages 1-9 tracked)
- `python3 scripts/run_all.py`: 6-stage core pipeline (00-05) only

Update these scripts to discover and use new infrastructure modules as needed.

## Quality Checklist

Before committing:

- [ ] Test coverage requirements met (60% minimum, currently 83.33% achieved - exceeds stretch goal!)
- [ ] All tests pass
- [ ] AGENTS.md complete
- [ ] README.md written
- [ ] Type hints on all public APIs
- [ ] Docstrings on all functions
- [ ] infrastructure/__init__.py updated
- [ ] infrastructure/AGENTS.md updated
- [ ] No linter errors
- [ ] Wrapper script created (if needed)

## Common Pitfalls

### ❌ Don't

- Import from project-specific code
- Hardcode paths or values
- Skip error handling
- Use mock methods in tests
- Assume specific research domain

### ✅ Do

- Keep modules focused and single-purpose
- Use configuration for flexibility
- Provide clear error messages
- Test with real data
- Design for reusability

## Complete Example Module

### Module Structure

```
infrastructure/example_module/
├── __init__.py           # Public API exports
├── core.py              # Core functionality
├── cli.py               # Command-line interface (optional)
├── config.py            # Configuration management (optional)
├── AGENTS.md            # Comprehensive documentation
└── README.md            # Quick reference
```

### __init__.py Example

```python
"""Example module - brief description.

Complete module description including main features and use cases.

Example:
    >>> from infrastructure.example_module import process_data
    >>> result = process_data("input")
    >>> print(result)
    'processed'
"""

from .core import process_data, validate_input, ExampleError
from .config import ExampleConfig

__all__ = [
    "process_data",
    "validate_input",
    "ExampleError",
    "ExampleConfig",
]
```

### core.py Example

```python
"""Core functionality for example module."""

from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import ValidationError

logger = get_logger(__name__)

class ExampleError(Exception):
    """Example module error."""
    pass

def process_data(data: str) -> str:
    """Process data.
    
    Args:
        data: Input data
        
    Returns:
        Processed result
        
    Raises:
        ValidationError: If data is invalid
        
    Example:
        >>> process_data("hello")
        'HELLO'
    """
    logger.debug(f"Processing data: {data}")
    
    try:
        result = validate_input(data)
        logger.info(f"Processing completed: {result}")
        return result.upper()
    except ValueError as e:
        logger.error(f"Processing failed: {e}")
        raise ValidationError("Invalid data") from e

def validate_input(data: str) -> str:
    """Validate input data.
    
    Args:
        data: Input to validate
        
    Returns:
        Validated data
        
    Raises:
        ValueError: If invalid
    """
    if not isinstance(data, str):
        raise ValueError("Data must be string")
    if len(data) == 0:
        raise ValueError("Data cannot be empty")
    return data
```

### config.py Example

```python
"""Configuration for example module."""

from dataclasses import dataclass
import os

@dataclass
class ExampleConfig:
    """Example module configuration."""
    
    timeout: int = 30
    retries: int = 3
    debug: bool = False
    
    @classmethod
    def from_env(cls) -> "ExampleConfig":
        """Load configuration from environment variables.
        
        Environment variables:
            EXAMPLE_TIMEOUT: Request timeout in seconds (default: 30)
            EXAMPLE_RETRIES: Number of retries (default: 3)
            EXAMPLE_DEBUG: Enable debug mode (default: false)
        
        Returns:
            ExampleConfig instance
        """
        return cls(
            timeout=int(os.getenv("EXAMPLE_TIMEOUT", "30")),
            retries=int(os.getenv("EXAMPLE_RETRIES", "3")),
            debug=os.getenv("EXAMPLE_DEBUG", "false").lower() == "true",
        )
```

### cli.py Example

```python
"""Command-line interface for example module."""

import argparse
from infrastructure.core.logging_utils import get_logger
from .core import process_data
from .config import ExampleConfig

logger = get_logger(__name__)

def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(description="Example module CLI")
    parser.add_argument("data", help="Data to process")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    try:
        config = ExampleConfig(debug=args.debug)
        result = process_data(args.data)
        print(f"Result: {result}")
        return 0
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())
```

## Integration Checklist

Before merging a new infrastructure module:

- [ ] Module structure matches recommended organization
- [ ] Test coverage requirements met (60% minimum, currently 83.33% achieved - exceeds stretch goal!)
- [ ] All public APIs have type hints
- [ ] AGENTS.md covers all features
- [ ] README.md has working quick-start
- [ ] Error handling uses custom exceptions
- [ ] Logging uses unified system
- [ ] Configuration documented
- [ ] CLI interface working (if applicable)
- [ ] No imports from project-specific code
- [ ] infrastructure/__init__.py updated
- [ ] infrastructure/AGENTS.md updated
- [ ] Tests pass locally
- [ ] No linter errors

## References

- [Infrastructure AGENTS.md](../infrastructure/AGENTS.md) - Module organization
- [Advanced Modules Guide](../docs/ADVANCED_MODULES_GUIDE.md) - Complete guide to all advanced modules
- [API Reference](../docs/API_REFERENCE.md) - Complete API documentation for all modules
- [Two-Layer Architecture](../docs/TWO_LAYER_ARCHITECTURE.md) - Architecture explanation
- [Testing Guide](testing_standards.md) - Testing infrastructure code
- [Error Handling Guide](error_handling.md) - Exception patterns
- [Logging Guide](python_logging.md) - Logging standards
- [Documentation Guide](documentation_standards.md) - Writing module docs
- [Type Hints Guide](type_hints_standards.md) - Type annotation patterns

