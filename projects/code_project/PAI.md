# PAI.md - Code Project Context

## Purpose

This project demonstrates the **optimization algorithms research** template pattern with analysis pipelines and test-driven development.

## PAI Integration Points

### Skill Compatibility

- **Performance Analysis**: Benchmarking utilities for PAI workflows
- **Statistical Methods**: Reusable analysis patterns
- **Visualization**: Publication-quality figure generation

### Key Modules for PAI Use

| Module | PAI Application |
|--------|-----------------|
| `src/optimizer.py` | Gradient descent optimization and quadratic functions |
| `scripts/optimization_analysis.py` | Analysis pipeline with scientific validation |
| `scripts/generate_api_docs.py` | API documentation generation |

### Example PAI Usage

```python
from projects.code_project.src import gradient_descent, quadratic_function, compute_gradient
import numpy as np

# Run optimization
result = gradient_descent(
    initial_point=np.array([0.0]),
    objective_func=lambda x: quadratic_function(x),
    gradient_func=lambda x: compute_gradient(x),
    step_size=0.1
)
print(f"Solution: {result.solution}, Converged: {result.converged}")
```

## Agent Guidelines

- **Thin Orchestrator**: Scripts import from src/, never implement logic
- **Test Coverage**: 90%+ required for all src/ modules
- **Deterministic**: Fixed seeds for reproducibility
- **Output Paths**: Print file paths to stdout for manifest collection
