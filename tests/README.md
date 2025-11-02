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

- **100% coverage** required for all `src/` modules
- Tests must pass before PDF generation
- Real data only (no mocks)
- Coverage report: `htmlcov/index.html`

## Test Organization

```
tests/
├── conftest.py                          # Configuration
├── test_*.py                            # Unit tests (match src/ modules)
├── test_integration_*.py                # Integration tests
├── test_repo_utilities.py               # Utilities tests
├── test_figure_equation_citation.py     # Fig/Eq/Citation tests
└── test_coverage_completion.py          # Additional coverage tests
```

## Test Categories

### Core Unit Tests
- `test_example.py` - Basic operations and template functions
- `test_glossary_gen.py` - API documentation generation
- `test_pdf_validator.py` - PDF validation and rendering

### Advanced Module Tests
- `test_build_verifier.py` - Build verification (400 lines)
- `test_integrity.py` - Integrity checking (496 lines)
- `test_quality_checker.py` - Quality analysis (463 lines)
- `test_reproducibility.py` - Reproducibility tracking (427 lines)
- `test_publishing.py` - Publishing tools (427 lines)
- `test_scientific_dev.py` - Scientific best practices (339 lines)

### Integration Tests
- `test_integration_pipeline.py` - End-to-end pipeline (821 lines)
- `test_example_figure.py` - Figure generation (452 lines)
- `test_generate_research_figures.py` - Research figures (588 lines)
- `test_repo_utilities.py` - Repository utilities (1318 lines)

### Specialized Tests
- `test_figure_equation_citation.py` - Figure/equation/citation handling (NEW)
- `test_coverage_completion.py` - Additional coverage for edge cases (NEW)

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

**Overall**: 79% (Target: 100%)

## See Also

- [`AGENTS.md`](AGENTS.md) - Detailed testing guide
- [`conftest.py`](conftest.py) - Test configuration
- [`../src/README.md`](../src/README.md) - Modules being tested
- [`../docs/WORKFLOW.md`](../docs/WORKFLOW.md) - Development workflow
