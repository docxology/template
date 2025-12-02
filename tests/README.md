# tests/ - Test Suite

Comprehensive test suite ensuring 100% coverage of all `src/` modules.

## Quick Start

### Run All Tests
```bash
# With coverage report
pytest tests/ --cov=src --cov-report=html

# Using uv
uv run pytest tests/ --cov=src --cov-report=html

# Require 100% coverage
pytest tests/ --cov=src --cov-fail-under=100
```

### Run Specific Tests
```bash
# Single test file
pytest tests/test_example.py -v

# By pattern
pytest tests/ -k "test_add" -v

# Stop on first failure
pytest tests/ -x
```

## Coverage Requirements

- **70% minimum coverage** required for project/src/ modules
- **49% minimum coverage** required for infrastructure/ modules
- Tests must pass before PDF generation
- Real data only (no mocks)
- Coverage report: `htmlcov/index.html`

## Test Organization

```
tests/
├── conftest.py                          # Root test configuration
├── infrastructure/                      # Infrastructure module tests
│   ├── build/                           # Build validation tests
│   ├── core/                            # Core utilities tests
│   ├── documentation/                   # Documentation handling tests
│   ├── literature/                      # Literature search tests
│   ├── llm/                             # LLM integration tests
│   ├── publishing/                      # Publishing tools tests
│   ├── rendering/                       # Rendering pipeline tests
│   ├── scientific/                      # Scientific tools tests
│   └── validation/                      # Validation tests
├── integration/                         # Integration tests
├── test_coverage_completion.py          # Additional coverage tests
├── test_figure_equation_citation.py     # Fig/Eq/Citation tests
└── test_repo_utilities.py               # Repository utilities tests
```

## Test Categories

### Infrastructure Module Tests

**Build Module** (`infrastructure/build/`)
- `test_build_verifier.py` - Build verification and validation
- `test_quality_checker.py` - Document quality analysis
- `test_reproducibility.py` - Build reproducibility tracking

**Core Module** (`infrastructure/core/`)
- `test_config_loader.py` - Configuration file handling
- `test_exceptions.py` - Custom exception handling
- `test_logging_utils.py` - Logging utilities

**Documentation Module** (`infrastructure/documentation/`)
- `test_figure_manager.py` - Figure management and registration
- `test_image_manager.py` - Image handling in markdown
- `test_glossary_gen.py` - API documentation generation
- `test_markdown_integration.py` - Markdown processing integration

**Literature Module** (`infrastructure/literature/`)
- `test_core.py` - Literature search core functionality
- `test_api.py` - API client implementations (arXiv, Semantic Scholar, etc.)
- `test_config.py` - Literature search configuration
- `test_cli.py` - CLI wrapper for search
- `test_integration.py` - Full workflow integration

**LLM Module** (`infrastructure/llm/`)
- `test_core.py` - LLM client core functionality
- `test_context.py` - Conversation context management
- `test_templates.py` - Template system for common tasks
- `test_config.py` - LLM configuration
- `test_validation.py` - Input validation

**Publishing Module** (`infrastructure/publishing/`)
- `test_publishing.py` - Publishing metadata and citations
- `test_api.py` - Platform API clients (Zenodo, arXiv, GitHub)
- `test_cli.py` - CLI wrapper for publishing

**Rendering Module** (`infrastructure/rendering/`)
- `test_core.py` - Render manager core
- `test_latex_utils.py` - LaTeX compilation utilities
- `test_renderers.py` - PDF, HTML, and slides renderers
- `test_config.py` - Rendering configuration
- `test_poster_renderer.py` - Scientific poster generation
- `test_cli.py` - CLI wrapper for rendering

**Scientific Module** (`infrastructure/scientific/`)
- `test_scientific_dev.py` - Scientific computing best practices

**Validation Module** (`infrastructure/validation/`)
- `test_markdown_validator.py` - Markdown validation
- `test_pdf_validator.py` - PDF validation
- `test_integrity.py` - Integrity verification
- `test_check_links.py` - Documentation link checking
- `test_doc_scanner.py` - Comprehensive documentation scanning
- `test_repo_scanner.py` - Repository accuracy/completeness
- `test_cli.py` - CLI wrapper for validation

### Integration Tests
- `test_module_interoperability.py` - Cross-module integration (239 lines)
- `test_integration/` - Integration test suite

### Specialized Tests
- `test_figure_equation_citation.py` - Figure/equation/citation handling
- `test_coverage_completion.py` - Additional coverage for edge cases
- `test_repo_utilities.py` - Repository utilities (1318 lines)

## Debugging

```bash
# Verbose output
pytest tests/ -vv

# Show print statements
pytest tests/ -s

# Run last failed tests
pytest tests/ --lf
```

## Writing Tests

```python
"""Tests for src/module.py"""
import pytest
from module import function

def test_basic_usage():
    """Test basic functionality."""
    result = function("input")
    assert result == "expected"

def test_error_handling():
    """Test error conditions."""
    with pytest.raises(ValueError):
        function("invalid")
```

## Figure, Equation, and Citation Tests

The test suite includes comprehensive validation for:

### Figure Handling
- Figure generation with proper paths
- Figure referencing in markdown
- LaTeX figure environments and captioning
- Multiple figures with unique labels

### Equation Handling
- Equation labeling and cross-referencing
- Multiple equations with unique labels
- Detection of unlabeled equations
- Equation reference resolution

### Citation Handling
- Citation formatting in markdown
- Bibliography file structure
- Multiple citations in sentences
- Citation extraction and validation

### Integrated Workflows
- Complete manuscript sections with all elements
- Cross-section references
- Validation integration
- PDF generation integration

## Test Coverage Statistics

Current coverage by module:
- `example.py`: 100% ✅
- `glossary_gen.py`: 100% ✅
- `pdf_validator.py`: 100% ✅
- `build_verifier.py`: 66% (improving)
- `integrity.py`: 79% (improving)
- `quality_checker.py`: 87% (improving)
- `publishing.py`: 81% (improving)
- `reproducibility.py`: 74% (improving)
- `scientific_dev.py`: 86% (improving)

**Project**: 99.88% (Target: 70%+)
**Infrastructure**: 55.89% (Target: 49%+)

## See Also

- [`AGENTS.md`](AGENTS.md) - Detailed testing guide
- [`conftest.py`](conftest.py) - Test configuration
- [`../infrastructure/README.md`](../infrastructure/README.md) - Infrastructure modules being tested
- [`../project/src/README.md`](../project/src/README.md) - Project modules being tested
- [`../docs/WORKFLOW.md`](../docs/WORKFLOW.md) - Development workflow
