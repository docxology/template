# .cursorrules - Quick Reference

Development standards and coding guidelines for the Research Project Template.

## Files

- **AGENTS.md** - Complete overview and navigation (start here)
- **README.md** - This file (quick reference)
- **error_handling.md** - Exception handling patterns
- **python_logging.md** - Logging standards
- **infrastructure_modules.md** - Infrastructure development guide

## Key Principles

### Two-Layer Architecture

- **Layer 1: Infrastructure** (`infrastructure/`): Generic, reusable tools
  - Works with any project
  - 100% test coverage required
  - Can be copied to other repositories

- **Layer 2: Project** (`project/`): Research-specific code
  - Domain-specific algorithms and analysis
  - Uses Layer 1 tools
  - 100% test coverage required

### Thin Orchestrator Pattern

- **Business logic**: Implemented in module `core.py` or equivalent
- **Orchestration**: Delegated to CLI wrappers and entry points (`scripts/`)
- **Scripts**: Only coordinate, never duplicate logic
- **Key principle**: "Import functions, don't implement algorithms"

### Quality Standards

- **Tests**: 100% coverage with real data (no mocks)
- **Types**: Type hints on all public APIs and functions
- **Docs**: AGENTS.md + README.md for every directory
- **Errors**: Use custom exception hierarchy from `infrastructure.core.exceptions`
- **Logging**: Unified logging via `infrastructure.core.logging_utils`

### Terminology Standards

These terms are used consistently across the codebase:

| Term | Definition | Example |
|------|-----------|---------|
| **Layer 1** | Infrastructure (generic) | `infrastructure/validation/` |
| **Layer 2** | Project-specific | `project/src/` |
| **Thin orchestrator** | Script that coordinates but doesn't implement | `scripts/03_render_pdf.py` |
| **Business logic** | Core computation and algorithms | `infrastructure/validation/core.py` |
| **Module** | Self-contained functionality | `infrastructure/rendering/` |
| **CLI** | Command-line interface | `infrastructure/rendering/cli.py` |

## Quick Patterns

### Imports

```python
from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import TemplateError
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
