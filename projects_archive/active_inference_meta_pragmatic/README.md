# Active Inference Meta-Pragmatic Framework

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

**Status**: Archived / Research Complete

An implementation of Active Inference as a meta-(pragmatic/epistemic) methodology, featuring a 2×2 matrix framework for analyzing cognitive processes across multiple levels of abstraction.

## Overview

This project demonstrates that Active Inference operates not just as a theory of cognition, but as a meta-methodology that enables researchers to specify the very frameworks within which intelligence operates. Through a systematic 2×2 matrix analysis, we reveal how Active Inference transcends traditional approaches by providing meta-pragmatic and meta-epistemic control.

## Key Features

### Meta-Level Framework

- **Meta-Pragmatic**: Specify pragmatic frameworks beyond simple rewards
- **Meta-Epistemic**: Define epistemic boundaries and knowledge architectures
- **2x2 Matrix Analysis**: Systematic framework for cognitive process analysis

### Four Quadrants of Cognition

- **Q1**: Data Processing (Cognitive) - Basic EFE computation
- **Q2**: Meta-Data Organization (Cognitive) - processing with meta-information
- **Q3**: Reflective Processing (Meta-Cognitive) - Self-monitoring and adaptation
- **Q4**: Higher-Order Reasoning (Meta-Cognitive) - Framework-level optimization

### Implementation

- **Theoretical Models**: Free Energy Principle, generative models, meta-cognition
- **Visualization Suite**: 8+ figures demonstrating key concepts
- **Testing**: ~17 test files, 95%+ coverage target, no mocks
- **Source Modules**: 11 modules across 4 subpackages (core, framework, analysis, visualization) + utils
- **Research Manuscript**: 13-section paper with 52 bibliography entries

## Quick Start

### Installation

```bash
pip install -e .
```

### Basic Usage

```python
from src.active_inference import ActiveInferenceFramework
from src.generative_models import create_simple_generative_model

# Create generative model
model = create_simple_generative_model()

# Initialize Active Inference framework
framework = ActiveInferenceFramework(model)

# Make inference
observation = [0.8, 0.2]  # Sensory input
posterior = framework.perception_as_inference(observation)

# Calculate policy
posterior_beliefs = [0.6, 0.4]
policy = [0]  # Action selection
efe, components = framework.calculate_expected_free_energy(posterior_beliefs, policy)
```

### Run Analysis Pipeline

```bash
# Generate visualizations
python scripts/generate_quadrant_matrix.py
python scripts/generate_active_inference_concepts.py

# Run analysis
python scripts/analysis_pipeline.py --stages 1,2,3
```

## Project Structure

```text
active_inference_meta_pragmatic/
├── src/                          # Core implementation (11 modules, 4 subpackages)
│   ├── core/                     # Foundational implementations
│   │   ├── active_inference.py   # EFE calculations, policy selection, perception
│   │   ├── free_energy_principle.py  # FEP, Markov blankets, structure preservation
│   │   └── generative_models.py  # A, B, C, D matrix models
│   ├── framework/                # Higher-level conceptual frameworks
│   │   ├── quadrant_framework.py # 2×2 matrix framework
│   │   ├── meta_cognition.py     # Meta-cognitive monitoring and control
│   │   ├── modeler_perspective.py # Meta-level analysis (architect/subject)
│   │   └── cognitive_security.py # Threat modeling and anomaly detection
│   ├── analysis/                 # Data and validation tools
│   │   ├── data_generator.py     # Synthetic data generation
│   │   ├── statistical_analysis.py # Statistical testing and analysis
│   │   └── validation.py         # Framework validation suite
│   └── visualization/            # Plotting
│       └── visualization.py      # Publication-quality figures
├── tests/                        # Test suite (~17 test files, 95%+ coverage)
│   └── test_*.py                 # Unit and integration tests
├── scripts/                      # Analysis workflows
│   ├── analysis_pipeline.py      # 6-stage pipeline orchestrator
│   ├── generate_*.py             # Visualization scripts
│   └── insert_all_figures.py     # Manuscript figure integration
├── manuscript/                   # Research paper (13 sections)
│   ├── 01_abstract.md            # Abstract with keywords
│   ├── 02_introduction.md        # Motivation, contributions, paper organization
│   ├── 03_related_work.md        # Active Inference, meta-cognition, predictive processing, AI safety, cognitive security
│   ├── 04_background.md          # FEP, EFE, generative models, meta-aspects
│   ├── 05_methodology.md         # Theoretical approach and computational validation
│   ├── 06_quadrant_model.md      # 2x2 framework with Q1-Q4
│   ├── 07_security_implications.md # Threat model, cognitive security, AI safety
│   ├── 08_discussion.md          # Theoretical contributions and limitations
│   ├── 09_conclusion.md          # Summary, insights, future directions
│   ├── 10_acknowledgments.md     # Acknowledgments
│   ├── 11_appendix.md            # Mathematical derivations, algorithms, benchmarks
│   ├── 98_symbols_glossary.md    # Mathematical notation and glossary
│   ├── 99_references.md          # Bibliography references
│   ├── config.yaml               # Paper metadata
│   ├── preamble.md               # LaTeX preamble
│   └── references.bib            # BibTeX bibliography (52 entries)
├── doc/                          # Documentation
│   ├── architecture.md           # System architecture and design decisions
│   ├── api_reference.md          # Comprehensive API reference
│   ├── theoretical_primer.md     # Accessible introduction to Active Inference
│   └── quickstart.md             # 5-minute getting-started guide
├── output/                       # Generated outputs
│   ├── figures/                  # Visualizations
│   ├── data/                     # Analysis data
│   └── reports/                  # Pipeline reports
└── pyproject.toml                # Project configuration
```

## Documentation

- [Quickstart Guide](doc/quickstart.md) -- Get running in 5 minutes
- [Theoretical Primer](doc/theoretical_primer.md) -- Accessible introduction to Active Inference and the 2x2 framework
- [API Reference](doc/api_reference.md) -- Comprehensive class and method documentation
- [Architecture](doc/architecture.md) -- System design, module dependencies, data flow

## Theoretical Foundation

### Active Inference as Meta-Methodology

Active Inference is revealed as a meta-(pragmatic/epistemic) methodology through:

1. **Epistemic Framework Specification**: Define what agents can know via matrix A
2. **Pragmatic Landscape Design**: Specify value systems through matrix C
3. **Meta-Cognitive Control**: Self-monitoring via quadrant 3 operations
4. **Framework Optimization**: Higher-order adaptation in quadrant 4

### Key Insights

- **Intelligence as Framework Design**: Cognition involves designing and adapting fundamental frameworks
- **Recursive Self-Understanding**: Active Inference enables modeling cognition with cognition
- **Meta-Level Security**: Framework-level vulnerabilities and defenses
- **Unified Cognitive Architecture**: Single formalism spanning biological and artificial systems

## Research Contributions

### Theoretical

- Meta-level interpretation of Active Inference
- 2×2 matrix framework for cognitive analysis
- Integration with Free Energy Principle
- Recursive modeler perspective

### Methodological

- generative model implementations
- Meta-cognitive monitoring systems
- Framework optimization algorithms
- Theoretical validation suite

### Practical

- Visualization tools for complex concepts
- Reproducible research pipeline
- Educational framework for cognitive science
- Foundation for meta-level AI development

## Validation Results

### Theoretical Correctness

- ✅ EFE calculations match mathematical derivations
- ✅ Free energy minimization follows FEP principles
- ✅ Bayesian inference properly implemented
- ✅ Meta-cognitive operations theoretically sound

### Implementation Quality

- ✅ Core functionality tested and validated
- ✅ Numerical stability verified for key operations
- ✅ Error handling with proper validation
- ✅ Type hints and documentation

### Research Standards

- 13-section manuscript with cross-references
- 52-entry bibliography spanning 6 research traditions
- Mathematical notation standardized (symbols glossary)
- Figures properly integrated with LaTeX labels

## Applications

### Cognitive Science

- Understanding meta-cognitive development
- Analyzing cognitive security vulnerabilities
- Designing educational interventions
- Modeling cultural cognitive frameworks

### Artificial Intelligence

- Meta-learning system development
- Value alignment frameworks
- Self-improving AI architectures
- Robust AI safety mechanisms

### Neuroscience

- Meta-cognitive brain mechanisms
- Higher-order cognitive processes
- Consciousness and self-awareness
- Cognitive development trajectories

## Citation

If you use this work, please cite:

```bibtex
@misc{friedman2026active,
  title={Active Inference as a Meta-(Pragmatic/Epistemic) Method},
  author={Friedman, Daniel},
  year={2026},
  note={Active Inference Meta-Pragmatic Framework Implementation}
}
```

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](../../LICENSE) file for details.

## Acknowledgments

Special thanks to Karl Friston and the Active Inference research community for foundational theoretical work.
