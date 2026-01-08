# Project Source Code

Research-specific algorithms, data generation, and analysis functions. This directory contains the core computational logic for your research project.

## Overview

The `project/src/` directory holds **project-specific code** that implements your research methodology. Unlike the generic `infrastructure/` modules, this code is customized for your particular research domain and questions.

## Directory Structure

```
project/src/
├── __init__.py          # Package initialization
├── example.py           # Example research functions
├── data_generator.py    # Data generation utilities
├── [analysis].py        # Your analysis functions
├── [models].py          # Your model implementations
└── [utils].py           # Project-specific utilities
```

## Key Principles

### Data Analysis
- **No mock methods** - all functions use computations
- **Deterministic outputs** - reproducible results with fixed seeds
- **Scientific accuracy** - mathematically correct implementations

### Modular Design
- **Single responsibility** - each function has one clear purpose
- **Clear interfaces** - well-documented input/output specifications
- **Testable units** - functions designed for testing

### Research Reproducibility
- **Version control** - all code committed to git
- **Documentation** - clear explanations of algorithms and assumptions
- **Parameter exposure** - configurable parameters with sensible defaults

## Usage in Scripts

Project source code is imported by analysis scripts:

```python
# In project/scripts/analysis_pipeline.py
from project.src.data_generator import generate_research_data
from project.src.analysis import run_optimization_study
from project.src.figures import create_result_plots

# Generate data
data = generate_research_data(n_samples=1000, seed=42)

# Run analysis
results = run_optimization_study(data)

# Create visualizations
figures = create_result_plots(results)
```

## Testing Requirements

Project source code must maintain **90% test coverage** (currently 100%):

```bash
# Test project source code
pytest project/tests/ --cov=project.src --cov-report=term-missing --cov-fail-under=90

# Run specific module tests
pytest project/tests/test_data_generator.py -v
```

## Adding New Research Code

### 1. Create Module
```python
# project/src/my_analysis.py
"""Research analysis functions for [specific methodology]."""

import numpy as np
from typing import Dict, List, Any


def analyze_results(data: Dict[str, Any], parameters: Dict[str, float]) -> Dict[str, Any]:
    """Analyze research results using [methodology].

    Args:
        data: Research data dictionary
        parameters: Analysis parameters

    Returns:
        Analysis results dictionary
    """
    # Implementation here
    pass
```

### 2. Add Tests
```python
# project/tests/test_my_analysis.py
"""Tests for my_analysis module."""

import pytest
import numpy as np
from project.src.my_analysis import analyze_results


class TestAnalyzeResults:
    """Test analysis functionality."""

    def test_basic_analysis(self):
        """Test basic analysis with valid data."""
        data = {"values": np.random.rand(100)}
        params = {"threshold": 0.5}

        result = analyze_results(data, params)

        assert "summary" in result
        assert isinstance(result["summary"], dict)

    def test_edge_cases(self):
        """Test analysis with edge case inputs."""
        # Test with minimal data, empty data, etc.
        pass
```

### 3. Update Scripts
```python
# project/scripts/run_analysis.py
from project.src.my_analysis import analyze_results

def main():
    """Run analysis pipeline."""
    data = load_data()
    params = get_parameters()

    results = analyze_results(data, params)
    save_results(results)
```

## Example Modules

### Data Generation
```python
# data_generator.py
def generate_research_data(n_samples: int = 100, seed: int = 42) -> Dict[str, np.ndarray]:
    """Generate synthetic research data.

    Creates realistic data for testing research hypotheses with
    known statistical properties for validation.
    """
    np.random.seed(seed)

    return {
        'independent_vars': np.random.normal(0, 1, n_samples),
        'dependent_vars': np.random.normal(0, 1, n_samples),
        'covariates': np.random.rand(n_samples, 3)
    }
```

### Analysis Functions
```python
# analysis.py
def perform_statistical_test(data: Dict[str, np.ndarray],
                           test_type: str = 't-test') -> Dict[str, float]:
    """Perform statistical analysis on research data.

    Args:
        data: Data dictionary with required fields
        test_type: Type of statistical test to perform

    Returns:
        Test results with p-values, effect sizes, etc.
    """
    # Implementation with real statistical computations
    pass
```

## Quality Standards

### Code Quality
- **Type hints** on all public functions
- **Docstrings** following Google/Numpy style
- **Clear variable names** (no abbreviations)
- **Error handling** with informative messages

### Scientific Rigor
- **Mathematical correctness** - verified algorithms
- **Statistical validity** - appropriate test selection
- **Assumption checking** - validation of statistical assumptions
- **Result interpretation** - clear explanation of findings

### Performance
- **Efficient algorithms** - appropriate complexity for data size
- **Memory management** - avoid unnecessary memory usage
- **Scalability** - functions work with varying data sizes

## Integration with Infrastructure

Project code integrates with infrastructure modules:

```python
from infrastructure.rendering import create_figure
from infrastructure.validation import validate_data
from project.src.analysis import run_experiment

# Validate input data
validate_data(data)

# Run analysis
results = run_experiment(data)

# Create publication-ready figures
figure = create_figure(results, "publication_quality")
```

## Testing Strategy

### Unit Tests
- Test individual functions with controlled inputs
- Verify mathematical correctness
- Check edge cases and error conditions

### Integration Tests
- Test function combinations
- Validate data flow between modules
- Check performance with realistic data sizes

### Property-Based Testing
- Test mathematical properties (e.g., conservation laws)
- Verify statistical properties of generated data
- Check invariance under transformations

## See Also

- [AGENTS.md](AGENTS.md) - Technical documentation
- [../tests/](../tests/) - Test suite
- [../scripts/](../scripts/) - Analysis scripts
- [../../../infrastructure/](../../../infrastructure/) - Reusable infrastructure