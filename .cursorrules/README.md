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
- **llm_standards.md** - LLM/Ollama integration patterns
- **code_style.md** - Code formatting and style standards
- **git_workflow.md** - Git workflow and commit standards
- **security.md** - Security standards and guidelines
- **api_design.md** - API design and interface standards
- **manuscript_style.md** - Manuscript formatting and style standards

## Key Principles

### Two-Layer Architecture

- **Layer 1: Infrastructure** (`infrastructure/`): Generic, reusable tools
  - Works with any project
  - 70%+ test coverage required (49% infra, 70% project)
  - Can be copied to other repositories

- **Layer 2: Project** (`project/`): Research-specific code
  - Domain-specific algorithms and analysis
  - Uses Layer 1 tools
  - 70%+ test coverage required (49% infra, 70% project)

### Thin Orchestrator Pattern

- **Business logic**: Implemented in module `core.py` or equivalent
- **Orchestration**: Delegated to CLI wrappers and entry points (`scripts/`)
- **Scripts**: Only coordinate, never duplicate logic
- **Key principle**: "Import functions, don't implement algorithms"

### Quality Standards

- **Tests**: 70%+ coverage required (49% infra, 70% project) with real data (no mocks)
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

### Manuscript Formatting

```markdown
# Equations
\begin{equation}
\label{eq:objective}
f(x) = \sum_{i=1}^{n} w_i \phi_i(x)
\end{equation}
Using \eqref{eq:objective}...

# Figures
\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/figure.png}
\caption{Descriptive caption.}
\label{fig:figure_name}
\end{figure}
See Figure \ref{fig:figure_name}...

# Tables
\begin{table}[h]
\centering
\begin{tabular}{|l|c|}
\hline
\textbf{Column 1} & \textbf{Column 2} \\
\hline
Data 1 & Data 2 \\
\hline
\end{tabular}
\caption{Table description.}
\label{tab:table_name}
\end{table}
Table \ref{tab:table_name} shows...

# Citations
According to \cite{author2023}, the method...
Multiple sources \cite{key1,key2,key3} show...
```

## Checklist

Before commit:

- [ ] Test coverage requirements met (49% infra, 70% project)
- [ ] All tests pass
- [ ] No linter errors
- [ ] Docs updated
- [ ] Type hints complete

## Navigation Tips

**Pick your task:**
- Writing code → [type_hints_standards.md](type_hints_standards.md)
- Handling errors → [error_handling.md](error_handling.md)
- Writing secure code → [security.md](security.md)
- Logging → [python_logging.md](python_logging.md)
- Testing → [testing_standards.md](testing_standards.md)
- Building modules → [infrastructure_modules.md](infrastructure_modules.md)
- Writing docs → [documentation_standards.md](documentation_standards.md)
- Writing manuscripts → [manuscript_style.md](manuscript_style.md)
- Using LLM/Ollama → [llm_standards.md](llm_standards.md)

## More Info

- See [AGENTS.md](AGENTS.md) for comprehensive documentation and navigation guide
- See [Quick Navigation Guide](AGENTS.md#quick-navigation-guide) for activity-based guidance
- See [../docs/AGENTS.md](../docs/AGENTS.md) for main project documentation
- See [../docs/HOW_TO_USE.md](../docs/HOW_TO_USE.md) for complete usage guide
- See [../docs/SECURITY.md](../docs/SECURITY.md) for security policy
