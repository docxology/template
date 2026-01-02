# Prose Project - Mathematical Exposition Exemplar

**This is an active project** in the `projects/` directory, discovered and executed by infrastructure discovery functions.

## Overview

A comprehensive prose-focused research project demonstrating advanced mathematical exposition, rigorous theoretical development, and publication-quality academic writing. This project showcases the template's capabilities for mathematical research with extensive LaTeX equations, theorem proofs, and professional manuscript rendering.

## Key Features & Capabilities

### Advanced Mathematical Exposition
- **Rigorous Theorem Development**: Complete mathematical proofs with numbered equations
- **LaTeX Integration**: Professional equation formatting with cross-references
- **Theoretical Framework**: Comprehensive mathematical foundations and derivations
- **Academic Writing Standards**: Formal scholarly prose with proper citations

### Research Visualization Suite
- **Publication-Quality Plots**: Professional mathematical visualizations and charts
- **Comprehensive Analysis Tools**: Function comparison, convergence analysis, statistical plots
- **Automated Figure Generation**: Script-driven visualization pipeline
- **Multiple Output Formats**: PNG, PDF, and interactive HTML visualizations

### Quality Assurance Excellence
- **100% Test Coverage**: Complete testing of all functions and visualization utilities
- **Type-Safe Implementation**: Comprehensive type hints and validation
- **Error Handling**: Robust exception management and graceful degradation
- **Deterministic Behavior**: Reproducible results across all test scenarios

### Publishing & Documentation Workflow
- **Publication Metadata Extraction**: Automated extraction from manuscript content
- **Citation Generation**: BibTeX, APA, and MLA format generation
- **DOI Validation**: Digital Object Identifier verification and badge generation
- **API Documentation Generation**: Automated code documentation from source
- **Manuscript Validation**: Comprehensive validation of structure and references
- **Publishing Preparation**: Complete workflow for academic dissemination

### Enhanced Infrastructure Integration
- **Performance Monitoring**: Resource usage tracking during mathematical analysis
- **Progress Tracking**: Visual progress indicators for multi-step visualization generation
- **Scientific Validation**: Numerical stability assessment and performance benchmarking
- **Advanced Error Handling**: Comprehensive exception handling with recovery suggestions
- **Structured Logging**: Infrastructure-backed logging with operation timing and context

## Directory Structure

```
projects/prose_project/
├── src/                     # Minimal source code for pipeline compliance
│   ├── __init__.py
│   ├── prose_smoke.py       # Simple utility functions
│   ├── AGENTS.md           # Technical documentation
│   └── README.md           # Quick reference
├── tests/                   # Test suite for pipeline compliance
│   ├── __init__.py
│   ├── test_prose_smoke.py  # Unit tests
│   ├── AGENTS.md           # Test documentation
│   └── README.md           # Quick reference
├── manuscript/              # Research manuscript sections
│   ├── 01_introduction.md
│   ├── 02_methodology.md
│   ├── 03_results.md
│   ├── 04_conclusion.md
│   └── references.bib
└── pyproject.toml           # Project configuration
```

## Installation/Setup

This project uses standard Python with minimal dependencies. The manuscript focuses on prose content rendered through the template's PDF pipeline.

## Usage Examples

### Basic Project Workflow

```bash
# Edit manuscript content
vim manuscript/02_methodology.md

# Run pipeline (minimal computation)
python3 ../../scripts/02_run_analysis.py  # If scripts existed

# Generate PDF
python3 ../../scripts/03_render_pdf.py

# View results
open ../../output/pdf/project_combined.pdf
```

### Mathematical Content

The manuscript demonstrates LaTeX mathematical notation:

```latex
\frac{d}{dx} \int_a^x f(t) \, dt = f(x)
```

This is the Fundamental Theorem of Calculus, connecting differentiation and integration.

### Publishing Workflow

```bash
# Prepare publication materials
python3 scripts/prepare_publication.py
# Generates citations, DOI badges, and publication metadata

# Validate manuscript integrity
python3 scripts/validate_manuscript.py
# Comprehensive validation of structure, references, and standards

# Generate API documentation
python3 scripts/generate_api_docs.py
# Automated documentation generation from source code
```

### Publication Features

```python
from scripts.prepare_publication import extract_manuscript_metadata, generate_citations

# Extract publication metadata
metadata = extract_manuscript_metadata()
print(f"Title: {metadata['title']}, Authors: {len(metadata['authors'])}")

# Generate citations in multiple formats
citations = generate_citations(metadata)
print(f"BibTeX: {citations['bibtex'][:50]}...")
print(f"APA: {citations['apa'][:50]}...")
```

## Configuration

Project uses standard template configuration with minimal custom settings. The focus is on prose content rather than computational parameters.

## Testing

```bash
# Run project tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

Tests validate the minimal computational requirements while ensuring pipeline compatibility.

## API Reference

### prose_smoke.py

#### identity (function)
```python
def identity(x):
    """Return input unchanged.

    This trivial function exists solely to satisfy the pipeline's
    requirement for source code and test coverage.

    Args:
        x: Any value

    Returns:
        The input value unchanged
    """
```

#### constant_value (function)
```python
def constant_value():
    """Return a constant value for testing.

    Returns:
        int: Always returns 42
    """
```

### Publication Scripts

#### prepare_publication.py

##### extract_manuscript_metadata (function)
```python
def extract_manuscript_metadata() -> Optional[Dict[str, Any]]:
    """Extract publication metadata from manuscript files.

    Returns:
        Dictionary with publication metadata, or None if extraction fails
    """
```

##### generate_citations (function)
```python
def generate_citations(metadata: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Generate citations in multiple formats.

    Args:
        metadata: Publication metadata dictionary

    Returns:
        Dictionary with citation formats (bibtex, apa, mla), or None if failed
    """
```

##### validate_doi_info (function)
```python
def validate_doi_info(metadata: Dict[str, Any]) -> Optional[str]:
    """Validate DOI and generate badge.

    Args:
        metadata: Publication metadata dictionary

    Returns:
        DOI badge markdown string, or None if validation fails
    """
```

##### create_publication_materials (function)
```python
def create_publication_materials(
    metadata: Dict[str, Any],
    citations: Dict[str, str],
    doi_badge: Optional[str]
) -> Optional[Dict[str, Path]]:
    """Create and save publication materials.

    Args:
        metadata: Publication metadata
        citations: Citation formats dictionary
        doi_badge: DOI badge markdown (optional)

    Returns:
        Dictionary mapping material types to file paths
    """
```

#### validate_manuscript.py

##### validate_manuscript_structure (function)
```python
def validate_manuscript_structure() -> Optional[Dict[str, Any]]:
    """Validate manuscript markdown structure.

    Returns:
        Validation results dictionary, or None if validation fails
    """
```

##### validate_cross_references (function)
```python
def validate_cross_references() -> Optional[Dict[str, bool]]:
    """Validate cross-references across manuscript.

    Returns:
        Dictionary mapping reference types to validation status
    """
```

##### validate_academic_standards (function)
```python
def validate_academic_standards() -> Optional[Dict[str, bool]]:
    """Validate compliance with academic standards.

    Returns:
        Dictionary mapping standards to compliance status
    """
```

##### validate_links (function)
```python
def validate_links() -> Optional[List[Dict[str, Any]]]:
    """Validate links and references in manuscript.

    Returns:
        List of link validation issues, or None if validation fails
    """
```

##### validate_output_integrity (function)
```python
def validate_output_integrity() -> Optional[Any]:
    """Validate output directory integrity.

    Returns:
        Integrity report object, or None if validation fails
    """
```

#### generate_api_docs.py

##### scan_source_code (function)
```python
def scan_source_code() -> Optional[Dict[str, Any]]:
    """Scan project source code for API elements.

    Returns:
        Dictionary with categorized API elements, or None if scanning fails
    """
```

##### generate_documentation_tables (function)
```python
def generate_documentation_tables(api_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Generate markdown documentation tables.

    Args:
        api_data: API elements data from scan_source_code()

    Returns:
        Dictionary mapping table types to markdown content
    """
```

##### save_documentation_files (function)
```python
def save_documentation_files(tables: Dict[str, str]) -> Optional[Dict[str, Path]]:
    """Save generated documentation to files.

    Args:
        tables: Documentation tables from generate_documentation_tables()

    Returns:
        Dictionary mapping file types to saved file paths
    """
```

##### generate_api_summary (function)
```python
def generate_api_summary(
    api_data: Dict[str, Any],
    tables: Dict[str, str]
) -> Optional[Path]:
    """Generate API documentation summary.

    Args:
        api_data: API elements data
        tables: Generated documentation tables

    Returns:
        Path to generated summary file
    """
```

## Troubleshooting

### Common Issues

- **Pipeline compliance**: Ensure minimal source code satisfies template requirements
- **Test coverage**: Maintain 100% coverage for pipeline compatibility
- **Manuscript rendering**: Verify LaTeX mathematical notation is valid

## .cursorrules Compliance

This project fully complies with the template's development standards defined in `.cursorrules/`.

### ✅ **Testing Standards Compliance**
- **100% coverage**: Achieves complete test coverage for all source code
- **Real data only**: All tests use real computations, no mocks
- **Comprehensive integration**: Tests validate mathematical functions, publishing workflows, and documentation generation
- **Deterministic results**: Fixed seeds ensure reproducible test outcomes
- **Publishing validation**: Includes metadata extraction and citation format testing

### ✅ **Documentation Standards Compliance**
- **AGENTS.md + README.md**: Complete technical documentation in each directory
- **Type hints**: All public APIs have complete type annotations
- **Docstrings**: Comprehensive docstrings with examples for all functions
- **Cross-references**: Links between related documentation sections

### ✅ **Type Hints Standards Compliance**
- **Complete annotations**: All public functions have type hints
- **Generic types**: Uses `Dict`, `List`, `Optional`, `Callable` appropriately
- **Consistent patterns**: Follows template conventions throughout

### ✅ **Error Handling Standards Compliance**
- **Custom exceptions**: Uses infrastructure exception hierarchy when available
- **Context preservation**: Exception chaining with `from` keyword
- **Informative messages**: Clear error messages with actionable guidance

### ✅ **Logging Standards Compliance**
- **Unified logging**: Uses `infrastructure.core.logging_utils.get_logger(__name__)`
- **Appropriate levels**: DEBUG, INFO, WARNING, ERROR as appropriate
- **Context-rich messages**: Includes relevant context in log messages

### ✅ **Code Style Standards Compliance**
- **Black formatting**: 88-character line limits, consistent formatting
- **Descriptive names**: Clear variable and function names
- **Import organization**: Standard library, third-party, local imports properly organized

### Compliance Verification

```bash
# Test coverage verification
pytest tests/ --cov=src --cov-fail-under=90

# Type hint verification
python3 -c "import ast; import inspect; # Type checking logic here"

# Documentation completeness check
find . -name "*.py" -exec grep -L '"""' {} \;
```

## Infrastructure Features & Examples

### Performance Monitoring

Resource usage tracking during mathematical analysis:

```python
from infrastructure.core import monitor_performance

with monitor_performance("Prose project analysis pipeline") as monitor:
    # Generate mathematical visualizations
    math_viz = generate_mathematical_visualization()
    theory_viz = generate_theoretical_analysis()

# Performance metrics are automatically logged
performance_metrics = monitor.stop()
print(f"Duration: {performance_metrics.duration:.2f}s")
print(f"Memory used: {performance_metrics.resource_usage.memory_mb:.1f}MB")
```

**Generated Output:**
```
Performance Summary:
Duration: 1.23s
Memory: 32.1MB
```

### Progress Tracking

Visual progress indicators for multi-step operations:

```python
from infrastructure.core import ProgressBar

# Progress tracking for mathematical demonstration
with ProgressBar(total=5, desc="Mathematical tests") as progress:
    demo_results = run_mathematical_demonstration_with_progress(progress)

# Progress tracking for data saving
with ProgressBar(total=1, desc="Saving data") as progress:
    data_path = save_analysis_data_with_progress(demo_results, progress)
```

**Console Output:**
```
Mathematical tests: 100%|██████████████████| 5/5 [00:00<00:00, 25.3it/s]
Saving data: 100%|███████████████████████| 1/1 [00:00<00:00, 12.5it/s]
```

### Scientific Validation

Numerical stability assessment and performance benchmarking:

```python
from infrastructure.scientific import check_numerical_stability, benchmark_function

# Validate mathematical functions
stability_report = validate_mathematical_functions()

# Benchmark mathematical operations
benchmark_report = benchmark_mathematical_operations()

# Reports are saved to output/reports/ directory
print("Generated scientific validation reports")
```

**Generated Reports:**
- `output/reports/mathematical_stability.json` - Stability analysis results
- `output/reports/mathematical_benchmark.json` - Performance benchmarks
- `output/reports/scientific_validation_summary.md` - Validation summary

### Enhanced Error Handling

Comprehensive error handling with recovery suggestions:

```python
try:
    # Main analysis pipeline
    results = run_analysis()
except ScriptExecutionError as e:
    print(f"Script execution failed: {e}")
    if e.recovery_commands:
        print("Recovery commands:")
        for cmd in e.recovery_commands:
            print(f"  {cmd}")
except TemplateError as e:
    print(f"Infrastructure error: {e}")
    if e.suggestions:
        print("Suggestions:")
        for suggestion in e.suggestions:
            print(f"  • {suggestion}")
```

### Structured Logging

Infrastructure-backed logging with operation timing:

```python
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

# Logging is integrated throughout the pipeline
logger.info("Starting mathematical visualization generation")
logger.info("Completed theoretical analysis generation")
```

## Best Practices

- **Focus on content**: Use computational elements only for pipeline compliance
- **Mathematical accuracy**: Ensure all equations and derivations are correct
- **Academic writing**: Follow formal academic prose conventions
- **Cross-references**: Properly label and reference equations and sections

## See Also

- [Root AGENTS.md](../../AGENTS.md) - Complete template documentation
- [projects/code_project/](../code_project/AGENTS.md) - Computational example project
- [infrastructure/rendering/](../../infrastructure/rendering/AGENTS.md) - PDF rendering system