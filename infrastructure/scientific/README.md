# Scientific Module - Quick Reference

Utilities for scientific computing and research software development.

## Quick Start

```python
from infrastructure.scientific import (
    check_numerical_stability,
    benchmark_function,
    validate_scientific_best_practices
)

# Check numerical stability
stability = check_numerical_stability(
    your_algorithm,
    [test_input_1, test_input_2]
)

# Benchmark performance
benchmark = benchmark_function(
    your_algorithm,
    [test_input_1, test_input_2],
    iterations=100
)

# Validate scientific implementation
report = validate_scientific_best_practices(your_module)
```

## Module Architecture

```mermaid
graph TD
    subgraph ScientificModule["infrastructure/scientific/"]
        STABILITY[stability.py<br/>Numerical stability<br/>check_numerical_stability()]
        BENCHMARKING[benchmarking.py<br/>Performance analysis<br/>benchmark_function()]
        DOCUMENTATION[documentation.py<br/>API documentation<br/>generate_scientific_documentation()]
        VALIDATION[validation.py<br/>Best practices<br/>validate_scientific_implementation()]
        TEMPLATES[templates.py<br/>Code templates<br/>create_scientific_module_template()]
    end

    subgraph CoreFeatures["Core Features"]
        NUMERICAL[Numerical Stability<br/>Algorithm robustness]
        PERFORMANCE[Performance Analysis<br/>Timing & memory tracking]
        DOC_GEN[Documentation Generation<br/>API docs from code]
        COMPLIANCE[Best Practices Validation<br/>Scientific standards]
        BOILERPLATE[Module Templates<br/>Research code patterns]
    end

    subgraph Usage["Usage Patterns"]
        ALGORITHM_DEV[Algorithm Development<br/>Stability testing]
        PERFORMANCE_OPT[Performance Optimization<br/>Benchmarking workflows]
        PACKAGE_DEV[Package Development<br/>Documentation generation]
        QUALITY_ASSURANCE[Quality Assurance<br/>Compliance checking]
        RAPID_PROTOTYPING[Rapid Prototyping<br/>Template-based development]
    end

    STABILITY --> NUMERICAL
    BENCHMARKING --> PERFORMANCE
    DOCUMENTATION --> DOC_GEN
    VALIDATION --> COMPLIANCE
    TEMPLATES --> BOILERPLATE

    NUMERICAL --> ALGORITHM_DEV
    PERFORMANCE --> PERFORMANCE_OPT
    DOC_GEN --> PACKAGE_DEV
    COMPLIANCE --> QUALITY_ASSURANCE
    BOILERPLATE --> RAPID_PROTOTYPING

    class STABILITY,BENCHMARKING,DOCUMENTATION,VALIDATION,TEMPLATES module
    class NUMERICAL,PERFORMANCE,DOC_GEN,COMPLIANCE,BOILERPLATE feature
    class ALGORITHM_DEV,PERFORMANCE_OPT,PACKAGE_DEV,QUALITY_ASSURANCE,RAPID_PROTOTYPING usage
```

## Modules

- **stability.py** - Numerical stability checking and algorithm robustness analysis
- **benchmarking.py** - Performance measurement and optimization analysis
- **documentation.py** - Scientific documentation generation from code
- **validation.py** - Best practices compliance and research standards validation
- **templates.py** - Research workflow and module boilerplate generation

## Key Functions

### Numerical Stability
- `check_numerical_stability()` - Test algorithm stability

### Performance Analysis
- `benchmark_function()` - Function performance measurement

### Documentation
- `generate_scientific_documentation()` - API documentation from docstrings

### Validation
- `validate_scientific_implementation()` - implementation check
- `validate_scientific_best_practices()` - Best practices compliance

## Usage Notes

The scientific module is a library module. Import functions from `infrastructure.scientific` or from the specific submodules (e.g. `infrastructure.scientific.benchmarking`) when you need narrower dependencies.

## Testing

```bash
pytest tests/infra_tests/test_scientific/
```

For detailed documentation, see [AGENTS.md](AGENTS.md).

