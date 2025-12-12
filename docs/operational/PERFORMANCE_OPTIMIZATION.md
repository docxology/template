# Performance Optimization Guide

This guide provides strategies for optimizing pipeline performance and identifying bottlenecks.

## Performance Metrics

The pipeline tracks performance metrics for each stage:

- **Stage Duration**: Time taken for each stage
- **Total Duration**: Complete pipeline execution time
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
- Bottleneck warnings (if >10s and >20% of total)

## Identifying Bottlenecks

### Automatic Detection

The pipeline automatically identifies bottlenecks:
- Stages taking >10 seconds
- Stages consuming >20% of total time
- Marked with ⚠ bottleneck indicator

### Manual Analysis

```bash
# Run pipeline with timing
time ./run_manuscript.sh --pipeline

# Check individual stage times
python3 scripts/00_setup_environment.py
time python3 scripts/01_run_tests.py
time python3 scripts/02_run_analysis.py
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
pytest tests/ -n auto

# Skip slow tests
pytest tests/ -m "not slow"
```

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
./run_manuscript.sh --pipeline  # LLM stages are optional

# Use faster model
export LLM_MODEL="llama3:8b"  # Smaller, faster model
```

## Resource Monitoring

### Memory Usage

Monitor memory consumption:

```bash
# Check memory usage during pipeline
/usr/bin/time -v python3 scripts/run_all.py

# Monitor continuously
watch -n 1 'ps aux | grep python'
```

### CPU Usage

Monitor CPU utilization:

```bash
# Check CPU usage
top -p $(pgrep -f "python3 scripts")

# Profile CPU-intensive operations
python3 -m cProfile -o profile.stats scripts/03_render_pdf.py
```

### Disk I/O

Monitor file operations:

```bash
# Check disk I/O
iostat -x 1

# Monitor specific directory
watch -n 1 'du -sh project/output/*'
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
python3 -m cProfile -o pipeline.prof scripts/run_all.py

# Analyze profile
python3 -m pstats pipeline.prof
```

### Stage-Specific Profiling

```bash
# Profile specific stage
python3 -m cProfile -o stage.prof scripts/03_render_pdf.py
```

### Memory Profiling

```bash
# Memory profiler
python3 -m memory_profiler scripts/run_all.py
```

## Caching Strategies

### Test Results Caching

```bash
# Enable pytest cache
pytest tests/ --cache-clear  # Clear cache
pytest tests/  # Uses cache for faster runs
```

### Build Artifact Caching

- LaTeX intermediate files (`.aux`, `.bbl`) are cached
- Figure generation results cached in `project/output/figures/`
- Re-run only if source files changed

### LLM Response Caching

- Review results saved to `project/output/llm/`
- Re-use previous reviews if manuscript unchanged
- Clear cache: `rm -rf project/output/llm/*`

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
grep "Completed in" project/output/*.log | awk '{print $NF}'
```

## Best Practices

### Development Workflow

1. **Fast Iteration**: Skip slow stages during development
2. **Selective Execution**: Run only changed stages
3. **Caching**: Enable all caching mechanisms
4. **Parallel Tests**: Use pytest-xdist for test execution

### Production Workflow

1. **Full Pipeline**: Run complete pipeline for final builds
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

- [`scripts/run_all.py`](../scripts/run_all.py) - Performance tracking implementation
- [`infrastructure/core/performance.py`](../infrastructure/core/performance.py) - Performance utilities
- [`TROUBLESHOOTING_GUIDE.md`](../operational/TROUBLESHOOTING_GUIDE.md) - Performance troubleshooting
