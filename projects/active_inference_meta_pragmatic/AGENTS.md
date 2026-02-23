# Active Inference Meta-Pragmatic Framework - Technical Documentation

## System Architecture

This project implements Active Inference as a meta-(pragmatic/epistemic) methodology using a modular architecture with local utilities.

### Layer 1: Local Utilities

- **Logging Framework**: Simple logging with `utils.logging`
- **Validation System**: Local validation with `utils.exceptions`
- **Figure Management**: Automated figure registration and cross-referencing
- **Rendering Pipeline**: LaTeX/PDF generation with manuscript processing

### Layer 2: Domain Implementation (Project-Specific)

- **Theoretical Models**: Active Inference, Free Energy Principle, Meta-Cognition
- **Quadrant Framework**: 2×2 matrix implementation for cognitive analysis
- **Generative Models**: A, B, C, D matrix implementations with validation
- **Visualization Engine**: Publication-quality plotting with consistent styling

## Source Architecture

The `src/` directory contains 11 modules organized into 4 subpackages:

```
src/
├── core/                     # No internal cross-dependencies
│   ├── active_inference.py
│   ├── free_energy_principle.py
│   └── generative_models.py
├── framework/                # Depends on core
│   ├── quadrant_framework.py
│   ├── meta_cognition.py
│   ├── modeler_perspective.py
│   └── cognitive_security.py
├── analysis/                 # Depends on core + framework
│   ├── data_generator.py
│   ├── statistical_analysis.py
│   └── validation.py
└── visualization/            # Depends on all
    └── visualization.py
```

Import convention: `from src.core.active_inference import ActiveInferenceFramework` (with subpackage) or `from src.active_inference import ActiveInferenceFramework` (flat, for backward compatibility via `__init__.py` re-exports).

## Core Modules

### Active Inference Framework (`src/core/active_inference.py`)

**Purpose**: Core Active Inference implementation with EFE calculations
**Key Classes**:

- `ActiveInferenceFramework`: Main framework with generative model integration
**Key Methods**:
- `calculate_expected_free_energy()`: EFE computation with epistemic/pragmatic decomposition
- `select_optimal_policy()`: Policy selection via EFE minimization
- `perception_as_inference()`: Bayesian perception implementation
**Validation**: Theoretical correctness against EFE mathematics

### Free Energy Principle (`src/free_energy_principle.py`)

**Purpose**: FEP implementation for system boundary analysis and structure preservation
**Key Classes**:

- `FreeEnergyPrinciple`: FEP framework with system state modeling
**Key Methods**:
- `calculate_free_energy()`: Variational free energy computation
- `define_system_boundary()`: Markov blanket identification
- `demonstrate_structure_preservation()`: Long-term system organization analysis
**Validation**: Free energy minimization and system boundary correctness

### Quadrant Framework (`src/quadrant_framework.py`)

**Purpose**: 2×2 matrix framework for systematic cognitive process analysis
**Key Classes**:

- `QuadrantFramework`: Framework management and quadrant definitions
**Key Methods**:
- `analyze_processing_level()`: Data/cognitive level assessment
- `demonstrate_quadrant_transitions()`: Developmental and situational transitions
- `create_quadrant_matrix_visualization()`: Figure data generation
**Validation**: Quadrant consistency and transition logic

### Generative Models (`src/generative_models.py`)

**Purpose**: Probabilistic generative model implementations (A, B, C, D matrices)
**Key Classes**:

- `GenerativeModel`: generative model with matrix validation
**Key Methods**:
- `predict_observations()`: Forward prediction P(o|s)
- `predict_state_transition()`: Transition prediction P(s'|s,a)
- `perform_inference()`: Bayesian inference P(s|o)
- `demonstrate_modeler_specifications()`: Meta-level specification analysis
**Validation**: Matrix compatibility and probabilistic correctness

### Meta-Cognition (`src/meta_cognition.py`)

**Purpose**: Meta-cognitive monitoring and self-reflective processing
**Key Classes**:

- `MetaCognitiveSystem`: Meta-cognitive monitoring and control
**Key Methods**:
- `assess_inference_confidence()`: Confidence evaluation with entropy analysis
- `adjust_attention_allocation()`: Adaptive resource allocation
- `implement_meta_cognitive_control()`: Higher-level cognitive control
- `evaluate_strategy_effectiveness()`: Strategy performance assessment
**Validation**: Confidence calculation accuracy and adaptation stability

### Modeler Perspective (`src/modeler_perspective.py`)

**Purpose**: Dual role analysis of modeler as architect and subject
**Key Classes**:

- `ModelerPerspective`: Framework specification and self-reflection
**Key Methods**:
- `specify_epistemic_framework()`: Epistemic boundary definition
- `specify_pragmatic_framework()`: Pragmatic landscape specification
- `analyze_self_reflective_modeling()`: Recursive self-modeling analysis
- `synthesize_meta_theoretical_perspective()`: meta-theory synthesis
**Validation**: Framework consistency and recursive logic

### Cognitive Security (`src/framework/cognitive_security.py`)

**Purpose**: Cognitive security analysis within the Active Inference framework
**Key Classes**:

- `CognitiveSecurityAnalyzer`: Attack surface mapping, parameter drift simulation, anomaly detection
**Key Methods**:
- `analyze_attack_surface()`: Map potential attack vectors across all four quadrants
- `simulate_parameter_drift()`: Simulate gradual corruption of A/B/C/D matrices and measure impact
- `detect_anomaly()`: Detect anomalous observations using KL divergence thresholds
- `validate_framework_integrity()`: Comprehensive integrity check across all model components
**Validation**: Drift detection accuracy, anomaly sensitivity, integrity report correctness

### Data Generator (`src/analysis/data_generator.py`)

**Purpose**: Synthetic data generation for demonstrations and testing
**Key Classes**:

- `DataGenerator`: Controlled data generation with reproducible seeding
**Key Methods**:
- `generate_time_series()`: Synthetic time series with configurable trends and seasonality
- `generate_categorical_observations()`: Categorical observation generation
- `generate_state_sequences()`: Hidden state sequence generation (Markov, random)
- `generate_observation_matrix()`: Observation likelihood matrix A generation
- `generate_transition_matrix()`: State transition matrix B generation
- `generate_preference_vector()`: Preference vector C generation
- `generate_synthetic_dataset()`: Classification dataset generation
**Validation**: Probabilistic correctness and statistical properties

### Statistical Analysis (`src/statistical_analysis.py`)

**Purpose**: Statistical testing, regression, and hypothesis validation
**Key Classes**:

- `StatisticalAnalyzer`: Statistical analysis toolkit with configurable significance
**Key Methods**:
- `calculate_descriptive_stats()`: Comprehensive descriptive statistics
- `calculate_correlation()`: Pearson, Spearman, and Kendall correlation
- `calculate_confidence_interval()`: Confidence intervals for means
- `anova_test()`: One-way ANOVA testing
- `perform_t_test()`: Independent and paired t-tests with effect sizes
- `analyze_algorithm_performance()`: Comparative algorithm analysis
**Validation**: Statistical correctness and interpretation accuracy

### Validation Framework (`src/validation.py`)

**Purpose**: Theoretical correctness verification and numerical stability checking
**Key Classes**:

- `ValidationFramework`: Comprehensive validation with configurable tolerance
**Key Methods**:
- `validate_probability_distribution()`: Distribution validity checking
- `validate_generative_model()`: Generative model structure validation (A, B, C, D)
- `validate_theoretical_correctness()`: Algorithm correctness against expectations
- `validate_algorithm_performance()`: Performance against requirements
- `create_validation_report()`: Comprehensive multi-validation reporting
**Validation**: Self-validating with recursive correctness checks

## Analysis Scripts

### Thin Orchestrator Pattern

All scripts follow the thin orchestrator pattern: import business logic from `src/` modules, handle I/O and coordination only.

### Pipeline Scripts

- `analysis_pipeline.py`: workflow orchestration (6 stages)
- `generate_quadrant_matrix.py`: Quadrant visualization with detailed annotations
- `generate_active_inference_concepts.py`: Core concept visualizations (EFE, perception-action loop, generative models)
- `generate_fep_visualizations.py`: Free Energy Principle diagrams (system boundaries, minimization dynamics)
- `generate_quadrant_examples.py`: Quadrant-specific examples with mathematical demonstrations

### Script Architecture

```python
# Standard pattern for all analysis scripts
from utils.logging import get_logger
from utils.figure_manager import FigureManager
# Import domain modules from src/
# Setup output directories
# Execute analysis
# Register figures for cross-referencing
# Log completion
```

## Testing Framework

### Test Organization

- **Unit Tests**: Individual function/method validation
- **Integration Tests**: Cross-module interaction validation
- **Theoretical Tests**: Mathematical correctness validation
- **Validation Tests**: Framework compliance checking

### Coverage Requirements

- **Project Code**: 95%+ coverage target
- **Utilities**: Local utilities with basic functionality
- **No Mocks Policy**: All tests use real data and computations
- **Theoretical Validation**: Mathematics correctness verification

### Test Categories (~17 test files)

- `test_active_inference.py`: Core EFE and policy selection
- `test_free_energy_principle.py`: FEP calculations and system boundaries
- `test_quadrant_framework.py`: Matrix framework and transitions
- `test_generative_models.py`: Matrix operations and modeler specifications
- `test_meta_cognition.py`: Confidence assessment and adaptation
- `test_modeler_perspective.py`: Framework specification and synthesis
- `test_cognitive_security.py`: Attack surface, drift simulation, anomaly detection
- `test_data_generator.py`: Data generation correctness and reproducibility
- `test_statistical_analysis.py`: Statistical methods and hypothesis testing
- `test_validation.py`: Validation framework self-checks
- `test_visualization.py`: Figure generation and saving

## Manuscript Structure

### Section Organization

- **01**: Abstract with keywords and MSC codes
- **02**: Introduction (motivation, contributions, paper organization)
- **03**: Related Work (5 research traditions surveyed)
- **04**: Background and Theoretical Foundations (FEP, EFE, generative models, meta-aspects)
- **05**: Methodology (theoretical approach, computational validation)
- **06**: The 2x2 Quadrant Model (Q1-Q4 with formulations and demonstrations)
- **07**: Security Implications (threat model, cognitive security, AI safety, ethics)
- **08**: Discussion (contributions, limitations, future directions)
- **09**: Conclusion (summary, key insights, closing perspective)
- **10**: Acknowledgments
- **11**: Appendix (mathematical derivations, algorithms, benchmarks)
- **98**: Symbols and Notation glossary
- **99**: References (52 BibTeX entries)

### Cross-Reference System

- `\\ref{sec:methodology}`: Section references
- `\\ref{fig:quadrant_matrix}`: Figure references
- `\\eqref{eq:efe}`: Equation references
- `\\cite{friston2010free}`: Citation references

### Rendering Pipeline

1. **Markdown Combination**: Individual sections merged into single document
2. **Cross-Reference Resolution**: All references validated and linked
3. **LaTeX Generation**: Mathematical notation and formatting applied
4. **Figure Integration**: Registered figures embedded with captions
5. **Bibliography Processing**: Citations formatted and linked
6. **PDF Rendering**: Final document generation with validation

## Quality Assurance

### Validation Checks

- **Theoretical Correctness**: Mathematical derivations validated
- **Numerical Stability**: Edge cases and numerical issues detected
- **Cross-Reference Integrity**: All references resolve correctly
- **Figure Registration**: All figures properly linked and captioned
- **Code Quality**: Type hints, docstrings, and style compliance

### Performance Benchmarks

- **Runtime**: EFE calculation < 50ms for typical models
- **Memory**: < 10MB for analysis pipeline
- **Scalability**: Handles models up to 1000+ states
- **Accuracy**: 99%+ theoretical correctness on validation suite

## Extension Points

### Adding New Quadrants

1. Extend `QuadrantFramework` class with new quadrant definitions
2. Add transition logic in `demonstrate_quadrant_transitions()`
3. Create corresponding visualization methods
4. Update manuscript sections with new analysis

### Integrating New Theories

1. Create module in `src/` following established patterns
2. Add tests with 90%+ coverage
3. Integrate with existing visualization framework
4. Update manuscript with theoretical integration

### Scaling Improvements

1. Implement sparse matrix representations for large models
2. Add parallel computation for ensemble methods
3. Develop hierarchical optimization for meta-level processing
4. Create approximate inference algorithms for complex systems

## Dependencies

### Core Dependencies

- **numpy**: Numerical computations and matrix operations
- **scipy**: Statistical functions and optimization
- **matplotlib**: Visualization and plotting
- **pytest**: Testing framework with coverage reporting

### Local Dependencies

- **utils.logging**: Simple logging utilities
- **utils.exceptions**: Basic exception handling
- **utils.figure_manager**: Figure registration and management
- **utils.markdown_integration**: Basic markdown integration

## Development Workflow

### Adding Features

1. Implement in appropriate `src/` module with type hints and docstrings
2. Add tests achieving 90%+ coverage
3. Update visualization scripts if needed
4. Integrate with analysis pipeline
5. Update manuscript and documentation
6. Validate system functionality

### Code Quality Standards

- **Type Hints**: All public APIs must have type annotations
- **Documentation**: Google-style docstrings with theoretical context
- **Testing**: test suite with data (no mocks)
- **Style**: Black formatting with 88-character line limits
- **Imports**: Absolute imports with proper module organization

### Validation Pipeline

1. **Unit Tests**: Individual component validation
2. **Integration Tests**: Cross-module interaction verification
3. **Theoretical Validation**: Mathematical correctness checking
4. **Performance Testing**: Runtime and memory benchmarking
5. **Rendering Validation**: manuscript processing verification

## Troubleshooting

### Common Import Issues

**Subpackage imports fail**: If `from src.core.active_inference import ...` fails, ensure that `__init__.py` files exist in `src/`, `src/core/`, `src/framework/`, `src/analysis/`, and `src/visualization/`. The flat import path (`from src.active_inference import ...`) may still work via re-exports.

**`utils` not found**: The `utils/` package must be on the Python path. When running from the project root, set `PYTHONPATH=.` or use `uv run` which handles paths automatically.

**`ModuleNotFoundError` for scipy**: Install with `uv sync` or `pip install scipy>=1.10.0`. The `statistical_analysis.py` module requires scipy for hypothesis testing.

### Common Test Issues

**Coverage below threshold**: The project targets 95%+ coverage. If tests fail the coverage gate, check for untested branches in newly added code. Run `uv run pytest tests/ --cov=src --cov-report=term-missing` to see uncovered lines.

**Matplotlib backend errors**: Set `MPLBACKEND=Agg` for headless environments. This is handled automatically by the pipeline but may need manual setting in CI or SSH sessions.

**Numerical tolerance failures**: Some tests validate floating-point properties (probability sums, entropy bounds). If tests fail with small numerical discrepancies, check that numpy version is >= 1.24 and that no global numpy settings have been modified.

## Documentation

Detailed documentation is available in the `doc/` directory:

- `doc/architecture.md` -- System architecture, module dependencies, data flow
- `doc/api_reference.md` -- Comprehensive API reference with signatures and examples
- `doc/theoretical_primer.md` -- Accessible introduction to Active Inference theory
- `doc/quickstart.md` -- 5-minute getting-started guide

This framework provides a solid foundation for implementing, validating, and extending Active Inference as a meta-(pragmatic/epistemic) methodology, with rigorous theoretical foundations and practical implementation quality.
