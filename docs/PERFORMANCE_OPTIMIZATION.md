# Performance Optimization Guide

> **Strategies and techniques** for optimizing build times and performance

**Quick Reference:** [Build System](BUILD_SYSTEM.md) | [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md) | [Common Workflows](COMMON_WORKFLOWS.md)

This guide provides comprehensive strategies for optimizing build performance, reducing execution times, and improving overall system efficiency.

## Overview

The Research Project Template currently achieves a **75-second build time** for complete regeneration. This guide covers strategies to optimize performance further and maintain fast builds as projects grow.

## Build Time Analysis

### Current Performance Metrics

From [Build System](BUILD_SYSTEM.md) analysis:

| Stage | Time | Percentage | Optimization Potential |
|-------|------|------------|------------------------|
| **Test Suite** | 27s | 36% | High - Parallel execution |
| **Script Execution** | 2s | 3% | Low - Already fast |
| **Repository Utilities** | 1s | 1% | Low - Minimal overhead |
| **Individual PDFs** | 35s | 46% | Medium - Parallel builds |
| **Combined PDF** | 10s | 13% | Low - Sequential required |
| **HTML Version** | 1s | 1% | Low - Already fast |
| **Total** | **76s** | **100%** | **Overall: Medium** |

### Optimization Targets

**Realistic goals:**
- **Test Suite**: 27s → 15s (parallel execution)
- **Individual PDFs**: 35s → 20s (parallel builds)
- **Total Build Time**: 76s → 45s (40% improvement)

## Optimization Strategies

### 1. Test Suite Optimization

#### Parallel Test Execution

**Use pytest-xdist for parallel execution:**
```bash
# Install pytest-xdist
uv add --dev pytest-xdist

# Run tests in parallel
uv run pytest tests/ -n auto

# Specific worker count
uv run pytest tests/ -n 4
```

**Benefits:**
- Reduces test execution time by 40-60%
- Scales with CPU cores
- No code changes required

**Configuration:**
```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "-n auto"
```

#### Test Caching

**Enable pytest caching:**
```bash
# Cache is enabled by default
# View cache stats
uv run pytest tests/ --cache-show

# Clear cache
uv run pytest tests/ --cache-clear
```

**Benefits:**
- Skips unchanged tests
- Faster subsequent runs
- Automatic caching

#### Test Selection

**Run only relevant tests:**
```bash
# Run only changed tests (requires tooling)
uv run pytest tests/ -k "test_name_pattern"

# Run only specific module
uv run pytest tests/test_example.py
```

### 2. Script Execution Optimization

#### Batch Operations

**Combine multiple operations:**
```python
# Instead of multiple scripts
python script1.py
python script2.py
python script3.py

# Single script with batch processing
python generate_all_figures.py
```

**Benefits:**
- Reduces Python startup overhead
- Shared data loading
- Better resource utilization

#### Caching Figure Generation

**Cache generated figures:**
```python
import hashlib
from pathlib import Path

def get_figure_hash(data):
    return hashlib.md5(str(data).encode()).hexdigest()

def should_regenerate_figure(figure_path, data_hash):
    if not figure_path.exists():
        return True
    # Check if hash matches
    cached_hash = figure_path.with_suffix('.hash').read_text()
    return cached_hash != data_hash
```

### 3. PDF Generation Optimization

#### Parallel PDF Building

**Build PDFs in parallel:**
```bash
# Build individual PDFs in parallel
find manuscript -name "*.md" -print0 | xargs -0 -P 4 -I {} \
  pandoc {} -o output/pdf/{}.pdf

# Or use GNU parallel
parallel pandoc {} -o output/pdf/{}.pdf ::: manuscript/*.md
```

**Benefits:**
- Reduces PDF generation time by 50-70%
- Utilizes multiple CPU cores
- Independent builds

**Implementation:**
```bash
# In render_pdf.sh
build_pdfs_parallel() {
    local files=("$@")
    local max_jobs=4
    
    for file in "${files[@]}"; do
        while [ $(jobs -r | wc -l) -ge $max_jobs ]; do
            sleep 0.1
        done
        build_single_pdf "$file" &
    done
    wait
}
```

#### Incremental PDF Building

**Only rebuild changed files:**
```bash
# Check modification times
find manuscript -name "*.md" -newer output/pdf/combined.pdf

# Build only changed files
for file in $(find manuscript -name "*.md" -newer last_build); do
    build_pdf "$file"
done
```

### 4. Dependency Management Optimization

#### Dependency Caching

**Cache Python packages:**
```bash
# uv caches automatically
# Location: ~/.cache/uv

# Pre-warm cache
uv sync --offline
```

**Benefits:**
- Faster dependency installation
- Offline capability
- Reduced network usage

#### Lock File Optimization

**Keep lock file up-to-date:**
```bash
# Update lock file efficiently
uv lock --upgrade-package package-name

# Instead of full upgrade
uv sync --upgrade
```

### 5. Build System Optimization

#### Selective Execution

**Skip unnecessary steps:**
```bash
# Skip validation if not needed
SKIP_VALIDATION=1 ./repo_utilities/render_pdf.sh

# Skip figure generation
SKIP_FIGURES=1 ./repo_utilities/render_pdf.sh
```

**Configuration:**
```bash
# In render_pdf.sh
if [ "${SKIP_VALIDATION:-0}" = "1" ]; then
    echo "Skipping validation..."
    # Skip validation steps
fi
```

#### Output Directory Optimization

**Use faster storage:**
```bash
# Use RAM disk for temporary files
export TMPDIR=/tmp/ramdisk

# Or use SSD for output directory
export OUTPUT_DIR=/ssd/output
```

## Caching Best Practices

### pytest Caching

**Automatic caching:**
- pytest caches test results automatically
- Cache location: `.pytest_cache/`
- Cleared with `--cache-clear`

**Configuration:**
```toml
[tool.pytest.ini_options]
cache_dir = ".pytest_cache"
```

### Build Artifact Caching

**Cache build outputs:**
```bash
# Store build artifacts
tar -czf build_cache.tar.gz output/

# Restore if unchanged
if [ -f build_cache.tar.gz ]; then
    tar -xzf build_cache.tar.gz
fi
```

### Dependency Caching (CI/CD)

**Cache in GitHub Actions:**
```yaml
- name: Cache dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/uv
    key: ${{ runner.os }}-uv-${{ hashFiles('**/uv.lock') }}
```

## Parallel Execution

### Test Parallelization

**Configuration:**
```bash
# Auto-detect CPU count
uv run pytest tests/ -n auto

# Manual worker count
uv run pytest tests/ -n 4

# Per-worker configuration
uv run pytest tests/ -n auto --dist worksteal
```

**Best Practices:**
- Use `auto` for optimal worker count
- Monitor memory usage
- Balance between speed and resource usage

### PDF Parallelization

**Build multiple PDFs simultaneously:**
```bash
#!/bin/bash
build_pdfs_parallel() {
    local files=("$@")
    local pids=()
    
    for file in "${files[@]}"; do
        build_single_pdf "$file" &
        pids+=($!)
    done
    
    # Wait for all to complete
    for pid in "${pids[@]}"; do
        wait "$pid"
    done
}
```

## Resource Management

### Memory Optimization

**Monitor memory usage:**
```bash
# Check memory during build
watch -n 1 free -h

# Limit memory usage
ulimit -v 2097152  # 2GB limit
```

### CPU Optimization

**Set CPU affinity:**
```bash
# Limit CPU usage
taskset -c 0-3 ./repo_utilities/render_pdf.sh

# Or use nice
nice -n 10 ./repo_utilities/render_pdf.sh
```

## Profiling and Benchmarking

### Profiling Build Time

**Profile build stages:**
```bash
#!/bin/bash
time_start=$(date +%s)

echo "Starting tests..."
time_start_tests=$(date +%s)
uv run pytest tests/
time_end_tests=$(date +%s)
echo "Tests took $((time_end_tests - time_start_tests)) seconds"

echo "Starting PDF generation..."
time_start_pdf=$(date +%s)
# PDF generation...
time_end_pdf=$(date +%s)
echo "PDFs took $((time_end_pdf - time_start_pdf)) seconds"
```

### Benchmarking Functions

**Use scientific_dev module:**
```python
from scientific_dev import benchmark_function

def my_function(data):
    # Your code here
    pass

result = benchmark_function(my_function, test_inputs, iterations=100)
print(f"Average time: {result.execution_time:.4f}s")
```

## Performance Monitoring

### Build Time Tracking

**Track build times over time:**
```bash
# Log build times
echo "$(date): Build took 75 seconds" >> build_times.log

# Analyze trends
awk '{sum+=$NF; count++} END {print "Average:", sum/count}' build_times.log
```

### Resource Usage Monitoring

**Monitor during build:**
```bash
# CPU and memory usage
top -b -n 1 | head -20

# Disk I/O
iostat -x 1
```

## Optimization Checklist

### Quick Wins

- [ ] Enable parallel test execution (`pytest-xdist`)
- [ ] Parallel PDF building
- [ ] Enable pytest caching
- [ ] Cache dependencies
- [ ] Skip unnecessary validation

### Medium Impact

- [ ] Incremental builds
- [ ] Batch script operations
- [ ] Optimize figure generation
- [ ] Selective test execution

### Advanced

- [ ] Custom build orchestration
- [ ] Distributed builds
- [ ] Build artifact caching
- [ ] RAM disk for temporary files

## Troubleshooting Performance Issues

### Build Too Slow

**Diagnosis:**
```bash
# Profile each stage
time uv run pytest tests/
time python scripts/example_figure.py
time ./repo_utilities/render_pdf.sh
```

**Solutions:**
1. Enable parallel execution
2. Check for bottlenecks
3. Optimize slowest stage
4. Consider incremental builds

### Memory Issues

**Symptoms:**
- Build fails with out-of-memory errors
- System becomes unresponsive

**Solutions:**
1. Reduce parallel workers
2. Clear caches
3. Limit resource usage
4. Use swap space

### CPU Overload

**Symptoms:**
- System becomes slow
- Build takes longer than expected

**Solutions:**
1. Limit CPU usage
2. Reduce parallel jobs
3. Use nice priority
4. Schedule builds during low usage

## Summary

Performance optimization strategies:

1. **Parallel execution** - Tests and PDFs
2. **Caching** - Dependencies, tests, artifacts
3. **Incremental builds** - Only rebuild changed
4. **Resource management** - Memory and CPU
5. **Monitoring** - Track and analyze performance

**Expected improvements:**
- Test suite: 27s → 15s (44% faster)
- PDF generation: 35s → 20s (43% faster)
- Total build: 76s → 45s (41% faster)

For more information, see:
- [Build System](BUILD_SYSTEM.md) - Current performance
- [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md) - Performance issues
- [Common Workflows](COMMON_WORKFLOWS.md) - Optimization workflows

---

**Related Documentation:**
- [Build System](BUILD_SYSTEM.md) - Performance metrics
- [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md) - Performance debugging
- [CI/CD Integration](CI_CD_INTEGRATION.md) - CI performance optimization

