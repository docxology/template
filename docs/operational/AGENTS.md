# Operational Documentation

## Overview

The `docs/operational/` directory contains operational procedures, configuration guides, troubleshooting resources, and maintenance instructions for the Research Project Template. These documents focus on day-to-day usage, system administration, and operational excellence.

## Directory Structure

```
docs/operational/
├── AGENTS.md                       # This technical documentation
├── BUILD_SYSTEM.md                 # Build pipeline and execution details
├── CHECKPOINT_RESUME.md            # Checkpoint and resume functionality
├── CI_CD_INTEGRATION.md            # Continuous integration setup
├── CONFIGURATION.md                # Configuration system guide
├── DEPENDENCY_MANAGEMENT.md        # Dependency management procedures
├── ERROR_HANDLING_GUIDE.md         # Error handling and debugging
├── LLM_REVIEW_TROUBLESHOOTING.md   # LLM review system troubleshooting
├── LOGGING_GUIDE.md                # Logging system usage and configuration
├── PERFORMANCE_OPTIMIZATION.md     # Performance tuning and optimization
├── README.md                       # Quick reference for operational docs
└── TROUBLESHOOTING_GUIDE.md        # Comprehensive troubleshooting guide
```

## Key Documentation Files

### Build System (`BUILD_SYSTEM.md`)

**Complete build pipeline documentation:**

**Pipeline Stages:**
- Environment setup and validation
- Test execution and coverage analysis
- Analysis script execution
- PDF generation and rendering
- Output validation and quality checks
- Final deliverable copying

**Execution Modes:**
- Complete pipeline execution
- Individual stage execution
- Resume from checkpoint
- Clean rebuild options

### Configuration System (`CONFIGURATION.md`)

**Configuration management and customization:**

**Configuration Sources:**
- YAML configuration files (`project/manuscript/config.yaml`)
- Environment variables (highest priority)
- Default values (fallback)

**Configuration Areas:**
- Project metadata (title, author, affiliations)
- Build settings (output formats, quality thresholds)
- External service credentials (API tokens, endpoints)
- System preferences (logging levels, performance settings)

### Troubleshooting Guide (`TROUBLESHOOTING_GUIDE.md`)

**Comprehensive problem-solving guide:**

**Common Issues:**
- Build failures and compilation errors
- Dependency installation problems
- Configuration validation errors
- Output generation failures

**Diagnostic Procedures:**
- Log analysis techniques
- System state inspection
- Error message interpretation
- Recovery and workaround procedures

### Performance Optimization (`PERFORMANCE_OPTIMIZATION.md`)

**System performance tuning and optimization:**

**Performance Areas:**
- Build pipeline optimization
- Memory usage management
- CPU utilization improvement
- I/O operation efficiency

**Optimization Techniques:**
- Parallel processing configuration
- Caching strategy implementation
- Resource limit management
- Profiling and bottleneck identification

## Operational Procedures

### Daily Operations

**Standard Workflow:**
```bash
# 1. Environment check
python3 scripts/00_setup_environment.py

# 2. Code development and testing
python3 scripts/01_run_tests.py

# 3. Analysis execution
python3 scripts/02_run_analysis.py

# 4. Output generation
python3 scripts/03_render_pdf.py

# 5. Quality validation
python3 scripts/04_validate_output.py

# 6. Delivery preparation
python3 scripts/05_copy_outputs.py
```

**Health Monitoring:**
```bash
# Check system status
python3 -c "
from infrastructure.core import environment
status = environment.check_system_requirements()
for component, info in status.items():
    print(f'{component}: {\"✓\" if info[\"available\"] else \"✗\"} - {info[\"version\"]}')
"
```

### Maintenance Procedures

**Regular Maintenance Tasks:**

**Weekly:**
```bash
# Update dependencies
uv lock --upgrade

# Run full test suite
python3 scripts/01_run_tests.py

# Check disk usage
du -sh output/ project/output/

# Review logs for issues
grep "ERROR\|WARNING" output/logs/*.log | tail -20
```

**Monthly:**
```bash
# Full system backup
tar -czf "backup_$(date +%Y%m%d).tar.gz" \
    --exclude="__pycache__" \
    --exclude=".pytest_cache" \
    project/

# Dependency security audit
safety check

# Performance benchmark
python3 scripts/02_run_analysis.py --benchmark
```

### Configuration Management

**Configuration Best Practices:**
```yaml
# project/manuscript/config.yaml
paper:
  title: "Research Project Title"
  version: "1.0"

authors:
  - name: "Dr. Primary Author"
    orcid: "0000-0000-0000-1234"
    email: "author@university.edu"
    affiliation: "Research University"

publication:
  doi: "10.5281/zenodo.12345678"
  license: "Apache-2.0"

# Build optimization settings
build:
  parallel_jobs: 4
  memory_limit: "8GB"
  timeout: 3600

# External service configuration
services:
  ollama_endpoint: "http://localhost:11434"
  zenodo_token: "${ZENODO_TOKEN}"  # Environment variable
```

**Environment Variables:**
```bash
# Essential variables
export LOG_LEVEL=1                    # 0=DEBUG, 1=INFO, 2=WARN, 3=ERROR
export AUTHOR_NAME="Dr. Researcher"
export PROJECT_TITLE="Research Project"

# Performance tuning
export MAX_PARALLEL_SUMMARIES=2       # Parallel LLM operations
export PDF_MEMORY_LIMIT="4GB"         # PDF processing memory limit

# External services
export OLLAMA_HOST="http://localhost:11434"
export ZENODO_TOKEN="your-zenodo-token"
export GITHUB_TOKEN="your-github-token"
```

### Error Handling and Recovery

**Error Classification:**
- **Configuration Errors**: Invalid settings or missing files
- **Dependency Errors**: Missing packages or version conflicts
- **Build Errors**: Compilation failures or resource issues
- **Validation Errors**: Quality check failures

**Recovery Procedures:**
```bash
# Configuration error recovery
python3 -c "
from infrastructure.core import load_config
try:
    config = load_config()
    print('Configuration valid')
except Exception as e:
    print(f'Configuration error: {e}')
    print('Check project/manuscript/config.yaml syntax')
"

# Build error recovery
LOG_LEVEL=0 python3 scripts/03_render_pdf.py  # Debug logging
# Check LaTeX installation
which xelatex
tlmgr list --only-installed | grep multirow

# Validation error recovery
python3 scripts/04_validate_output.py --verbose
# Review validation report in output/reports/
```

## System Administration

### Environment Setup

**Development Environment:**
```bash
# Python environment
python3 -m venv research_env
source research_env/bin/activate

# Install dependencies
uv pip install -e .

# Verify installation
python3 -c "import infrastructure; print('Installation successful')"
```

**Production Environment:**
```bash
# System dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y python3 python3-pip texlive-xetex pandoc

# Verify installations
which python3 xelatex pandoc
python3 --version
```

### Monitoring and Alerting

**System Monitoring:**
```python
# Performance monitoring
from infrastructure.core import PerformanceMonitor

monitor = PerformanceMonitor()
with monitor.track('build_pipeline'):
    run_build_pipeline()

print(f"Build completed in {monitor.get_duration('build_pipeline'):.2f}s")
print(f"Peak memory: {monitor.get_memory_peak() / 1024 / 1024:.1f}MB")
```

**Log Analysis:**
```bash
# Recent errors
grep "ERROR" output/logs/*.log | tail -10

# Performance summary
grep "completed in" output/logs/*.log | tail -5

# Resource usage
grep "Memory\|CPU" output/logs/*.log | tail -10
```

### Backup and Recovery

**Backup Strategy:**
```bash
# Source code backup
git bundle create "repo-$(date +%Y%m%d).bundle" --all

# Data backup (excluding generated files)
tar -czf "data-$(date +%Y%m%d).tar.gz" \
    --exclude="output" \
    --exclude="__pycache__" \
    --exclude=".pytest_cache" \
    project/manuscript/ \
    project/src/ \
    project/tests/ \
    project/scripts/
```

**Recovery Procedures:**
```bash
# Repository recovery
git clone repo-20241227.bundle recovery-repo

# Data recovery
tar -xzf data-20241227.tar.gz
cd recovered-data

# Validate recovery
python3 scripts/01_run_tests.py
python3 scripts/03_render_pdf.py
```

## Performance Management

### Performance Monitoring

**Build Performance Tracking:**
```python
import time
from infrastructure.core import PerformanceMonitor

class BuildProfiler:
    """Profile build pipeline performance."""

    def __init__(self):
        self.monitor = PerformanceMonitor()

    def profile_build(self):
        """Profile complete build pipeline."""
        start_time = time.time()

        # Stage 1: Environment setup
        with self.monitor.track('setup'):
            run_environment_setup()

        # Stage 2: Testing
        with self.monitor.track('testing'):
            run_test_suite()

        # Stage 3: Analysis
        with self.monitor.track('analysis'):
            run_analysis_scripts()

        # Stage 4: Rendering
        with self.monitor.track('rendering'):
            generate_outputs()

        # Stage 5: Validation
        with self.monitor.track('validation'):
            validate_outputs()

        total_time = time.time() - start_time

        # Generate performance report
        report = {
            'total_time': total_time,
            'stage_times': {
                stage: self.monitor.get_duration(stage)
                for stage in ['setup', 'testing', 'analysis', 'rendering', 'validation']
            },
            'memory_peak': self.monitor.get_memory_peak(),
            'bottlenecks': self.identify_bottlenecks()
        }

        return report
```

**Performance Optimization:**
```bash
# Parallel processing configuration
export MAX_PARALLEL_SUMMARIES=4
export PYTHONUNBUFFERED=1  # Real-time log output

# Memory optimization
export PDF_MEMORY_LIMIT="8GB"
export PYTHONMALLOC=jemalloc  # Alternative memory allocator

# I/O optimization
export OUTPUT_BUFFER_SIZE="64MB"
```

### Resource Management

**Memory Management:**
```python
# Monitor memory usage
import psutil
import os

def monitor_resources():
    """Monitor system resource usage."""
    process = psutil.Process(os.getpid())

    memory_info = process.memory_info()
    memory_usage = {
        'rss': memory_info.rss / 1024 / 1024,  # MB
        'vms': memory_info.vms / 1024 / 1024,  # MB
        'percent': process.memory_percent()
    }

    cpu_usage = process.cpu_percent(interval=1)

    return {
        'memory': memory_usage,
        'cpu': cpu_usage,
        'system_memory': psutil.virtual_memory().percent
    }

# Usage in long-running operations
resources = monitor_resources()
if resources['memory']['percent'] > 80:
    print("Warning: High memory usage detected")
```

**Disk Space Management:**
```bash
# Check disk usage
df -h .

# Clean up generated files
python3 scripts/run_all.py --clean

# Archive old outputs
find output/ -name "*.pdf" -mtime +30 -exec mv {} archives/ \;

# Compress logs
find output/logs/ -name "*.log" -mtime +7 -exec gzip {} \;
```

## Troubleshooting Procedures

### Systematic Problem Solving

**Diagnostic Framework:**
1. **Reproduce the Issue**
   ```bash
   # Create minimal test case
   mkdir test_case && cd test_case
   cp -r /path/to/template/* .
   # Reproduce with minimal configuration
   ```

2. **Gather Information**
   ```bash
   # System information
   uname -a
   python3 --version
   pip list | grep -E "(infrastructure|pandoc|texlive)"

   # Log analysis
   LOG_LEVEL=0 python3 scripts/problematic_script.py 2>&1 | tee debug.log
   ```

3. **Isolate the Problem**
   ```bash
   # Test individual components
   python3 -c "from infrastructure.core import load_config; print('Config loads')"
   python3 -c "from infrastructure.validation import validate_pdf_rendering; print('Validation imports')"
   ```

4. **Apply Fix and Test**
   ```bash
   # Implement fix
   vim fixed_file.py

   # Test fix
   python3 scripts/01_run_tests.py
   python3 scripts/affected_script.py
   ```

### Common Issues and Solutions

**LaTeX Compilation Failures:**
```bash
# Check LaTeX installation
which xelatex
xelatex --version

# Install missing packages
sudo tlmgr update --self
sudo tlmgr install multirow cleveref doi newunicodechar

# Test compilation
xelatex --interaction=nonstopmode test.tex
```

**Memory Issues:**
```bash
# Check system memory
free -h

# Reduce parallelism
export MAX_PARALLEL_SUMMARIES=1
export PDF_MEMORY_LIMIT="2GB"

# Monitor memory usage
python3 -c "
import psutil
print(f'Memory usage: {psutil.virtual_memory().percent}%')
"
```

**Network Issues:**
```bash
# Test connectivity
curl -I https://api.semanticscholar.org/
curl -I https://zenodo.org/api/

# Check DNS resolution
nslookup api.semanticscholar.org

# Test with timeout
export REQUEST_TIMEOUT=30
```

## Security Operations

### Secure Configuration

**Credential Management:**
```python
# Secure credential handling
from infrastructure.core.credentials import CredentialManager

credential_manager = CredentialManager()

# Store credentials securely
credential_manager.store_credential('zenodo_token', 'your-token-here')

# Retrieve for use
token = credential_manager.get_credential('zenodo_token')
if token:
    publish_to_zenodo(metadata, files, token)
```

**Environment Security:**
```bash
# Secure environment setup
export ZENODO_TOKEN="$(cat ~/.zenodo_token)"
export GITHUB_TOKEN="$(cat ~/.github_token)"

# Avoid logging sensitive data
python3 -c "
import os
token = os.getenv('ZENODO_TOKEN')
if token:
    print(f'Token loaded (length: {len(token)})')
else:
    print('No token found')
"
```

### Security Monitoring

**Vulnerability Scanning:**
```bash
# Python package security
safety check
pip-audit

# System security
sudo rkhunter --check
sudo chkrootkit

# File integrity
find . -name "*.py" -exec python3 -m py_compile {} \;
```

## Continuous Improvement

### Operational Metrics

**Key Performance Indicators:**
- Build success rate (>95%)
- Average build time (<30 minutes)
- Test coverage maintenance (>90% project, >60% infrastructure)
- Mean time to resolution for issues (<24 hours)

**Monitoring Dashboard:**
```python
class OperationalDashboard:
    """Monitor system operational metrics."""

    def generate_report(self):
        """Generate comprehensive operational report."""
        return {
            'build_metrics': self.get_build_metrics(),
            'test_metrics': self.get_test_metrics(),
            'performance_metrics': self.get_performance_metrics(),
            'error_metrics': self.get_error_metrics(),
            'resource_metrics': self.get_resource_metrics()
        }

    def get_build_metrics(self):
        """Analyze build pipeline performance."""
        # Implementation for build metrics
        pass

    def get_test_metrics(self):
        """Analyze test suite performance."""
        # Implementation for test metrics
        pass
```

### Process Optimization

**Workflow Improvements:**
- Automate repetitive tasks
- Implement parallel processing where beneficial
- Optimize resource utilization
- Streamline deployment processes

**Feedback Integration:**
- Monitor user-reported issues
- Track feature usage patterns
- Collect performance feedback
- Implement user-requested improvements

## See Also

**Operational Documentation:**
- [`BUILD_SYSTEM.md`](BUILD_SYSTEM.md) - Build pipeline details
- [`TROUBLESHOOTING_GUIDE.md`](TROUBLESHOOTING_GUIDE.md) - Problem-solving guide
- [`PERFORMANCE_OPTIMIZATION.md`](PERFORMANCE_OPTIMIZATION.md) - Performance tuning
- [`CONFIGURATION.md`](CONFIGURATION.md) - Configuration management

**System Documentation:**
- [`../AGENTS.md`](../AGENTS.md) - Complete system overview
- [`../DOCUMENTATION_INDEX.md`](../DOCUMENTATION_INDEX.md) - Documentation index
- [`../../AGENTS.md`](../../AGENTS.md) - Root system documentation