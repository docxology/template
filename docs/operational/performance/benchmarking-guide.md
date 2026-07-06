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

**Function-level:** Use the `@monitor_performance(...)` decorator from `infrastructure.core.runtime.function_profiler`

```python
from infrastructure.core.runtime.function_profiler import monitor_performance

@monitor_performance("compute_expensive_operation")
def compute_expensive_operation(data: np.ndarray) -> Result:
    # This function's time and memory will be tracked
    return heavy_computation(data)
```

Profile results appear in pipeline telemetry and can be aggregated.

---

### Python `cProfile`

For deeper analysis:

```bash
uv run python -m cProfile -o profile.out scripts/pipeline/stage_02_analysis.py --project template_code_project
uv run python -m pstats profile.out
```

Or use `snakeviz` for visualization:

```bash
uv run python scripts/pipeline/stage_02_analysis.py --profile
snakeviz profile.prof
```

---

### Memory Profiling

Use `memray` (optional) for memory allocation tracking:

```bash
uv run memray run -o memray.bin scripts/pipeline/stage_02_analysis.py --project template_code_project
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

The repo's own microbenchmarks live in `tests/infra_tests/benchmark/` (see §12
for the exact convention: `@pytest.mark.bench`, `pytest-benchmark`, opt-in
only). Follow the same convention for new project-level benchmarks.

### Example Benchmark Test

```python
# tests/infra_tests/benchmark/test_optimizer_performance.py
import pytest
from src.optimizer import gradient_descent

@pytest.mark.bench
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
uv run pytest tests/infra_tests/benchmark/ -m bench --benchmark-only
```

---

## 4. Reporting Metrics

Infrastructure automatically tracks:

- **Stage duration** (wall time)
- **Peak memory** (RSS if psutil available)
- **CPU usage** (% if psutil available)
- **Function hotspots** (decorated with `@monitor_performance`)

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

The real CI integration is the `performance:` job in
[`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml) (there is no
separate `benchmark.yml`). Today it is **informational only, never blocking**:
a hard import-time threshold check (`MAX_IMPORT_SECONDS = 5.0`, fails the job
if exceeded) followed by the §12 microbench suite run with `|| true` and
uploaded as the `bench-results` artifact for manual trend comparison — there
is no `--benchmark-save`/`--benchmark-compare-fail` gate wired up yet. To add
a hard regression gate, extend that job with `pytest-benchmark`'s
`--benchmark-save=baseline` / `--benchmark-compare-fail=mean:10%` flags against
a committed baseline.

---

## 8. Pipeline Bottleneck Analysis

When pipeline slows down:

1. Check `output/<project>/reports/telemetry.json` for slowest stages
2. Enable verbose logging: `LOG_LEVEL=DEBUG ./run.sh --pipeline`
3. Profile stage script directly: `uv run python -m cProfile -o stage.prof scripts/pipeline/stage_02_analysis.py`
4. Look for I/O blocking, large data serialization, or unnecessary re-reads

---

## 9. Memory Leak Detection

Use `tracemalloc` or `memray` to detect growing allocations:

```bash
uv run python -X tracemalloc=25 scripts/pipeline/stage_02_analysis.py --project template_code_project
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

## 12. Project-setup-hook + analysis-pipeline benchmarks

**Location:** [`tests/infra_tests/benchmark/`](../../../tests/infra_tests/benchmark/)
**Marker:** `@pytest.mark.bench` — skipped by default; opt-in only.
**Driver:** `pytest-benchmark` ≥ 5 (declared in `pyproject.toml#[dependency-groups].dev`).
**Policy:** Zero-mocks. Real `tmp_path` filesystems, real subprocesses, real `pytest-benchmark` fixtures.

### Invocation

```bash
uv run pytest tests/infra_tests/benchmark/ -m bench --benchmark-only \
    --benchmark-min-rounds=3 --benchmark-json=bench-results.json --timeout=180
```

CI (`.github/workflows/ci.yml#performance`) runs this step after the
import-timer check and uploads `bench-results.json` as the `bench-results`
artifact. The bench step is informational only (`|| true`); it cannot fail
the build.

### What each bench measures

| Bench | Subject | Operation |
| --- | --- | --- |
| A | `find_setup_hook` (no-hook miss) | `Path.is_file()` lookups on a hook-less project |
| B | `find_setup_hook` (Python-hook hit) | `Path.is_file()` resolving to `setup_hook.py` |
| C | `run_project_setup_hook` (no hook) | Pure no-op early return |
| D | `run_project_setup_hook` (trivial Python hook) | Real `subprocess.run` of an exit-0 hook |
| E1 | `run_analysis_pipeline` N=1 | One trivial script via real subprocess |
| E5 | `run_analysis_pipeline` N=5 | Five trivial scripts in sequence |
| E25 | `run_analysis_pipeline` N=25 | Twenty-five trivial scripts in sequence |

### Expected order of magnitude (macOS, Apple Silicon, Python 3.12)

| Bench | Median |
| --- | --- |
| `find_setup_hook` (hit) | ~8 µs |
| `find_setup_hook` (miss) | ~14 µs |
| `run_project_setup_hook` (no hook) | ~15 µs |
| `run_project_setup_hook` (trivial hook) | ~25 ms (interpreter startup) |
| `run_analysis_pipeline` N=1 | ~30 ms |
| `run_analysis_pipeline` N=5 | ~160 ms |
| `run_analysis_pipeline` N=25 | ~800 ms |

The setup-hook discovery functions sit comfortably in the µs regime —
they are not pipeline-startup bottlenecks. The cost of *running* a hook
or an analysis script is dominated by Python interpreter startup
(~25 ms per `python script.py` fork). Linux runners typically read 2–3×
slower for the subprocess-bound benches; the µs-regime discovery
benches are platform-insensitive within a small constant.

### When to look at the artifact

* PR introduces new work into `find_setup_hook` / `run_project_setup_hook` /
  `run_analysis_pipeline` / `build_analysis_script_cmd_and_env`.
* PR changes how analysis-script subprocesses are constructed
  (PYTHONPATH, env, cmd argv).
* You suspect a regression in pipeline startup time and want a
  before/after delta.

Compare medians across runs — `pytest-benchmark` writes the structured
JSON the artifact preserves; the CLI table prints µs / ms / s with
`Min / Max / Mean / StdDev / Median / IQR`.

---

## 13. Continuous Monitoring

For long-running servers or repeated executions, consider:

- Exporting telemetry to Grafana/Prometheus (future enhancement)
- Logging stage durations to CSV for trend analysis
- Setting alerts on memory thresholds

---

*Keep this guide updated as performance tools evolve.*
