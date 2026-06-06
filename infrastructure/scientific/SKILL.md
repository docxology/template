---
name: infrastructure-scientific
description: Skill for the scientific infrastructure module providing numerical stability checks, performance benchmarking, scientific documentation generation, implementation validation, and module/workflow templates. Use when benchmarking functions, checking numerical stability, validating scientific implementations, or creating scientific module scaffolds.
---

# Scientific Module

Scientific computing utilities for research software development.

## Numerical Stability (`stability.py`)

```python
from infrastructure.scientific import check_numerical_stability, StabilityTest

# Check numerical stability of a function over a range of inputs
test = check_numerical_stability(
    func=my_computation,
    test_inputs=[0.0, 1e-6, 1.0, 1e10, float("nan"), float("inf")],
    tolerance=1e-12,
)

# Inspect results
print(test.function_name, test.stability_score, test.actual_behavior)
print(test.recommendations)
```

## Benchmarking (`benchmarking.py`)

```python
from infrastructure.scientific import (
    benchmark_function,
    BenchmarkResult,
    format_benchmark_report,
    generate_performance_report,
)

# Benchmark a function across multiple inputs
result = benchmark_function(
    func=my_algorithm,
    test_inputs=[10, 100, 1000],
    iterations=100,
)

# Inspect results
print(result.function_name, result.execution_time, result.memory_usage)
print(result.iterations, result.result_summary, result.timestamp)

# Generate Markdown reports
md_report = format_benchmark_report([result])
perf_report = generate_performance_report([result])
```

## Improvement Confirmation (`confirmation.py`)

```python
from infrastructure.scientific import confirm_improvement, Confirmation

# Confirm a candidate beats a baseline metric beyond the noise band
result = confirm_improvement(
    evaluate=my_evaluator,        # (params, seed) -> metric
    candidate=(0.1, 0.2),
    baseline_metric=1.0,
    seeds=[0, 1, 2, 3],
    noise_scale=0.05,
    sigma=2.0,                     # noise band width in standard errors of the mean
)

# Inspect the Confirmation dataclass
print(result.candidate_mean, result.baseline_metric, result.delta)
print(result.noise_band, result.confirmed)
```

## Scientific Documentation (`documentation.py`)

```python
from infrastructure.scientific import generate_scientific_documentation, generate_api_documentation

# Generate scientific documentation for a function
docs = generate_scientific_documentation(my_func)

# Generate API documentation for a module
api_docs = generate_api_documentation(my_module)
```

## Implementation Validation (`validation.py`)

```python
from infrastructure.scientific import (
    validate_scientific_implementation,
    validate_scientific_best_practices,
    check_research_compliance,
)

# Validate implementation against scientific standards
issues = validate_scientific_implementation(my_func, [(input_1, expected_1), (input_2, expected_2)])

# Check best practices
bp_issues = validate_scientific_best_practices(my_module)

# Check research compliance
compliance = check_research_compliance(my_func)
```

## Templates (`templates.py`)

Generate scaffolding for new scientific modules and workflows:

```python
from infrastructure.scientific import (
    create_scientific_module_template,
    create_scientific_test_suite,
    create_scientific_workflow_template,
)

# Create a new scientific module (returns the template source as a string)
module_src = create_scientific_module_template("signal_processing")

# Create matching test suite
test_src = create_scientific_test_suite("signal_processing")

# Create a workflow template
workflow_src = create_scientific_workflow_template("spectral_analysis")
```
