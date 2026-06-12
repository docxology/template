---
name: infrastructure-scientific
description: Skill for the scientific infrastructure module providing numerical stability checks, performance benchmarking, and independent improvement confirmation. Use when benchmarking functions, checking numerical stability, or confirming a candidate beats a baseline beyond the noise band.
---

# Scientific Module

Scientific computing utilities for research software development.

> **Tier: exemplar-support.** Layer-1 by location, imported only by its
> scientific exemplar(s) — not generic-reach across `infrastructure/`.

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
