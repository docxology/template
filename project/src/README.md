# Scientific Layer - Quick Reference

Project-specific algorithms, analysis, and visualization.

## What's Here

Domain-specific scientific code for this research project.

**Not reusable elsewhere.** Implements algorithms and analysis specific to this problem.

## Quick Start

### Using Scientific Modules

```python
# Run simulation
from simulation import SimpleSimulation

sim = SimpleSimulation()
results = sim.run()

# Analyze results
from statistics import calculate_descriptive_stats

stats = calculate_descriptive_stats(results)

# Visualize
from visualization import VisualizationEngine

viz = VisualizationEngine()
fig = viz.create_figure()
# ...add plots...
viz.save_figure(fig, "results.png")
```

### In Scripts

Scripts orchestrate scientific code:

```python
# scripts/analysis_pipeline.py
from data_generator import generate_synthetic_data
from statistics import analyze_results
from infrastructure.documentation.figure_manager import FigureManager

# Science: Generate and analyze
data = generate_synthetic_data()
analysis = analyze_results(data)

# Infrastructure: Manage outputs
fm = FigureManager()
fm.register_figure("results.png", label="fig:results")
```

## Modules

| Module | Purpose |
|--------|---------|
| `example.py` | Basic operations (template) |
| `simulation.py` | Scientific simulations |
| `parameters.py` | Parameter management |
| `data_generator.py` | Synthetic data generation |
| `data_processing.py` | Data preprocessing |
| `statistics.py` | Statistical analysis |
| `metrics.py` | Performance metrics |
| `performance.py` | Convergence and scalability |
| `validation.py` | Result validation |
| `visualization.py` | Figure generation |
| `plots.py` | Plot implementations |
| `reporting.py` | Report generation |

## Key Concepts

### Layer 2 Architecture

This is **Layer 2** of the two-layer design:
- **Algorithms and analysis** (this layer)
- **Build and validation** (infrastructure/ layer)

Scientific code is **project-specific** and **domain-focused**.

### 100% Tested

All modules have 100% test coverage. No code ships without tests.

## File Organization

```
src/scientific/
├── __init__.py                    # Package initialization
├── AGENTS.md                      # Detailed documentation
├── README.md                      # This file
├── example.py                     # Template example
├── simulation.py                  # Simulation framework
├── parameters.py                  # Parameter management
├── data_generator.py              # Synthetic data
├── data_processing.py             # Data preprocessing
├── statistics.py                  # Statistical analysis
├── metrics.py                     # Performance metrics
├── performance.py                 # Convergence analysis
├── validation.py                  # Result validation
├── visualization.py               # Figure generation
├── plots.py                       # Plot implementations
└── reporting.py                   # Report generation
```

## Testing

```bash
# Test scientific layer
pytest tests/scientific/ --cov=src/scientific

# All tests with coverage
pytest tests/ --cov=src
```

## See Also

- [`AGENTS.md`](AGENTS.md) - Complete documentation
- [`../../infrastructure/README.md`](../../infrastructure/README.md) - Infrastructure layer
- [`../../docs/TWO_LAYER_ARCHITECTURE.md`](../../docs/TWO_LAYER_ARCHITECTURE.md) - Architecture guide
- [`../../docs/DECISION_TREE.md`](../../docs/DECISION_TREE.md) - Code placement guide
- [`../../scripts/README.md`](../../scripts/README.md) - Script orchestration

## Quick Facts

- **Project-specific** ✅
- **100% test coverage** ✅
- **Domain-focused** ✅
- **Well-tested** ✅
- **Orchestrated by scripts/** ✅

