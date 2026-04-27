# Performance Benchmarking Guide

**Purpose:** Establish standards for measuring, reporting, and optimizing performance in the Research Project Template.

**Audience:** Developers optimizing infrastructure modules, project algorithms, and pipeline execution.

---

## 1. When to Benchmark

Benchmark when:

- Adding new computational functionality to `infrastructure/` or `projects/*/src/`
- Changing algorithmic complexity (e.g., O(n²) → O(n log n))
- Modifying I/O patterns or data processing
- Observing slowdowns in pipeline stage execution
- Comparing alternative implementations

---

## 2. Tooling

### Built-in Profiling

**Function-level:** Use `@profile` decorator from `infrastructure.core.runtime.function_profiler`

```python
from infrastructure.core.runtime.function_profiler import profile

@profile
def compute_expensive_operation(data: np.ndarray) -> Result:
    # This function's time and memory will be tracked
    return heavy_computation(data)
```

Profile results appear in pipeline telemetry and can be aggregated.

---

### Python `cProfile`

For deeper analysis:

```bash
uv run python -m cProfile -o profile.out scripts/02_run_analysis.py --project code_project
uv run python -m pstats profile.out
```

Or use `snakeviz` for visualization:

```bash
uv run python scripts/02_run_analysis.py --profile
snakeviz profile.prof
```

---

### Memory Profiling

Use `memray` (optional) for memory allocation tracking:

```bash
uv run memray run -o memray.bin scripts/02_run_analysis.py --project code_project
uv run memray flamegraph memray.bin
```

---

### Timing with `time`

Simple wall-clock timing for quick checks:

```python
import time

start = time.perf_counter()
result = compute()
elapsed = time.perf_counter() - start
logger.info(f"Computation took {elapsed:.3f}s")
```

---

## 3. Benchmark Structure

Place benchmarks in `tests/benchmarks/` or use `pytest-benchmark` for regression testing.

### Example Benchmark Test

```python
# tests/benchmarks/test_optimizer_performance.py
import pytest
import time
from src.optimizer import gradient_descent

def test_gradient_descent_performance(benchmark):
    """Benchmark gradient descent convergence speed."""
    result = benchmark(
        gradient_descent,
        initial_point=np.array([5.0, 5.0]),
        objective_func=quadratic_function,
        gradient_func=compute_gradient,
        step_size=0.1,
        tolerance=1e-6
    )
    assert result.converged
```

Run with:

```bash
uv run pytest tests/benchmarks/ --benchmark-only
```

---

## 4. Reporting Metrics

Infrastructure automatically tracks:

- **Stage duration** (wall time)
- **Peak memory** (RSS if psutil available)
- **CPU usage** (% if psutil available)
- **Function hotspots** (decorated with `@profile`)

Metrics appear in:

- `projects/<name>/output/reports/telemetry.json`
- Multi-project executive summary (`output/multi_project_summary/`)

---

## 5. Performance Standards

| Component | Threshold | Monitoring |
|-----------|-----------|------------|
| Infrastructure stage (avg) | <30s | Telemetry stage duration |
| Project analysis script | <2min | Manual timing |
| Memory growth | <100MB increase per 1k data points | psutil or memray |
| Test suite total | <5min (infra), <10min (project) | `pytest --durations=10` |

**Slow Stage Detection:** Pipeline automatically warns if a stage exceeds `slow_stage_multiplier` × median duration (configurable in `pipeline.yaml` telemetry section).

---

## 6. Optimization Checklist

- [ ] Profile before optimizing — identify actual bottleneck
- [ ] Use vectorized NumPy operations, not Python loops
- [ ] Cache expensive lookups with `@lru_cache`
- [ ] Batch I/O operations (read/write in chunks)
- [ ] Avoid redundant recomputation (store intermediate results)
- [ ] Use appropriate data structures (dict vs list vs set)
- [ ] For large datasets, consider memory-mapped files (`np.memmap`)
- [ ] Parallelize independent work with `concurrent.futures` or `multiprocessing`
- [ ] Move heavy work to `src/`, keep `scripts/` thin

---

## 7. Regression Detection

Add benchmark tests to CI to catch performance regressions:

```yaml
# .github/workflows/benchmark.yml
- name: Run benchmarks
  run: |
    uv run pytest tests/benchmarks/ --benchmark-save=baseline
- name: Compare to baseline
  run: |
    uv run pytest tests/benchmarks/ --benchmark-compare=baseline --benchmark-compare-fail=mean:10%
```

---

## 8. Pipeline Bottleneck Analysis

When pipeline slows down:

1. Check `output/<project>/reports/telemetry.json` for slowest stages
2. Enable verbose logging: `LOG_LEVEL=DEBUG ./run.sh --pipeline`
3. Profile stage script directly: `uv run python -m cProfile -o stage.prof scripts/02_run_analysis.py`
4. Look for I/O blocking, large data serialization, or unnecessary re-reads

---

## 9. Memory Leak Detection

Use `tracemalloc` or `memray` to detect growing allocations:

```bash
uv run python -X tracemalloc=25 scripts/02_run_analysis.py --project code_project
# Or with memray as above
```

Compare snapshots before/after to find accumulating objects.

---

## 10. Distributed/Parallel Considerations

If scaling beyond one machine:

- Use `pytest-xdist` for parallel test execution (`uv run pytest -n auto`)
- Infrastructure already supports parallel figure generation via `ProcessPoolExecutor`
- For large data, consider Dask or Ray (add to dependencies)

---

## 11. Documentation Changes

When performance characteristics change:

- Update docstrings with complexity notes (e.g., "O(n log n) sorting")
- Revise README.md benchmarks section if applicable
- Add performance regression notes to CHANGELOG.md

---

## 12. Continuous Monitoring

For long-running servers or repeated executions, consider:

- Exporting telemetry to Grafana/Prometheus (future enhancement)
- Logging stage durations to CSV for trend analysis
- Setting alerts on memory thresholds

---

*Keep this guide updated as performance tools evolve.*
