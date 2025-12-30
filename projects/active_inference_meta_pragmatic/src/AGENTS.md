# Source Code Directory Documentation

## Overview

This directory contains the core implementation of the Active Inference meta-pragmatic framework. All modules follow the Research Project Template standards with comprehensive type hints, docstrings, error handling, and testing.

## Module Architecture

### Core Principle: Thin Orchestrator Pattern
- **Business Logic**: All computational logic resides in `src/` modules
- **Script Role**: `scripts/` directory contains thin orchestrators that import from `src/` and handle I/O
- **No Business Logic in Scripts**: Scripts only coordinate workflows and manage data flow

### Design Patterns
- **Type Hints**: All public APIs have complete type annotations
- **Google Docstrings**: Comprehensive documentation with examples
- **Error Handling**: Custom exceptions with informative messages
- **Logging**: Structured logging using `get_logger(__name__)`
- **Pure Functions**: Functional programming where appropriate
- **Class-Based Design**: Object-oriented architecture for complex systems

## Module Index

### `active_inference.py` - Core Active Inference Framework
**Purpose**: Implements Expected Free Energy calculations, policy selection, and perception as inference

**Key Components**:
- `ActiveInferenceFramework`: Main framework class with generative model integration
- `calculate_expected_free_energy()`: EFE computation with epistemic/pragmatic decomposition
- `select_optimal_policy()`: Policy optimization via EFE minimization
- `perception_as_inference()`: Bayesian perception implementation
- `demonstrate_active_inference_concepts()`: Conceptual demonstrations

**Validation**: Theoretical correctness against EFE mathematics, numerical stability

### `free_energy_principle.py` - Free Energy Principle Implementation
**Purpose**: Implements FEP concepts for system boundary analysis and structure preservation

**Key Components**:
- `FreeEnergyPrinciple`: FEP framework with system state modeling
- `calculate_free_energy()`: Variational free energy computation
- `define_system_boundary()`: Markov blanket identification
- `demonstrate_structure_preservation()`: Long-term system organization dynamics
- `define_what_is_a_thing()`: Philosophical analysis of system definitions

**Validation**: Free energy minimization trajectories, system boundary correctness

### `quadrant_framework.py` - 2×2 Matrix Framework
**Purpose**: Implements the systematic 2×2 matrix for cognitive process analysis

**Key Components**:
- `QuadrantFramework`: Framework management and quadrant definitions
- `analyze_processing_level()`: Data/cognitive level assessment
- `demonstrate_quadrant_transitions()`: Developmental and situational transitions
- `create_quadrant_matrix_visualization()`: Figure data generation
- `demonstrate_quadrant_framework()`: Complete framework demonstration

**Validation**: Quadrant consistency, transition logic, processing level assessment

### `generative_models.py` - Generative Model Mathematics
**Purpose**: Implements probabilistic generative models with A, B, C, D matrix operations

**Key Components**:
- `GenerativeModel`: Complete generative model with matrix validation
- `predict_observations()`: Forward prediction P(o|s)
- `predict_state_transition()`: Transition prediction P(s'|s,a)
- `perform_inference()`: Bayesian inference P(s|o)
- `demonstrate_generative_model_concepts()`: Conceptual demonstrations
- `demonstrate_modeler_specifications()`: Meta-level specification analysis

**Validation**: Matrix compatibility, probabilistic correctness, modeler specification power

### `meta_cognition.py` - Meta-Cognitive Processing
**Purpose**: Implements meta-cognitive monitoring, confidence assessment, and adaptive control

**Key Components**:
- `MetaCognitiveSystem`: Meta-cognitive monitoring and control system
- `assess_inference_confidence()`: Confidence evaluation with entropy analysis
- `adjust_attention_allocation()`: Adaptive resource allocation based on confidence
- `implement_meta_cognitive_control()`: Higher-level cognitive control
- `evaluate_strategy_effectiveness()`: Strategy performance assessment
- `demonstrate_meta_cognitive_processes()`: Process demonstrations
- `demonstrate_thinking_about_thinking()`: Conceptual demonstrations

**Validation**: Confidence calculation accuracy, adaptation stability, meta-level control

### `modeler_perspective.py` - Modeler Dual Role Analysis
**Purpose**: Implements the dual role of modeler as architect and subject in Active Inference

**Key Components**:
- `ModelerPerspective`: Framework specification and self-reflection management
- `specify_epistemic_framework()`: Epistemic boundary definition
- `specify_pragmatic_framework()`: Pragmatic landscape specification
- `analyze_self_reflective_modeling()`: Recursive self-modeling analysis
- `demonstrate_meta_epistemic_modeling()`: Epistemic specification demonstrations
- `demonstrate_meta_pragmatic_modeling()`: Pragmatic specification demonstrations
- `synthesize_meta_theoretical_perspective()`: Complete meta-theory synthesis

**Validation**: Framework consistency, recursive logic, meta-theoretical coherence

### `visualization.py` - Visualization Engine
**Purpose**: Provides publication-quality visualization capabilities for complex concepts

**Key Components**:
- `VisualizationEngine`: Enhanced visualization with consistent styling
- `create_figure()`: Standardized figure creation with proper formatting
- `create_quadrant_matrix_plot()`: 2×2 matrix visualization
- `create_generative_model_diagram()`: Generative model structure diagrams
- `create_fep_visualization()`: Free Energy Principle illustrations
- `save_figure()`: Multi-format figure saving with registration

**Validation**: Visual correctness, publication quality, figure registration

### `data_generator.py` - Synthetic Data Generation
**Purpose**: Provides controlled synthetic data for demonstrations and testing

**Key Components**:
- `DataGenerator`: Configurable data generation with reproducibility
- `generate_time_series()`: Time series with various trend patterns
- `generate_categorical_observations()`: Categorical data with different distributions
- `generate_state_sequences()`: Hidden state sequences for testing
- `create_synthetic_dataset()`: Classification datasets for validation

**Validation**: Statistical properties, reproducibility, distribution correctness

### `statistics.py` - Statistical Analysis Toolkit
**Purpose**: Comprehensive statistical analysis for algorithm evaluation and validation

**Key Components**:
- `StatisticalAnalyzer`: Full statistical analysis suite
- `calculate_descriptive_stats()`: Comprehensive descriptive statistics
- `calculate_correlation()`: Correlation analysis with multiple methods
- `calculate_confidence_interval()`: Confidence interval computation
- `perform_t_test()`: Hypothesis testing between groups
- `analyze_algorithm_performance()`: Comparative algorithm evaluation

**Validation**: Statistical correctness, effect size calculations, hypothesis testing validity

### `validation.py` - Validation Framework
**Purpose**: Theoretical and numerical validation of implementations

**Key Components**:
- `ValidationFramework`: Comprehensive validation suite
- `validate_probability_distribution()`: Distribution validation
- `validate_generative_model()`: Model structure validation
- `validate_theoretical_correctness()`: Theoretical validation
- `validate_algorithm_performance()`: Performance validation
- `create_validation_report()`: Comprehensive reporting

**Validation**: Validation framework self-consistency, error detection accuracy

## Code Quality Standards

### Type Annotations
```python
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
from numpy.typing import NDArray

def process_data(data: NDArray, threshold: float = 0.5) -> Tuple[NDArray, Dict[str, float]]:
    """Process data with comprehensive type hints."""
```

### Documentation Standards
```python
def calculate_expected_free_energy(
    self,
    posterior_beliefs: NDArray,
    policy: NDArray,
    observations: Optional[NDArray] = None
) -> Tuple[float, Dict[str, float]]:
    """Calculate Expected Free Energy for policy evaluation.

    Computes the Expected Free Energy (EFE) combining epistemic and pragmatic
    components according to Active Inference theory.

    Args:
        posterior_beliefs: Current posterior beliefs over hidden states
        policy: Action policy sequence
        observations: Optional current observations for context

    Returns:
        Tuple of (total_EFE, component_dict) where component_dict contains:
        - 'epistemic': Epistemic affordance component
        - 'pragmatic': Pragmatic value component
        - 'total': Total EFE value

    Raises:
        ValidationError: If inputs are malformed or incompatible

    Examples:
        >>> framework = ActiveInferenceFramework(model)
        >>> efe, components = framework.calculate_expected_free_energy(
        ...     posterior_beliefs, policy
        ... )
        >>> print(f"EFE: {efe:.3f}")
    """
```

### Error Handling
```python
try:
    # Core logic
    result = self._perform_calculation(inputs)
except Exception as e:
    logger.error(f"Error in {operation_name}: {e}")
    raise ValidationError(f"{operation_name} failed: {e}") from e
```

### Logging Integration
```python
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

def operation():
    logger.debug("Starting operation with parameters: %s", parameters)
    # Operation logic
    logger.info("Operation completed successfully")
    return result
```

## Testing Integration

### Test Coverage Requirements
- **Public APIs**: 100% coverage of all public methods
- **Error Paths**: Coverage of exception handling
- **Edge Cases**: Boundary condition testing
- **Integration**: Cross-module interaction testing

### Test Structure
```python
class TestModuleName:
    def test_public_method(self):
        """Test public method functionality."""
        # Setup
        instance = ModuleClass()

        # Execute
        result = instance.public_method(args)

        # Validate
        assert result == expected
        assert isinstance(result, ExpectedType)

    def test_error_conditions(self):
        """Test error handling."""
        instance = ModuleClass()

        with pytest.raises(ValidationError):
            instance.public_method(invalid_args)

    def test_edge_cases(self):
        """Test boundary conditions."""
        # Test with extreme values, empty inputs, etc.
```

## Performance Characteristics

### Computational Complexity
- **EFE Calculation**: O(n_states × n_actions × horizon)
- **Inference**: O(n_states × n_observations)
- **Meta-Cognitive Assessment**: O(n_beliefs)
- **Framework Optimization**: O(iterations × parameters)

### Memory Usage
- **Base Models**: O(n_states × n_observations)
- **Meta-Cognitive State**: O(history_length × n_beliefs)
- **Visualization**: O(figure_complexity)
- **Statistical Analysis**: O(dataset_size)

### Optimization Strategies
- **Sparse Representations**: For large state spaces
- **Batch Processing**: For multiple evaluations
- **Approximate Methods**: For complex optimization
- **Caching**: For repeated computations

## Extension Guidelines

### Adding New Modules
1. Follow established patterns (type hints, docstrings, logging, error handling)
2. Create comprehensive tests achieving 90%+ coverage
3. Add to validation framework if applicable
4. Update visualization capabilities if needed
5. Integrate with existing analysis pipeline

### Modifying Existing Modules
1. Maintain backward compatibility
2. Update all dependent tests
3. Update documentation and docstrings
4. Validate performance impact
5. Update cross-references in manuscript

### Integration with Infrastructure
1. Use provided logging utilities
2. Leverage validation framework
3. Register figures with figure manager
4. Follow rendering pipeline requirements
5. Maintain separation of concerns

This source code directory provides a solid, well-tested foundation for implementing and extending the Active Inference meta-pragmatic framework, with rigorous attention to code quality, theoretical correctness, and practical usability.