# Code Development Prompt

## Purpose

Develop standards-compliant code for the Research Project Template, ensuring full compliance with all development standards and architecture patterns.

## Context

This prompt leverages development standards to create production-ready code:

- [`../../.cursorrules/`](../../.cursorrules/) directory - All development standards
- [`../core/workflow.md`](../core/workflow.md) - Development workflow
- [`../../.cursorrules/testing_standards.md`](../../.cursorrules/testing_standards.md) - Standards compliance
- [`../core/architecture.md`](../core/architecture.md) - Architecture principles

## Prompt Template

```
You are developing code for the Research Project Template. All code must follow the development standards and architecture patterns. Choose the appropriate layer and implement according to the thin orchestrator pattern.

CODE TASK: [Describe the specific code to implement - algorithm, utility, analysis method, etc.]

LAYER: [Specify: "infrastructure" for generic/reusable code OR "project" for domain-specific code]

IMPLEMENTATION REQUIREMENTS:

## 1. Architecture Compliance

### Layer Selection and Placement
- **Infrastructure Layer**: Generic, reusable utilities in `infrastructure/`
  - Domain-independent functionality
  - Reusable across research projects
  - 60% minimum test coverage
  - Stable, version-controlled APIs

- **Project Layer**: Domain-specific code in `projects/{name}/src/`
  - Research algorithms and analysis
  - Project-specific functionality
  - 90% minimum test coverage
  - Custom research implementations

### Thin Orchestrator Pattern
- **Business Logic**: All computational logic in modules (`src/` or `infrastructure/`)
- **Orchestration**: Thin coordination layer in scripts (`scripts/`)
- **Separation**: Clear distinction between computation and I/O

## 2. Code Standards Implementation

### Type Hints ([`../../.cursorrules/type_hints_standards.md`](../../.cursorrules/type_hints_standards.md))
```python
from typing import List, Dict, Optional, Any, Union
from pathlib import Path

def process_data(
    data: List[Dict[str, Any]],
    output_path: Path,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Process research data with full type annotations.

    Args:
        data: Input data to process
        output_path: Path for output files
        config: Optional configuration dictionary

    Returns:
        Processing results dictionary

    Raises:
        ValueError: If data validation fails
        FileNotFoundError: If output path is invalid
    """
```

### Error Handling ([`../../.cursorrules/error_handling.md`](../../.cursorrules/error_handling.md))
```python
from infrastructure.core.exceptions import TemplateError, ValidationError

class ResearchAlgorithmError(TemplateError):
    """Custom exception for research algorithm failures."""
    pass

def validate_algorithm_input(data: Any) -> None:
    """Validate algorithm input data.

    Args:
        data: Input data to validate

    Raises:
        ResearchAlgorithmError: If validation fails
    """
    if not data:
        raise ResearchAlgorithmError("Input data cannot be empty")

    try:
        # Validation logic
        if not isinstance(data, (list, np.ndarray)):
            raise ResearchAlgorithmError("Data must be list or numpy array")
    except Exception as e:
        raise ResearchAlgorithmError(f"Validation failed: {e}") from e
```

### Logging ([`../../.cursorrules/python_logging.md`](../../.cursorrules/python_logging.md))
```python
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

def research_algorithm(data: List[float]) -> Dict[str, Any]:
    """Execute research algorithm with logging.

    Args:
        data: Input data for algorithm

    Returns:
        Algorithm results dictionary
    """
    logger.info(f"Starting algorithm with {len(data)} data points")

    try:
        # Algorithm implementation
        result = perform_algorithm(data)
        logger.info(f"Algorithm completed successfully: {result}")

        return result

    except Exception as e:
        logger.error(f"Algorithm failed: {e}")
        raise ResearchAlgorithmError(f"Algorithm execution failed: {e}") from e
```

### Code Style ([`../../.cursorrules/code_style.md`](../../.cursorrules/code_style.md))
- **Formatting**: Black code formatter (line length 88)
- **Imports**: isort with section separation
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Structure**: Clear function/method organization

### API Design ([`../../.cursorrules/api_design.md`](../../.cursorrules/api_design.md))
```python
def analyze_dataset(
    dataset_path: Path,
    *,
    method: str = "default",
    parameters: Optional[Dict[str, Any]] = None,
    validate_input: bool = True
) -> AnalysisResult:
    """Analyze research dataset with configurable parameters.

    Args:
        dataset_path: Path to dataset file
        method: Analysis method to use
        parameters: Optional method-specific parameters
        validate_input: Whether to validate input data

    Returns:
        Analysis results object
    """
```

## 3. Documentation Requirements

### Docstrings ([`../../.cursorrules/documentation_standards.md`](../../.cursorrules/documentation_standards.md))
- **Google Style**: with Args, Returns, Raises sections
- **Examples**: Include runnable code examples
- **Comprehensive**: Cover all parameters, return values, exceptions

### Module Documentation
```python
"""Research algorithm implementations.

This module provides optimized implementations of research algorithms
for data analysis and processing. All algorithms include validation, error handling, and performance monitoring.

Example:
    >>> from research_algorithms import optimize_parameters
    >>> result = optimize_parameters(data, method="gradient_descent")
    >>> print(f"Optimal parameters: {result.parameters}")
"""

__version__ = "1.0.0"
__author__ = "Research Team"
```

## 4. Testing Integration

### Test Structure ([`../../.cursorrules/testing_standards.md`](../../.cursorrules/testing_standards.md))
- **No Mocks Policy**: data testing only
- **Coverage Requirements**: 90% (project) or 60% (infrastructure)
- **Test Organization**: Clear class/method structure
- **Data**: Use actual datasets, not synthetic mocks

### Test Implementation
```python
import pytest
from pathlib import Path
import numpy as np

from research_algorithms import optimize_parameters, ResearchAlgorithmError

class TestParameterOptimization:
    """Test suite for parameter optimization algorithms."""

    def test_basic_optimization(self):
        """Test basic parameter optimization functionality."""
        # Use test data
        test_data = np.random.randn(100, 5)
        target = np.random.randn(100)

        result = optimize_parameters(test_data, target)

        assert result is not None
        assert hasattr(result, 'parameters')
        assert len(result.parameters) > 0

    def test_error_handling(self):
        """Test error handling for invalid inputs."""
        with pytest.raises(ResearchAlgorithmError):
            optimize_parameters([], [])

    @pytest.mark.parametrize("method", ["gradient_descent", "newton", "adam"])
    def test_optimization_methods(self, method):
        """Test different optimization methods."""
        test_data = np.random.randn(50, 3)
        target = np.random.randn(50)

        result = optimize_parameters(test_data, target, method=method)

        assert result.converged
        assert result.final_loss < result.initial_loss
```

## 5. Module Organization

### Infrastructure Module Structure
```
infrastructure/research_algorithms/
├── __init__.py          # Public API exports
├── core.py             # Core algorithm implementations
├── validation.py       # Input validation functions
├── exceptions.py       # Custom exceptions
├── AGENTS.md           # Technical documentation
├── README.md           # Quick reference
└── tests/
    ├── __init__.py
    ├── test_core.py
    └── test_validation.py
```

### Project Module Structure
```
projects/research/src/
├── algorithms.py       # Research algorithms
├── data_processing.py  # Data preprocessing
├── analysis.py         # Analysis methods
├── validation.py       # Result validation
├── visualization.py    # Plotting functions
├── AGENTS.md          # Technical documentation
├── README.md          # Quick reference
└── tests/
    ├── test_algorithms.py
    ├── test_data_processing.py
    └── test_analysis.py
```

## 6. Quality Assurance

### Validation Checks
- **Type Checking**: mypy validation passes
- **Linting**: flake8/black compliance
- **Import Sorting**: isort validation
- **Test Coverage**: pytest-cov meets requirements
- **Documentation**: All public APIs documented

### Performance Considerations
- **Efficiency**: Algorithms optimized for performance
- **Memory Usage**: Memory-efficient implementations
- **Scalability**: Handles varying data sizes appropriately
- **Monitoring**: Performance logging and metrics

## Key Requirements

- [ ] Correct layer placement (infrastructure vs project)
- [ ] Thin orchestrator pattern compliance
- [ ] Type hints on all public APIs
- [ ] error handling with custom exceptions
- [ ] Unified logging system integration
- [ ] Black formatting and isort compliance
- [ ] Google-style docstrings with examples
- [ ] No mocks testing with data
- [ ] Coverage requirements met (90% project, 60% infrastructure)
- [ ] AGENTS.md and README.md documentation
- [ ] Architecture pattern validation

## Standards Compliance Checklist

### Code Quality Standards
- [ ] Type hints on all public APIs ([`../../.cursorrules/type_hints_standards.md`](../../.cursorrules/type_hints_standards.md))
- [ ] Error handling with custom exceptions ([`../../.cursorrules/error_handling.md`](../../.cursorrules/error_handling.md))
- [ ] Logging using unified system ([`../../.cursorrules/python_logging.md`](../../.cursorrules/python_logging.md))
- [ ] Code style compliance ([`../../.cursorrules/code_style.md`](../../.cursorrules/code_style.md))
- [ ] API design consistency ([`../../.cursorrules/api_design.md`](../../.cursorrules/api_design.md))

### Testing Standards
- [ ] No mocks policy (data only) ([`../../.cursorrules/testing_standards.md`](../../.cursorrules/testing_standards.md))
- [ ] Coverage requirements met ([`../../.cursorrules/testing_standards.md`](../../.cursorrules/testing_standards.md))
- [ ] Test organization and structure ([`../../.cursorrules/testing_standards.md`](../../.cursorrules/testing_standards.md))

### Documentation Standards
- [ ] AGENTS.md with technical documentation ([`../../.cursorrules/documentation_standards.md`](../../.cursorrules/documentation_standards.md))
- [ ] README.md with Mermaid diagrams ([`../../.cursorrules/documentation_standards.md`](../../.cursorrules/documentation_standards.md))
- [ ] Cross-references between documents ([`../../.cursorrules/documentation_standards.md`](../../.cursorrules/documentation_standards.md))

### Architecture Standards
- [ ] Two-layer architecture compliance ([`../../docs/core/architecture.md`](../../docs/core/architecture.md))
- [ ] Thin orchestrator pattern ([`../../docs/core/architecture.md`](../../docs/core/architecture.md))
- [ ] Module organization correctness ([`../../docs/core/architecture.md`](../../docs/core/architecture.md))

## Example Usage

**Input:**
```
CODE TASK: Implement a gradient descent optimization algorithm for machine learning parameter tuning
LAYER: project
```

**Expected Output:**
- `src/optimization.py` module with gradient descent implementation
- type hints and error handling
- Full test suite in `tests/test_optimization.py` (90% coverage)
- AGENTS.md and README.md documentation
- Integration with logging and validation systems

## Related Documentation

- [`../../.cursorrules/README.md`](../../.cursorrules/README.md) - development standards overview
- [`../core/workflow.md`](../core/workflow.md) - Development workflow guide
- [`../../.cursorrules/testing_standards.md`](../../.cursorrules/testing_standards.md) - Standards compliance
- [`../core/architecture.md`](../core/architecture.md) - Architecture principles
```
