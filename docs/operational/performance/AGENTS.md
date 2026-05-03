# Performance Documentation

## Overview

Technical guide for `docs/operational/performance/` — benchmarking standards, profiling tooling, and performance optimization guidance.

## Files

| File | Purpose |
|------|---------|
| `benchmarking-guide.md` | Standards for measuring, reporting, and optimizing performance |

## Key Conventions

- Use `monitor_performance` decorator or `CodeProfiler` class from `infrastructure.core.runtime.function_profiler` for function-level profiling.
- Benchmark when adding computational functionality, changing algorithmic complexity, or observing slowdowns.
- Performance results should be reproducible — use deterministic seeds and fixed input sizes.

## See Also

- [README.md](README.md) — Quick navigation
- [../config/performance-optimization.md](../config/performance-optimization.md) — Performance tuning guidance
- [../config/AGENTS.md](../config/AGENTS.md) — Configuration & performance docs
