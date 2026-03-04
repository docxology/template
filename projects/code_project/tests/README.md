# tests/ - Zero-Mock Test Suite

An uncompromising validation layer for the mathematical algorithms. Enforces a strict Zero-Mock policy.

## Quick Start

```bash
# Run all tests
pytest .

# Run with coverage
pytest . --cov=../src --cov-report=term

# Run specific tests
pytest -k "TestGradientDescent" -v
```

## Key Features

- **Real data testing** (no mocks)
- **Numerical accuracy validation**
- **Edge case coverage**
- **Deterministic results**

## Common Commands

### Run Tests

```bash
pytest . -v              # Verbose output
pytest . -k "gradient"   # Filter by name
pytest . --tb=short      # Shorter tracebacks
```

### Coverage

```bash
pytest . --cov=../src --cov-report=html
open htmlcov/index.html
```

## Architecture

```mermaid
graph TD
    A[test_optimizer.py — 45 tests] --> B[TestQuadraticFunction]
    A --> C[TestComputeGradient]
    A --> D[TestGradientDescent]
    A --> E[TestOptimizationResult]
    A --> F[TestPerformanceBenchmarks]
    A --> G[TestStabilityAnalysis]
    A --> H[TestPerformanceBenchmarking]
    A --> I[TestAnalysisDashboard]
    A --> J[TestLoggingBranches]
    A --> K[TestImportFallback]

    B --> L[Function Evaluation]
    C --> M[Gradient Computation]
    D --> N[Optimization Algorithm]
    E --> O[Data Structures]
```

> **Zero-Mock Policy**: All 45 tests use real `OptimizationResult` instances and real computations. No `unittest.mock`, `MagicMock`, `@patch`, or synthetic `type()` objects.

## More Information

See [AGENTS.md](AGENTS.md) for technical documentation.
