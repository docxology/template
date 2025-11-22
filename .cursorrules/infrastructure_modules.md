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
3. **Well-Tested**: 100% coverage with real data
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

- **100% coverage** mandatory for all infrastructure code
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

Update these scripts to discover and use new infrastructure modules as needed.

## Quality Checklist

Before committing:

- [ ] 100% test coverage verified
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

## References

- [Infrastructure AGENTS.md](../infrastructure/AGENTS.md)
- [Two-Layer Architecture](../docs/TWO_LAYER_ARCHITECTURE.md)
- [Testing Guide](../docs/TESTING_GUIDE.md)
- [Error Handling Guide](../docs/ERROR_HANDLING_GUIDE.md)

