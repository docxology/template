# Infrastructure Layer - Build and Validation Tools

## Purpose

This package contains **reusable, generic build and validation infrastructure** that applies to any research project using this template. These modules handle document generation, validation, verification, and publishing tasks independent of the specific research domain.

## Architectural Role (Layer 1)

This is **Layer 1** of the two-layer architecture:
- **Handles:** Build orchestration, document validation, publishing support
- **Reusable:** Across all research projects
- **Not Specific:** Doesn't depend on domain-specific research
- **Tests:** Must achieve 100% coverage with real data

## Module Organization

### Core Build & Verification Modules

| Module | Purpose | Lines | Coverage |
|--------|---------|-------|----------|
| `build_verifier.py` | Build process verification and artifact validation | 398 | 100% |
| `integrity.py` | File integrity checking and cross-reference validation | 354 | 95% |
| `reproducibility.py` | Build reproducibility tracking and environment capture | 264 | 97% |

### Document Quality & Analysis

| Module | Purpose | Lines | Coverage |
|--------|---------|-------|----------|
| `quality_checker.py` | Document quality metrics and academic standards | 252 | 88% |
| `pdf_validator.py` | PDF rendering validation and issue detection | 51 | 100% |

### Academic Publishing Support

| Module | Purpose | Lines | Coverage |
|--------|---------|-------|----------|
| `publishing.py` | Academic publishing workflow assistance | 305 | 94% |

### Documentation & Figure Management

| Module | Purpose | Lines | Coverage |
|--------|---------|-------|----------|
| `glossary_gen.py` | Auto-generate API documentation from source code | 56 | 100% |
| `markdown_integration.py` | Figure insertion and markdown cross-reference management | 85 | 100% |
| `figure_manager.py` | Automatic figure numbering and LaTeX block generation | 84 | 100% |
| `image_manager.py` | Image file management and insertion | 91 | 100% |

### System Infrastructure (NEW)

| Module | Purpose | Lines | Coverage |
|--------|---------|-------|----------|
| `logging_utils.py` | Unified Python logging with context managers and decorators | 350+ | 100% |
| `exceptions.py` | Custom exception hierarchy with context preservation | 400+ | 100% |

## Module Descriptions

### logging_utils.py (NEW)

Unified Python logging system with consistent formatting.

**Key Features:**
- `setup_logger()` / `get_logger()` - Logger configuration
- `log_operation()` - Context manager for operation tracking
- `log_timing()` - Performance timing context manager
- `log_function_call()` - Function call decorator
- `log_success()`, `log_header()`, `log_progress()` - Utilities
- Environment-based log level control (LOG_LEVEL=0-3)
- Integration with bash logging.sh format

**Use Case:** Consistent logging across all Python scripts

### exceptions.py (NEW)

Custom exception hierarchy with context preservation.

**Key Classes:**
- `TemplateError` - Base exception for all template errors
- `ConfigurationError` - Configuration issues
- `ValidationError` - Validation failures
- `BuildError` - Build/compilation failures
- `FileOperationError` - File I/O issues
- `DependencyError` - Missing dependencies
- `TestError` - Test failures
- `IntegrationError` - Integration issues

**Key Functions:**
- `raise_with_context()` - Raise with keyword context
- `format_file_context()` - Format file/line context
- `chain_exceptions()` - Chain exception context

**Use Case:** Consistent error handling with detailed context

### build_verifier.py

Comprehensive build verification and validation.

**Key Functions:**
- `run_build_command()` - Execute build commands with monitoring
- `verify_build_artifacts()` - Check expected outputs exist
- `verify_build_reproducibility()` - Compare multiple builds
- `verify_build_environment()` - Validate dependencies and environment

**Use Case:** Ensure builds are reproducible and artifact-complete

### integrity.py

File and cross-reference integrity verification.

**Key Functions:**
- `verify_file_integrity()` - Hash-based file validation
- `verify_cross_references()` - Check markdown cross-refs resolve
- `verify_academic_standards()` - Compliance checking
- `verify_output_completeness()` - All expected files present

**Use Case:** Validate research document structure and integrity

### reproducibility.py

Build reproducibility and environment tracking.

**Key Functions:**
- `capture_environment_state()` - Snapshot system state
- `generate_reproducibility_report()` - Build manifest
- `verify_reproducibility()` - Compare builds
- `create_reproducible_environment()` - Environment setup

**Use Case:** Ensure builds are reproducible and well-documented

### quality_checker.py

Document quality analysis and metrics.

**Key Functions:**
- `analyze_readability()` - Flesch score, Gunning Fog index
- `analyze_academic_standards()` - Research writing compliance
- `analyze_structural_integrity()` - Document organization
- `calculate_overall_quality_score()` - Comprehensive metrics

**Use Case:** Assess document quality and academic standards compliance

### pdf_validator.py

PDF rendering validation.

**Key Functions:**
- `extract_text_from_pdf()` - Text extraction from PDFs
- `scan_for_issues()` - Detect rendering problems
- `validate_pdf_rendering()` - Comprehensive validation

**Use Case:** Verify PDF generation succeeded and looks correct

### publishing.py

Academic publishing workflow support.

**Key Functions:**
- `extract_publication_metadata()` - Parse manuscript metadata
- `generate_citation_bibtex()` - BibTeX format generation
- `validate_doi()` - DOI format and checksum validation
- `create_publication_package()` - Submission bundle creation

**Use Case:** Support academic publication workflows

### glossary_gen.py

Auto-generate API documentation.

**Key Functions:**
- `build_api_index()` - Scan and extract public APIs
- `generate_markdown_table()` - Create formatted documentation
- `inject_between_markers()` - Update documentation files

**Use Case:** Keep API reference documentation synchronized with code

### markdown_integration.py

Integrate figures and references into markdown.

**Key Functions:**
- `detect_sections()` - Find markdown sections
- `insert_figure_in_section()` - Add figures to sections
- `update_all_references()` - Update cross-references
- `validate_manuscript()` - Validate document structure

**Use Case:** Automatically integrate figures into manuscript

### figure_manager.py

Manage figure numbering and references.

**Key Functions:**
- `FigureManager` class - Central figure management
- `register_figure()` - Register with automatic numbering
- `generate_latex_figure_block()` - Create LaTeX code
- `generate_reference()` - Create LaTeX references

**Use Case:** Automated figure numbering and cross-referencing

### image_manager.py

Manage image files and insertion.

**Key Functions:**
- `ImageManager` class - Central image management
- `insert_figure()` - Insert into markdown
- `insert_reference()` - Add figure reference
- `validate_figures()` - Validate figure integrity

**Use Case:** Manage figure files and markdown integration

## Design Principles

### Generic First

All code in this layer is designed to be reusable across projects:
- No hardcoded paths or project-specific values
- Generic configuration and parameters
- Clear interfaces independent of research domain

### Non-Domain-Specific

Infrastructure modules should:
- ✅ Handle any research project
- ✅ Work with generic document structures
- ✅ Support any type of analysis output
- ❌ NOT depend on specific algorithms
- ❌ NOT assume research domain
- ❌ NOT import from scientific layer

### 100% Test Coverage

All infrastructure code requires:
- Comprehensive unit tests
- Real data testing (no mocks)
- Integration testing where applicable
- Clear error messages and handling

## Integration Points

### With repo_utilities/

Infrastructure modules are used by utility scripts:
```
repo_utilities/
├── render_pdf.sh                          # Orchestration
├── validate_pdf_output.py → pdf_validator.py
├── generate_glossary.py → glossary_gen.py
└── validate_markdown.py → markdown_integration.py
```

### With Scientific Layer

Scientific code uses infrastructure for document management:
```python
# src/scientific/analysis.py
from infrastructure.figure_manager import FigureManager
from infrastructure.markdown_integration import MarkdownIntegration

def generate_analysis_figure():
    # Scientific computation
    results = analyze_data()
    
    # Use infrastructure for document mgmt
    fm = FigureManager()
    fm.register_figure("results.png", "fig:results")
```

### With Build Pipeline

Infrastructure validates entire pipeline:
```
render_pdf.sh
├── (Phase 1) Run tests - ✅ tests/infrastructure/
├── (Phase 2) Run scripts - Scientific layer
├── (Phase 2.5) Validation - ✅ infrastructure modules
├── (Phase 3-5) Generate PDFs - ✅ infrastructure
└── (Phase 6) Validate quality - ✅ pdf_validator.py
```

## Requirements

### Test Coverage
- **100% required** for all modules
- No code ships without tests
- Real data testing (no mocks)
- Tests in `tests/infrastructure/`

### Code Standards
- Type hints on all public APIs
- Comprehensive docstrings
- Pure functions preferred
- Clear error messages
- Follow PEP 8 style

### Documentation
- Module docstrings explaining purpose
- Function docstrings with parameters
- Usage examples where applicable
- Consider project-independent context

## Adding New Infrastructure Modules

### Checklist

1. Create module in `src/infrastructure/` with infrastructure-focused logic
2. Add comprehensive tests in `tests/infrastructure/test_<module>.py`
3. Ensure 100% test coverage
4. Document with clear, generic examples
5. Update this AGENTS.md file
6. Consider integration with build pipeline
7. Add to `src/infrastructure/__init__.py`

### Template

```python
"""Module description.

This module provides [purpose] for [generic use case].
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any


def public_function(arg: str) -> str:
    """Function description with generic context.
    
    Works with any project following this template structure.
    
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

### Design Questions

Before adding infrastructure:
- ✅ Would another research group use this unchanged?
- ✅ Is this independent of research domain?
- ✅ Does this support the build/document pipeline?
- ❌ Is this specific to our research?
- ❌ Does this depend on domain knowledge?

If "no" to top questions → belongs in Scientific layer

## Best Practices

### Do's
✅ Keep modules focused and single-purpose  
✅ Use type hints extensively  
✅ Write comprehensive docstrings  
✅ Test with real scenarios  
✅ Provide clear error messages  
✅ Document non-obvious design choices  
✅ Consider extensibility and customization  

### Don'ts
❌ Import from scientific layer  
❌ Assume specific research domain  
❌ Skip tests or coverage  
❌ Mix concerns or responsibilities  
❌ Hardcode project-specific values  
❌ Duplicate code across modules  
❌ Skip error handling  

## Testing Infrastructure Code

```bash
# Test infrastructure modules specifically
pytest tests/infrastructure/ --cov=src/infrastructure --cov-fail-under=100

# Test integration with build system
pytest tests/integration/ -k infrastructure

# Full coverage including infrastructure
pytest tests/ --cov=src --cov-report=html
```

## See Also

- [`../scientific/AGENTS.md`](../scientific/AGENTS.md) - Scientific layer documentation
- [`../../docs/TWO_LAYER_ARCHITECTURE.md`](../../docs/TWO_LAYER_ARCHITECTURE.md) - Architecture overview
- [`../../docs/DECISION_TREE.md`](../../docs/DECISION_TREE.md) - Code placement guide
- [`../../AGENTS.md`](../../AGENTS.md) - Complete system documentation
- [`../../repo_utilities/AGENTS.md`](../../repo_utilities/AGENTS.md) - Utility scripts documentation

## Key Principles

1. **Generic** - Reusable across projects
2. **Independent** - Doesn't assume research domain
3. **Well-Tested** - 100% test coverage
4. **Well-Documented** - Clear APIs and examples
5. **Self-Contained** - Doesn't depend on scientific layer

