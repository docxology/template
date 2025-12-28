# scripts/ - Analysis Scripts

## Overview

The `scripts/` directory contains thin orchestrators that demonstrate proper integration with `src/` modules. Scripts import and use tested algorithms from `src/` to perform analysis, generate figures, and export data.

## Key Concepts

- **Thin orchestrator pattern**: Scripts coordinate business logic implemented in `src/`
- **Integration examples**: Demonstrates how to use `src/` modules in research workflows
- **Automated figure generation**: Scripts generate publication-ready figures
- **Data export**: Structured data output for further analysis

## Directory Structure

```
scripts/
├── optimization_analysis.py    # Main analysis pipeline
├── AGENTS.md                  # This technical documentation
└── README.md                  # Quick reference
```

## Installation/Setup

Scripts require the project dependencies:

- `numpy` - Numerical computations
- `matplotlib` - Plotting and visualization
- `infrastructure` - Template utilities (optional, for figure registration)

## Usage Examples

### Running the Complete Analysis

```python
# From project root
python3 scripts/optimization_analysis.py
```

This script:
1. Runs optimization experiments with different step sizes
2. Generates convergence plots
3. Saves numerical results to CSV
4. Registers figures with the manuscript system

### Manual Script Execution

```python
import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Import and run analysis
from optimization_analysis import main
main()
```

## Configuration

Scripts use hardcoded parameters for reproducibility:

- **Step sizes**: `[0.01, 0.05, 0.1, 0.2]` for convergence comparison
- **Initial point**: `[0.0]` for 1D optimization
- **Plot settings**: 300 DPI, tight bounding box
- **Output directories**: `output/figures/`, `output/data/`

## Testing

Scripts are tested through integration tests:

```bash
# Run integration tests
pytest ../tests/integration/ -v

# Test script outputs exist
pytest ../tests/integration/test_generate_research_figures.py
```

## API Reference

### optimization_analysis.py

#### run_convergence_experiment (function)
```python
def run_convergence_experiment() -> Dict[float, OptimizationResult]:
    """Run gradient descent with different step sizes and track convergence.

    Returns:
        Dictionary mapping step sizes to optimization results
    """
```

#### generate_convergence_plot (function)
```python
def generate_convergence_plot(results: Dict[float, OptimizationResult]) -> Path:
    """Generate convergence plot showing objective value vs iteration.

    Args:
        results: Dictionary of step size to optimization result

    Returns:
        Path to generated plot file
    """
```

#### simulate_trajectory (function)
```python
def simulate_trajectory(step_size: float, max_iter: int = 50) -> Dict[str, List]:
    """Simulate gradient descent trajectory to collect intermediate values.

    Args:
        step_size: Step size for gradient descent
        max_iter: Maximum iterations to simulate

    Returns:
        Dictionary with 'iterations' and 'objectives' lists
    """
```

#### save_optimization_results (function)
```python
def save_optimization_results(results: Dict[float, OptimizationResult]) -> Path:
    """Save optimization results to CSV file.

    Args:
        results: Dictionary of step size to optimization result

    Returns:
        Path to saved CSV file
    """
```

#### register_figure (function)
```python
def register_figure() -> None:
    """Register the generated figure for manuscript reference.

    Attempts to import infrastructure.figure_manager and register
    the convergence plot. Gracefully handles missing infrastructure.
    """
```

#### main (function)
```python
def main() -> None:
    """Main analysis function.

    Executes complete analysis pipeline:
    1. Run convergence experiments
    2. Generate convergence plot
    3. Save numerical results
    4. Register figure for manuscript
    """
```

## Troubleshooting

### Common Issues

- **Import errors**: Ensure script is run from project root directory
- **Path issues**: Scripts assume standard project directory structure
- **Missing infrastructure**: Figure registration fails gracefully if infrastructure unavailable

### Debug Tips

Add debug output to scripts:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Best Practices

- **Path handling**: Use `pathlib.Path` for cross-platform compatibility
- **Error handling**: Scripts should handle missing infrastructure gracefully
- **Output validation**: Verify generated files exist and have content
- **Reproducibility**: Use fixed parameters for consistent results

## See Also

- [README.md](README.md) - Quick reference
- [../src/optimizer.py](../src/optimizer.py) - Core algorithms used by scripts
- [../tests/integration/test_generate_research_figures.py](../tests/integration/test_generate_research_figures.py) - Integration tests