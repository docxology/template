# 🔧 Intermediate Usage Guide

> **Add figures and automation** to your research project

**Previous**: [Getting Started](../guides/GETTING_STARTED.md) (Levels 1-3) | **Next**: [Advanced Usage](../guides/ADVANCED_USAGE.md) (Levels 7-9)

This guide covers **Levels 4-6** of the Research Project Template. Perfect for users ready to add custom figures, data analysis, and automated workflows.

## 📚 What You'll Learn

By the end of this guide, you'll be able to:

- ✅ Generate figures from data using scripts
- ✅ Understand and apply the thin orchestrator pattern
- ✅ Add new Python modules with proper testing
- ✅ Create data analysis pipelines
- ✅ Automate complete workflows

**Estimated Time:** 1-2 days

## 🎯 Prerequisites

- Completed [Getting Started Guide](../guides/GETTING_STARTED.md)
- Basic Python programming knowledge
- Understanding of matplotlib or similar visualization library
- Text editor configured for Python

## 📖 Table of Contents

- [Level 4: Add Basic Figures](#level-4-add-basic-figures)
- [Level 5: Basic Data Analysis](#level-5-basic-data-analysis)
- [Level 6: Automated Workflows](#level-6-automated-workflows)
- [What to Read Next](#what-to-read-next)

---

## Level 4: Add Basic Figures

**Goal**: Generate figures from data using the thin orchestrator pattern

**Time**: 3-4 hours

### Understanding the Thin Orchestrator Pattern

**Core Principle**: Scripts orchestrate, `project/src/` implements.

```
┌─────────────────┐
│  project/src/   │  ← ALL business logic here
│  example.py     │  ← Mathematical functions
│  analysis.py    │  ← Algorithms
└────────┬────────┘
         │ import
         ↓
┌─────────────────┐
│  project/scripts/│  ← Thin orchestrators
│  my_figure.py   │  ← Visualization only
└─────────────────┘
         │ generate
         ↓
┌─────────────────┐
│  output/        │  ← Generated files
│  figures/       │  ← PNG, PDF files
│  data/          │  ← CSV, NPZ files
└─────────────────┘
```

**Why This Pattern?**
- **Maintainability**: Business logic in one place
- **Testability**: Test logic without visualization
- **Reusability**: Use same logic in multiple scripts
- **Clarity**: Clear separation of concerns

**See [THIN_ORCHESTRATOR_SUMMARY.md](../architecture/THIN_ORCHESTRATOR_SUMMARY.md) for complete details.**

### Using Existing Figure Scripts

The template includes example scripts:

```bash
# Generate basic example figure
python3 project/scripts/example_figure.py

# Generate research-quality figures
python3 scripts/generate_research_figures.py
```

**What they demonstrate**:
- Importing from `project/src/` modules
- Using tested methods for computation
- Handling only visualization and I/O
- Printing output paths for build system

### Anatomy of a Thin Orchestrator Script

```python
#!/usr/bin/env python3
"""Example demonstrating thin orchestrator pattern."""

import os
import matplotlib
matplotlib.use('Agg')  # Headless backend
import matplotlib.pyplot as plt

# IMPORT from project/src/ - never implement algorithms here
from example import calculate_average, find_maximum, find_minimum

def main():
    # Sample data
    data = [1.2, 2.3, 1.8, 3.4, 2.1]
    
    # USE project/src/ methods for computation - NEVER implement here
    avg = calculate_average(data)  # From project/src/example.py
    max_val = find_maximum(data)   # From project/src/example.py
    min_val = find_minimum(data)   # From project/src/example.py
    
    # Script ONLY handles visualization
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(data, marker='o', label='Data')
    ax.axhline(avg, color='r', linestyle='--', label=f'Average: {avg:.2f}')
    ax.axhline(max_val, color='g', linestyle=':', label=f'Max: {max_val:.2f}')
    ax.axhline(min_val, color='b', linestyle=':', label=f'Min: {min_val:.2f}')
    ax.legend()
    ax.set_title('Data Analysis')
    ax.set_xlabel('Index')
    ax.set_ylabel('Value')
    
    # Save output
    output_dir = 'output/figures'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'my_analysis.png')
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    # Print path for build system manifest
    print(output_path)

if __name__ == '__main__':
    main()
```

**Key Points**:
1. ✅ **Import** from `project/src/` - line 8
2. ✅ **Use** tested methods - lines 14-16
3. ✅ **Handle** visualization only - lines 18-28
4. ✅ **Save** to output directory - lines 30-34
5. ✅ **Print** path for manifest - line 37

### Creating Your Own Figure Script

**Step 1: Plan your figure**
- What data will you visualize?
- What computations are needed?
- What type of plot (line, scatter, bar, etc.)?

**Step 2: Ensure business logic exists in `project/src/`**

If computation logic doesn't exist, add it to `project/src/` first:

```python
# project/src/statistics.py
def calculate_variance(values):
    """Calculate sample variance."""
    mean = sum(values) / len(values)
    return sum((x - mean) ** 2 for x in values) / (len(values) - 1)

def calculate_std_dev(values):
    """Calculate standard deviation."""
    return calculate_variance(values) ** 0.5
```

**Step 3: Create tests (comprehensive coverage required)**

```python
# tests/test_statistics.py
from statistics import calculate_variance, calculate_std_dev

def test_calculate_variance():
    values = [1, 2, 3, 4, 5]
    var = calculate_variance(values)
    assert abs(var - 2.5) < 1e-10

def test_calculate_std_dev():
    values = [1, 2, 3, 4, 5]
    std = calculate_std_dev(values)
    assert abs(std - 1.5811388) < 1e-6
```

**Step 4: Run tests**

```bash
pytest tests/test_statistics.py --cov=src.statistics --cov-report=term-missing
```

**Step 5: Create thin orchestrator script**

```python
# scripts/statistics_figure.py
#!/usr/bin/env python3
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from statistics import calculate_std_dev  # Import from src/

def main():
    # Generate sample data
    np.random.seed(42)  # Reproducible
    data = np.random.normal(0, 1, 100)
    
    # Use src/ method for computation
    std = calculate_std_dev(data.tolist())
    
    # Script handles visualization only
    fig, ax = plt.subplots()
    ax.hist(data, bins=20, alpha=0.7, label='Data')
    ax.axvline(std, color='r', linestyle='--', label=f'Std Dev: {std:.2f}')
    ax.axvline(-std, color='r', linestyle='--')
    ax.legend()
    ax.set_title('Distribution with Standard Deviation')
    
    # Save
    output_path = 'output/figures/statistics_figure.png'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    # Print for manifest
    print(output_path)

if __name__ == '__main__':
    main()
```

**Step 6: Run script**

```bash
python3 scripts/statistics_figure.py
```

**Step 7: Add to manuscript**

```markdown
\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{../output/figures/statistics_figure.png}
\caption{Data distribution showing one standard deviation}
\label{fig:statistics}
\end{figure}
```

### Common Figure Types

**Line Plot**:
```python
ax.plot(x_data, y_data, marker='o', label='Series')
```

**Scatter Plot**:
```python
ax.scatter(x_data, y_data, alpha=0.5)
```

**Bar Chart**:
```python
ax.bar(categories, values)
```

**Histogram**:
```python
ax.hist(data, bins=30, alpha=0.7)
```

**Subplots**:
```python
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
ax1.plot(x1, y1)
ax2.plot(x2, y2)
```

**See [matplotlib documentation](https://matplotlib.org/stable/gallery/index.html) for more examples.**

---

## Level 5: Basic Data Analysis

**Goal**: Add data analysis capabilities with proper testing

**Time**: 4-6 hours

### Extending Source Code

When adding new analysis capabilities:

1. **Design the API** - What functions do you need?
2. **Write tests first** (TDD) - Define expected behavior
3. **Implement in `project/src/`** - Write the business logic
4. **Achieve required coverage** - Test all critical code paths (90% project, 60% infra)
5. **Use in scripts** - Create thin orchestrators

### Example: Correlation Analysis

**Step 1: Design API**

```python
# What do we need?
# - calculate_correlation(x, y) -> float
# - calculate_r_squared(x, y) -> float
# - linear_regression(x, y) -> (slope, intercept)
```

**Step 2: Write tests first**

```python
# tests/test_correlation.py
import pytest
from correlation import calculate_correlation, calculate_r_squared, linear_regression

def test_calculate_correlation_perfect():
    """Test perfect positive correlation."""
    x = [1, 2, 3, 4, 5]
    y = [2, 4, 6, 8, 10]
    corr = calculate_correlation(x, y)
    assert abs(corr - 1.0) < 1e-10

def test_calculate_correlation_negative():
    """Test negative correlation."""
    x = [1, 2, 3, 4, 5]
    y = [10, 8, 6, 4, 2]
    corr = calculate_correlation(x, y)
    assert abs(corr - (-1.0)) < 1e-10

def test_calculate_r_squared():
    """Test R-squared calculation."""
    x = [1, 2, 3, 4, 5]
    y = [2, 4, 6, 8, 10]
    r2 = calculate_r_squared(x, y)
    assert abs(r2 - 1.0) < 1e-10

def test_linear_regression():
    """Test linear regression."""
    x = [1, 2, 3, 4, 5]
    y = [2, 4, 6, 8, 10]
    slope, intercept = linear_regression(x, y)
    assert abs(slope - 2.0) < 1e-10
    assert abs(intercept - 0.0) < 1e-10
```

**Step 3: Implement in `project/src/`**

```python
# project/src/correlation.py
"""Correlation and regression analysis functions."""

def calculate_correlation(x: list[float], y: list[float]) -> float:
    """Calculate Pearson correlation coefficient.
    
    Args:
        x: First variable
        y: Second variable
    
    Returns:
        Correlation coefficient between -1 and 1
    """
    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator_x = sum((x[i] - mean_x) ** 2 for i in range(n)) ** 0.5
    denominator_y = sum((y[i] - mean_y) ** 2 for i in range(n)) ** 0.5
    
    return numerator / (denominator_x * denominator_y)

def calculate_r_squared(x: list[float], y: list[float]) -> float:
    """Calculate R-squared (coefficient of determination).
    
    Args:
        x: Independent variable
        y: Dependent variable
    
    Returns:
        R-squared value between 0 and 1
    """
    corr = calculate_correlation(x, y)
    return corr ** 2

def linear_regression(x: list[float], y: list[float]) -> tuple[float, float]:
    """Perform simple linear regression.
    
    Args:
        x: Independent variable
        y: Dependent variable
    
    Returns:
        Tuple of (slope, intercept)
    """
    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
    
    slope = numerator / denominator
    intercept = mean_y - slope * mean_x
    
    return slope, intercept
```

**Step 4: Run tests**

```bash
pytest tests/test_correlation.py --cov=src.correlation --cov-report=term-missing
```

Ensure coverage requirements are met before proceeding.

**Step 5: Use in scripts**

```python
# scripts/correlation_analysis.py
#!/usr/bin/env python3
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from correlation import calculate_correlation, linear_regression  # From project/src/

def main():
    # Generate sample data
    np.random.seed(42)
    x = np.linspace(0, 10, 50)
    y = 2 * x + 1 + np.random.normal(0, 1, 50)
    
    # Use project/src/ methods for computation
    corr = calculate_correlation(x.tolist(), y.tolist())
    slope, intercept = linear_regression(x.tolist(), y.tolist())
    
    # Script handles visualization only
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(x, y, alpha=0.5, label='Data')
    ax.plot(x, slope * x + intercept, 'r-', label=f'y = {slope:.2f}x + {intercept:.2f}')
    ax.set_title(f'Linear Regression (r = {corr:.3f})')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Save
    output_path = 'output/figures/correlation_analysis.png'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    # Print for manifest
    print(output_path)

if __name__ == '__main__':
    main()
```

### Saving Data Files

In addition to figures, save the underlying data:

```python
import numpy as np
import csv

# Save as NPZ (NumPy compressed)
np.savez('output/data/analysis_data.npz', 
         x=x, y=y, correlation=corr)

# Save as CSV (portable)
with open('output/data/analysis_data.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['x', 'y'])
    writer.writerows(zip(x, y))

# Print both paths
print('output/data/analysis_data.npz')
print('output/data/analysis_data.csv')
```

---

## Level 6: Automated Workflows

**Goal**: Automate complete research workflows

**Time**: 2-3 hours

### Understanding the Build Pipeline

The pipeline orchestrator (`scripts/run_all.py`) orchestrates everything:

```bash
python3 scripts/run_all.py
```

**What happens**:
1. **Tests** (27s) - Validates coverage requirements
2. **Scripts** (1s) - Executes all figure generation
3. **Utilities** (1s) - Validates markdown, generates glossary
4. **Individual PDFs** (32s) - Builds each section
5. **Combined PDF** (10s) - Assembles complete document
6. **Validation** (1s) - Checks for rendering issues

**Total**: ~84 seconds (without optional LLM review)

**See [BUILD_SYSTEM.md](../operational/BUILD_SYSTEM.md) for detailed breakdown.**

### Output Directory Structure

```
output/
├── figures/          # PNG files from scripts
│   ├── example_figure.png
│   ├── correlation_analysis.png
│   └── statistics_figure.png
│
├── data/             # CSV/NPZ data files
│   ├── analysis_data.csv
│   └── analysis_data.npz
│
├── pdf/              # Individual + combined PDFs
│   ├── 01_abstract.pdf
│   ├── 02_introduction.pdf
│   ├── ...
│   └── project_combined.pdf
│
└── tex/              # LaTeX source files
    ├── 01_abstract.tex
    └── ...
```

**All files in `output/` are disposable** - they can be regenerated anytime.

### Automating Your Workflow

**Basic workflow**:
```bash
# 1. Edit source code
vim project/src/my_module.py

# 2. Write tests
vim project/tests/test_my_module.py

# 3. Run tests
pytest tests/test_my_module.py --cov=src.my_module

# 4. Create/update script
vim scripts/my_figure.py

# 5. Run complete build
python3 scripts/run_all.py

# 6. View result (top-level output after stage 5)
open output/project_combined.pdf
```

**Advanced workflow with validation**:
```bash
# 1. Full rebuild with validation (recommended - all 6 stages)
python3 scripts/run_all.py

# Or use unified interactive menu
./run.sh

# Alternative: Manual steps
# # Pipeline automatically handles cleanup
# python3 scripts/run_all.py
# python3 scripts/04_validate_output.py
```

### Creating Custom Build Scripts

For specific workflows, create custom scripts:

```bash
#!/bin/bash
# custom_build.sh

set -e  # Exit on error

echo "Running custom build pipeline..."

# 1. Run specific tests
echo "Testing analysis module..."
pytest tests/test_correlation.py --cov=src.correlation

# 2. Generate specific figures
echo "Generating figures..."
python3 scripts/correlation_analysis.py
python3 scripts/statistics_figure.py

# 3. Build specific sections
echo "Building results section..."
pandoc manuscript/04_experimental_results.md \
    -o output/pdf/04_experimental_results.pdf \
    --pdf-engine=xelatex

echo "Custom build complete!"
```

### Batch Processing Multiple Datasets

```python
# scripts/batch_analysis.py
#!/usr/bin/env python3
import os
from correlation import calculate_correlation, linear_regression

def process_dataset(filename):
    """Process single dataset."""
    # Load data
    data = load_data(filename)  # Implement as needed
    
    # Use src/ methods
    corr = calculate_correlation(data['x'], data['y'])
    slope, intercept = linear_regression(data['x'], data['y'])
    
    # Generate figure
    generate_figure(data, corr, slope, intercept, filename)
    
    return corr, slope, intercept

def main():
    datasets = ['data1.csv', 'data2.csv', 'data3.csv']
    results = {}
    
    for dataset in datasets:
        print(f"Processing {dataset}...")
        results[dataset] = process_dataset(dataset)
    
    # Save summary
    save_results_table(results)

if __name__ == '__main__':
    main()
```

---

## Quick Tips

### Performance Optimization

1. **Cache expensive computations**
```python
import functools

@functools.lru_cache(maxsize=None)
def expensive_calculation(x):
    # Computation here
    return result
```

2. **Use vectorized operations** (NumPy)
```python
# Slow
result = [x**2 for x in data]

# Fast
result = np.array(data) ** 2
```

3. **Parallel processing** (when appropriate)
```python
from multiprocessing import Pool

with Pool() as pool:
    results = pool.map(process_dataset, datasets)
```

### Common Mistakes to Avoid

| Mistake | Problem | Solution |
|---------|---------|----------|
| **Implementing logic in scripts** | Not testable, duplicated code | Move to `project/src/`, test thoroughly |
| **Not testing edge cases** | Fails on real data | Test empty lists, single values, etc. |
| **Hardcoded paths** | Breaks on other systems | Use `os.path.join()`, relative paths |
| **Not using seeds** | Non-reproducible results | Set `np.random.seed(42)` |
| **Ignoring coverage gaps** | Untested code paths | Check `--cov-report=term-missing` |

### Best Practices

1. ✅ **Always import from `project/src/`** - Never implement algorithms in scripts
2. ✅ **Test before scripting** - Ensure `project/src/` code works first
3. ✅ **Use descriptive names** - `calculate_correlation` not `calc_corr`
4. ✅ **Add docstrings** - Document parameters and return values
5. ✅ **Set random seeds** - Make results reproducible
6. ✅ **Save both figures and data** - Enable verification
7. ✅ **Print output paths** - Build system needs them

---

## What to Read Next

### If you're ready to...

**Learn test-driven development**
→ Read **[Advanced Usage Guide](../guides/ADVANCED_USAGE.md)** (Levels 7-9)

**Build custom architectures**
→ Read **[Expert Usage Guide](../guides/EXPERT_USAGE.md)** (Levels 10-12)

**Understand the architecture deeply**
→ Read **[Architecture Guide](ARCHITECTURE.md)**

**See the thin orchestrator pattern in detail**
→ Read **[Thin Orchestrator Summary](../architecture/THIN_ORCHESTRATOR_SUMMARY.md)**

**Find specific workflows**
→ Read **[Common Workflows](../reference/COMMON_WORKFLOWS.md)**

### Related Documentation

- **[Quick Start Cheatsheet](../reference/QUICK_START_CHEATSHEET.md)** - Essential commands
- **[Glossary](../reference/GLOSSARY.md)** - Terms and definitions
- **[Build System](../operational/BUILD_SYSTEM.md)** - Complete build system reference
- **[Examples Showcase](../usage/EXAMPLES_SHOWCASE.md)** - Real-world applications
- **[Documentation Index](../DOCUMENTATION_INDEX.md)** - Complete reference

---

## Success Checklist

After completing this guide, you should be able to:

- [x] Generate custom figures using thin orchestrator pattern
- [x] Add new analysis modules to `project/src/` with tests
- [x] Achieve required test coverage for new code
- [x] Save both figures and data files
- [x] Run automated build pipelines
- [x] Create custom build scripts for specific workflows

**Congratulations!** You've mastered intermediate usage. Ready for test-driven development? Check out **[Advanced Usage](../guides/ADVANCED_USAGE.md)**.

---

**Need help?** Check the **[FAQ](../reference/FAQ.md)** or **[Common Workflows](../reference/COMMON_WORKFLOWS.md)**

**Quick Reference**: [Cheatsheet](../reference/QUICK_START_CHEATSHEET.md) | [Glossary](../reference/GLOSSARY.md)


