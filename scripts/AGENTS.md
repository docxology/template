# scripts/ - Thin Orchestrators

## Purpose

The `scripts/` directory contains **thin orchestrators** that demonstrate proper integration with `src/` modules. Scripts import and use tested methods from `src/` - they never implement business logic themselves.

## Thin Orchestrator Pattern

### Core Principle
**All business logic lives in `src/`, scripts handle orchestration only.**

```
┌─────────────┐
│   src/      │ ← Business logic (100% tested)
│   example.py│
└──────┬──────┘
       │ import
       ↓
┌──────────────────┐
│   scripts/       │ ← Orchestration only
│   example_figure.py │
└──────────────────┘
       │ generates
       ↓
┌──────────────────┐
│   output/        │ ← Figures and data
│   figures/       │
└──────────────────┘
```

### What Scripts Do
✅ **Import** methods from `src/` modules  
✅ **Orchestrate** data flow and execution  
✅ **Generate** visualizations and outputs  
✅ **Handle** file I/O and directory management  
✅ **Provide** clear error messages  
✅ **Demonstrate** integration patterns  

### What Scripts Don't Do
❌ **Implement** mathematical algorithms (use `src/`)  
❌ **Duplicate** business logic (import from `src/`)  
❌ **Contain** complex computations (delegate to `src/`)  
❌ **Define** new data structures (extend `src/`)  

## Current Scripts

### example_figure.py
**Purpose**: Basic integration example demonstrating simple `src/` usage

**src/ Methods Used**:
- `add_numbers()` - Basic arithmetic
- `multiply_numbers()` - Scaling operations  
- `calculate_average()` - Statistical analysis
- `find_maximum()` - Data analysis
- `find_minimum()` - Data analysis

**What It Generates**:
- `output/figures/example_figure.png` - Two-panel visualization
- `output/data/example_data.csv` - Processed data
- `output/data/example_data.npz` - NumPy array data

**Key Pattern**: Shows how to import multiple functions from one module and compose them.

### generate_research_figures.py
**Purpose**: Advanced integration example showing complex figure generation

**src/ Methods Used**:
- `add_numbers()` - Data validation
- `multiply_numbers()` - Data processing
- `calculate_average()` - Statistical analysis
- `is_even()`, `is_odd()` - Validation logic

**What It Generates**:
- `output/figures/convergence_plot.png` - Convergence analysis
- `output/figures/experimental_setup.png` - Setup diagram
- `output/figures/data_structure.png` - Data visualization
- `output/figures/scalability_analysis.png` - Performance plots
- `output/figures/ablation_study.png` - Component analysis
- `output/figures/hyperparameter_sensitivity.png` - Parameter study
- `output/figures/step_size_analysis.png` - Step size impact
- `output/figures/image_classification_results.png` - Classification results
- `output/figures/recommendation_scalability.png` - Scalability metrics
- `output/data/convergence_data.npz` - Convergence data
- `output/data/performance_comparison.csv` - Performance metrics
- `output/data/dataset_summary.csv` - Dataset statistics

**Key Pattern**: Shows how to generate multiple related figures using the same `src/` methods.

## Script Structure

### Standard Template

```python
#!/usr/bin/env python3
"""Script description.

This script demonstrates [functionality] using src/ modules.
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
        from example import add_numbers, calculate_average
        print("✅ Successfully imported from src/")
    except ImportError as e:
        print(f"❌ Failed to import from src/: {e}")
        return
    
    # Use src/ methods for computation
    data = [1, 2, 3, 4, 5]
    avg = calculate_average(data)  # From src/
    
    # Script handles visualization and output
    fig, ax = plt.subplots()
    ax.plot(data)
    ax.set_title(f"Average: {avg}")
    
    # Save outputs
    output_dir = os.path.join(os.path.dirname(__file__), "..", "output", "figures")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "my_figure.png")
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    
    # Print path for render system
    print(output_path)


if __name__ == "__main__":
    main()
```

## Import Pattern

### Step 1: Add src/ to Path
```python
def _ensure_src_on_path() -> None:
    """Ensure src/ is on Python path."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src_path = os.path.join(repo_root, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

_ensure_src_on_path()
```

### Step 2: Import with Error Handling
```python
try:
    from example import add_numbers, calculate_average
    from quality_checker import analyze_document_quality
    print("✅ Successfully imported from src/")
except ImportError as e:
    print(f"❌ Failed to import from src/: {e}")
    print("   Ensure src/ modules exist and are importable")
    return
```

### Step 3: Use Imported Methods
```python
# Instead of implementing:
# result = sum(data) / len(data)  # ❌ Don't do this

# Use src/ methods:
result = calculate_average(data)  # ✅ Do this
```

## Integration Examples

### Data Processing
```python
# ❌ BAD: Implementing logic in script
def process_data(values):
    total = 0
    for v in values:
        total += v * 2
    return total / len(values)

# ✅ GOOD: Using src/ methods
from example import multiply_numbers, calculate_average

def process_data(values):
    scaled = [multiply_numbers(v, 2) for v in values]
    return calculate_average(scaled)
```

### Statistical Analysis
```python
# ❌ BAD: Implementing statistics
avg = sum(data) / len(data)
maximum = max(data)

# ✅ GOOD: Using src/ methods
from example import calculate_average, find_maximum

avg = calculate_average(data)
maximum = find_maximum(data)
```

### Validation
```python
# ❌ BAD: Implementing validation
is_valid = len(data) % 2 == 0

# ✅ GOOD: Using src/ methods
from example import is_even

is_valid = is_even(len(data))
```

## Testing Scripts

Scripts are tested through:
1. **Unit tests** in `tests/test_example_figure.py` and `tests/test_generate_research_figures.py`
2. **Integration tests** in `tests/test_integration_pipeline.py`
3. **Execution tests** during `render_pdf.sh`

### Test Structure
```python
"""Tests for scripts/example_figure.py"""
import pytest
from unittest.mock import patch, MagicMock

def test_script_imports_src_modules():
    """Test that script properly imports from src/."""
    # Mock src/ imports
    with patch('example_figure.add_numbers') as mock_add:
        mock_add.return_value = 5
        # Run script
        # Verify src/ methods were called
```

## Error Handling

### Import Errors
```python
try:
    from example import add_numbers
except ImportError as e:
    print(f"❌ Failed to import from src/: {e}")
    print("   1. Ensure src/example.py exists")
    print("   2. Verify src/ is on Python path")
    print("   3. Check for syntax errors in src/")
    return
```

### Computation Errors
```python
try:
    result = calculate_average(data)
except ValueError as e:
    print(f"❌ Calculation failed: {e}")
    print(f"   Data: {data}")
    return
```

### File I/O Errors
```python
try:
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
except OSError as e:
    print(f"❌ Failed to save figure: {e}")
    print(f"   Path: {output_path}")
    return
```

## Adding New Scripts

### Checklist
- [ ] Script imports from `src/` modules
- [ ] Uses `src/` methods for all computation
- [ ] Handles only I/O, visualization, orchestration
- [ ] Includes `_ensure_src_on_path()` function
- [ ] Has error handling for imports
- [ ] Sets `MPLBACKEND=Agg` for headless operation
- [ ] Prints output paths to stdout
- [ ] Saves to appropriate `output/` subdirectories
- [ ] Has corresponding test file
- [ ] Documented with clear docstring

### Development Process
1. **Identify needed functionality** - what does script need to do?
2. **Check if src/ has it** - look in `src/` modules
3. **If missing, add to src/ first** - implement and test in `src/`
4. **Create script** - import and use `src/` methods
5. **Test script** - add tests in `tests/`
6. **Integrate** - ensure `render_pdf.sh` runs it

## Integration with Build System

### Automatic Execution
`render_pdf.sh` automatically:
1. Runs all tests (validates `src/` works)
2. Executes all `*.py` files in `scripts/`
3. Captures output paths
4. Validates generated files exist
5. Fails build if any script fails

### Output Structure
```
output/
├── figures/     # PNG files from scripts
│   ├── example_figure.png
│   ├── convergence_plot.png
│   └── ...
├── data/        # CSV, NPZ files from scripts
│   ├── example_data.csv
│   ├── convergence_data.npz
│   └── ...
├── pdf/         # Generated PDFs (from manuscript/)
└── tex/         # LaTeX sources (from manuscript/)
```

## Best Practices

### Do's
✅ Import extensively from `src/` modules  
✅ Use descriptive variable names  
✅ Handle errors gracefully  
✅ Print clear progress messages  
✅ Save outputs to correct directories  
✅ Use type hints  
✅ Document what src/ methods are used  

### Don'ts
❌ Implement algorithms (add to `src/` instead)  
❌ Duplicate logic from `src/`  
❌ Skip error handling  
❌ Use relative imports from script to script  
❌ Hardcode paths  
❌ Mix computation and visualization logic  

## See Also

- [`README.md`](README.md) - Scripts overview and quick start
- [`../src/AGENTS.md`](../src/AGENTS.md) - Available src/ modules
- [`../tests/AGENTS.md`](../tests/AGENTS.md) - Testing scripts
- [`../docs/THIN_ORCHESTRATOR_SUMMARY.md`](../docs/THIN_ORCHESTRATOR_SUMMARY.md) - Pattern details
- [`../AGENTS.md`](../AGENTS.md) - Complete system documentation




