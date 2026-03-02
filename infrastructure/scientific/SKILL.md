---
name: infrastructure-scientific
description: Skill for the scientific infrastructure module providing numerical stability checks, performance benchmarking, scientific documentation generation, implementation validation, and module/workflow templates. Use when benchmarking functions, checking numerical stability, validating scientific implementations, or creating scientific module scaffolds.
---

# Scientific Module

Scientific computing utilities for research software development.

## Numerical Stability (`stability.py`)

```python
from infrastructure.scientific import check_numerical_stability, StabilityTest

# Check numerical stability of a function
test = check_numerical_stability(
    func=my_computation,
    inputs=test_inputs,
    perturbation=1e-6,
)

# Inspect results
print(test.is_stable, test.max_deviation, test.condition_number)
```

## Benchmarking (`benchmarking.py`)

```python
from infrastructure.scientific import benchmark_function, BenchmarkResult, generate_performance_report

# Benchmark a function
result = benchmark_function(
    func=my_algorithm,
    args=(data,),
    iterations=100,
)

# Inspect results
print(result.mean_time, result.std_time, result.min_time, result.max_time)

# Generate performance report
report = generate_performance_report(results=[result])
```

## Scientific Documentation (`documentation.py`)

```python
from infrastructure.scientific import generate_scientific_documentation, generate_api_documentation

# Generate scientific documentation for a module
docs = generate_scientific_documentation(module_path)

# Generate API documentation
api_docs = generate_api_documentation(module_path)
```

## Implementation Validation (`validation.py`)

```python
from infrastructure.scientific import (
    validate_scientific_implementation,
    validate_scientific_best_practices,
    check_research_compliance,
)

# Validate implementation against scientific standards
issues = validate_scientific_implementation(source_dir)

# Check best practices
bp_issues = validate_scientific_best_practices(source_dir)

# Check research compliance
compliance = check_research_compliance(project_path)
```

## Templates (`templates.py`)

Generate scaffolding for new scientific modules and workflows:

```python
from infrastructure.scientific import (
    create_scientific_module_template,
    create_scientific_test_suite,
    create_scientific_workflow_template,
)

# Create a new scientific module
create_scientific_module_template(
    module_name="signal_processing",
    output_dir=project_src_dir,
)

# Create matching test suite
create_scientific_test_suite(
    module_name="signal_processing",
    output_dir=project_tests_dir,
)

# Create a workflow template
create_scientific_workflow_template(
    workflow_name="spectral_analysis",
    output_dir=project_scripts_dir,
)
```
