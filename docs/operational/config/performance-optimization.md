# Performance Optimization Guide

This guide provides strategies for optimizing pipeline performance and identifying bottlenecks.

## Performance Metrics

The pipeline tracks performance metrics for each stage:

- **Stage Duration**: Time taken for each stage
- **Total Duration**: pipeline execution time
- **Bottleneck Identification**: Automatic detection of slowest stages
- **ETA Calculations**: Estimated time remaining during execution

## Viewing Performance Metrics

### Pipeline Summary

After pipeline completion, a summary is displayed:

```
Performance Metrics:
  Total Execution Time: 2m 15s
  Average Stage Time: 22.5s
  Slowest Stage: Stage 5 - PDF Rendering (45s, 33%)
  Fastest Stage: Stage 2 - Project Tests (5s)
```

### Stage-Level Metrics

Each stage reports:
- Execution time
- Percentage of total time
- Bottleneck warnings (flagged when a stage exceeds 10s; the percentage is reported for context)

## Identifying Bottlenecks

### Automatic Detection

The pipeline automatically identifies bottlenecks:
- Stages taking >10 seconds
- Stages consuming >20% of total time
- Marked with ⚠ bottleneck indicator

### Manual Analysis

```bash
# Run pipeline with timing
time ./run.sh --pipeline

# Check individual stage times
uv run python scripts/pipeline/stage_00_setup.py --project templates/template_code_project
time uv run python scripts/pipeline/stage_01_test.py --project templates/template_code_project
time uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_code_project
```

## Optimization Strategies

### 1. Test Execution

**Bottleneck**: Test execution can be slow with large test suites

**Optimizations**:
- Use pytest-xdist for parallel test execution
- Skip slow tests during development
- Use pytest caching for faster repeated runs

```bash
# Parallel test execution
uv run pytest tests/ -n auto

# Skip slow tests
uv run pytest tests/ -m "not slow"
```

### 1a. Fast local test loop (agent iteration)

For tight agent edit/test loops, run a fixed high-signal subset instead of the
whole suite. The full infrastructure gate
(`scripts/pipeline/stage_01_test.py --infra-only --infra-scope full`) remains
the merge authority; the fast loop is only for iteration speed and is
negative-control-protected by
`tests/infra_tests/git_hook_smoke/test_fast_loop_selector.py`, which fails when
a fast-loop entry is deleted, renamed, or stops collecting tests.

```bash
# Highest-signal subset; -p no:cacheprovider avoids cache writes on slow disks
uv run --frozen pytest \
  tests/infra_tests/git_hook_smoke \
  tests/infra_tests/core/test_pytest_orchestration.py \
  tests/infra_tests/core/test_pipeline.py \
  -q -p no:cacheprovider
```

Measured cost drivers on a slow external-drive checkout (2026-09-14, macOS
ARM, repo on an external HDD/SSD-grade volume):

| Cost | Measured | Note |
| ---- | -------- | ---- |
| `uv run python -m infrastructure.validation.cli --help` (cold) | ~64 s | uv re-verifies the lockfile against the tree on every invocation |
| same with `uv run --frozen` | ~17 s | `--frozen` skips lock verification; use whenever the venv is already synced |
| full smoke lane on the same checkout | >2 min, subprocess tests hit pytest-timeout | dominated by per-CLI-test `uv run` subprocess cost and discovery globs over `projects/` |

Practical rules:

- **Prefer `uv run --frozen`** for test/CLI invocations once `uv sync` has run;
  it is the single largest per-subprocess win (measured ~4x on this checkout).
- **Batch CLI tests**: every test that spawns `uv run` pays the full uv
  resolution + interpreter + import cost; prefer in-process module imports for
  unit-level assertions and reserve subprocess smoke tests for real CLI paths.
- **Per-project suites stay per-project**: one pytest process per
  `projects/<name>/tests/` remains canonical (conftest plugin-name collisions);
  do not merge processes to save time.
- **pytest-xdist**: `resolve_xdist_args` already bounds inner parallelism and
  macOS full-coverage lanes stay at <=2 workers; the not-xdist-safe suites
  (notably `template_active_inference`) remain excluded from parallel lanes.
- **Hypothesis profiles**: set `HYPOTHESIS_PROFILE=fast` (registered in
  `tests/conftest.py`, max_examples=5, deadline=None) for smoke/agent loops;
  unset it for full-profile scheduled runs. Opt-in only; the variable costs
  nothing when absent.
- **Select by path, never by full-tree collection**: on a slow external-drive
  checkout, `pytest tests/infra_tests --collect-only` alone was measured I/O-bound
  at >15 minutes (near-zero CPU, blocked in scandir). Always point pytest at the
  specific file(s)/directory you changed; subset collection is seconds.
- **TMPDIR locality**: pytest `tmp_path` already lands on the OS temp dir
  (local SSD via `/var/folders` on macOS). Do not silently redirect the global
  `TMPDIR` for other consumers; if a checkout lives on a slow external drive,
  the dominant I/O cost is the repo tree itself (collection and git scans),
  which only a faster checkout location removes.

### 2. PDF Rendering

**Bottleneck**: LaTeX compilation is CPU-intensive

**Optimizations**:
- Use incremental compilation (only rebuild changed sections)
- Cache LaTeX intermediate files
- Use faster LaTeX engines (xelatex vs pdflatex)

```bash
# Check LaTeX compilation time
time xelatex document.tex

# Use incremental builds (if supported)
```

### 3. Analysis Scripts

**Bottleneck**: Data processing and figure generation

**Optimizations**:
- Parallelize independent analysis scripts
- Cache intermediate results
- Optimize data processing algorithms

```python
# Example: Parallel script execution
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor() as executor:
    results = executor.map(run_script, scripts)
```

### 4. LLM Review

**Bottleneck**: LLM generation is slow (minutes per review)

**Optimizations**:
- Use faster models for initial reviews
- Stream responses for progress visibility
- Cache review results
- Skip optional reviews during development

```bash
# Skip LLM reviews during development
./run.sh --pipeline  # LLM stages are optional

# Use faster model
export OLLAMA_MODEL="smollm2"  # Smaller, faster model
```

## Resource Monitoring

### Memory Usage

Monitor memory consumption:

```bash
# Check memory usage during pipeline
/usr/bin/time -v uv run python scripts/runner/execute_pipeline.py --project {name} --core-only

# Monitor continuously
watch -n 1 'ps aux | grep python'
```

### CPU Usage

Monitor CPU utilization:

```bash
# Check CPU usage
top -p $(pgrep -f "python3 scripts")

# Profile CPU-intensive operations
uv run python -m cProfile -o profile.stats scripts/pipeline/stage_03_render.py --project templates/template_code_project
```

### Disk I/O

Monitor file operations:

```bash
# Check disk I/O
iostat -x 1

# Monitor specific directory
watch -n 1 'du -sh projects/{name}/output/*'
```

## Performance Benchmarks

### Baseline Performance

Typical pipeline execution times:

- **Setup**: 1-2 seconds
- **Infrastructure Tests**: 30-60 seconds
- **Project Tests**: 2-5 seconds
- **Analysis**: 5-15 seconds
- **PDF Rendering**: 30-90 seconds
- **Validation**: 1-3 seconds
- **Copy Outputs**: 1-2 seconds
- **LLM Review**: 5-15 minutes (optional)

**Total (without LLM)**: ~2-3 minutes
**Total (with LLM)**: ~7-18 minutes

### Optimization Targets

- **Test Execution**: Reduce by 30-50% with parallel execution
- **PDF Rendering**: Reduce by 20-30% with incremental builds
- **Analysis**: Reduce by 40-60% with parallelization

## Profiling

### Python Profiling

```bash
# Profile entire pipeline
uv run python -m cProfile -o pipeline.prof scripts/runner/execute_pipeline.py --project {name} --core-only

# Analyze profile
uv run python -m pstats pipeline.prof
```

### Stage-Specific Profiling

```bash
# Profile specific stage
uv run python -m cProfile -o stage.prof scripts/pipeline/stage_03_render.py --project templates/template_code_project
```

### Memory Profiling

```bash
# Memory profiler
uv run python -m memory_profiler scripts/runner/execute_pipeline.py --project {name} --core-only
```

## Caching Strategies

### Test Results Caching

```bash
# Enable pytest cache
uv run pytest tests/ --cache-clear  # Clear cache
uv run pytest tests/  # Uses cache for faster runs
```

### Build Artifact Caching

- LaTeX intermediate files (`.aux`, `.bbl`) are cached
- Figure generation results cached in `projects/{name}/output/figures/`
- Re-run only if source files changed

### LLM Response Caching

- Review results saved to `projects/{name}/output/llm/`
- Re-use previous reviews if manuscript unchanged
- Clear cache: `rm -rf projects/{name}/output/llm/*`

## Parallel Execution

### Independent Stages

Some stages can run in parallel:

- **Tests**: Infrastructure and project tests (if independent)
- **Analysis Scripts**: Multiple scripts can run concurrently
- **PDF Sections**: Individual section PDFs can render in parallel

### Implementation

```python
# Example: Parallel stage execution
from concurrent.futures import ThreadPoolExecutor

stages = [stage1, stage2, stage3]  # Independent stages
with ThreadPoolExecutor(max_workers=3) as executor:
    results = executor.map(run_stage, stages)
```

**Note**: Parallel execution requires careful dependency management.

## Performance Monitoring

### Continuous Monitoring

```bash
# Monitor pipeline execution
watch -n 1 'ps aux | grep -E "(python|pytest|xelatex)"'
```

### Log Analysis

```bash
# Analyze pipeline logs for timing
grep "Completed in" projects/{name}/output/*.log | awk '{print $NF}'
```

## Best Practices

### Development Workflow

1. **Fast Iteration**: Skip slow stages during development
2. **Selective Execution**: Run only changed stages
3. **Caching**: Enable all caching mechanisms
4. **Parallel Tests**: Use pytest-xdist for test execution

### Production Workflow

1. **Full Pipeline**: Run pipeline for final builds
2. **Performance Baseline**: Establish performance benchmarks
3. **Monitoring**: Track performance over time
4. **Optimization**: Address bottlenecks systematically

## Troubleshooting Performance Issues

### Slow Test Execution

**Symptoms**: Tests take >60 seconds

**Solutions**:
- Enable parallel execution: `pytest -n auto`
- Skip slow tests: `pytest -m "not slow"`
- Optimize test data generation
- Use test fixtures for expensive setup

### Slow PDF Rendering

**Symptoms**: PDF rendering takes >90 seconds

**Solutions**:
- Check LaTeX installation and version
- Use incremental compilation
- Optimize figure sizes
- Reduce number of figures

### High Memory Usage

**Symptoms**: Pipeline runs out of memory

**Solutions**:
- Process data in chunks
- Clear large objects after use
- Use generators instead of lists
- Increase system memory

## See Also

- [`scripts/runner/execute_pipeline.py`](../../../scripts/runner/execute_pipeline.py) - Performance tracking implementation
- [`infrastructure/core/pipeline/stage_monitor.py`](../../../infrastructure/core/pipeline/stage_monitor.py) - Stage timing and progress tracking
- [`infrastructure/core/runtime/function_profiler.py`](../../../infrastructure/core/runtime/function_profiler.py) - Function-level profiling utilities
- [Troubleshooting](../troubleshooting/) - Performance troubleshooting
