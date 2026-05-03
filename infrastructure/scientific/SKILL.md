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
