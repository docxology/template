# Project Source Code

Research-specific algorithms, data generation, and analysis functions for the Ento-Linguistic research project. This directory contains the core computational logic organized into five subdirectory packages.

## Directory Structure

```
src/
├── __init__.py
├── analysis/              # Text analysis, NLP, and domain-specific modules
│   ├── cace_scoring.py
│   ├── conceptual_mapping.py
│   ├── discourse_analysis.py
│   ├── discourse_patterns.py
│   ├── domain_analysis.py
│   ├── performance.py
│   ├── persuasive_analysis.py
│   ├── rhetorical_analysis.py
│   ├── semantic_entropy.py
│   ├── statistics.py
│   ├── term_extraction.py
│   └── text_analysis.py
├── core/                  # Core utilities, validation, metrics
│   ├── example.py
│   ├── exceptions.py
│   ├── logging.py
│   ├── markdown_integration.py
│   ├── metrics.py
│   ├── parameters.py
│   ├── validation.py
│   └── validation_utils.py
├── data/                  # Data loading, generation, literature mining
│   ├── data_generator.py
│   ├── data_processing.py
│   ├── literature_mining.py
│   └── loader.py
├── pipeline/              # Simulation and reporting
│   ├── reporting.py
│   └── simulation.py
└── visualization/         # Visualization and figure generation
    ├── concept_visualization.py
    ├── figure_manager.py
    ├── plots.py
    ├── statistical_visualization.py
    └── visualization.py
```

## Key Principles

### Data Analysis

- **No mock methods** - all functions use real computations
- **Deterministic outputs** - reproducible results with fixed seeds
- **Scientific accuracy** - mathematically correct implementations

### Modular Design

- **Single responsibility** - each function has one clear purpose
- **Clear interfaces** - well-documented input/output specifications
- **Testable units** - functions designed for testing

## Usage in Scripts

Source code is imported by analysis scripts:

```python
from analysis.term_extraction import TerminologyExtractor
from analysis.domain_analysis import DomainAnalyzer
from visualization.concept_visualization import ConceptVisualizer

extractor = TerminologyExtractor()
terms = extractor.extract_terms(texts)
```

## Testing Requirements

Project source code must maintain **90% test coverage**:

```bash
pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=90
```

## See Also

- [AGENTS.md](AGENTS.md) - Detailed module documentation
- [../tests/](../tests/) - Test suite
- [../scripts/](../scripts/) - Analysis scripts
