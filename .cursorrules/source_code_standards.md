# Source Code Standards

## Type Hints

All public APIs must have complete type hints:

```python
# ✅ GOOD - Complete type hints
def compute_mean(data: np.ndarray) -> float:
    """Calculate mean value."""
    return np.mean(data)

def process_records(records: List[Dict[str, Any]]) -> Tuple[List, List]:
    """Process records and return results."""
    ...

# ❌ BAD - Missing type hints
def compute_mean(data):
    return np.mean(data)

def process_records(records):
    ...
```

## Naming Conventions

### Functions and Variables
- Use `snake_case` for functions and variables
- Avoid 1-2 character names
- Descriptive, meaningful names

```python
# ✅ GOOD
def calculate_convergence_rate(iterations, errors):
    """Calculate convergence rate."""
    return errors[0] / errors[-1]

# ❌ BAD
def calc_cr(i, e):
    """Calc conv rate."""
    return e[0] / e[-1]
```

### Classes and Types
- Use `PascalCase` for classes
- Descriptive class names

```python
class DataProcessor:
    """Process and analyze data."""
    pass

class ConvergenceAnalyzer:
    """Analyze convergence patterns."""
    pass
```

### Constants
- Use `UPPER_SNAKE_CASE`
- Define at module level

```python
DEFAULT_LEARNING_RATE = 0.01
MAX_ITERATIONS = 1000
CONVERGENCE_THRESHOLD = 1e-6
```

## Documentation

### Module Docstrings
```python
"""Data processing module for analysis pipelines.

This module provides utilities for loading, cleaning, and analyzing data
with comprehensive error handling and validation.
"""
```

### Function Docstrings
```python
def analyze_convergence(data: np.ndarray, threshold: float = 1e-6) -> Dict[str, Any]:
    """Analyze data convergence patterns.
    
    Args:
        data: Input array with convergence trajectory
        threshold: Convergence threshold (default: 1e-6)
    
    Returns:
        Dictionary with convergence analysis results
    
    Raises:
        ValueError: If data is empty or invalid
    """
    ...
```

### Inline Comments
```python
# Explain WHY, not WHAT

# ✅ GOOD - Explains reasoning
# Use logarithmic scale because raw values span orders of magnitude
log_values = np.log10(raw_values)

# ❌ BAD - States obvious
# Convert to log scale
log_values = np.log10(raw_values)
```

## Error Handling

### Guard Clauses
```python
# ✅ GOOD - Handle errors first
def process_data(data: np.ndarray) -> np.ndarray:
    """Process data array."""
    if data is None:
        raise ValueError("Data cannot be None")
    
    if len(data) == 0:
        raise ValueError("Empty data array")
    
    # Main logic here
    return cleaned_data
```

### Meaningful Error Messages
```python
# ✅ GOOD - Clear, actionable
if not os.path.exists(config_file):
    raise FileNotFoundError(
        f"Configuration file not found: {config_file}\n"
        "Expected location: src/config.yaml"
    )

# ❌ BAD - Vague
if not os.path.exists(config_file):
    raise FileNotFoundError("File not found")
```

## Code Organization

### Module Structure
```python
"""Module docstring."""

# Imports
import numpy as np
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

# Constants
DEFAULT_VALUE = 0.5

# Public functions
def public_function():
    """Public API."""
    pass

# Private functions
def _private_helper():
    """Internal helper."""
    pass

# Classes
class DataProcessor:
    """Main class."""
    pass
```

### Function Length
- Keep functions focused and short
- Single responsibility principle
- Extract helper functions
- Typical: 10-30 lines

## Testing Integration

### Make Code Testable
```python
# ✅ GOOD - Easy to test
def calculate_statistics(data):
    """Calculate statistics from data."""
    return {
        'mean': np.mean(data),
        'std': np.std(data),
        'count': len(data)
    }

# ❌ BAD - Hard to test
def calculate_and_plot_statistics(data, filename):
    """Calculate and plot statistics."""
    stats = {...}
    plt.plot(...)
    plt.savefig(filename)
```

## Dependencies

### Import Organization
```python
# Standard library first
import json
import os
from pathlib import Path
from typing import List, Dict

# Third-party packages
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Local imports
from src.data_processing import load_data
from src.analysis import compute_metrics
```

### Avoid Circular Imports
- Design to prevent circular dependencies
- Use dependency injection if needed

## Performance Considerations

### Efficient Code
```python
# ✅ GOOD - Efficient vectorized operations
result = np.array([x**2 for x in data])  # Vectorized

# ❌ BAD - Inefficient loop
result = []
for x in data:
    result.append(x**2)
```

### Avoid Premature Optimization
```python
# Focus on correctness first, optimize if needed
# Profile before optimizing

# ✅ GOOD - Clear, correct, then optimize if needed
def calculate_distance(p1, p2):
    """Calculate Euclidean distance."""
    return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
```

## Version Control Integration

### Meaningful Commits
```bash
# Good commit messages
git commit -m "feat: add convergence analysis module

- Implement convergence detection algorithm
- Add comprehensive test coverage
- Include documentation and examples"

# Avoid generic messages
git commit -m "fix stuff"
git commit -m "update"
```

## Code Review Checklist

- [ ] Type hints on all public APIs
- [ ] Meaningful variable names (no 1-2 chars)
- [ ] Clear docstrings for functions and modules
- [ ] Guard clauses for error handling
- [ ] Meaningful error messages
- [ ] Focused, short functions
- [ ] Proper import organization
- [ ] Testable code (no complex logic in tests)
- [ ] Comments explain WHY, not WHAT
- [ ] No duplication of logic

## See Also

- [testing.md](testing.md) - Testing standards
- [thin_orchestrator.md](thin_orchestrator.md) - Script standards
- [../src/AGENTS.md](../src/AGENTS.md) - Source code documentation
- [../AGENTS.md](../AGENTS.md) - System documentation

