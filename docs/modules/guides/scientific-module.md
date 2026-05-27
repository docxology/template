# Scientific Development Module

> **Scientific computing best practices and tools**

**Location:** `infrastructure/scientific/` (modular package)
**Quick Reference:** [Modules Guide](../modules-guide.md) | [API Reference](../../reference/api-reference.md)

---

## Key Features

- **Numerical Stability**: Algorithm stability testing and validation
- **Performance Benchmarking**: Execution time and memory analysis
- **Scientific Documentation**: API documentation generation
- **Best Practices Validation**: Code quality assessment
- **Research Workflow Templates**: Reproducible experiment templates

---

## Usage Examples

### Numerical Stability Testing

```python
from infrastructure.scientific import check_numerical_stability

# Test function stability across input ranges
def my_algorithm(x):
    return x**2 / (x + 1e-10)  # Potential numerical issues

stability_report = check_numerical_stability(
    my_algorithm,
    test_inputs=[0.0, 1e-8, 1e-6, 0.1, 1.0, 10.0],
    tolerance=1e-12
)

print(f"Stability Score: {stability_report.stability_score:.2f}")
print(f"Input Range: {stability_report.input_range}")

if stability_report.recommendations:
    print("Recommendations:")
    for rec in stability_report.recommendations:
        print(f"- {rec}")
```

### Performance Benchmarking

```python
from infrastructure.scientific import benchmark_function

# Benchmark algorithm performance
result = benchmark_function(
    my_algorithm,
    test_inputs=[0.1, 1.0, 10.0, 100.0],
    iterations=100
)

print(f"Function: {result.function_name}")
print(f"Average Execution Time: {result.execution_time:.6f}s")
print(f"Memory Usage: {result.memory_usage or 'Not measured'} MB")
```

---

## Programmatic API

The scientific module is used as a Python library — it ships no standalone CLI. Import the helpers directly:

```python
from infrastructure.scientific import (
    benchmark_function,
    check_numerical_stability,
    validate_scientific_implementation,
)
```

See the examples above and [`infrastructure/scientific/SKILL.md`](../../../infrastructure/scientific/SKILL.md) for the full exported surface.

---

**Related:** [LLM Module](llm-module.md) | [Modules Guide](../modules-guide.md)
