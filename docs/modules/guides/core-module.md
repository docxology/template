# Core Infrastructure Module

> **Foundation utilities for logging, configuration, exceptions, pipeline execution, and runtime monitoring**

**Location:** `infrastructure/core/`  
**Quick Reference:** [Modules Guide](../modules-guide.md) | [API Reference](../../reference/api-reference.md)

---

## Key Features

- **Logging**: Structured logging with `get_logger`, decorators (`log_operation`), stage reporting (`log_stage`), and duration formatting
- **Exceptions**: Unified `TemplateError` hierarchy with context-preserving helpers (`raise_with_context`, `chain_exceptions`)
- **Configuration**: YAML config loading (`load_config`) with auto-discovery (`find_config_file`)
- **Pipeline**: DAG-based pipeline execution (`PipelineExecutor`, `PipelineConfig`) with multi-project orchestration
- **Checkpoint**: Resumable execution via `CheckpointManager` for long-running pipelines
- **Health Checks**: Dependency and environment validation (`SystemHealthChecker`, `quick_health_check`)
- **Performance**: Function-level profiling (`monitor_performance`) and system resource monitoring
- **Progress**: Terminal progress bars (`ProgressBar`) for pipeline stage reporting
- **Telemetry**: Stage-level resource metrics collection (`TelemetryCollector`)

---

## Usage Examples

### Logging

```python
from infrastructure.core import get_logger, log_operation, log_stage, log_success, format_duration

logger = get_logger(__name__)
logger.info("Processing started")

# Decorator for automatic operation logging
@log_operation("Rendering manuscript")
def render():
    pass

# Stage-based progress reporting (for pipeline scripts)
log_stage(3, 10, "Running project tests")
log_success("All tests passed")

# Human-readable duration formatting
elapsed = format_duration(127.4)  # "2m 7s"
```

### Exception Hierarchy

All project exceptions inherit from `TemplateError`, enabling consistent error handling across the infrastructure layer.

```python
from infrastructure.core.exceptions import (
    TemplateError,
    ConfigurationError,
    ValidationError,
    BuildError,
    RenderingError,
    LLMError,
    raise_with_context,
    chain_exceptions,
)

# Raise with file context for debugging
raise_with_context(ValidationError("Invalid format"), file_path="doc.md", line=42)

# Chain exceptions to preserve causal context
try:
    render()
except RenderingError as e:
    chain_exceptions(BuildError("Pipeline failed"), e)
```

**Exception tree:** `TemplateError` > `ConfigurationError`, `ValidationError`, `BuildError`, `FileOperationError`, `DependencyError`, `TestError`, `IntegrationError`, `LLMError`, `LLMConnectionError`, `LLMTemplateError`, `RenderingError`, `FormatError`, `PublishingError`, `UploadError`, `LiteratureSearchError`, `APIRateLimitError`

### Configuration Loading

```python
from infrastructure.core.config.loader import load_config, find_config_file, get_config_as_dict
from pathlib import Path

# Load a project's config.yaml
config = load_config(Path("projects/my_project/manuscript/config.yaml"))

# Auto-discover config file from project root
config_path = find_config_file(Path("projects/my_project"))

# Get config as a plain dictionary
config_dict = get_config_as_dict(config_path)
```

### Pipeline Execution

```python
from infrastructure.core.pipeline import PipelineConfig, PipelineExecutor

config = PipelineConfig(project_name="code_project", core_only=True)
executor = PipelineExecutor(config)
result = executor.run()
```

### Multi-Project Orchestration

```python
from infrastructure.core.pipeline.multi_project import MultiProjectConfig, MultiProjectOrchestrator

config = MultiProjectConfig(projects=["proj_a", "proj_b"])
orchestrator = MultiProjectOrchestrator(config)
result = orchestrator.run()
```

### Checkpoint and Resume

```python
from infrastructure.core import CheckpointManager
from infrastructure.core.runtime.checkpoint import PipelineCheckpoint

manager = CheckpointManager(checkpoint_dir)
manager.save(PipelineCheckpoint(stage=5, status="complete"))

# Resume from saved state on next run
checkpoint = manager.load()
```

### Health Checks

```python
from infrastructure.core import SystemHealthChecker
from infrastructure.core.runtime.health_check import quick_health_check, get_health_status

# Quick validation of environment
status = quick_health_check()

# Detailed system health
checker = SystemHealthChecker()
report = checker.run()
```

### Performance Monitoring

```python
from infrastructure.core import monitor_performance
from infrastructure.core.runtime.function_profiler import CodeProfiler

# Context manager for profiling a block
profiler = CodeProfiler()
with profiler.monitor("heavy_computation"):
    heavy_computation()

# System resource snapshot
from infrastructure.core.pipeline.stage_monitor import get_system_resources
resources = get_system_resources()
```

### Progress Tracking

```python
from infrastructure.core import ProgressBar

progress = ProgressBar(total=100, prefix="Rendering")
for i in range(100):
    do_work(i)
    progress.update(1)
```

### Telemetry

```python
from infrastructure.core.telemetry import TelemetryCollector, TelemetryConfig

config = TelemetryConfig()
collector = TelemetryCollector(config)
# Collector records CPU, memory, and wall-clock time per pipeline stage
```

---

## Configuration

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `LOG_LEVEL` | Logging verbosity (0=DEBUG, 1=INFO, 2=WARN, 3=ERROR) | `1` |
| `MPLBACKEND` | Matplotlib backend for headless rendering | `Agg` |

### Project Config (`manuscript/config.yaml`)

The `load_config` function parses the standard project config file containing paper metadata, author information, publication details, and LLM settings. See the [Configuration section in CLAUDE.md](../../reference/api-reference.md) for the full schema.

---

## Submodule Layout

```
infrastructure/core/
  __init__.py              # Re-exports commonly used symbols
  exceptions.py            # TemplateError hierarchy
  config/
    loader.py              # load_config, find_config_file, get_config_as_dict
  logging/
    helpers.py             # format_duration
    utils.py               # get_logger, log_operation, log_stage, log_success
  pipeline/
    __init__.py            # PipelineConfig, PipelineExecutor
    stage_monitor.py       # PerformanceMonitor, get_system_resources
    multi_project.py       # MultiProjectConfig, MultiProjectOrchestrator
  progress.py              # ProgressBar
  runtime/
    checkpoint.py          # CheckpointManager, PipelineCheckpoint
    environment.py         # check_python_version, setup_directories
    function_profiler.py   # CodeProfiler, monitor_performance
    health_check.py        # SystemHealthChecker, quick_health_check
  security.py              # SecurityValidator, RateLimiter, validate_llm_input
  telemetry.py             # TelemetryCollector, TelemetryConfig
```

---

## Related Documentation

- [Modules Guide](../modules-guide.md) -- overview of all infrastructure modules
- [Rendering Module](rendering-module.md) -- PDF, slides, and web output generation
- [Architecture: Two-Layer System](../../architecture/two-layer-architecture.md) -- how core fits into the infrastructure layer
- [Testing Strategy](../../architecture/testing-strategy.md) -- no-mocks policy and coverage requirements
- [Troubleshooting: Build Tools](../../operational/troubleshooting/build-tools.md) -- common dependency issues
