# .cursorrules - Development Standards and Guidelines

## Overview

This directory contains comprehensive development standards, coding guidelines, and best practices for the Research Project Template system. All code must follow these standards.

## Files

| File | Purpose | Best For |
|------|---------|----------|
| [AGENTS.md](AGENTS.md) | This file - overview and navigation | Understanding the complete system |
| [README.md](README.md) | Quick reference guide | Finding quick answers |
| [error_handling.md](error_handling.md) | Error handling and exception patterns | Writing error handling code |
| [python_logging.md](python_logging.md) | Logging standards and best practices | Adding logging to code |
| [infrastructure_modules.md](infrastructure_modules.md) | Infrastructure module development standards | Creating new infrastructure modules |
| [testing_standards.md](testing_standards.md) | Testing patterns and 100% coverage (NEW) | Writing tests with pytest |
| [documentation_standards.md](documentation_standards.md) | AGENTS.md and README.md writing guide (NEW) | Writing documentation |
| [type_hints_standards.md](type_hints_standards.md) | Type annotation patterns (NEW) | Adding type hints |

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
- **Orchestration** → `scripts/` (entry points)
- **No logic in scripts** - only coordination

### 3. Quality Standards

- **Testing**: 100% coverage, real data only
- **Documentation**: AGENTS.md + README.md for each directory
- **Type Safety**: Type hints on all public APIs
- **Error Handling**: Use custom exception hierarchy
- **Logging**: Unified logging system throughout

## Quick Start

### For AI Agents (New to the System)

1. **Start here**: Read [AGENTS.md](AGENTS.md) (this file) for complete overview
2. **Pick your task** - Read the appropriate guide:
   - **Writing code**: [error_handling.md](error_handling.md), [python_logging.md](python_logging.md), [type_hints_standards.md](type_hints_standards.md)
   - **Creating modules**: [infrastructure_modules.md](infrastructure_modules.md), [testing_standards.md](testing_standards.md)
   - **Writing docs**: [documentation_standards.md](documentation_standards.md)
   - **Writing tests**: [testing_standards.md](testing_standards.md)
3. **Follow the standards** - Apply the patterns and examples from the guide
4. **Cross-reference** - See "See Also" sections for related guides

### For Developers (Quick Reference)

1. **Quick lookup**: Use [README.md](README.md) for fast pattern references
2. **Deep dive**: Read specific guide files as needed
3. **Copy patterns**: Use code examples from appropriate guide
4. **Reference**: Keep this directory open during development

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
- Use custom exception hierarchy from `infrastructure/core/exceptions.py`
- Always chain exceptions with `from`
- Provide context in exceptions
- Log before raising critical errors

**Example**:
```python
from infrastructure.core.exceptions import ValidationError

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
from infrastructure.core.logging_utils import get_logger

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
- Follow thin orchestrator pattern
- Use custom exceptions from `core.exceptions`
- Use unified logging from `core.logging_utils`

**Structure**:
```
infrastructure/<module>/
├── __init__.py           # Public API
├── core.py              # Core logic
├── cli.py               # Command-line interface (optional)
├── config.py            # Configuration (optional)
├── AGENTS.md            # Detailed docs
└── README.md            # Quick reference
```

**Related Documentation:**
- [../infrastructure/AGENTS.md](../infrastructure/AGENTS.md) - Module organization
- [infrastructure_modules.md](infrastructure_modules.md) - Development standards
- [error_handling.md](error_handling.md) - Exception patterns
- [python_logging.md](python_logging.md) - Logging standards

## Testing Standards

### Coverage Requirements

- **Infrastructure**: 49% minimum (currently achieving 55.89%)
- **Project code**: 70% minimum (currently achieving 99.88%)
- **Integration tests**: All critical workflows covered

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
from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import TemplateError

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
from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import TemplateError

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
├── infrastructure/        # Reusable infrastructure
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

## All Development Guidelines

This directory provides modular development standards. Each file covers specific aspects:

| File | Purpose | Best For |
|------|---------|----------|
| [AGENTS.md](AGENTS.md) | Overview & navigation | Understanding the system |
| [README.md](README.md) | Quick reference | Finding patterns fast |
| [error_handling.md](error_handling.md) | Exception patterns | Writing error handling |
| [python_logging.md](python_logging.md) | Logging standards | Adding logging to code |
| [infrastructure_modules.md](infrastructure_modules.md) | Infrastructure development | Creating new modules |
| [testing_standards.md](testing_standards.md) | Testing patterns | Writing tests (NEW) |
| [documentation_standards.md](documentation_standards.md) | Documentation guidelines | Writing docs (NEW) |
| [type_hints_standards.md](type_hints_standards.md) | Type annotation patterns | Adding type hints (NEW) |

## Integration with Main Documentation

The .cursorrules standards align with and support the main documentation:

| Development Aspect | .cursorrules File | Main Documentation |
|---|---|---|
| System Design | [AGENTS.md](AGENTS.md) | [Root AGENTS.md](../AGENTS.md) |
| Architecture | [AGENTS.md](AGENTS.md) | [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) |
| Infrastructure | [infrastructure_modules.md](infrastructure_modules.md) | [infrastructure/AGENTS.md](../infrastructure/AGENTS.md) |
| Error Handling | [error_handling.md](error_handling.md) | [docs/TROUBLESHOOTING_GUIDE.md](../docs/TROUBLESHOOTING_GUIDE.md) |
| Logging | [python_logging.md](python_logging.md) | [docs/LOGGING_GUIDE.md](../docs/LOGGING_GUIDE.md) |
| Testing | [testing_standards.md](testing_standards.md) | [tests/AGENTS.md](../tests/AGENTS.md) |
| Workflow | [documentation_standards.md](documentation_standards.md) | [docs/WORKFLOW.md](../docs/WORKFLOW.md) |
| Type Safety | [type_hints_standards.md](type_hints_standards.md) | [docs/TYPE_SAFETY.md](../docs/TYPE_SAFETY.md) |

## Cross-Reference Guide

**For Architecture Decisions:**
→ Check [AGENTS.md](AGENTS.md) for decision criteria  
→ Read [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) for full architectural overview  
→ Consult [../docs/THIN_ORCHESTRATOR_SUMMARY.md](../docs/THIN_ORCHESTRATOR_SUMMARY.md) for pattern details

**For Infrastructure Development:**
→ Check [infrastructure_modules.md](infrastructure_modules.md) for standards  
→ Study [../infrastructure/AGENTS.md](../infrastructure/AGENTS.md) for module organization  
→ Review [../infrastructure/README.md](../infrastructure/README.md) for quick patterns

**For Code Quality:**
→ Check [error_handling.md](error_handling.md) and [python_logging.md](python_logging.md)  
→ Read [../docs/BEST_PRACTICES.md](../docs/BEST_PRACTICES.md) for comprehensive practices  
→ See [../docs/ERROR_HANDLING_GUIDE.md](../docs/ERROR_HANDLING_GUIDE.md) for detailed patterns

## Quick Navigation Guide

### By Development Activity

| Activity | Start Here | Then Read |
|----------|-----------|-----------|
| Writing functions | [type_hints_standards.md](type_hints_standards.md) | [error_handling.md](error_handling.md), [python_logging.md](python_logging.md) |
| Handling errors | [error_handling.md](error_handling.md) | [python_logging.md](python_logging.md) for context |
| Adding logging | [python_logging.md](python_logging.md) | [error_handling.md](error_handling.md) for error logging |
| Writing tests | [testing_standards.md](testing_standards.md) | [error_handling.md](error_handling.md) for error testing |
| Creating modules | [infrastructure_modules.md](infrastructure_modules.md) | All of the above standards |
| Writing docs | [documentation_standards.md](documentation_standards.md) | Specific guide for your doc type |
| Adding type hints | [type_hints_standards.md](type_hints_standards.md) | [documentation_standards.md](documentation_standards.md) for docstrings |

### By File Size & Detail Level

**Quick Reference (< 100 lines)**
- [README.md](README.md) - Fast patterns lookup

**Medium Details (100-300 lines)**
- [error_handling.md](error_handling.md) - Exception patterns
- [python_logging.md](python_logging.md) - Logging standards
- [type_hints_standards.md](type_hints_standards.md) - Type annotation patterns

**Comprehensive Guides (300-600 lines)**
- [testing_standards.md](testing_standards.md) - Complete testing guide
- [infrastructure_modules.md](infrastructure_modules.md) - Module development guide
- [documentation_standards.md](documentation_standards.md) - Documentation writing guide

**System Overview (400+ lines)**
- [AGENTS.md](AGENTS.md) - This file - complete system overview

## Maintenance

This directory is maintained as part of the template repository. All updates should:

1. Maintain consistency across files
2. Update this AGENTS.md when adding new rule files
3. Keep README.md in sync with new guides
4. Follow the same standards described here
5. Ensure cross-references to main documentation are accurate
6. Test all code examples in guides
7. Keep "See Also" sections current

### Adding New Guidelines

When creating a new .cursorrules file:

1. Add entry to Files table in this file
2. Add entry to Files section in README.md
3. Create "See Also" section linking to related guides
4. Include code examples for all patterns
5. Test all examples before committing
6. Update integration table with main docs

---

**Version**: 2.1.0  
**Last Updated**: 2025-11-22  
**Status**: All 8 guideline files complete and cross-referenced  
**Maintainer**: Template Team
