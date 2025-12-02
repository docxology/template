# ⚡ Performance Optimization Guide

> **Build time optimization** and caching strategies for the Research Project Template

**Quick Reference:** [Build System](BUILD_SYSTEM.md) | [CI/CD Integration](CI_CD_INTEGRATION.md) | [Troubleshooting](TROUBLESHOOTING_GUIDE.md)

This guide covers performance optimization strategies for the Research Project Template, focusing on build time reduction, caching, and efficient resource utilization.

## Current Performance Baseline

**Build Time:** 58 seconds (878 tests + PDF generation)  
**Test Suite:** 27 seconds for 878 tests  
**Coverage:** 81.90% across 1989 statements  
**Platform:** Ubuntu 22.04, Python 3.11, uv package manager

---

## 🔍 Performance Analysis

### Build Pipeline Breakdown

| Stage | Time | Percentage | Optimization Potential |
|-------|------|------------|----------------------|
| **Infrastructure Tests** | 6s | 10% | Medium (parallelization) |
| **Project Tests** | 3s | 5% | Medium (parallelization) |
| **Project Analysis** | 4s | 7% | High (caching, selective execution) |
| **PDF Rendering** | 44s | 76% | High (PDF caching, parallel compilation) |
| **Output Validation** | 1s | 2% | Low (already optimized) |
| **Copy Outputs** | 0s | 0% | Low (I/O bound) |
| **Total** | **58s** | **100%** | **~25% improvement possible** |

### Performance Bottlenecks

1. **PDF Compilation (76% of build time)**
   - XeLaTeX multiple passes
   - Bibliography processing
   - Font loading and rendering

2. **Figure Generation (7% of build time)**
   - Data processing
   - Plot rendering
   - Image file I/O

3. **Test Execution (15% of build time)**
   - 878 tests across multiple modules
   - Coverage measurement overhead

---

## 🚀 Optimization Strategies

### 1. PDF Compilation Optimization

#### Parallel PDF Generation

**Current:** Sequential compilation of 14 PDFs  
**Target:** Parallel compilation with dependency management

```bash
#!/bin/bash
# parallel_pdf_build.sh

# Function to compile individual PDF
compile_pdf() {
    local md_file="$1"
    local pdf_file="$2"
    echo "Compiling $md_file → $pdf_file"
    pandoc "$md_file" -o "$pdf_file" --pdf-engine=xelatex
}

# Export function for parallel execution
export -f compile_pdf

# Parallel compilation (max 4 concurrent processes)
cat << 'EOF' | parallel -j 4 compile_pdf {} output/pdf/{/.}.pdf
manuscript/01_abstract.md
manuscript/02_introduction.md
manuscript/03_methodology.md
manuscript/04_experimental_results.md
EOF
```

#### PDF Caching Strategy

```python
# pdf_cache.py - Intelligent PDF caching
import hashlib
import os
from pathlib import Path

class PDFCache:
    def __init__(self, cache_dir="output/pdf_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def get_cache_key(self, md_file, dependencies):
        """Generate cache key based on file content and dependencies."""
        content_hash = hashlib.sha256()
        with open(md_file, 'rb') as f:
            content_hash.update(f.read())

        for dep in dependencies:
            if os.path.exists(dep):
                with open(dep, 'rb') as f:
                    content_hash.update(f.read())

        return content_hash.hexdigest()

    def is_cached(self, md_file, dependencies):
        """Check if PDF is cached and valid."""
        cache_key = self.get_cache_key(md_file, dependencies)
        cache_file = self.cache_dir / f"{cache_key}.pdf"
        return cache_file.exists()

    def get_cached_pdf(self, md_file, dependencies):
        """Get cached PDF if valid."""
        if self.is_cached(md_file, dependencies):
            cache_key = self.get_cache_key(md_file, dependencies)
            return self.cache_dir / f"{cache_key}.pdf"
        return None

    def cache_pdf(self, pdf_file, md_file, dependencies):
        """Cache a generated PDF."""
        cache_key = self.get_cache_key(md_file, dependencies)
        cache_file = self.cache_dir / f"{cache_key}.pdf"
        import shutil
        shutil.copy2(pdf_file, cache_file)
        return cache_file
```

#### Incremental PDF Builds

```python
# incremental_build.py
from pdf_cache import PDFCache
from pathlib import Path

def incremental_pdf_build():
    """Build only PDFs that have changed."""
    cache = PDFCache()

    manuscript_dir = Path("manuscript")
    output_dir = Path("output/pdf")
    output_dir.mkdir(exist_ok=True)

    for md_file in manuscript_dir.glob("*.md"):
        pdf_file = output_dir / f"{md_file.stem}.pdf"

        # Check dependencies (figures, data files)
        dependencies = list(Path("output/figures").glob("*.png"))
        dependencies.extend(Path("output/data").glob("*.csv"))

        # Skip if cached and up-to-date
        cached_pdf = cache.get_cached_pdf(md_file, dependencies)
        if cached_pdf and pdf_file.exists():
            print(f"Using cached PDF: {md_file.name}")
            continue

        # Build PDF
        print(f"Building PDF: {md_file.name}")
        build_single_pdf(md_file, pdf_file)

        # Cache result
        cache.cache_pdf(pdf_file, md_file, dependencies)
```

### 2. Figure Generation Optimization

#### Selective Figure Regeneration

```python
# selective_figure_build.py
import os
from pathlib import Path
import hashlib

def needs_regeneration(script_file, output_files):
    """Check if figure script needs to run."""
    if not all(os.path.exists(f) for f in output_files):
        return True

    # Check if script has changed
    script_mtime = os.path.getmtime(script_file)
    oldest_output = min(os.path.getmtime(f) for f in output_files)
    if script_mtime > oldest_output:
        return True

    # Check if dependencies have changed
    for dep in get_script_dependencies(script_file):
        if os.path.getmtime(dep) > oldest_output:
            return True

    return False

def get_script_dependencies(script_file):
    """Extract data file dependencies from script."""
    dependencies = []
    with open(script_file, 'r') as f:
        content = f.read()

    # Look for data loading patterns
    import re
    data_patterns = [
        r'pd\.read_csv\(["\']([^"\']+)["\']',
        r'np\.load\(["\']([^"\']+)["\']',
        r'open\(["\']([^"\']+)["\']',
    ]

    for pattern in data_patterns:
        matches = re.findall(pattern, content)
        dependencies.extend(matches)

    return dependencies

# Usage in build script
if needs_regeneration('scripts/example_figure.py',
                     ['output/figures/example.png', 'output/data/example.csv']):
    print("Regenerating example figure...")
    run_script('scripts/example_figure.py')
else:
    print("Example figure is up-to-date")
```

#### Figure Caching by Content Hash

```python
# figure_cache.py
import hashlib
from pathlib import Path

class FigureCache:
    def __init__(self, cache_dir="output/figure_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def get_content_hash(self, script_file):
        """Generate hash of script and its data dependencies."""
        content_hash = hashlib.sha256()

        # Hash script content
        with open(script_file, 'rb') as f:
            content_hash.update(f.read())

        # Hash data dependencies
        for data_file in get_data_dependencies(script_file):
            if Path(data_file).exists():
                with open(data_file, 'rb') as f:
                    content_hash.update(f.read())

        return content_hash.hexdigest()

    def is_uptodate(self, script_file, output_files):
        """Check if figure outputs are up-to-date."""
        if not all(Path(f).exists() for f in output_files):
            return False

        cache_file = self.cache_dir / f"{Path(script_file).stem}_hash.txt"
        if not cache_file.exists():
            return False

        with open(cache_file, 'r') as f:
            cached_hash = f.read().strip()

        current_hash = self.get_content_hash(script_file)
        return cached_hash == current_hash

    def update_cache(self, script_file):
        """Update cache with current content hash."""
        current_hash = self.get_content_hash(script_file)
        cache_file = self.cache_dir / f"{Path(script_file).stem}_hash.txt"

        with open(cache_file, 'w') as f:
            f.write(current_hash)
```

### 3. Test Execution Optimization

#### Parallel Test Execution

```bash
# Parallel test execution with pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest tests/ -n auto --cov=src --cov-report=xml

# Or specify number of workers
pytest tests/ -n 4 --cov=src --cov-report=xml
```

#### Selective Test Execution

```python
# selective_test_runner.py
import subprocess
import os
from pathlib import Path

def run_selective_tests(changed_files):
    """Run only tests related to changed files."""

    # Map source files to test files
    test_mapping = {
        'src/example.py': 'tests/test_example.py',
        'src/quality_checker.py': 'tests/test_quality_checker.py',
        # Add more mappings...
    }

    tests_to_run = set()

    for changed_file in changed_files:
        if changed_file in test_mapping:
            tests_to_run.add(test_mapping[changed_file])
        elif changed_file.startswith('src/'):
            # Run all tests if core module changed
            tests_to_run.add('tests/')
            break

    if tests_to_run:
        for test_path in tests_to_run:
            print(f"Running tests: {test_path}")
            result = subprocess.run([
                'pytest', test_path,
                '--cov=src', '--cov-report=term-missing'
            ], capture_output=True, text=True)

            if result.returncode != 0:
                print(f"Test failures in {test_path}")
                print(result.stdout)
                print(result.stderr)
                return False

    return True
```

#### Test Caching

```python
# test_cache.py
import pickle
from pathlib import Path

class TestCache:
    def __init__(self, cache_dir=".pytest_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def get_test_hash(self, test_file):
        """Get hash of test file and dependencies."""
        import hashlib
        content_hash = hashlib.sha256()

        with open(test_file, 'rb') as f:
            content_hash.update(f.read())

        # Include source files in hash
        src_files = list(Path("src").glob("*.py"))
        for src_file in src_files:
            with open(src_file, 'rb') as f:
                content_hash.update(f.read())

        return content_hash.hexdigest()

    def should_skip_tests(self, test_file):
        """Check if tests can be skipped based on cache."""
        cache_file = self.cache_dir / f"{Path(test_file).stem}_results.pkl"

        if not cache_file.exists():
            return False

        # Load cached results
        with open(cache_file, 'rb') as f:
            cached_data = pickle.load(f)

        current_hash = self.get_test_hash(test_file)

        if cached_data['hash'] != current_hash:
            return False

        if cached_data['passed']:
            print(f"Skipping {test_file} (cached results)")
            return True

        return False

    def cache_test_results(self, test_file, passed):
        """Cache test execution results."""
        cache_file = self.cache_dir / f"{Path(test_file).stem}_results.pkl"
        current_hash = self.get_test_hash(test_file)

        cache_data = {
            'hash': current_hash,
            'passed': passed,
            'timestamp': datetime.now().isoformat()
        }

        with open(cache_file, 'wb') as f:
            pickle.dump(cache_data, f)
```

---

## 🧰 Caching Strategies

### 1. Dependency Caching

#### UV Dependency Cache

```yaml
# .github/workflows/ci.yml
- name: Cache uv dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/uv
    key: ${{ runner.os }}-uv-${{ hashFiles('**/uv.lock') }}
    restore-keys: |
      ${{ runner.os }}-uv-
```

#### Python Package Cache

```yaml
- name: Cache pip dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

### 2. Build Artifact Caching

#### PDF Artifact Cache

```yaml
- name: Cache PDF artifacts
  uses: actions/cache@v3
  with:
    path: output/pdf/
    key: ${{ runner.os }}-pdfs-${{ github.sha }}
    restore-keys: |
      ${{ runner.os }}-pdfs-
```

#### Figure Cache

```yaml
- name: Cache figures
  uses: actions/cache@v3
  with:
    path: output/figures/
    key: ${{ runner.os }}-figures-${{ hashFiles('output/data/**') }}
    restore-keys: |
      ${{ runner.os }}-figures-
```

### 3. Test Result Caching

#### Coverage Cache

```yaml
- name: Cache coverage data
  uses: actions/cache@v3
  with:
    path: .coverage
    key: ${{ runner.os }}-coverage-${{ github.sha }}
    restore-keys: |
      ${{ runner.os }}-coverage-
```

---

## 📊 Performance Monitoring

### Build Time Tracking

```python
# build_timer.py
import time
from contextlib import contextmanager
from pathlib import Path

class BuildTimer:
    def __init__(self, log_file="output/build_times.log"):
        self.log_file = Path(log_file)
        self.start_times = {}
        self.stage_times = {}

    @contextmanager
    def time_stage(self, stage_name):
        """Time a build stage."""
        start_time = time.time()
        self.start_times[stage_name] = start_time

        try:
            yield
        finally:
            end_time = time.time()
            duration = end_time - start_time
            self.stage_times[stage_name] = duration
            print(f"Stage '{stage_name}': {duration:.2f}s")

    def save_report(self):
        """Save build timing report."""
        total_time = sum(self.stage_times.values())

        with open(self.log_file, 'w') as f:
            f.write("Build Performance Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Total Build Time: {total_time:.2f}s\n\n")
            f.write("Stage Breakdown:\n")

            for stage, duration in self.stage_times.items():
                percentage = (duration / total_time) * 100
                f.write("25")

            f.write("\nRecommendations:\n")
            for stage, duration in sorted(self.stage_times.items(),
                                        key=lambda x: x[1], reverse=True):
                if duration > 5.0:  # Flag stages taking > 5 seconds
                    f.write(f"- Optimize {stage} ({duration:.2f}s)\n")

# Usage in build script
timer = BuildTimer()

with timer.time_stage("Tests"):
    run_tests()

with timer.time_stage("PDF Generation"):
    generate_pdfs()

with timer.time_stage("Validation"):
    validate_outputs()

timer.save_report()
```

### Performance Dashboard

```python
# performance_dashboard.py
import json
import matplotlib.pyplot as plt
from pathlib import Path

class PerformanceDashboard:
    def __init__(self, data_dir="output/performance"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def load_build_data(self):
        """Load historical build performance data."""
        data_file = self.data_dir / "build_history.json"
        if data_file.exists():
            with open(data_file, 'r') as f:
                return json.load(f)
        return []

    def save_build_data(self, build_data):
        """Save build performance data."""
        data = self.load_build_data()
        data.append(build_data)

        # Keep last 50 builds
        data = data[-50:]

        data_file = self.data_dir / "build_history.json"
        with open(data_file, 'w') as f:
            json.dump(data, f, indent=2)

    def generate_report(self):
        """Generate performance trend report."""
        data = self.load_build_data()
        if not data:
            return "No performance data available"

        # Extract metrics
        dates = [d['date'] for d in data]
        total_times = [d['total_time'] for d in data]
        test_times = [d.get('test_time', 0) for d in data]
        pdf_times = [d.get('pdf_time', 0) for d in data]

        # Generate plot
        plt.figure(figsize=(12, 6))
        plt.plot(dates, total_times, 'b-', label='Total Time', linewidth=2)
        plt.plot(dates, test_times, 'g--', label='Test Time', alpha=0.7)
        plt.plot(dates, pdf_times, 'r--', label='PDF Time', alpha=0.7)

        plt.xlabel('Build Date')
        plt.ylabel('Time (seconds)')
        plt.title('Build Performance Trends')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)

        plot_file = self.data_dir / "performance_trend.png"
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        plt.close()

        return f"Performance report generated: {plot_file}"
```

---

## 🔧 Implementation Examples

### Optimized Build Script

```bash
#!/bin/bash
# optimized_build.sh - High-performance build script

set -euo pipefail

# Configuration
MAX_PARALLEL=4
CACHE_DIR="output/cache"
LOG_FILE="output/build.log"

# Logging function
log() {
    echo "[$(date +%T)] $*" | tee -a "$LOG_FILE"
}

# Cache checking function
is_cached() {
    local cache_key="$1"
    local output_file="$2"

    if [[ -f "$CACHE_DIR/$cache_key" ]] && [[ -f "$output_file" ]]; then
        cached_mtime=$(stat -c %Y "$CACHE_DIR/$cache_key" 2>/dev/null || stat -f %m "$CACHE_DIR/$cache_key")
        output_mtime=$(stat -c %Y "$output_file" 2>/dev/null || stat -f %m "$output_file")

        if [[ $cached_mtime -gt $output_mtime ]]; then
            return 0  # Cached
        fi
    fi
    return 1  # Not cached
}

# Main build function
main() {
    log "Starting optimized build"

    # Create cache directory
    mkdir -p "$CACHE_DIR"

    # Stage 1: Tests (run if needed)
    if ! is_cached "tests_complete" "output/test_results.xml"; then
        log "Running tests..."
        python -m pytest tests/ -n "$MAX_PARALLEL" --cov=src --cov-report=xml -q
        touch "$CACHE_DIR/tests_complete"
        log "Tests completed"
    else
        log "Tests up-to-date (cached)"
    fi

    # Stage 2: Scripts (parallel execution)
    log "Running analysis scripts..."
    scripts=(
        "scripts/example_figure.py"
        "scripts/generate_research_figures.py"
    )

    # Run scripts in parallel
    printf '%s\n' "${scripts[@]}" | xargs -n 1 -P "$MAX_PARALLEL" python

    # Stage 3: PDFs (optimized compilation)
    log "Generating PDFs..."
    python scripts/03_render_pdf.py

    # Stage 4: Validation
    log "Running validation..."
    python scripts/04_validate_output.py

    log "Build completed successfully"
}

# Run main function
main "$@"
```

### CI/CD Performance Optimization

```yaml
# .github/workflows/optimized-ci.yml
name: Optimized CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Cache uv
      uses: actions/cache@v3
      with:
        path: ~/.cache/uv
        key: ${{ runner.os }}-uv-${{ hashFiles('**/uv.lock') }}

    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install uv
      uses: astral-sh/setup-uv@v3

    - name: Install dependencies
      run: uv sync

    - name: Cache test results
      uses: actions/cache@v3
      with:
        path: .pytest_cache
        key: ${{ runner.os }}-pytest-${{ github.sha }}
        restore-keys: |
          ${{ runner.os }}-pytest-

    - name: Run tests (parallel)
      run: |
        uv run pytest tests/ -n auto --cov=src --cov-report=xml \
          --cache-dir .pytest_cache

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Cache build artifacts
      uses: actions/cache@v3
      with:
        path: |
          output/figures/
          output/data/
        key: ${{ runner.os }}-artifacts-${{ github.sha }}
        restore-keys: |
          ${{ runner.os }}-artifacts-

    - name: Setup environment
      run: |
        uv sync
        sudo apt-get update
        sudo apt-get install -y pandoc texlive-xetex texlive-fonts-recommended

    - name: Selective build
      run: |
        # Only rebuild changed components
        ./scripts/optimized_build.sh

    - name: Upload PDFs
      uses: actions/upload-artifact@v3
      with:
        name: pdfs
        path: output/pdf/
```

---

## 📈 Expected Performance Improvements

### Optimization Results

| Optimization | Current Time | Target Time | Improvement |
|---------------|-------------|-------------|-------------|
| **Parallel PDF compilation** | 44s | 15s | **66% faster** |
| **Figure caching** | 4s | 1s | **75% faster** |
| **Parallel test execution** | 9s | 4s | **55% faster** |
| **Selective builds** | 58s | 25s | **57% faster** |
| **Combined optimization** | **58s** | **15-20s** | **70-75% faster** |

### Memory Optimization

```python
# memory_optimization.py
import gc
import psutil
import os

class MemoryOptimizer:
    def __init__(self):
        self.process = psutil.Process(os.getpid())

    def get_memory_usage(self):
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024

    def optimize_memory(self):
        """Apply memory optimization strategies."""
        # Force garbage collection
        gc.collect()

        # Clear matplotlib cache if using matplotlib
        try:
            import matplotlib.pyplot as plt
            plt.close('all')
        except ImportError:
            pass

        # Clear numpy memory cache
        try:
            import numpy as np
            # Force cleanup of numpy arrays
            pass
        except ImportError:
            pass

    def monitor_function(self, func, *args, **kwargs):
        """Monitor memory usage of a function."""
        start_mem = self.get_memory_usage()

        result = func(*args, **kwargs)

        end_mem = self.get_memory_usage()
        memory_delta = end_mem - start_mem

        print(f"Memory usage: {start_mem:.1f}MB → {end_mem:.1f}MB "
              f"(Δ{memory_delta:+.1f}MB)")

        return result
```

---

## 🎯 Best Practices

### 1. **Measure Before Optimizing**
Always profile before making changes:

```bash
# Profile build performance
python -m cProfile -s time scripts/run_all.py

# Profile memory usage
python -m memory_profiler scripts/example_figure.py
```

### 2. **Implement Incrementally**
Apply optimizations one at a time:

```bash
# Test optimization impact
time python scripts/run_all.py  # Baseline

# Apply optimization 1
time python scripts/optimized_build.sh  # Measure improvement

# Apply optimization 2
# ...
```

### 3. **Monitor Performance Trends**

```python
# performance_monitor.py
from datetime import datetime
import json

def log_build_performance(stage_times, total_time):
    """Log build performance for trend analysis."""

    data = {
        'timestamp': datetime.now().isoformat(),
        'total_time': total_time,
        'stages': stage_times,
        'git_commit': get_git_commit(),
        'platform': get_platform_info()
    }

    # Append to performance log
    with open('output/performance_log.jsonl', 'a') as f:
        f.write(json.dumps(data) + '\n')
```

### 4. **Automate Performance Testing**

```bash
#!/bin/bash
# performance_test.sh

echo "Running performance regression test..."

# Run build and capture time
start_time=$(date +%s)
python scripts/run_all.py > build_output.log 2>&1
end_time=$(date +%s)

build_time=$((end_time - start_time))

# Check against baseline
baseline_time=60  # Expected max time in seconds
if [ $build_time -gt $baseline_time ]; then
    echo "⚠️ Performance regression detected!"
    echo "Build time: ${build_time}s (baseline: ${baseline_time}s)"
    exit 1
else
    echo "✅ Build performance within limits: ${build_time}s"
fi
```

---

## 🚨 Troubleshooting Performance Issues

### Slow PDF Compilation

**Symptoms:** PDF generation takes >30 seconds

**Solutions:**
1. Check LaTeX installation: `xelatex --version`
2. Update fonts: `sudo apt-get install texlive-fonts-recommended`
3. Use faster engine: Switch to `pdflatex` for simple documents
4. Enable PDF caching

### Slow Test Execution

**Symptoms:** Tests take >20 seconds

**Solutions:**
1. Run in parallel: `pytest -n auto`
2. Skip slow tests in CI: Use `@pytest.mark.slow` marker
3. Cache test results: Use pytest-cache
4. Profile slow tests: `pytest --durations=10`

### Memory Issues

**Symptoms:** Out of memory errors

**Solutions:**
1. Process files in chunks
2. Clear caches regularly: `gc.collect()`
3. Use memory-efficient data structures
4. Monitor memory usage: `psutil`

### Disk I/O Bottlenecks

**Symptoms:** High disk usage during builds

**Solutions:**
1. Use SSD storage for builds
2. Enable file system caching
3. Reduce temporary file creation
4. Use RAM disk for temp files: `tmpfs`

---

## 📊 Performance Metrics

### Key Performance Indicators (KPIs)

1. **Build Time**: Total time for complete pipeline
2. **Test Execution Time**: Time to run full test suite
3. **PDF Generation Time**: Time to compile all PDFs
4. **Memory Usage**: Peak memory consumption
5. **Cache Hit Rate**: Percentage of cached operations
6. **Parallelization Efficiency**: Speedup from parallel execution

### Monitoring Dashboard

```python
# performance_kpis.py
import time
import psutil
from pathlib import Path

class PerformanceKPIs:
    def __init__(self):
        self.start_time = time.time()
        self.peak_memory = 0
        self.operations = []

    def log_operation(self, name, duration, success=True):
        """Log operation performance."""
        self.operations.append({
            'name': name,
            'duration': duration,
            'success': success,
            'timestamp': time.time()
        })

    def update_memory(self):
        """Update peak memory tracking."""
        process = psutil.Process()
        current_mem = process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = max(self.peak_memory, current_mem)

    def generate_report(self):
        """Generate comprehensive performance report."""
        total_time = time.time() - self.start_time

        report = {
            'total_time': total_time,
            'peak_memory_mb': self.peak_memory,
            'operations': self.operations,
            'success_rate': sum(1 for op in self.operations if op['success']) / len(self.operations),
            'slowest_operation': max(self.operations, key=lambda x: x['duration'])['name']
        }

        return report

# Usage
kpis = PerformanceKPIs()

# During build process
with time_block("PDF Generation"):
    kpis.log_operation("PDF Generation", duration)
    kpis.update_memory()

# Generate final report
report = kpis.generate_report()
```

---

## 🎯 Summary

Performance optimization strategies for the Research Project Template:

### **Primary Optimizations:**
1. **Parallel PDF compilation** - 66% reduction in PDF generation time
2. **Intelligent caching** - Skip unchanged components
3. **Selective builds** - Only rebuild what changed
4. **Parallel test execution** - 55% reduction in test time

### **Expected Results:**
- **70-75% faster builds** (58s → 15-20s)
- **50% reduction in CI/CD costs** through caching
- **Improved developer experience** with faster feedback
- **Scalable performance** as project grows

### **Implementation Approach:**
1. **Measure current performance** - Establish baseline
2. **Apply optimizations incrementally** - One change at a time
3. **Monitor impact** - Track improvements and regressions
4. **Automate monitoring** - Continuous performance tracking

For more information, see:
- **[Build System](BUILD_SYSTEM.md)** - Current performance baseline
- **[CI/CD Integration](CI_CD_INTEGRATION.md)** - CI/CD performance optimization
- **[Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md)** - Performance issue diagnosis

---

**Performance optimization is an ongoing process. Regular monitoring and incremental improvements ensure the build system remains fast and efficient as the project grows.**
