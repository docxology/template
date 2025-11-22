# .cursorrules - Development Standards and Guidelines

## Overview

This directory contains comprehensive development standards, coding guidelines, and best practices for the Research Project Template system. All code must follow these standards.

## Files

| File | Purpose |
|------|---------|
| [AGENTS.md](AGENTS.md) | This file - overview and navigation |
| [README.md](README.md) | Quick reference guide |
| [error_handling.md](error_handling.md) | Error handling and exception patterns |
| [python_logging.md](python_logging.md) | Logging standards and best practices |
| [infrastructure_modules.md](infrastructure_modules.md) | Infrastructure module development standards |

## Key Principles

### 1. Two-Layer Architecture

**Layer 1: Infrastructure** (Generic, reusable)
- Domain-independent tools
- Reusable across projects
- 100% test coverage required

**Layer 2: Project** (Specific, customizable)
- Research-specific code
- Uses infrastructure utilities
- 100% test coverage required

### 2. Thin Orchestrator Pattern

- **Business logic** → `src/` or `infrastructure/`
- **Orchestration** → `scripts/` or `repo_utilities/`
- **No logic in scripts** - only coordination

### 3. Quality Standards

- **Testing**: 100% coverage, real data only
- **Documentation**: AGENTS.md + README.md for each directory
- **Type Safety**: Type hints on all public APIs
- **Error Handling**: Use custom exception hierarchy
- **Logging**: Unified logging system throughout

## Quick Start

### For AI Agents

1. Read [AGENTS.md](AGENTS.md) (this file) for overview
2. Read domain-specific rule file for your task:
   - `error_handling.md` - Exception handling
   - `python_logging.md` - Logging
   - `infrastructure_modules.md` - Infrastructure development
3. Follow the standards strictly

### For Developers

1. Read [README.md](README.md) for quick reference
2. Check specific guideline files as needed
3. Use as reference during development

## Development Workflow

### Before Starting

1. ✅ Read relevant .cursorrules files
2. ✅ Understand two-layer architecture
3. ✅ Review existing similar code
4. ✅ Plan with thin orchestrator pattern

### During Development

1. ✅ Write tests first (TDD)
2. ✅ Follow type hints standards
3. ✅ Use unified logging
4. ✅ Handle errors properly
5. ✅ Document as you go

### Before Committing

1. ✅ 100% test coverage verified
2. ✅ All tests pass
3. ✅ No linter errors
4. ✅ Documentation complete
5. ✅ AGENTS.md and README.md updated

## Standards by Topic

### Error Handling

See [error_handling.md](error_handling.md)

**Key Points**:
- Use custom exception hierarchy from `infrastructure/exceptions.py`
- Always chain exceptions with `from`
- Provide context in exceptions
- Log before raising critical errors

**Example**:
```python
from infrastructure.exceptions import ValidationError

try:
    result = process_data(input)
except ValueError as e:
    raise ValidationError("Invalid input", context={"input": input}) from e
```

### Logging

See [python_logging.md](python_logging.md)

**Key Points**:
- Use `infrastructure.logging_utils.get_logger(__name__)`
- Log at appropriate levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Include context in log messages
- Use structured logging where possible

**Example**:
```python
from infrastructure.logging_utils import get_logger

logger = get_logger(__name__)
logger.info(f"Processing {count} items")
```

### Infrastructure Development

See [infrastructure_modules.md](infrastructure_modules.md)

**Key Points**:
- Generic and domain-independent only
- 100% test coverage mandatory
- Complete AGENTS.md + README.md
- Public API in `__init__.py`
- Type hints on all functions

**Structure**:
```
infrastructure/<module>/
├── __init__.py           # Public API
├── core.py              # Core logic
├── AGENTS.md            # Detailed docs
└── README.md            # Quick reference
```

## Testing Standards

### Coverage Requirements

- **Infrastructure**: 100% coverage (strictly enforced)
- **Project code**: 100% coverage (strictly enforced)
- **Integration tests**: All workflows covered

### Test Organization

```
tests/
├── infrastructure/      # Infrastructure tests
│   └── test_<module>/
│       ├── __init__.py
│       ├── conftest.py
│       └── test_*.py
├── scientific/         # Scientific code tests
└── integration/        # End-to-end workflow tests
```

### Test Principles

1. **No mocks** for core logic - use real data
2. **Test behavior**, not implementation
3. **Clear names** - test should be self-documenting
4. **Fast execution** - unit tests < 1s each
5. **Isolated** - tests should not depend on each other

## Documentation Standards

### Directory Documentation

Every directory must have:

1. **AGENTS.md** - Comprehensive documentation
   - Purpose and architecture
   - Usage examples
   - Configuration options
   - Testing instructions
   - Best practices

2. **README.md** - Quick reference
   - Quick start
   - Key features
   - Common commands
   - Links to detailed docs

### Code Documentation

**Module docstrings**:
```python
"""Module description.

Detailed explanation of module purpose and contents.
"""
```

**Function docstrings**:
```python
def function(arg: str) -> str:
    """One-line summary.
    
    Detailed description.
    
    Args:
        arg: Description
        
    Returns:
        Description
        
    Raises:
        ExceptionType: When this happens
        
    Example:
        >>> function("test")
        'result'
    """
```

## Common Patterns

### Import Standards

```python
# Standard library
import os
from pathlib import Path

# Third party
import requests
import pytest

# Local infrastructure
from infrastructure.logging_utils import get_logger
from infrastructure.exceptions import TemplateError

# Local project
from project.src import module
```

### Configuration Pattern

```python
from dataclasses import dataclass
import os

@dataclass
class ModuleConfig:
    """Module configuration."""
    
    setting: str = "default"
    
    @classmethod
    def from_env(cls) -> "ModuleConfig":
        """Load from environment variables."""
        return cls(
            setting=os.getenv("MODULE_SETTING", "default")
        )
```

### Error Handling Pattern

```python
from infrastructure.logging_utils import get_logger
from infrastructure.exceptions import TemplateError

logger = get_logger(__name__)

try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise TemplateError("High-level description") from e
```

## File Organization

### Project Structure

```
template/
├── infrastructure/         # Layer 1: Generic tools
│   ├── <module>/
│   │   ├── __init__.py
│   │   ├── core.py
│   │   ├── AGENTS.md
│   │   └── README.md
│   └── ...
├── project/               # Layer 2: Research code
│   ├── src/
│   ├── tests/
│   ├── scripts/
│   └── manuscript/
├── scripts/               # Generic entry points
├── tests/                 # Infrastructure tests
├── repo_utilities/        # Build utilities
├── docs/                  # Documentation
└── .cursorrules/          # Development standards (THIS DIR)
```

## Checklist for New Code

### Before Writing

- [ ] Understand two-layer architecture
- [ ] Identify correct layer (infrastructure vs project)
- [ ] Review relevant .cursorrules files
- [ ] Plan with thin orchestrator pattern

### While Writing

- [ ] Write tests first (TDD)
- [ ] Add type hints to all functions
- [ ] Use unified logging system
- [ ] Handle errors with custom exceptions
- [ ] Document as you go

### Before Committing

- [ ] 100% test coverage achieved
- [ ] All tests pass
- [ ] No linter errors
- [ ] AGENTS.md complete
- [ ] README.md updated
- [ ] Code reviewed against standards
- [ ] Integration tests pass

## References

### Internal Documentation

- [Root AGENTS.md](../AGENTS.md) - System overview
- [Infrastructure AGENTS.md](../infrastructure/AGENTS.md) - Infrastructure layer
- [Project AGENTS.md](../project/AGENTS.md) - Project layer
- [docs/](../docs/) - Comprehensive guides

### External Resources

- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [pytest Documentation](https://docs.pytest.org/)
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)

## Maintenance

This directory is maintained as part of the template repository. All updates should:

1. Maintain consistency across files
2. Update this AGENTS.md when adding new rule files
3. Keep README.md in sync
4. Follow the same standards described here

---

**Version**: 2.0.0  
**Last Updated**: 2025-11-22  
**Maintainer**: Template Team
