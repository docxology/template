# Rendering Infrastructure Tests

## Overview

The `tests/infra_tests/rendering/` directory contains tests for the multi-format rendering infrastructure. These tests validate the PDF generation, HTML rendering, slide creation, and poster rendering capabilities of the Research Project Template.

## Directory Structure

```
tests/infra_tests/rendering/
├── AGENTS.md                           # This technical documentation
├── __init__.py                        # Test package initialization
├── conftest.py                        # Test configuration and fixtures
├── test_cli.py                        # CLI interface tests
├── test_config.py                     # Configuration tests
├── test_core.py                       # Core rendering functionality tests
├── test_latex_package_validator.py    # LaTeX package validation tests
├── test_latex_utils.py                # LaTeX utility tests
├── test_manuscript_discovery.py       # Manuscript discovery tests
├── test_pdf_renderer_additional.py    # Additional PDF renderer tests
├── test_pdf_renderer_combined.py      # Combined PDF renderer tests
├── test_pdf_renderer_coverage.py       # PDF renderer coverage tests
├── test_pdf_renderer_fixes.py         # PDF renderer bug fix tests
├── test_pdf_renderer_full.py          # Full PDF renderer tests
├── test_poster_renderer.py            # Poster renderer tests
├── test_render_all_cli.py             # Render all CLI tests
├── test_renderers.py                  # General renderer tests
├── test_rendering_cli_full.py         # Full rendering CLI tests
├── test_rendering_cli.py              # Rendering CLI tests
├── test_slides_renderer_comprehensive.py # slides renderer tests
├── test_slides_renderer_coverage.py   # Slides renderer coverage tests
├── test_web_renderer_coverage.py      # Web renderer coverage tests
```

## Test Categories

### Core Rendering Tests

**PDF Renderer Tests (`test_pdf_renderer_*.py`)**
- PDF generation validation
- LaTeX compilation testing with various configurations
- Font and styling verification
- Cross-reference resolution testing
- Error handling for malformed manuscripts

**Key Test Scenarios:**
```python
def test_pdf_renderer_basic_compilation():
    """Test basic PDF compilation with minimal manuscript."""
    # Create minimal test manuscript
    manuscript = create_test_manuscript("Basic Test", "Test content")

    # Render PDF
    renderer = PDFRenderer()
    pdf_path = renderer.render(manuscript)

    # Verify PDF was created and is valid
    assert pdf_path.exists()
    assert is_valid_pdf(pdf_path)

    # Check PDF content
    pdf_text = extract_pdf_text(pdf_path)
    assert "Basic Test" in pdf_text
    assert "Test content" in pdf_text

def test_pdf_renderer_cross_references():
    """Test cross-reference resolution in PDF output."""
    manuscript = create_manuscript_with_cross_references()

    pdf_path = render_pdf(manuscript)

    # Verify cross-references are resolved (not showing ??)
    pdf_text = extract_pdf_text(pdf_path)
    assert "??" not in pdf_text  # No unresolved references
    assert "[1]" in pdf_text     # Citation present
    assert "Figure 1" in pdf_text # Figure reference present
```

### Alternative Format Tests

**HTML Renderer Tests (`test_web_renderer_*.py`)**
- HTML generation from markdown manuscripts
- MathJax integration for mathematical content
- CSS styling and responsive design
- Link and reference validation

**Slides Renderer Tests (`test_slides_renderer_*.py`)**
- Beamer LaTeX slide generation
- Reveal.js HTML slide creation
- Slide structure and navigation
- Content layout and formatting

**Poster Renderer Tests (`test_poster_renderer.py`)**
- Large-format poster generation
- Layout optimization for print
- Font scaling and readability
- Content organization for poster format

### CLI and Configuration Tests

**CLI Interface Tests (`test_cli.py`, `test_rendering_cli*.py`)**
- Command-line argument parsing
- Option validation and error handling
- Output path management
- Integration with core rendering modules

**Configuration Tests (`test_config.py`)**
- Rendering configuration validation
- Default value handling
- Environment variable integration
- Configuration override testing

### Utility and Helper Tests

**LaTeX Utilities (`test_latex_utils.py`)**
- LaTeX command generation
- Package inclusion validation
- Template variable substitution
- Error message parsing

**LaTeX Package Validator (`test_latex_package_validator.py`)**
- Package availability checking
- Installation verification
- Compatibility validation
- Error reporting for missing packages

**Manuscript Discovery (`test_manuscript_discovery.py`)**
- Manuscript file detection
- Content parsing and validation
- Metadata extraction
- File structure analysis

## Test Design Principles

### Realistic Testing Approach

**Full Integration Testing:**
- Unlike many infrastructure tests, rendering tests often require full LaTeX installation
- Tests create actual PDF/HTML/Slide files for validation
- File system operations are real (not mocked) for accuracy
- External dependencies (LaTeX, Pandoc) are assumed available

**Validation:**
```python
def validate_rendered_output(output_path: Path, expected_content: List[str]) -> bool:
    """Validate rendered output contains expected content."""

    if not output_path.exists():
        pytest.fail(f"Output file not created: {output_path}")

    # Format-specific validation
    if output_path.suffix == '.pdf':
        return validate_pdf_content(output_path, expected_content)
    elif output_path.suffix == '.html':
        return validate_html_content(output_path, expected_content)
    elif output_path.name.endswith('.tex'):
        return validate_latex_content(output_path, expected_content)
    else:
        return validate_generic_content(output_path, expected_content)

def validate_pdf_content(pdf_path: Path, expected_content: List[str]) -> bool:
    """Validate PDF contains expected text content."""
    try:
        # Extract text from PDF
        pdf_text = extract_pdf_text(pdf_path)

        # Check all expected content is present
        for content in expected_content:
            if content not in pdf_text:
                return False

        # Additional PDF structure validation
        return validate_pdf_structure(pdf_path)

    except Exception as e:
        pytest.fail(f"PDF validation failed: {e}")
        return False
```

### Test Organization

**Modular Test Structure:**
- Each renderer type has dedicated test files
- CLI functionality tested separately from core rendering
- Configuration and utilities tested in isolation
- Integration tests combine multiple components

**Test Naming Convention:**
```python
# Format: test_[component]_[aspect]_[condition]
def test_pdf_renderer_basic_compilation():
def test_pdf_renderer_cross_references():
def test_pdf_renderer_error_handling():
def test_html_renderer_mathjax_integration():
def test_slides_renderer_navigation():
def test_cli_argument_parsing():
def test_config_override_behavior():
```

## Test Infrastructure

### Fixtures and Setup

**Common Test Fixtures:**
```python
@pytest.fixture
def temp_output_dir(tmp_path):
    """Provide temporary directory for output files."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir

@pytest.fixture
def sample_manuscript():
    """Provide sample manuscript content."""
    return {
        'title': 'Test Manuscript',
        'content': '# Introduction\n\nThis is a test manuscript.',
        'metadata': {'author': 'Test Author', 'date': '2024'}
    }

@pytest.fixture
def latex_installation():
    """Ensure LaTeX is available for PDF tests."""
    if not shutil.which('xelatex'):
        pytest.skip("LaTeX (xelatex) not available")

    # Check required packages
    required_packages = ['multirow', 'cleveref', 'doi']
    missing_packages = check_latex_packages(required_packages)
    if missing_packages:
        pytest.skip(f"Missing LaTeX packages: {missing_packages}")
```

### Test Utilities

**Content Generation:**
```python
def create_test_manuscript(title: str, content: str, metadata: dict = None) -> Path:
    """Create temporary manuscript file for testing."""
    manuscript = f"""---
title: {title}
author: {metadata.get('author', 'Test Author') if metadata else 'Test Author'}
---

{content}
"""

    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
    temp_file.write(manuscript)
    temp_file.close()

    return Path(temp_file.name)

def create_manuscript_with_cross_references() -> Path:
    """Create manuscript with citations and figure references."""
    content = """
# Introduction

This paper presents novel findings [cite:key1].

# Methods

The methodology is illustrated in Figure 1.

![Methodology Overview](figures/method.png){#fig:method}

# References

[@key1]: Smith et al. (2024). Novel Method. Journal.
"""

    return create_test_manuscript("Cross-Reference Test", content)
```

**Validation Helpers:**
```python
def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text content from PDF for validation."""
    try:
        with open(pdf_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        pytest.fail(f"Failed to extract PDF text: {e}")

def validate_pdf_structure(pdf_path: Path) -> bool:
    """Validate PDF has proper structure."""
    try:
        with open(pdf_path, 'rb') as f:
            reader = pypdf.PdfReader(f)

            # Check for pages
            if len(reader.pages) == 0:
                return False

            # Check for metadata
            metadata = reader.metadata
            if not metadata.get('/Title'):
                return False

            return True
    except Exception:
        return False
```

## Running Tests

### Test Execution

```bash
# Run all rendering tests
pytest tests/infra_tests/rendering/

# Run specific renderer tests
pytest tests/infra_tests/rendering/test_pdf_renderer_full.py

# Run CLI tests only
pytest tests/infra_tests/rendering/ -k "cli"

# Run with LaTeX requirement check
pytest tests/infra_tests/rendering/ --ignore-glob="*latex*"  # Skip if no LaTeX
```

### Conditional Test Execution

**LaTeX-Dependent Tests:**
```python
# conftest.py - Conditional test skipping
def pytest_collection_modifyitems(config, items):
    """Skip LaTeX-dependent tests if LaTeX not available."""
    if not shutil.which('xelatex'):
        skip_latex = pytest.mark.skip(reason="LaTeX (xelatex) not available")
        for item in items:
            if "latex" in item.name or "pdf" in item.name:
                item.add_marker(skip_latex)
```

**External Dependency Checks:**
```bash
# Check test requirements
python3 -c "
import shutil
print('LaTeX available:', bool(shutil.which('xelatex')))
print('Pandoc available:', bool(shutil.which('pandoc')))

try:
    import pypdf
    print('PyPDF available: True')
except ImportError:
    print('PyPDF available: False')
"
```

## Test Coverage and Quality

### Coverage Goals

**Rendering Module Coverage:**
- PDF rendering: 95%+ coverage
- HTML rendering: 90%+ coverage
- Slides rendering: 85%+ coverage
- CLI interface: 95%+ coverage
- Configuration: 90%+ coverage

### Test Quality Metrics

**Test Effectiveness:**
- All rendering formats produce valid output files
- Error conditions properly handled and reported
- Configuration options work as documented
- CLI commands execute successfully
- Cross-references and citations resolve correctly

**Performance Benchmarks:**
- PDF compilation completes within reasonable time
- Large manuscripts render without memory issues
- CLI commands respond quickly to user input
- Error messages provide clear diagnostic information

## Common Test Issues

### LaTeX-Related Failures

**Missing LaTeX Packages:**
```bash
# Diagnose LaTeX issues
tlmgr list --only-installed | grep -E "(multirow|cleveref|doi)"

# Install missing packages
sudo tlmgr install multirow cleveref doi newunicodechar
```

**Font Issues:**
```bash
# Check font availability
fc-list | grep -i "computer modern"

# Test LaTeX compilation manually
xelatex --interaction=nonstopmode test.tex
```

### File System Issues

**Permission Problems:**
```bash
# Check output directory permissions
ls -la output/

# Clean test artifacts
find . -name "*.pdf" -mtime +1 -delete
find . -name "*.aux" -mtime +1 -delete
```

**Path Resolution:**
```python
# Debug path issues in tests
def debug_test_paths():
    """Debug path resolution in tests."""
    import tempfile
    import os

    print(f"Current directory: {os.getcwd()}")
    print(f"Temp directory: {tempfile.gettempdir()}")

    # Check if output paths are writable
    test_output = Path("test_output")
    test_output.mkdir(exist_ok=True)
    test_file = test_output / "test.txt"
    test_file.write_text("test")
    print(f"Output writable: {test_file.exists()}")
    test_file.unlink()
    test_output.rmdir()
```

## Integration with CI/CD

### CI Pipeline Integration

**GitHub Actions Compatibility:**
```yaml
# .github/workflows/ci.yml - Rendering tests
- name: Test Rendering Infrastructure
  run: |
    # Install LaTeX for PDF tests
    sudo apt-get update
    sudo apt-get install -y texlive-xetex texlive-fonts-recommended

    # Install LaTeX packages
    sudo tlmgr install multirow cleveref doi newunicodechar

    # Run rendering tests
    uv run pytest tests/infra_tests/rendering/ -v
```

### Test Result Analysis

**Coverage Reporting:**
```bash
# Generate coverage for rendering module
pytest tests/infra_tests/rendering/ --cov=infrastructure.rendering --cov-report=html

# Check coverage thresholds
pytest tests/infra_tests/rendering/ --cov=infrastructure.rendering --cov-fail-under=90
```

## Future Test Enhancements

### Planned Improvements

**Testing:**
- **Visual Regression Testing**: Compare rendered output appearance
- **Performance Benchmarking**: Track rendering speed over time
- **Cross-Platform Testing**: Windows and macOS LaTeX compatibility
- **Accessibility Testing**: Screen reader compatibility for HTML output

**Test Infrastructure:**
- **Parallel Test Execution**: Speed up test runs with multiple workers
- **Test Result Caching**: Avoid redundant LaTeX compilations
- **Mock LaTeX Installation**: Simulate LaTeX for faster testing
- **Visual Diff Tools**: Automated comparison of rendered outputs

## Troubleshooting

### Test Debugging

**Verbose Test Output:**
```bash
# Run with detailed output
pytest tests/infra_tests/rendering/test_pdf_renderer_full.py -v -s

# Debug LaTeX compilation
pytest tests/infra_tests/rendering/ --pdb --tb=long
```

**Log Analysis:**
```bash
# Check test logs for LaTeX errors
grep "LaTeX" test_output.log
grep "compilation" test_output.log

# Check LaTeX compilation logs
find . -name "*.log" -exec grep -l "Error" {} \;
```

### Environment Validation

**Pre-Test Setup:**
```bash
# Validate test environment
python3 -c "
import sys
print(f'Python: {sys.version}')

import shutil
print(f'xelatex: {bool(shutil.which(\"xelatex\"))}')
print(f'pandoc: {bool(shutil.which(\"pandoc\"))}')

try:
    import pypdf
    print('pypdf: ✓')
except ImportError:
    print('pypdf: ✗')
"
```

## See Also

**Related Documentation:**
- [`../../../infrastructure/rendering/AGENTS.md`](../../../infrastructure/rendering/AGENTS.md) - Rendering module details
- [`../AGENTS.md`](../AGENTS.md) - Infrastructure test suite overview
- [`../../../AGENTS.md`](../../../AGENTS.md) - System documentation

**Testing Standards:**
- [`../../../.cursorrules/testing_standards.md`](../../../.cursorrules/testing_standards.md) - Testing standards
- [`../../../docs/development/TESTING_GUIDE.md`](../../../docs/development/TESTING_GUIDE.md) - Testing guide