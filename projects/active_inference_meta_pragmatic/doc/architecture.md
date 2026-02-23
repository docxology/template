# System Architecture

## Overview

The Active Inference Meta-Pragmatic project follows a two-layer architecture separating generic infrastructure (Layer 1) from project-specific domain code (Layer 2). All business logic resides in source modules; scripts serve only as thin orchestrators for I/O, visualization, and pipeline coordination.

This project is part of a larger multi-project research template. The repository root provides shared infrastructure for rendering, validation, and pipeline execution, while this project contributes domain-specific implementations of Active Inference theory.

## Module Dependency Graph

```
                    +-----------+
                    |   utils   |  (shared: logging, exceptions, figure_manager)
                    +-----------+
                          |
          +---------------+---------------+
          |                               |
    +-----v------+                 +------v------+
    |    core     |                |  framework   |
    +------------+                 +-------------+
    | active_inference.py          | quadrant_framework.py
    | free_energy_principle.py     | meta_cognition.py
    | generative_models.py         | modeler_perspective.py
    +------------+                 | cognitive_security.py
          |                        +------+------+
          |                               |
          +-------+-----------+-----------+
                  |           |
           +------v----+ +---v-----------+
           |  analysis  | | visualization |
           +-----------+ +---------------+
           | data_generator.py       | visualization.py
           | statistical_analysis.py |
           | validation.py           |
           +-----------+             +---------------+
```

### Dependency Rules

1. **core** modules have no internal cross-dependencies. Each can be used independently.
2. **framework** modules depend on core (e.g., `quadrant_framework` references Active Inference concepts; `cognitive_security` references generative models and meta-cognition).
3. **analysis** modules depend on core and framework (e.g., `validation` checks generative model structures; `statistical_analysis` evaluates algorithm outputs).
4. **visualization** depends on all other packages for rendering domain concepts.
5. **utils** is a shared dependency available to all modules.

## Subpackage Organization

The source code is organized into four subpackages plus a shared utilities package:

### core/

Foundational Active Inference implementations with no internal cross-dependencies.

| Module | Responsibility |
|--------|---------------|
| `active_inference.py` | EFE calculations, policy selection, perception as inference |
| `free_energy_principle.py` | Variational free energy, Markov blankets, structure preservation |
| `generative_models.py` | A, B, C, D matrix management, forward prediction, Bayesian inference |

### framework/

Higher-level conceptual frameworks that build on core Active Inference primitives.

| Module | Responsibility |
|--------|---------------|
| `quadrant_framework.py` | 2x2 matrix (Data/Meta-Data x Cognitive/Meta-Cognitive), quadrant transitions |
| `meta_cognition.py` | Confidence assessment, attention allocation, strategy evaluation |
| `modeler_perspective.py` | Dual role analysis (architect/subject), epistemic and pragmatic framework specification |
| `cognitive_security.py` | Attack surface analysis, parameter drift simulation, anomaly detection, framework integrity |

### analysis/

Data generation, statistical testing, and validation tools.

| Module | Responsibility |
|--------|---------------|
| `data_generator.py` | Synthetic time series, categorical data, state sequences, generative model matrices |
| `statistical_analysis.py` | Descriptive statistics, correlation, t-tests, ANOVA, algorithm comparison |
| `validation.py` | Probability distribution checks, generative model validation, numerical stability |

### visualization/

Publication-quality figure generation.

| Module | Responsibility |
|--------|---------------|
| `visualization.py` | Quadrant matrix plots, generative model diagrams, FEP visualizations, meta-cognitive flow diagrams |

### utils/

Shared utilities inherited from the project template.

| Module | Responsibility |
|--------|---------------|
| `logging.py` | Structured logging with configurable levels |
| `exceptions.py` | `ValidationError` and custom exception hierarchy |
| `figure_manager.py` | Figure registration, cross-referencing, manifest tracking |

## Data Flow

The system processes data through a clear pipeline:

```
1. Generative Models          2. Active Inference         3. Quadrant Framework
   (A, B, C, D matrices)  -->    (EFE computation,    -->    (2x2 analysis,
                                  policy selection,           quadrant assignment,
                                  perception)                 meta-level classification)

4. Meta-Cognition             5. Validation               6. Visualization
   (confidence assessment, -->    (probability checks, -->    (publication-quality
    attention allocation,         theoretical correctness,     figures, diagrams,
    strategy evaluation)          numerical stability)         quadrant matrices)
```

### Detailed Flow

1. **Model Specification**: The modeler defines generative model matrices (A: observation likelihoods, B: state transitions, C: preferences, D: priors). This is where meta-epistemic and meta-pragmatic decisions are made.

2. **Inference and Action**: `ActiveInferenceFramework` uses the generative model to perform perception as inference (updating beliefs from observations) and action selection (minimizing Expected Free Energy across candidate policies).

3. **Quadrant Analysis**: `QuadrantFramework` classifies processing along two dimensions (Data/Meta-Data and Cognitive/Meta-Cognitive), producing a structured analysis of which quadrant governs the current operation.

4. **Meta-Cognitive Evaluation**: `MetaCognitiveSystem` assesses confidence in inference results, adjusts attention allocation, and implements adaptive control strategies based on uncertainty levels.

5. **Validation**: `ValidationFramework` checks all outputs for theoretical correctness (EFE decomposition, probability normalization, matrix compatibility) and numerical stability.

6. **Visualization**: `VisualizationEngine` renders the results as publication-quality figures suitable for the research manuscript.

## Key Design Decisions

### Thin Orchestrator Pattern

Scripts in `scripts/` never implement algorithms or business logic. They import from `src/` modules, set up I/O paths, call computation functions, and save outputs. This ensures all logic is tested and reusable.

```python
# scripts/generate_quadrant_matrix.py (orchestrator)
from src.quadrant_framework import QuadrantFramework
from src.visualization import VisualizationEngine

framework = QuadrantFramework()
viz_data = framework.create_quadrant_matrix_visualization()
engine = VisualizationEngine(output_dir="output/figures")
fig = engine.create_quadrant_matrix_plot(viz_data)
engine.save_figure(fig, "quadrant_matrix")
```

### No-Mocks Testing

All tests use real numerical data and computations. HTTP interactions use `pytest-httpserver`, file operations use `tmp_path`, and PDFs are created with `reportlab`. This ensures tests validate actual behavior rather than mocked interfaces.

### Computational Validation

Rather than asserting string outputs or mock call counts, tests verify mathematical properties:

- Probability distributions sum to 1
- EFE decomposes correctly into epistemic and pragmatic components
- Free energy decreases under correct inference
- Matrix dimensions are compatible across the generative model
- Confidence scores respond appropriately to belief entropy changes

### Reproducibility

All stochastic operations accept optional `seed` parameters. The `DataGenerator` class wraps `np.random.RandomState` for deterministic output generation, ensuring figures and analysis results are reproducible across runs.
