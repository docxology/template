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

### Running the Analysis

```python
# From project root
python3 scripts/optimization_analysis.py
```

This script:
1. Runs optimization experiments with different step sizes (with progress tracking)
2. Generates convergence plots and analysis visualizations
3. Saves numerical results to CSV and analysis data
4. Performs numerical stability assessment and performance benchmarking
5. Creates HTML dashboard with analysis metrics
6. Registers figures with the manuscript system
7. Generates publishing materials and citations
8. Tracks performance metrics and resource usage
9. Provides error handling with recovery suggestions

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

#### Scientific Analysis Functions

##### run_stability_analysis (function)
```python
def run_stability_analysis() -> Optional[str]:
    """Assess numerical stability of optimization algorithms.

    Returns:
        Path to stability analysis JSON report, or None if analysis fails
    """
```

##### run_performance_benchmarking (function)
```python
def run_performance_benchmarking() -> Optional[str]:
    """Benchmark gradient descent performance across different inputs.

    Returns:
        Path to performance benchmark JSON report, or None if benchmarking fails
    """
```

##### generate_stability_visualization (function)
```python
def generate_stability_visualization(stability_path: Optional[str]) -> Optional[str]:
    """Generate visualization of stability analysis results.

    Args:
        stability_path: Path to stability analysis JSON report

    Returns:
        Path to generated stability visualization PNG, or None if generation fails
    """
```

##### generate_benchmark_visualization (function)
```python
def generate_benchmark_visualization(benchmark_path: Optional[str]) -> Optional[str]:
    """Generate visualization of benchmark results.

    Args:
        benchmark_path: Path to performance benchmark JSON report

    Returns:
        Path to generated benchmark visualization PNG, or None if generation fails
    """
```

##### generate_analysis_dashboard (function)
```python
def generate_analysis_dashboard(
    results: Dict[str, Any],
    stability_path: Optional[str] = None,
    benchmark_path: Optional[str] = None
) -> Optional[str]:
    """Generate analysis dashboard.

    Args:
        results: Optimization results dictionary
        stability_path: Path to stability analysis report
        benchmark_path: Path to performance benchmark report

    Returns:
        Path to generated HTML dashboard, or None if generation fails
    """
```

#### main (function)
```python
def main() -> None:
    """Main analysis function.

    Executes analysis pipeline:
    1. Run convergence experiments with progress tracking
    2. Generate convergence and analysis plots
    3. Save numerical results and analysis data
    4. Run scientific stability and performance analysis
    5. Generate dashboard
    6. Register figures for manuscript reference
    """
```

## Infrastructure Integration

### Performance Monitoring

The script uses infrastructure-backed performance monitoring:

```python
from infrastructure.core import monitor_performance

with monitor_performance("Optimization analysis pipeline") as monitor:
    # Main analysis execution
    results = run_analysis()

# Performance metrics are automatically logged
performance_metrics = monitor.stop()
```

### Error Handling Patterns

error handling with recovery suggestions:

```python
try:
    # Main execution
    main_analysis()
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

### Progress Tracking

Visual progress indicators for long-running operations:

```python
from infrastructure.core import ProgressBar

# Progress tracking for experiments
with ProgressBar(total=4, desc="Step sizes") as progress:
    for step_size in [0.01, 0.05, 0.1, 0.2]:
        result = run_single_experiment(step_size)
        progress.update(1)
```

### Publishing Integration

Automated citation generation and metadata extraction:

```python
# Extract metadata from optimization results
metadata = extract_optimization_metadata(results)

# Generate citations in multiple formats
citations = generate_citations_from_metadata(metadata)

# Citations are saved to output/citations/ directory
```

### Structured Logging

Infrastructure-backed logging with operation timing:

```python
from infrastructure.core.logging_utils import log_operation, log_success

with log_operation("Running convergence experiments", logger=logger):
    results = run_convergence_experiment()

log_success("Analysis completed successfully!", logger=logger)
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