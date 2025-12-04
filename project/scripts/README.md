# Scripts Directory: Thin Orchestrators for src/ Methods

## Overview

The `scripts/` directory contains **thin orchestrators** that demonstrate how to use the fully-tested methods from `@src/` modules. These scripts are **NOT** meant to contain business logic or mathematical implementations - they are lightweight wrappers that:

1. **Import and use** methods from `@src/` modules
2. **Orchestrate** the execution flow
3. **Generate** figures and data outputs
4. **Demonstrate** proper integration patterns

## Key Principles

### 🚫 What Scripts Should NOT Do
- **Implement mathematical algorithms** (use `@src/` instead)
- **Duplicate business logic** (import from `@src/` instead)
- **Contain complex computations** (delegate to `@src/` instead)
- **Define new data structures** (extend `@src/` instead)

### ✅ What Scripts SHOULD Do
- **Import** methods from `@src/` modules
- **Orchestrate** data flow and execution
- **Generate** visualizations and outputs
- **Handle** file I/O and directory management
- **Provide** clear error messages and logging
- **Demonstrate** proper integration patterns

## Script Architecture

### Import Pattern
```python
def _ensure_src_on_path() -> None:
    """Ensure src/ is on Python path for imports."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src_path = os.path.join(repo_root, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

# Import src/ methods
from example import add_numbers, multiply_numbers, calculate_average
```

### Usage Pattern
```python
def generate_figure():
    # Use src/ methods for computation
    data = [1, 2, 3, 4, 5]
    avg = calculate_average(data)  # From src/example.py
    
    # Script handles visualization and output
    fig, ax = plt.subplots()
    ax.plot(data)
    ax.set_title(f"Average: {avg}")
    
    # Save output
    fig.savefig("output.png")
    return "output.png"
```

## Current Scripts

### 1. `example_figure.py` - Basic Integration Example
**Purpose**: Demonstrates basic integration with `@src/` modules
**src/ Usage**: 
- `add_numbers()` - for data processing
- `multiply_numbers()` - for scaling operations
- `calculate_average()` - for statistical analysis
- `find_maximum()` - for data analysis
- `find_minimum()` - for data analysis

**What it does**:
- Imports mathematical functions from `src/example.py`
- Uses these functions to process data
- Generates a two-panel figure showing data processing
- Saves both the figure and processed data

### 2. `generate_research_figures.py` - Advanced Integration Example
**Purpose**: Demonstrates comprehensive integration with `@src/` modules
**src/ Usage**:
- `add_numbers()` - for data validation
- `multiply_numbers()` - for data processing
- `calculate_average()` - for statistical analysis
- `is_even()` - for validation logic
- `is_odd()` - for validation logic

**What it does**:
- Imports multiple functions from `src/example.py`
- Uses these functions to process convergence data
- Generates research-quality figures with statistics
- Demonstrates error handling for missing imports

### 3. `analysis_pipeline.py` - Statistical Analysis Workflow
**Purpose**: Demonstrates complete statistical analysis workflow
**src/ Usage**:
- `generate_classification_dataset()`, `generate_synthetic_data()` - Data generation
- `normalize_data()`, `detect_outliers()`, `clean_data()` - Data processing
- `calculate_accuracy()`, `calculate_precision_recall_f1()`, `calculate_all_metrics()` - Metrics
- `analyze_scalability()`, `benchmark_comparison()` - Performance analysis
- `calculate_descriptive_stats()`, `calculate_correlation()`, `anova_test()` - Statistics
- `ValidationFramework` - Result validation
- `plot_comparison()`, `plot_scatter()`, `plot_bar()` - Visualization
- `FigureManager`, `ReportGenerator` - Figure and report management

**What it does**:
- Demonstrates complete workflow from data generation through analysis to reporting
- Generates statistical comparison plots and analysis reports
- Shows integration of multiple src/ modules in a single workflow

### 4. `scientific_simulation.py` - Simulation Framework
**Purpose**: Demonstrates simulation framework with parameter management
**src/ Usage**:
- `generate_time_series()`, `generate_synthetic_data()` - Data generation
- `ParameterSet`, `ParameterSweep` - Parameter management
- `SimpleSimulation`, `SimulationBase` - Simulation framework
- `analyze_convergence()`, `analyze_scalability()` - Performance analysis
- `calculate_descriptive_stats()` - Statistical analysis
- `ValidationFramework` - Result validation
- `ReportGenerator` - Report generation
- `FigureManager` - Figure management

**What it does**:
- Shows how to set up and run simulations with proper parameter management
- Generates simulation results, state files, and reports
- Demonstrates result tracking and validation

### 5. `generate_scientific_figures.py` - Automated Figure Generation
**Purpose**: Demonstrates automated figure generation with markdown integration
**src/ Usage**:
- `generate_time_series()`, `generate_synthetic_data()` - Data generation
- `FigureManager` - Figure management
- `ImageManager` - Image insertion
- `MarkdownIntegration` - Markdown integration
- `analyze_convergence()` - Performance analysis
- `plot_line()`, `plot_scatter()`, `plot_bar()`, `plot_convergence()`, `plot_comparison()` - Plotting
- `calculate_descriptive_stats()` - Statistical analysis
- `VisualizationEngine` - Visualization engine

**What it does**:
- Generates scientific figures automatically
- Inserts figures into markdown files with captions
- Updates cross-references in manuscript
- Demonstrates automated workflow integration

## Integration Examples

### Data Processing with src/ Methods
```python
# Instead of implementing math in the script:
# y = x * 2 + 1  # ❌ Don't do this

# Use src/ methods:
from example import add_numbers, multiply_numbers
y = add_numbers(multiply_numbers(x, 2), 1)  # ✅ Do this
```

### Statistical Analysis with src/ Methods
```python
# Instead of implementing statistics:
# avg = sum(data) / len(data)  # ❌ Don't do this

# Use src/ methods:
from example import calculate_average
avg = calculate_average(data)  # ✅ Do this
```

### Validation with src/ Methods
```python
# Instead of implementing validation:
# is_valid = len(data) % 2 == 0  # ❌ Don't do this

# Use src/ methods:
from example import is_even
is_valid = is_even(len(data))  # ✅ Do this
```

## Testing Integration

### Why This Pattern Works
1. **Single Source of Truth**: All business logic lives in `@src/`
2. **Fully Tested**: `@src/` methods have 100% test coverage
3. **Reusable**: Scripts can import and use any `@src/` method
4. **Maintainable**: Changes to logic only happen in `@src/`
5. **Testable**: Scripts can be tested by mocking `@src/` imports

### Test Coverage
- **src/ modules**: 100% coverage required
- **scripts/**: Tested through integration tests
- **render_pdf.sh**: Ensures both pass before PDF generation

## Adding New Scripts

### Template
```python
#!/usr/bin/env python3
"""Script description.

This script demonstrates [specific functionality] using src/ modules.
"""
from __future__ import annotations

import os
import sys
import matplotlib.pyplot as plt
import numpy as np

def _ensure_src_on_path() -> None:
    """Ensure src/ is on Python path for imports."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src_path = os.path.join(repo_root, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

def main() -> None:
    """Main script function."""
    # Set matplotlib backend for headless operation
    os.environ.setdefault("MPLBACKEND", "Agg")
    
    # Ensure src/ is on path
    _ensure_src_on_path()
    
    # Import src/ methods
    try:
        from example import relevant_function
        print("✅ Successfully imported from src/")
    except ImportError as e:
        print(f"❌ Failed to import from src/: {e}")
        return
    
    # Use src/ methods for computation
    result = relevant_function(input_data)
    
    # Script handles visualization and output
    # ... visualization code ...
    
    # Save outputs
    # ... save code ...
    
    # Print paths for render system
    print(output_path)

if __name__ == "__main__":
    main()
```

### Checklist
- [ ] Imports methods from `@src/` modules
- [ ] Uses `@src/` methods for all computation
- [ ] Script only handles I/O, visualization, and orchestration
- [ ] Includes proper error handling
- [ ] Prints output paths for render system
- [ ] Sets `MPLBACKEND=Agg` for headless operation
- [ ] Has clear documentation

## Best Practices

### Do's
- ✅ Import and use `@src/` methods extensively
- ✅ Handle file I/O and directory management
- ✅ Provide clear error messages and logging
- ✅ Use type hints and docstrings
- ✅ Follow the established import pattern
- ✅ Test integration with `@src/` modules

### Don'ts
- ❌ Implement mathematical algorithms
- ❌ Duplicate business logic from `@src/`
- ❌ Create complex data processing functions
- ❌ Hardcode mathematical formulas
- ❌ Skip error handling for imports
- ❌ Mix computation and visualization logic

## Integration with Build System

### Automatic Execution
The build pipeline (`python3 scripts/run_all.py` or `./run.sh`) automatically:
1. Runs all tests in `@tests/` (ensuring 100% coverage)
2. Executes all scripts in `@scripts/` (validating src/ integration)
3. Generates figures and data outputs
4. Builds PDFs with integrated figures

### Validation
- **Tests**: Ensure `@src/` methods work correctly
- **Scripts**: Ensure integration with `@src/` works
- **Figures**: Ensure outputs are generated and referenced
- **PDFs**: Ensure final documents include all figures

## Summary

The `scripts/` directory demonstrates the **thin orchestrator pattern** where:

- **`@src/`** contains all business logic, algorithms, and mathematical implementations
- **`@scripts/`** contains lightweight wrappers that use `@src/` methods
- **`@tests/`** ensures 100% coverage of `@src/` functionality
- **Build pipeline** (`python3 scripts/run_all.py` or `./run.sh`) orchestrates the entire pipeline

This architecture ensures:
- **Maintainability**: Single source of truth for business logic
- **Testability**: Fully tested core functionality
- **Reusability**: Scripts can use any `@src/` method
- **Clarity**: Clear separation of concerns
- **Quality**: Automated validation of the entire system

## See Also

- [`AGENTS.md`](AGENTS.md) - Detailed documentation
- [`../../scripts/README.md`](../../scripts/README.md) - Root-level scripts guide
- [`../../docs/THIN_ORCHESTRATOR_SUMMARY.md`](../../docs/THIN_ORCHESTRATOR_SUMMARY.md) - Pattern details
