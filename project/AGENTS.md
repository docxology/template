# Project - Complete Research Unit

## Overview

This is a complete, self-contained scientific research project. Everything needed for the research is in this folder:

- **src/** - Scientific algorithms and analysis code
- **tests/** - Comprehensive test suite (99.88% coverage)
- **scripts/** - Analysis workflows
- **manuscript/** - Research manuscript
- **docs/** - Project documentation
- **output/** - Generated results (figures, data, PDFs)

This folder can be copied as a complete unit to start new research based on this work.

## Architecture

### Scientific Code (src/)

Pure Python implementations of research algorithms and analysis:

```
src/
├── example.py              # Basic operations
├── simulation.py           # Simulation framework
├── statistics.py           # Statistical analysis
├── data_generator.py       # Data generation
├── data_processing.py      # Data preprocessing
├── metrics.py              # Performance metrics
├── parameters.py           # Parameter management
├── performance.py          # Performance analysis
├── plots.py                # Plotting functions
├── reporting.py            # Report generation
├── validation.py           # Result validation
└── visualization.py        # Figure generation
```

**Requirements:**
- 70% minimum test coverage (currently achieving 99.88%)
- Type hints on all public APIs
- Comprehensive docstrings
- No mock testing (real data only)
- Pure functions where possible

### Tests (tests/)

Comprehensive test suite validating all src/ code:

- **70% minimum coverage required** - All critical code paths tested (currently 99.88%)
- **Real data testing** - Use actual data, not mocks
- **Integration tests** - Test module interactions
- **Performance tests** - Validate algorithms

**Running tests:**
```bash
pytest tests/ --cov=src
pytest tests/ --cov=src --cov-report=html
```

### Scripts (scripts/)

Thin orchestrators that use src/ modules:

```
scripts/
├── example_figure.py       # Basic analysis example
├── analysis_pipeline.py    # Complete analysis workflow
└── ...
```

**Pattern:**
1. Import modules from src/
2. Call src/ functions
3. Orchestrate workflows
4. Generate outputs

### Manuscript (manuscript/)

Research content in Markdown:

```
manuscript/
├── 01_abstract.md
├── 02_introduction.md
├── 03_methodology.md
├── 04_experimental_results.md
├── 05_discussion.md
├── 06_conclusion.md
├── 08_acknowledgments.md
├── 09_appendix.md
├── config.yaml              # Metadata
├── references.bib           # Bibliography
└── preamble.md              # LaTeX preamble
```

### Output (output/)

Generated results (disposable):

```
output/
├── figures/                 # PNG/PDF figures
├── data/                    # CSV/NPZ data files
├── pdf/                     # Generated PDFs
├── latex_temp/              # LaTeX temporary files
└── reports/                 # Generated reports
```

These files are regenerated on each build and can be deleted safely.

## Development Workflow

### 1. Create New Analysis

**Step 1: Implement in src/**
```python
# src/my_analysis.py
def analyze_data(data):
    """Analyze data.
    
    Args:
        data: Input array
        
    Returns:
        Analysis results
    """
    pass
```

**Step 2: Add comprehensive tests**
```python
# tests/test_my_analysis.py
def test_analyze_data():
    """Test analyze_data function."""
    result = analyze_data(test_data)
    assert result is not None
```

**Step 3: Ensure coverage requirements met**
```bash
pytest tests/test_my_analysis.py --cov=src/my_analysis --cov-fail-under=70
```

**Step 4: Use in scripts**
```python
# scripts/run_analysis.py
from my_analysis import analyze_data

data = generate_data()
results = analyze_data(data)
```

**Step 5: Document in manuscript**
```markdown
# Methodology

We implemented the analysis using our src/my_analysis.py module...

![Results](../output/figures/analysis_results.png){fig:analysis width=0.8}
```

### 2. Generate Figures

Scripts generate figures that are integrated into the manuscript:

```python
# scripts/generate_results.py
from plots import plot_convergence
from infrastructure.documentation import FigureManager

fig = plot_convergence(results)
fm = FigureManager()
fm.register_figure(
    filename="results.png",
    caption="Convergence results visualization",
    label="fig:results"
)
```

Figures are automatically referenced:
```markdown
See [Figure @fig:results] for detailed results.
```

### 3. Build Manuscript

From template root:
```bash
python3 scripts/03_render_pdf.py
```

Or use the full pipeline:
```bash
python3 scripts/run_all.py
```

This:
1. Runs all project tests
2. Executes all scripts
3. Generates all figures
4. Builds manuscript PDFs
5. Validates quality

## Module Guide

### Core Modules

- **example.py** - Template example with basic operations
- **simulation.py** - Scientific simulation framework with reproducibility
- **parameters.py** - Parameter set management and validation

### Data Processing

- **data_generator.py** - Generate synthetic data for experiments
- **data_processing.py** - Preprocessing, cleaning, normalization
- **statistics.py** - Statistical analysis and hypothesis testing

### Analysis & Reporting

- **metrics.py** - Performance metrics and quality measures
- **performance.py** - Convergence and scalability analysis
- **validation.py** - Result validation and anomaly detection
- **reporting.py** - Automated report generation

### Visualization

- **visualization.py** - Publication-quality figure generation
- **plots.py** - Specific plot type implementations

## Testing

### Test Structure

```python
"""Tests for src/module_name.py"""
import pytest
from module_name import function_to_test

class TestFunctionName:
    """Test suite for function_to_test."""
    
    def test_basic_functionality(self):
        """Test basic usage."""
        result = function_to_test(test_data)
        assert result is not None
    
    def test_edge_cases(self):
        """Test edge case handling."""
        assert function_to_test(empty_data) is None
    
    def test_error_handling(self):
        """Test error conditions."""
        with pytest.raises(ValueError):
            function_to_test(invalid_data)
```

### Running Tests

```bash
# All tests with coverage
pytest tests/ --cov=src --cov-fail-under=100

# Specific test file
pytest tests/test_module_name.py -v

# Specific test class/function
pytest tests/test_module_name.py::TestClass::test_function -v

# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

## Best Practices

### Code Quality

✅ **Do:**
- Write clear, documented code
- Use type hints
- Test everything thoroughly
- Document algorithms
- Handle errors gracefully

❌ **Don't:**
- Skip tests or coverage
- Use mocks (test real behavior)
- Leave undocumented code
- Hardcode values
- Ignore edge cases

### Testing

✅ **Do:**
- Write tests first (TDD)
- Test real data
- Cover edge cases
- Test error handling
- Maintain coverage requirements

❌ **Don't:**
- Use mocks
- Skip error tests
- Leave untested code
- Test implementation details
- Accept low coverage

### Scripts

✅ **Do:**
- Import from src/
- Orchestrate workflows
- Generate figures/tables
- Handle I/O
- Provide clear output

❌ **Don't:**
- Implement algorithms in scripts
- Duplicate src/ logic
- Skip error handling
- Hardcode paths
- Mix computation and orchestration

## Deployment

### Standalone Project

Copy this folder to use independently:

```bash
cp -r /path/to/template/project /path/to/my_research
cd /path/to/my_research
pytest tests/ --cov=src
python3 scripts/analysis_pipeline.py
```

The project works completely independently - no template infrastructure needed.

### Integration with Template

To build the manuscript with template infrastructure:

```bash
cd /path/to/template
python3 scripts/03_render_pdf.py
```

Or use the full pipeline:
```bash
python3 scripts/run_all.py
```

This uses the template's build system while your project code remains in `project/`.

## Documentation

- This file (AGENTS.md) - Architecture and guidelines
- README.md - Quick start and overview
- docs/ - Additional documentation
- Docstrings - In-code documentation

## See Also

- Root AGENTS.md - Template architecture
- Root README.md - Template overview
- scripts/ - Build pipeline orchestrators
- infrastructure/ - Generic validation tools






