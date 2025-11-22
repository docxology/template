# .cursorrules - Quick Reference

Development standards and coding guidelines for the Research Project Template.

## Files

- **AGENTS.md** - Complete overview and navigation (start here)
- **README.md** - This file (quick reference)
- **error_handling.md** - Exception handling patterns
- **python_logging.md** - Logging standards
- **infrastructure_modules.md** - Infrastructure development guide

## Key Principles

### Architecture

- **Layer 1** (infrastructure/): Generic, reusable tools
- **Layer 2** (project/): Research-specific code
- **Thin Orchestrator**: Logic in modules, orchestration in scripts

### Quality

- **Tests**: 100% coverage with real data
- **Types**: Type hints on all public APIs
- **Docs**: AGENTS.md + README.md per directory
- **Errors**: Use custom exception hierarchy
- **Logging**: Unified logging system

## Quick Patterns

### Imports

```python
from infrastructure.logging_utils import get_logger
from infrastructure.exceptions import TemplateError
```

### Logging

```python
logger = get_logger(__name__)
logger.info("Processing data")
```

### Errors

```python
try:
    result = operation()
except ValueError as e:
    raise TemplateError("Failed") from e
```

### Tests

```python
def test_feature():
    """Test feature with real data."""
    result = function(real_input)
    assert result == expected
```

## Checklist

Before commit:

- [ ] 100% test coverage
- [ ] All tests pass
- [ ] No linter errors
- [ ] Docs updated
- [ ] Type hints complete

## More Info

See [AGENTS.md](AGENTS.md) for comprehensive documentation.
