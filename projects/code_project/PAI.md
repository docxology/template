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
| `optimizer.py` | Optimization algorithm implementations |
| `performance.py` | Performance measurement utilities |
| `visualization.py` | Figure generation patterns |

### Example PAI Usage
```python
from projects.code_project.src import optimize, measure_performance

# Run optimization
result = optimize(objective_function, initial_params)

# Measure performance
metrics = measure_performance(operation, iterations=100)
```

## Agent Guidelines
- **Thin Orchestrator**: Scripts import from src/, never implement logic
- **Test Coverage**: 90%+ required for all src/ modules
- **Deterministic**: Fixed seeds for reproducibility
- **Output Paths**: Print file paths to stdout for manifest collection
