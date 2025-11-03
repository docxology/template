# src/ - Core Business Logic

## Purpose

The `src/` directory contains **all core business logic, algorithms, and mathematical implementations** for the project. This is the single source of truth for computational functionality.

## Architectural Role

### Thin Orchestrator Pattern

In this architecture:
- **`src/`** = Core business logic (100% tested)
- **`scripts/`** = Thin orchestrators (import and use `src/` methods)
- **`tests/`** = Validation (100% coverage required)

Scripts **never** implement algorithms - they import and use `src/` methods.

## Module Organization

### Core Modules

| Module | Purpose | Lines | Test Coverage |
|--------|---------|-------|---------------|
| `example.py` | Basic mathematical operations (template example) | 95 | 100% |
| `glossary_gen.py` | API documentation generation from source code | 123 | 100% |
| `pdf_validator.py` | PDF rendering validation and issue detection | 186 | 100% |

### Advanced Modules

| Module | Purpose | Lines | Test Coverage |
|--------|---------|-------|---------------|
| `build_verifier.py` | Build artifact verification and validation | 1036 | 100% |
| `integrity.py` | Output integrity checking and cross-references | 753 | 100% |
| `quality_checker.py` | Document quality analysis and metrics | 624 | 100% |
| `reproducibility.py` | Environment tracking and build manifests | 758 | 100% |
| `publishing.py` | Academic publishing workflow assistance | 872 | 100% |
| `scientific_dev.py` | Scientific computing best practices | 978 | 100% |

## Requirements

### Test Coverage
- **100% coverage required** for all modules
- No code ships without tests
- Real data testing (no mocks policy)
- Tests live in `tests/` directory

### Code Standards
- Type hints on all public APIs
- Comprehensive docstrings
- Pure functions preferred
- Clear error messages
- Follow PEP 8 style

## Import Patterns

### From Scripts
```python
# In scripts/example_figure.py
import sys
import os

def _ensure_src_on_path():
    """Ensure src/ is on Python path."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src_path = os.path.join(repo_root, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

_ensure_src_on_path()

# Now import from src/
from example import add_numbers, calculate_average
```

### From Tests
```python
# Tests automatically have src/ on path via conftest.py
from example import add_numbers
from quality_checker import analyze_document_quality
```

### From Repo Utilities
```python
# In repo_utilities/validate_pdf_output.py
sys.path.insert(0, str(repo_root / "src"))
from pdf_validator import validate_pdf_rendering
```

## Module Descriptions

### example.py
Template module demonstrating basic patterns:
- `add_numbers()`, `multiply_numbers()` - Basic operations
- `calculate_average()` - Statistical functions
- `find_maximum()`, `find_minimum()` - Data analysis
- `is_even()`, `is_odd()` - Validation helpers

### glossary_gen.py
Generates API documentation from source code:
- `build_api_index()` - Scans src/ and extracts public APIs
- `generate_markdown_table()` - Creates formatted tables
- `inject_between_markers()` - Updates documentation files

### pdf_validator.py
Validates PDF rendering quality:
- `extract_text_from_pdf()` - Text extraction
- `scan_for_issues()` - Detects unresolved references, warnings
- `validate_pdf_rendering()` - Comprehensive validation

### build_verifier.py
Comprehensive build verification:
- `run_build_command()` - Execute and monitor builds
- `verify_build_artifacts()` - Check expected outputs
- `verify_build_reproducibility()` - Multiple build consistency
- `verify_build_environment()` - Dependency validation

### integrity.py
Output integrity verification:
- `verify_file_integrity()` - Hash-based validation
- `verify_cross_references()` - Markdown cross-refs
- `verify_academic_standards()` - Research document compliance
- `verify_output_completeness()` - All expected files present

### quality_checker.py
Document quality analysis:
- `analyze_readability()` - Flesch score, Gunning Fog
- `analyze_academic_standards()` - Research writing compliance
- `analyze_structural_integrity()` - Document organization
- `calculate_overall_quality_score()` - Comprehensive metrics

### reproducibility.py
Build reproducibility tracking:
- `capture_environment_state()` - System snapshot
- `generate_reproducibility_report()` - Build manifest
- `verify_reproducibility()` - Compare builds
- `create_reproducible_environment()` - Environment setup

### publishing.py
Academic publishing assistance:
- `extract_publication_metadata()` - Parse manuscript data
- `generate_citation_bibtex()` - BibTeX format
- `validate_doi()` - DOI format validation
- `create_publication_package()` - Submission bundle

### scientific_dev.py
Scientific computing best practices:
- `check_numerical_stability()` - Algorithm stability
- `benchmark_function()` - Performance analysis
- `generate_scientific_documentation()` - API docs
- `validate_scientific_implementation()` - Correctness checks

## Adding New Modules

### Checklist
1. Create module in `src/` with type hints and docstrings
2. Add comprehensive tests in `tests/test_<module>.py`
3. Ensure 100% test coverage
4. Update this documentation
5. Add to import examples if commonly used
6. Run full test suite to verify integration

### Template
```python
"""Module description.

This module provides functionality for [purpose].
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any


def public_function(arg: str) -> str:
    """Function description.
    
    Args:
        arg: Argument description
        
    Returns:
        Return value description
        
    Raises:
        ValueError: When input is invalid
    """
    if not arg:
        raise ValueError("arg cannot be empty")
    return f"processed: {arg}"
```

## Integration Points

- **Scripts**: Import and use src/ methods for all computation
- **Tests**: Validate src/ functionality with 100% coverage
- **Repo Utilities**: Use src/ for validation and analysis
- **Glossary**: Auto-generate API docs from src/ modules

## Best Practices

1. **Pure Functions**: Prefer stateless functions with no side effects
2. **Type Safety**: Use type hints extensively
3. **Documentation**: Every public API needs docstrings
4. **Error Handling**: Clear, actionable error messages
5. **Testing**: Write tests first (TDD)
6. **Modularity**: Single responsibility per function
7. **Performance**: Profile before optimizing
8. **Compatibility**: Support Python 3.10+

## See Also

- [`tests/AGENTS.md`](../tests/AGENTS.md) - Testing philosophy and organization
- [`scripts/AGENTS.md`](../scripts/AGENTS.md) - How scripts use src/ modules
- [`../AGENTS.md`](../AGENTS.md) - Complete system documentation
- [`../docs/THIN_ORCHESTRATOR_SUMMARY.md`](../docs/THIN_ORCHESTRATOR_SUMMARY.md) - Pattern details


