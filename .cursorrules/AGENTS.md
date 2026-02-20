# .cursorrules - Development Standards and Guidelines

## Overview

This directory contains development standards, coding guidelines, and best practices for the Research Project Template system. All code must follow these standards.

## Files

| File | Purpose | Best For |
|------|---------|----------|
| [AGENTS.md](AGENTS.md) | This file - overview and navigation | Understanding the system |
| [README.md](README.md) | Quick reference guide | Finding quick answers |
| [folder_structure.md](folder_structure.md) | Folder structure documentation standard | Understanding folder organization |
| [error_handling.md](error_handling.md) | Error handling and exception patterns | Writing error handling code |
| [security.md](security.md) | Security standards and guidelines | Writing secure code |
| [python_logging.md](python_logging.md) | Logging standards and best practices | Adding logging to code |
| [infrastructure_modules.md](infrastructure_modules.md) | Infrastructure module development standards | Creating new infrastructure modules |
| [testing_standards.md](testing_standards.md) | Testing patterns and coverage standards | Writing tests with pytest |
| [documentation_standards.md](documentation_standards.md) | AGENTS.md and README.md writing guide | Writing documentation |
| [type_hints_standards.md](type_hints_standards.md) | Type annotation patterns | Adding type hints |
| [llm_standards.md](llm_standards.md) | LLM/Ollama integration patterns | Using local LLMs for research |
| [code_style.md](code_style.md) | Code formatting and style standards | Writing consistent, readable code |
| [git_workflow.md](git_workflow.md) | Git workflow and commit standards | Managing version control |
| [api_design.md](api_design.md) | API design and interface standards | Creating clean, consistent APIs |
| [manuscript_style.md](manuscript_style.md) | Manuscript formatting and style standards | Writing research manuscripts |
| [reporting.md](reporting.md) | Reporting module standards and outputs | Using reporting utilities |
| [refactoring.md](refactoring.md) | Refactoring and modularization standards | Refactoring code with clean breaks |

## Key Principles

### 1. Two-Layer Architecture

**Layer 1: Infrastructure** (Generic, reusable)

- Location: `infrastructure/` (root level)
- Domain-independent tools
- Reusable across projects
- 60% minimum test coverage required (currently 83.33% achieved - exceeds stretch goal!)

**Layer 2: Project** (Specific, customizable)

- Location: `projects/{name}/src/` (project-specific code)
- Research-specific code
- Uses generic infrastructure utilities
- 90% minimum test coverage required (currently 100% achieved)
- Tests: `projects/{name}/tests/`
- Scripts: `projects/{name}/scripts/` (thin orchestrators)

### 2. Thin Orchestrator Pattern

- **Business logic** → `projects/{name}/src/` or `infrastructure/`
- **Orchestration** → `scripts/` (root, generic) or `projects/{name}/scripts/` (project-specific)
- **No logic in scripts** - only coordination

### 3. Quality Standards

- **Testing**: 90%+ coverage required (60% infra, 90% project), data only
- **Documentation**: AGENTS.md + README.md for each directory
- **Type Safety**: Type hints on all public APIs
- **Error Handling**: Use custom exception hierarchy
- **Logging**: Unified logging system throughout

### 4. Pipeline Entry Points

The template provides **two pipeline orchestrators** with different scope:

**Interactive Menu (`./run.sh`)**

- **Use for**: Full pipeline with optional LLM stages
- **Stages**: 0-9 (stage 0 cleanup, stages 1-9 displayed as [1/9] to [9/9])
- **Features**: Interactive menu, research templates, LLM reviews, translations
- **When to use**: builds, LLM features needed

**Python Orchestrator (`python3 scripts/run_all.py`)**

- **Use for**: Core pipeline only, programmatic execution
- **Stages**: 00-07 (zero-padded Python convention)
- **Features**: Minimal dependencies, fast execution
- **When to use**: Automated environments, no LLM requirements

## Quick Start

### For AI Agents (New to the System)

1. **Start here**: Read [AGENTS.md](AGENTS.md) (this file) for overview
2. **Pick your task** - Read the appropriate guide:
    - **Writing code**: [error_handling.md](error_handling.md), [python_logging.md](python_logging.md), [type_hints_standards.md](type_hints_standards.md)
    - **Creating modules**: [infrastructure_modules.md](infrastructure_modules.md), [testing_standards.md](testing_standards.md)
    - **Writing docs**: [documentation_standards.md](documentation_standards.md)
    - **Writing manuscripts**: [manuscript_style.md](manuscript_style.md)
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

1. ✅ Test coverage requirements met (60% infra, 90% project)
2. ✅ All tests pass
3. ✅ No linter errors
4. ✅ Documentation 5. ✅ AGENTS.md and README.md updated

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

- Use `infrastructure.core.logging_utils.get_logger(__name__)`
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
- 60% minimum test coverage required (currently 83.33% achieved)
- AGENTS.md + README.md
- Public API in `__init__.py`
- Type hints on all functions
- Follow thin orchestrator pattern
- Use custom exceptions from `core.exceptions`
- Use unified logging from `core.logging_utils`

**Structure**:

```text
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

### Manuscript Writing

See [manuscript_style.md](manuscript_style.md)

**Key Points**:

- Use equation environment for display math (not `$$`)
- Always label figures, tables, and equations
- Use descriptive labels (e.g., `fig:convergence_plot`, `eq:objective`)
- Reference using `\ref{}` for sections/figures/tables, `\eqref{}` for equations
- Place citations before punctuation
- Use relative paths for figures: `../output/figures/`

**Example**:

```markdown
\begin{equation}
\label{eq:objective}
f(x) = \sum_{i=1}^{n} w_i \phi_i(x)
\end{equation}

As shown in \eqref{eq:objective}, the objective function...
```

**Related Documentation:**

- [manuscript_style.md](manuscript_style.md) - manuscript formatting guide
- [../projects/act_inf_metaanalysis/manuscript/](../projects/act_inf_metaanalysis/manuscript/) - Manuscript content
- [../docs/usage/markdown-template-guide.md](../docs/usage/markdown-template-guide.md) - Markdown guide

## Testing Standards

### Coverage Requirements

- **Infrastructure**: 60% minimum (currently achieving 83.33% - exceeds stretch goal!)
- **Project code**: 90% minimum (currently achieving 100% - coverage!)
- **Integration tests**: All critical workflows covered

### Test Organization

```text
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

1. **No mocks** for core logic - use data
2. **Test behavior**, not implementation
3. **Clear names** - test should be self-documenting
4. **Fast execution** - unit tests < 1s each
5. **Isolated** - tests should not depend on each other

## Documentation Standards

### Directory Documentation

Every directory must have:

1. **AGENTS.md** - documentation
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

# Local infrastructure (Layer 1)
from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import TemplateError
from infrastructure.documentation import FigureManager

# Local project (Layer 2)
from project.src import module
from project.src.simulation import SimpleSimulation
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

```text
template/
├── infrastructure/         # [LAYER 1] Generic tools (root level)
│   ├── core/              # Core utilities (logging, config, exceptions)
│   ├── documentation/     # Documentation tools (figures, glossary)
│   ├── llm/               # LLM integration & research templates
│   ├── project/           # Project discovery & orchestration
│   ├── publishing/        # Publishing tools (DOI, citations)
│   ├── rendering/         # Multi-format rendering (PDF, HTML, slides)
│   ├── reporting/         # Pipeline reporting & error aggregation
│   ├── scientific/        # Scientific dev tools (benchmarking)
│   └── validation/        # Validation & integrity checking
├── projects/             # [LAYER 2] Research projects
│   ├── {name}/           # [LAYER 2] Research code
│   │   ├── src/           # Project-specific algorithms
│   │   ├── tests/         # Project tests
│   │   ├── scripts/       # Project orchestrators
│   │   └── manuscript/   # Research content
├── scripts/               # [LAYER 1] Generic entry points
├── tests/                 # [LAYER 1] Infrastructure tests
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

- [ ] Test coverage requirements met (60% infra, 90% project)
- [ ] All tests pass
- [ ] No linter errors
- [ ] AGENTS.md - [ ] README.md updated
- [ ] Code reviewed against standards
- [ ] Integration tests pass

## References

### Internal Documentation

- [Root AGENTS.md](../AGENTS.md) - System overview
- [Infrastructure AGENTS.md](../infrastructure/AGENTS.md) - Infrastructure layer
- [Projects AGENTS.md](../projects/AGENTS.md) - Projects layer
- [Documentation Hub](../docs/AGENTS.md) - guides

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
| [folder_structure.md](folder_structure.md) | Folder organization standard | Setting up documentation |
| [error_handling.md](error_handling.md) | Exception patterns | Writing error handling |
| [security.md](security.md) | Security standards | Writing secure code |
| [python_logging.md](python_logging.md) | Logging standards | Adding logging to code |
| [infrastructure_modules.md](infrastructure_modules.md) | Infrastructure development | Creating modules |
| [testing_standards.md](testing_standards.md) | Testing patterns | Writing tests |
| [documentation_standards.md](documentation_standards.md) | Documentation guidelines | Writing docs |
| [type_hints_standards.md](type_hints_standards.md) | Type annotation patterns | Adding type hints |
| [code_style.md](code_style.md) | Code formatting standards | Writing consistent code |
| [git_workflow.md](git_workflow.md) | Git workflow standards | Managing version control |
| [api_design.md](api_design.md) | API design standards | Creating clean APIs |
| [llm_standards.md](llm_standards.md) | LLM/Ollama patterns | Using local LLMs |
| [manuscript_style.md](manuscript_style.md) | Manuscript formatting standards | Writing research manuscripts |
| [reporting.md](reporting.md) | Reporting module standards | Reporting outputs and dashboards |

## Integration with Main Documentation

The .cursorrules standards align with and support the main documentation:

| Development Aspect | .cursorrules File | Main Documentation |
|---|---|---|
| System Design | [AGENTS.md](AGENTS.md) | [Root AGENTS.md](../AGENTS.md) |
| Documentation Structure | [folder_structure.md](folder_structure.md) | [Root AGENTS.md](../AGENTS.md) |
| Architecture | [AGENTS.md](AGENTS.md) | [docs/architecture.md](../docs/core/architecture.md) |
| Infrastructure | [infrastructure_modules.md](infrastructure_modules.md) | [infrastructure/AGENTS.md](../infrastructure/AGENTS.md) |
| Error Handling | [error_handling.md](error_handling.md) | [docs/troubleshooting-guide.md](../docs/operational/troubleshooting-guide.md) |
| Security | [security.md](security.md) | [docs/security.md](../docs/development/security.md) |
| Logging | [python_logging.md](python_logging.md) | [docs/logging-guide.md](../docs/operational/logging-guide.md) |
| Testing | [testing_standards.md](testing_standards.md) | [tests/AGENTS.md](../tests/AGENTS.md) |
| Code Style | [code_style.md](code_style.md) | [docs/best-practices.md](../docs/best-practices/best-practices.md) |
| Git Workflow | [git_workflow.md](git_workflow.md) | [docs/version-control.md](../docs/best-practices/version-control.md) |
| API Design | [api_design.md](api_design.md) | [docs/architecture.md](../docs/core/architecture.md) |
| Reporting | [reporting.md](reporting.md) | [docs/modules-guide.md](../docs/modules/modules-guide.md) |
| Documentation | [documentation_standards.md](documentation_standards.md) | [docs/workflow.md](../docs/core/workflow.md) |
| Type Safety | [type_hints_standards.md](type_hints_standards.md) | [docs/architecture.md](../docs/core/architecture.md) |
| LLM Integration | [llm_standards.md](llm_standards.md) | [infrastructure/llm/AGENTS.md](../infrastructure/llm/AGENTS.md) |
| Manuscript Writing | [manuscript_style.md](manuscript_style.md) | [act_inf_metaanalysis/manuscript/](../projects/act_inf_metaanalysis/manuscript/) |
| Refactoring | [refactoring.md](refactoring.md) | [docs/best-practices.md](../docs/best-practices/best-practices.md) |

## Cross-Reference Guide

**For Architecture Decisions:**
→ Check [AGENTS.md](AGENTS.md) for decision criteria  
→ Read [../docs/core/architecture.md](../docs/core/architecture.md) for full architectural overview  
→ Consult [../docs/architecture/thin-orchestrator-summary.md](../docs/architecture/thin-orchestrator-summary.md) for pattern details

**For Infrastructure Development:**
→ Check [infrastructure_modules.md](infrastructure_modules.md) for standards  
→ Study [../infrastructure/AGENTS.md](../infrastructure/AGENTS.md) for module organization  
→ Review [../infrastructure/README.md](../infrastructure/README.md) for quick patterns

**For Code Quality:**
→ Check [error_handling.md](error_handling.md) and [python_logging.md](python_logging.md)  
→ Read [../docs/best-practices/best-practices.md](../docs/best-practices/best-practices.md) for practices  
→ See [../docs/operational/error-handling-guide.md](../docs/operational/error-handling-guide.md) for detailed patterns

## Quick Navigation Guide

### By Development Activity

| Activity | Start Here | Then Read |
|----------|-----------|-----------|
| Setting up folders | [folder_structure.md](folder_structure.md) | [documentation_standards.md](documentation_standards.md) for writing docs |
| Writing functions | [type_hints_standards.md](type_hints_standards.md) | [error_handling.md](error_handling.md), [python_logging.md](python_logging.md) |
| Code formatting | [code_style.md](code_style.md) | [type_hints_standards.md](type_hints_standards.md) for consistency |
| Git workflow | [git_workflow.md](git_workflow.md) | [testing_standards.md](testing_standards.md) for commit testing |
| API design | [api_design.md](api_design.md) | [type_hints_standards.md](type_hints_standards.md) for type safety |
| Handling errors | [error_handling.md](error_handling.md) | [python_logging.md](python_logging.md) for context |
| Writing secure code | [security.md](security.md) | [error_handling.md](error_handling.md) for secure error handling |
| Adding logging | [python_logging.md](python_logging.md) | [error_handling.md](error_handling.md) for error logging |
| Writing tests | [testing_standards.md](testing_standards.md) | [error_handling.md](error_handling.md) for error testing |
| Creating modules | [infrastructure_modules.md](infrastructure_modules.md) | All of the above standards |
| Writing docs | [documentation_standards.md](documentation_standards.md) | Specific guide for your doc type |
| Writing manuscripts | [manuscript_style.md](manuscript_style.md) | [act_inf_metaanalysis/manuscript/](../projects/act_inf_metaanalysis/manuscript/) for manuscript structure |
| Adding type hints | [type_hints_standards.md](type_hints_standards.md) | [documentation_standards.md](documentation_standards.md) for docstrings |
| Using LLM/Ollama | [llm_standards.md](llm_standards.md) | [infrastructure_modules.md](infrastructure_modules.md) for module patterns |
| Generating reports | [reporting.md](reporting.md) | [docs/modules-guide.md](../docs/modules/modules-guide.md) for module details |

### By File Size & Detail Level

**Quick Reference (< 100 lines)**

- [README.md](README.md) - Fast patterns lookup

**Medium Details (100-300 lines)**

- [error_handling.md](error_handling.md) - Exception patterns
- [python_logging.md](python_logging.md) - Logging standards
- [type_hints_standards.md](type_hints_standards.md) - Type annotation patterns
- [code_style.md](code_style.md) - Code formatting standards
- [git_workflow.md](git_workflow.md) - Git workflow standards

**Guides (300-600 lines)**

- [api_design.md](api_design.md) - API design standards
- [testing_standards.md](testing_standards.md) - testing guide
- [infrastructure_modules.md](infrastructure_modules.md) - Module development guide
- [documentation_standards.md](documentation_standards.md) - Documentation writing guide
- [llm_standards.md](llm_standards.md) - LLM/Ollama integration guide
- [manuscript_style.md](manuscript_style.md) - Manuscript formatting and style guide

**System Overview (400+ lines)**

- [AGENTS.md](AGENTS.md) - This file - system overview

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

## See Also

**Development Standards:**

- [`README.md`](README.md) - Quick reference guide
- [`../AGENTS.md`](../AGENTS.md) - system documentation
- [`../infrastructure/AGENTS.md`](../infrastructure/AGENTS.md) - Infrastructure layer documentation
- [`../projects/AGENTS.md`](../projects/AGENTS.md) - Projects layer documentation

**Related Documentation:**

- [`../docs/core/architecture.md`](../docs/core/architecture.md) - System architecture overview
- [`../docs/core/workflow.md`](../docs/core/workflow.md) - Development workflow
- [`../tests/AGENTS.md`](../tests/AGENTS.md) - Testing philosophy and guide

---

**Version**: 2.5.0  
**Last Updated**: 2026-02-11  
**Files**: 17 (AGENTS.md + README.md + 15 guideline files)  
**Status**: All 15 guideline files cross-referenced  
**Updates**: All development rules and standards synchronized with docs/
