# Thin Orchestrator Pattern

## Pattern Definition

The thin orchestrator pattern separates business logic from coordination:

- **src/**: Contains all algorithms, computations, and business logic
- **scripts/**: Orchestrate, visualize, and coordinate components
- **Benefit**: Code is testable, reusable, and maintainable

## Core Principle

**Scripts are thin orchestrators, NOT algorithm implementations.**

### What Scripts MUST Do
1. Import methods from `src/` modules
2. Use `src/` methods for all computation
3. Handle I/O, visualization, orchestration
4. Demonstrate proper integration patterns
5. Be testable through `src/` method usage

### What Scripts MUST NOT Do
1. Implement mathematical algorithms
2. Duplicate business logic from `src/`
3. Contain complex computations
4. Define new data structures (extend `src/` instead)
5. Include untestable logic

## Implementation Example

### ❌ WRONG - Algorithm in Script

```python
# scripts/bad_example.py - VIOLATES PATTERN

import matplotlib.pyplot as plt
import numpy as np

def analyze_convergence():
    """BAD: Algorithm is in script, not reusable, not tested separately."""
    
    data = np.random.randn(100)
    
    # Algorithm duplicated from src/
    mean = np.sum(data) / len(data)
    variance = np.sum((data - mean) ** 2) / len(data)
    
    plt.plot(data)
    plt.savefig('output/figures/convergence.png')
    
    return mean, variance

if __name__ == '__main__':
    analyze_convergence()
```

### ✅ RIGHT - Thin Orchestrator

```python
# scripts/good_example.py - FOLLOWS PATTERN

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Import from src/ - where the logic lives
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from statistics import compute_mean, compute_variance
from visualization import create_convergence_plot

def analyze_convergence():
    """GOOD: Script orchestrates, src/ computes."""
    
    # Load data
    data = np.random.randn(100)
    
    # Use src/ functions for computation
    mean = compute_mean(data)
    variance = compute_variance(data)
    
    # Orchestrate visualization
    fig = create_convergence_plot(data)
    fig.savefig('output/figures/convergence.png')
    
    return mean, variance

if __name__ == '__main__':
    analyze_convergence()
```

## Pattern Structure

### src/ Module

```python
# src/statistics.py

def compute_mean(data: np.ndarray) -> float:
    """Compute mean of data."""
    return np.mean(data)

def compute_variance(data: np.ndarray) -> float:
    """Compute variance of data."""
    return np.var(data)

def normalize_data(data: np.ndarray) -> np.ndarray:
    """Normalize data to zero mean, unit variance."""
    mean = compute_mean(data)
    std = np.std(data)
    return (data - mean) / std
```

### Test Suite

```python
# tests/test_statistics.py

import numpy as np
from src.statistics import compute_mean, compute_variance

def test_compute_mean():
    """Test mean computation with real data."""
    data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    assert compute_mean(data) == 3.0

def test_compute_variance():
    """Test variance computation."""
    data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    expected = np.var(data)
    assert compute_variance(data) == expected
```

### Script Orchestrator

```python
# scripts/analyze_data.py

import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from statistics import compute_mean, normalize_data

def main():
    """Orchestrate data analysis."""
    
    # Load or generate data
    data = np.load('data/sample.npz')['values']
    
    # Use src/ functions
    mean = compute_mean(data)
    normalized = normalize_data(data)
    
    # Visualize and save
    plt.plot(normalized)
    plt.title(f'Data (mean={mean:.2f})')
    plt.savefig('output/figures/analysis.png')
    
    print(f"Analysis complete: mean={mean:.2f}")

if __name__ == '__main__':
    main()
```

## Integration Patterns

### Figure Generation

```python
# scripts/generate_figures.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from visualization import create_plot
from data_processing import load_and_process
from figure_manager import register_figure

def main():
    # Use src/ to load and process
    data = load_and_process('input/data.csv')
    
    # Orchestrate figure creation
    fig = create_plot(data)
    fig.savefig('output/figures/results.png', dpi=300)
    
    # Register figure
    register_figure(
        filename='results.png',
        title='Analysis Results',
        description='Results from data processing'
    )

if __name__ == '__main__':
    main()
```

### Analysis Pipeline

```python
# scripts/analysis_pipeline.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_processing import load_data, clean_outliers
from statistics import compute_stats
from reporting import generate_report
from validation import validate_results

def main():
    # Load and process using src/
    data = load_data('data/raw.csv')
    data = clean_outliers(data)
    
    # Compute statistics
    stats = compute_stats(data)
    
    # Validate
    if not validate_results(stats):
        raise ValueError("Validation failed")
    
    # Report
    report = generate_report(stats)
    print(report)
    
    Path('output/reports/analysis.md').write_text(report)

if __name__ == '__main__':
    main()
```

## Testing Orchestrators

Scripts are tested through their `src/` functions:

```python
# tests/test_analysis_pipeline.py

import sys
from pathlib import Path
from unittest.mock import patch

# Test the src/ functions (not the script)

def test_data_processing():
    """Test that src/ functions work correctly."""
    from src.data_processing import load_data, clean_outliers
    
    data = load_data('tests/fixtures/sample.csv')
    assert len(data) > 0
    
    clean = clean_outliers(data)
    assert len(clean) < len(data)

def test_statistics_computation():
    """Test statistics module."""
    from src.statistics import compute_stats
    import numpy as np
    
    data = np.random.randn(100)
    stats = compute_stats(data)
    
    assert 'mean' in stats
    assert 'std' in stats
```

## Benefits of the Pattern

### 1. Testability
- `src/` functions fully tested independently
- Scripts tested through `src/` integration
- No need to mock script I/O

### 2. Reusability
- `src/` functions used in multiple contexts
- Consistent API across scripts
- Easy to compose

### 3. Maintainability
- Clear separation of concerns
- Algorithm changes isolated to `src/`
- Scripts remain simple

### 4. Scalability
- New scripts easily added
- New `src/` modules easily added
- Existing code unchanged

### 5. Quality
- 100% `src/` coverage achievable
- Real integration testing
- Deterministic behavior

## Common Pitfalls

### ❌ Pitfall 1: Algorithm in Script
```python
# BAD
def analyze():
    # Algorithm here (should be in src/)
    for i in range(100):
        value = compute_something()  # ❌ In script
```

**Fix**: Move `compute_something()` to `src/`, import and use it.

### ❌ Pitfall 2: Complex Logic in Script
```python
# BAD
if complex_condition and other_check:
    result = process_data(x, y, z)  # ❌ Complex logic in script
    if result > threshold:
        # More logic
```

**Fix**: Move logic to `src/` as focused functions, call from script.

### ❌ Pitfall 3: Duplication
```python
# BAD - same function in script and src/
def mean(data):  # ❌ Also in src/statistics.py
    return sum(data) / len(data)
```

**Fix**: Use function from `src/statistics.py`, don't duplicate.

## Checklist

Script implementation checklist:

- [ ] All computation imported from `src/`
- [ ] No algorithm implementations in script
- [ ] No business logic duplication
- [ ] Clear input/output handling
- [ ] Proper error handling
- [ ] Documented dependencies on `src/`
- [ ] Functions tested through `src/` tests
- [ ] Clear logging of execution
- [ ] Output paths printed to stdout

## Comprehensive Documentation

For complete information on the thin orchestrator pattern and its implementation, consult:

- [`docs/THIN_ORCHESTRATOR_SUMMARY.md`](../docs/THIN_ORCHESTRATOR_SUMMARY.md) - Comprehensive implementation guide
- [`docs/WORKFLOW.md`](../docs/WORKFLOW.md) - Integration patterns and workflow
- [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) - System design overview
- [`docs/EXAMPLES_SHOWCASE.md`](../docs/EXAMPLES_SHOWCASE.md) - Real-world usage examples

## See Also

- [core_architecture.md](core_architecture.md) - Overall system design
- [testing.md](testing.md) - Testing the orchestrator pattern
- [source_code_standards.md](source_code_standards.md) - Code quality in src/
- [../scripts/AGENTS.md](../scripts/AGENTS.md) - Script documentation

