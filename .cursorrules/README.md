# .cursorrules - Quick Reference

Development standards and coding guidelines for the Research Project Template.

## Files

### Main Documents
- **AGENTS.md** - Complete overview and navigation (start here)
- **README.md** - This file (quick reference)

### Development Standards
- **error_handling.md** - Exception handling patterns
- **python_logging.md** - Logging standards and best practices
- **infrastructure_modules.md** - Infrastructure module development guide
- **testing_standards.md** - Testing patterns and coverage
- **documentation_standards.md** - AGENTS.md and README.md writing guide
- **type_hints_standards.md** - Type annotation patterns
- **llm_standards.md** - LLM/Ollama integration patterns (NEW)

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
# Standard library first
import os
from pathlib import Path

# Infrastructure core utilities
from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import TemplateError

# Type hints
from typing import List, Dict, Optional
```

### Logging

```python
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)
logger.debug("Debug message")
logger.info("Processing started")
logger.warning("Potential issue")
logger.error("Operation failed", exc_info=True)
```

### Errors

```python
from infrastructure.core.exceptions import ValidationError

try:
    result = operation()
except ValueError as e:
    raise ValidationError("Operation failed") from e
```

### Type Hints

```python
def process_data(items: list[str], count: int = 10) -> dict[str, int]:
    """Process data with type hints.
    
    Args:
        items: List of strings to process
        count: Number of items to process (default 10)
        
    Returns:
        Dictionary mapping item to processed count
    """
    return {item: len(item) for item in items[:count]}
```

### Tests

```python
import pytest

def test_feature_with_real_data():
    """Test feature using real test data (no mocks)."""
    result = function({"name": "Alice", "age": 30})
    assert result["valid"] is True

def test_feature_error_condition():
    """Test that errors are raised correctly."""
    with pytest.raises(ValidationError):
        function({})  # Missing required fields
```

### Documentation (AGENTS.md Structure)

```markdown
# Module Name

## Overview
[What is this, why exists, who uses it]

## Quick Example
[5-10 lines showing usage]

## API Reference
[Key functions/classes]

## Configuration
[Config options]

## Testing
[How to run tests]

## See Also
[Related docs]
```

### Documentation (README.md Structure)

```markdown
# Module Name

[One-line description]

## Quick Start
[Minimal working example]

## Common Commands
[3-5 most used tasks]

## More Information
See [AGENTS.md](AGENTS.md) for comprehensive docs
```

## Checklist

Before commit:

- [ ] 100% test coverage
- [ ] All tests pass
- [ ] No linter errors
- [ ] Docs updated
- [ ] Type hints complete

## Navigation Tips

**Pick your task:**
- Writing code → [type_hints_standards.md](type_hints_standards.md)
- Handling errors → [error_handling.md](error_handling.md)
- Logging → [python_logging.md](python_logging.md)
- Testing → [testing_standards.md](testing_standards.md)
- Building modules → [infrastructure_modules.md](infrastructure_modules.md)
- Writing docs → [documentation_standards.md](documentation_standards.md)
- Using LLM/Ollama → [llm_standards.md](llm_standards.md)

## More Info

- See [AGENTS.md](AGENTS.md) for comprehensive documentation and navigation guide
- See [Quick Navigation Guide](AGENTS.md#quick-navigation-guide) for activity-based guidance
