# Code Project - Optimization Research Exemplar

**This is an active project** in the `projects/` directory, discovered and executed by infrastructure discovery functions.

## Overview

A research project exemplifying mathematical optimization algorithms with rigorous implementation, extensive testing, and publication-quality analysis. This project demonstrates the template's full capabilities for computational research, including automated figure generation, reproducible results, and professional manuscript production.

## Key Features & Capabilities

### Mathematical Optimization

- **Gradient Descent Implementation**: Full algorithm with convergence analysis
- **Theoretical Convergence Bounds**: Rigorous mathematical analysis of convergence rates
- **Numerical Stability**: Robust implementation with proper error handling
- **Performance Characterization**: Comprehensive benchmarking and timing analysis

### Research Quality Assurance

- **100% Test Coverage**: 34 tests covering edge cases, stability analysis, and performance benchmarks
- **Deterministic Algorithms**: Reproducible results with fixed random seeds
- **Documentation**: Complete type hints, docstrings, and examples
- **Parameter Validation**: Robust input checking and error handling

### Publication-Ready Output

- **Professional Visualizations**: Automated figure generation with proper labeling and styling
- **Manuscript with Cross-References**: LaTeX-rendered PDF with equation numbering and citations
- **Automated Analysis Pipeline**: Script-driven data generation and visualization
- **Executive Reporting**: Multi-project comparative analysis capabilities

### Scientific Validation & Analysis

- **Numerical Stability Assessment**: Automated stability testing across input ranges
- **Performance Benchmarking**: Execution time and memory usage analysis
- **Reporting Dashboard**: Interactive HTML reports with analysis metrics
- **Progress Tracking**: Real-time monitoring with visual progress indicators
- **Performance Monitoring**: Resource usage tracking during analysis

### Infrastructure Integration

- **Advanced Error Handling**: Comprehensive exception handling with recovery suggestions
- **Structured Logging**: Infrastructure-backed logging with operation timing and context
- **Publishing Tools Integration**: Automated citation generation and publication metadata extraction
- **Context Manager Performance Monitoring**: Proper resource usage tracking with detailed metrics
- **Progress Bars**: Visual progress indicators for long-running optimization experiments

## Directory Structure

```
projects/code_project/
├── src/                    # Core algorithms and data processing
│   ├── __init__.py
│   ├── optimizer.py        # Optimization algorithms
│   ├── AGENTS.md          # Technical documentation
│   └── README.md          # Quick reference
├── scripts/                # Analysis workflows
│   ├── optimization_analysis.py  # Main analysis script
│   ├── generate_api_docs.py # API documentation generator
│   ├── AGENTS.md          # Script documentation
│   └── README.md          # Quick reference
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_optimizer.py   # Unit tests
│   ├── AGENTS.md          # Test documentation
│   └── README.md          # Quick reference
├── manuscript/             # Research content
│   ├── 00_abstract.md     # Abstract
│   ├── 01_introduction.md
│   ├── 02_methodology.md
│   ├── 03_results.md
│   ├── 04_conclusion.md
│   ├── config.yaml         # Publication metadata
│   ├── config.yaml.example # Example configuration
│   ├── preamble.md         # LaTeX preamble
│   ├── references.bib      # Bibliography
│   ├── AGENTS.md           # Manuscript documentation
│   └── README.md           # Manuscript quick reference
└── pyproject.toml          # Project configuration
```

## Installation/Setup

This project follows the template's standard structure and uses the root-level `pyproject.toml` for dependencies.

## Usage Examples

### Basic Optimization

```python
from src.optimizer import gradient_descent, quadratic_function, compute_gradient
import numpy as np

# Run gradient descent
result = gradient_descent(
    initial_point=np.array([5.0]),
    objective_func=quadratic_function,
    gradient_func=compute_gradient,
    step_size=0.1,
    tolerance=1e-6
)
print(f"Solution: {result.solution}, Converged: {result.converged}")
print(f"Iterations: {result.iterations}, Final objective: {result.objective_value}")
```

### Analysis Pipeline

```bash
# Execute the full analysis pipeline
python3 scripts/optimization_analysis.py
# Generates figures, data, reports, and dashboard in output/
```

### Scientific Analysis Features

```python
from scripts.optimization_analysis import run_stability_analysis, run_performance_benchmarking

# Assess numerical stability
stability_path = run_stability_analysis()
# Generates stability analysis report and visualization

# Run performance benchmarking
benchmark_path = run_performance_benchmarking()
# Generates performance metrics and comparison plots

# Access dashboard
# Automatically generated at output/reports/analysis_dashboard.html
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

#### OptimizationResult (dataclass)

```python
@dataclass
class OptimizationResult:
    """Container for optimization algorithm results."""
    solution: np.ndarray          # Optimal point found
    objective_value: float        # Function value at solution
    iterations: int               # Number of iterations performed
    converged: bool               # Whether algorithm converged
    gradient_norm: float          # Final gradient norm
    objective_history: Optional[list[float]] = None  # Objective values per iteration
```

#### quadratic_function (function)

```python
def quadratic_function(
    x: np.ndarray,
    A: Optional[np.ndarray] = None,
    b: Optional[np.ndarray] = None
) -> float:
    """Evaluate quadratic objective f(x) = (1/2) x^T A x - b^T x.

    Args:
        x: Input parameter array
        A: Quadratic coefficient matrix (defaults to identity)
        b: Linear term vector (defaults to ones)

    Returns:
        Function value
    """
```

#### compute_gradient (function)

```python
def compute_gradient(
    x: np.ndarray,
    A: Optional[np.ndarray] = None,
    b: Optional[np.ndarray] = None
) -> np.ndarray:
    """Compute analytical gradient ∇f(x) = Ax - b.

    Args:
        x: Input parameter array
        A: Quadratic coefficient matrix (defaults to identity)
        b: Linear term vector (defaults to ones)

    Returns:
        Gradient vector
    """
```

#### gradient_descent (function)

```python
def gradient_descent(
    initial_point: np.ndarray,
    objective_func: Callable[[np.ndarray], float],
    gradient_func: Callable[[np.ndarray], np.ndarray],
    max_iterations: int = 1000,
    tolerance: float = 1e-6,
    step_size: float = 0.01,
    verbose: bool = False,
) -> OptimizationResult:
    """Perform gradient descent optimization with fixed step size.

    Args:
        initial_point: Starting point for optimization
        objective_func: Objective function to minimize
        gradient_func: Gradient function
        max_iterations: Maximum number of iterations
        tolerance: Convergence tolerance on gradient norm
        step_size: Fixed step size (learning rate)
        verbose: Enable verbose logging

    Returns:
        OptimizationResult with solution and diagnostics
    """
```

### optimization_analysis.py

The main analysis script (`scripts/optimization_analysis.py`) is a thin orchestrator that runs the full pipeline via its `main()` function. Key internal functions:

#### Scientific Analysis Functions

##### run_stability_analysis (function)

```python
def run_stability_analysis() -> Optional[str]:
    """Assess numerical stability of optimization algorithms.

    Returns:
        Path to stability analysis JSON report, or None if failed
    """
```

##### run_performance_benchmarking (function)

```python
def run_performance_benchmarking() -> Optional[str]:
    """Benchmark gradient descent performance across different inputs.

    Returns:
        Path to performance benchmark JSON report, or None if failed
    """
```

##### generate_stability_visualization (function)

```python
def generate_stability_visualization(stability_path: Optional[str]) -> Optional[str]:
    """Generate visualization of stability analysis results.

    Args:
        stability_path: Path to stability analysis JSON report

    Returns:
        Path to generated stability visualization, or None if failed
    """
```

##### generate_benchmark_visualization (function)

```python
def generate_benchmark_visualization(benchmark_path: Optional[str]) -> Optional[str]:
    """Generate visualization of benchmark results.

    Args:
        benchmark_path: Path to performance benchmark JSON report

    Returns:
        Path to generated benchmark visualization, or None if failed
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
        Path to generated HTML dashboard, or None if failed
    """
```

## Troubleshooting

### Common Issues

- **Import Errors**: Ensure the project is run from the template root directory
- **Missing Dependencies**: Run `uv sync` to install dependencies
- **Test Failures**: Check that numpy/scipy are properly installed

## .cursorrules Compliance

This project complies with the template's development standards defined in `.cursorrules/`.

### ✅ **Testing Standards Compliance**

- **90%+ coverage**: Achieves 100% test coverage with 34 tests (exceeds 90% requirement)
- **Real data only**: All tests use computations, no mocks
- **Full integration**: Tests cover algorithm convergence, stability analysis, and performance benchmarking
- **Deterministic results**: Fixed seeds ensure reproducible test outcomes
- **Scientific validation**: Includes numerical stability and performance testing

### ✅ **Documentation Standards Compliance**

- **AGENTS.md + README.md**: Complete technical documentation in each directory
- **Type hints**: All public APIs have type annotations
- **Docstrings**: Comprehensive docstrings with examples for all functions
- **Cross-references**: Links between related documentation sections

### ✅ **Type Hints Standards Compliance**

- **Full annotations**: All public functions have type hints
- **Generic types**: Uses `List`, `Dict`, `Optional`, `Callable` appropriately
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

The project uses infrastructure-backed performance monitoring with automatic resource tracking:

```python
# Performance monitoring context manager
from infrastructure.core import monitor_performance

with monitor_performance("Optimization analysis pipeline") as monitor:
    # Run optimization experiments
    results = run_convergence_experiment()

# Access performance metrics
performance_metrics = monitor.stop()
print(f"Duration: {performance_metrics.duration:.2f}s")
print(f"Memory used: {performance_metrics.resource_usage.memory_mb:.1f}MB")
```

**Generated Output:**

```
Performance Summary:
Duration: 2.45s
Memory: 45.2MB
```

### Error Handling

error handling with recovery suggestions:

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
from infrastructure.core.logging_utils import log_operation, log_success

with log_operation("Running convergence experiments", logger=logger):
    results = run_convergence_experiment()

log_success("Analysis completed successfully!", logger=logger)
```

### Publishing Integration

Automated citation generation and metadata extraction:

```python
from scripts.optimization_analysis import extract_optimization_metadata, generate_citations_from_metadata

# Extract metadata from optimization results
metadata = extract_optimization_metadata(results)

# Generate citations
citations = generate_citations_from_metadata(metadata)

# Access different citation formats
print(citations['bibtex'])  # BibTeX format
print(citations['apa'])     # APA format
print(citations['mla'])     # MLA format
```

**Generated Citations:**

```
@misc{optimization_analysis,
  title={Optimization Algorithm Performance Analysis},
  author={Optimization Analysis Pipeline},
  year={2024}
}
```

### Progress Tracking

Visual progress indicators for long-running operations:

```python
from infrastructure.core import ProgressBar

# Progress tracking for step size experiments
with ProgressBar(total=4, desc="Step sizes") as progress:
    for step_size in [0.01, 0.05, 0.1, 0.2]:
        result = run_single_experiment(step_size)
        progress.update(1)  # Update progress
```

**Console Output:**

```
Step sizes: 100%|██████████████████| 4/4 [00:02<00:00, 1.85it/s]
```

## Best Practices

- Use fixed seeds for reproducible results
- Validate optimization convergence
- Generate multiple random starts for global optimization
- Document parameter choices in manuscript

## See Also

- [Root AGENTS.md](../../AGENTS.md) - Template documentation
- [projects/blake_active_inference/](../blake_active_inference/AGENTS.md) - Blake Active Inference manuscript project
- [infrastructure/scientific/](../../infrastructure/scientific/AGENTS.md) - Scientific utilities
