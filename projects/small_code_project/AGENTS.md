# Small Code Project

## Overview

A minimal research project demonstrating optimization algorithms and data analysis. This project showcases the template's capability to handle computational research with automated figure generation and reproducible results.

## Key Concepts

- **Optimization Algorithms**: Mathematical optimization techniques for parameter tuning
- **Data Analysis**: Statistical analysis and visualization of optimization results
- **Reproducible Research**: Fixed seeds and deterministic algorithms
- **Automated Reporting**: Script-driven figure generation and analysis

## Directory Structure

```
projects/small_code_project/
├── src/                    # Core algorithms and data processing
│   ├── __init__.py
│   ├── optimizer.py        # Optimization algorithms
│   ├── AGENTS.md          # Technical documentation
│   └── README.md          # Quick reference
├── scripts/                # Analysis workflows
│   ├── optimization_analysis.py  # Main analysis script
│   ├── AGENTS.md          # Script documentation
│   └── README.md          # Quick reference
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_optimizer.py   # Unit tests
│   ├── AGENTS.md          # Test documentation
│   └── README.md          # Quick reference
├── manuscript/             # Research content
│   ├── 01_introduction.md
│   ├── 02_methodology.md
│   ├── 03_results.md
│   ├── 04_conclusion.md
│   └── references.bib
└── pyproject.toml          # Project configuration
```

## Installation/Setup

This project follows the template's standard structure and uses the root-level `pyproject.toml` for dependencies.

## Usage Examples

### Basic Optimization

```python
from src.optimizer import Optimizer

# Create optimizer with default parameters
opt = Optimizer()

# Run optimization
result = opt.optimize(quadratic_function, bounds=[-5, 5])
print(f"Optimal value: {result['x']}, Function value: {result['fun']}")
```

### Analysis Pipeline

```python
from scripts.optimization_analysis import run_analysis

# Execute complete analysis pipeline
results = run_analysis()
# Generates figures and data in output/ directory
```

## Configuration

The project uses the template's configuration system via `pyproject.toml` and environment variables.

## Testing

```bash
# Run project tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

## API Reference

### optimizer.py

#### Optimizer (class)
```python
class Optimizer:
    """Mathematical optimization algorithms with reproducible results."""

    def __init__(self, method: str = "L-BFGS-B", seed: int = 42):
        """Initialize optimizer.

        Args:
            method: Optimization method to use
            seed: Random seed for reproducibility
        """

    def optimize(self, func: Callable, bounds: List[float], x0: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """Run optimization.

        Args:
            func: Objective function to minimize
            bounds: Parameter bounds [min, max]
            x0: Initial guess

        Returns:
            Dictionary with optimization results
        """
```

#### quadratic_function (function)
```python
def quadratic_function(x: np.ndarray) -> float:
    """Simple quadratic test function.

    Args:
        x: Input parameter array

    Returns:
        Function value
    """
```

### optimization_analysis.py

#### run_analysis (function)
```python
def run_analysis() -> Dict[str, Any]:
    """Run complete optimization analysis pipeline.

    Returns:
        Dictionary with analysis results
    """
```

#### generate_figures (function)
```python
def generate_figures(results: Dict[str, Any]) -> List[str]:
    """Generate analysis figures.

    Args:
        results: Analysis results from run_analysis()

    Returns:
        List of generated figure paths
    """
```

## Troubleshooting

### Common Issues

- **Import Errors**: Ensure the project is run from the template root directory
- **Missing Dependencies**: Run `uv sync` to install dependencies
- **Test Failures**: Check that numpy/scipy are properly installed

## Best Practices

- Use fixed seeds for reproducible results
- Validate optimization convergence
- Generate multiple random starts for global optimization
- Document parameter choices in manuscript

## See Also

- [Root AGENTS.md](../../AGENTS.md) - Complete template documentation
- [projects/project/](../project/AGENTS.md) - Full research project example
- [infrastructure/scientific/](../../infrastructure/scientific/AGENTS.md) - Scientific utilities