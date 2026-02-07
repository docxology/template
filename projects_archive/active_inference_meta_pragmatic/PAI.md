# PAI.md - Active Inference Meta-Pragmatic Context

## Purpose

This project explores **Active Inference** principles applied to meta-pragmatic analysis — how agents reason about and optimize their own reasoning processes. It implements a 2×2 quadrant model (Data/Meta-Data × Cognitive/Meta-Cognitive) alongside core Active Inference computations (EFE, generative models, meta-cognition).

## Architecture Overview

```mermaid
graph TD
    A[ActiveInferenceFramework] --> B[FreeEnergyPrinciple]
    A --> C[GenerativeModel]
    A --> D[QuadrantFramework]
    D --> E[MetaCognitiveSystem]
    D --> F[ModelerPerspective]
    G[DataGenerator] --> H[StatisticalAnalysis]
    H --> I[Validation]
    C --> J[Visualization]
```

### Source Modules (10)

| Module | Purpose |
| ------ | ------- |
| `active_inference.py` | Core EFE calculations and policy selection |
| `free_energy_principle.py` | FEP system boundary analysis and structure preservation |
| `quadrant_framework.py` | 2×2 matrix cognitive process analysis |
| `generative_models.py` | A, B, C, D matrix implementations |
| `meta_cognition.py` | Confidence assessment and adaptive control |
| `modeler_perspective.py` | Dual role analysis (architect and subject) |
| `data_generator.py` | Synthetic data generation for demonstrations |
| `statistical_analysis.py` | Statistical testing, regression, hypothesis validation |
| `validation.py` | Framework validation suite |
| `visualization.py` | Publication-quality plotting |

## PAI Integration Points

### Skill Compatibility

- **Meta-Cognition**: Frameworks for PAI self-monitoring
- **Free Energy Minimization**: Decision-making optimization
- **Belief Updating**: Bayesian inference patterns

### Key Concepts for PAI Use

| Concept | PAI Application |
| ------- | --------------- |
| Free Energy | Prediction error minimization in agent behavior |
| Active Inference | Action selection through expected free energy |
| Meta-Pragmatics | Reasoning about communication effectiveness |
| Quadrant Model | Cognitive/Metacognitive × Data/Metadata taxonomy |

### Theoretical Framework

The quadrant model provides structure for PAI agent cognition:

- **Q1 (Data, Cognitive)**: Direct perception and action
- **Q2 (Metadata, Cognitive)**: Context-aware processing
- **Q3 (Data, Metacognitive)**: Self-monitoring of processes
- **Q4 (Metadata, Metacognitive)**: Meta-level optimization

## Build and Test

```bash
# Install
pip install -e .

# Run all 360 tests
python -m pytest tests/ --tb=short -q

# Run with coverage (90% minimum threshold)
python -m pytest tests/ --cov=src --cov-report=term
```

## Dependencies

| Package | Use |
|---------|-----|
| numpy ≥1.24 | Numerical computations and matrix operations |
| scipy ≥1.10 | Statistical functions and optimization |
| matplotlib ≥3.7 | Visualization and plotting |
| pandas ≥2.0 | Data organization |
| psutil ≥5.9 | System resource monitoring |
| pytest ≥7.4 | Testing framework (dev) |
| pytest-cov ≥4.1 | Coverage reporting (dev) |

## Agent Guidelines

- **Theoretical Focus**: This project emphasizes formal frameworks
- **Mathematical Rigor**: Equations and proofs required
- **No Mocks Policy**: All tests use real data and computations
- **Cross-Reference**: Link to empirical implementations elsewhere
- **Publication Ready**: Academic manuscript format
