---
name: infrastructure-core
description: Skill for the core infrastructure module providing logging, configuration, exception handling, progress tracking, checkpoints, retry logic, pipeline execution, performance monitoring, security, file operations, and multi-project orchestration. Use when setting up logging, loading config, handling errors, running pipelines, or monitoring performance.
---

# Core Infrastructure Module

Foundation utilities used across the entire infrastructure layer and all project scripts.

## Logging (`logging_utils.py`)

```python
from infrastructure.core import get_logger, log_operation, log_stage, format_duration
from infrastructure.core.logging.setup import setup_logger
from infrastructure.core.logging.utils import log_timing, log_substep

logger = get_logger(__name__)
logger.info("Processing started")

# Decorators for automatic timing and logging
@log_operation("Processing data")
def process():
    pass

@log_timing
def expensive_operation():
    pass

# Structured progress logging
log_stage(1, 10, "Running Tests")
log_substep("Unit tests passed")

# ETA calculation
from infrastructure.core.runtime import calculate_eta
```

## Configuration (`config_loader.py`)

```python
from infrastructure.core.config.loader import load_config, find_config_file, get_config_as_dict

# Load project config.yaml
config = load_config(project_path / "manuscript" / "config.yaml")

# Auto-discover config file
config_path = find_config_file(project_root)
```

## Exception Hierarchy (`exceptions.py`)

All exceptions extend `TemplateError`. Use context-preserving helpers:

```python
from infrastructure.core import TemplateError
from infrastructure.core.exceptions import (
    ConfigurationError, ValidationError, BuildError,
    RenderingError, LLMError, PublishingError,
    raise_with_context, chain_exceptions, format_file_context,
)

# Raise with file context
raise_with_context(ValidationError("Invalid format"), file_path="doc.md", line=42)

# Chain exceptions
try:
    render()
except RenderingError as e:
    chain_exceptions(BuildError("Pipeline failed"), e)
```

**Exception tree:** `TemplateError` → `ConfigurationError`, `ValidationError`, `BuildError`, `FileOperationError`, `DependencyError`, `TestError`, `IntegrationError`, `LLMError`, `LLMConnectionError`, `LLMTemplateError`, `RenderingError`, `FormatError`, `PublishingError`, `UploadError`, `LiteratureSearchError`, `APIRateLimitError`

## Pipeline Execution (`pipeline.py`)

```python
from infrastructure.core.pipeline import PipelineExecutor, PipelineConfig

config = PipelineConfig(project_name="my_project", core_only=True)
executor = PipelineExecutor(config)
result = executor.run()
```

## Checkpoint & Resume (`checkpoint.py`)

```python
from infrastructure.core import CheckpointManager
from infrastructure.core.runtime.checkpoint import PipelineCheckpoint

manager = CheckpointManager(checkpoint_dir)
manager.save(PipelineCheckpoint(stage=5, status="complete"))
checkpoint = manager.load()  # Resume from saved state
```

## Progress Tracking (`progress.py`)

```python
from infrastructure.core import ProgressBar
from infrastructure.core.progress import SubStageProgress

progress = ProgressBar(total=100, prefix="Rendering")
progress.update(10)
```

## Retry Logic (`retry.py`)

```python
from infrastructure.core.runtime import retry_with_backoff

@retry_with_backoff(max_retries=3, base_delay=1.0)
def flaky_operation():
    pass
```

## Performance Monitoring (`stage_monitor.py`, `function_profiler.py`)

```python
from infrastructure.core.runtime.function_profiler import CodeProfiler, monitor_performance
from infrastructure.core.pipeline.stage_monitor import PerformanceMonitor, get_system_resources

resources = get_system_resources()
monitor = PerformanceMonitor()

profiler = CodeProfiler()
def heavy_computation() -> None:
    pass

with profiler.monitor("heavy_computation"):
    heavy_computation()
```

## Security (`security.py`)

```python
from infrastructure.core.security import SecurityValidator, RateLimiter, rate_limit
from infrastructure.llm.core.sanitization import sanitize_llm_input

validator = SecurityValidator()
validator.validate_input(user_text)

sanitized = sanitize_llm_input(user_text)

@rate_limit(calls=10, period=60)
def api_call():
    pass
```

## Environment Setup (`environment.py`)

```python
from infrastructure.core.runtime.environment import (
    check_python_version, check_dependencies, check_build_tools,
    setup_directories, verify_source_structure,
)
```

## File Operations (`file_operations.py`)

```python
from infrastructure.core.files.cleanup import clean_output_directory
from infrastructure.core.files.operations import copy_final_deliverables
clean_output_directory(output_path)
copy_final_deliverables(source, destination)
```

## Multi-Project Orchestration (`multi_project.py`)

```python
from infrastructure.core.pipeline.multi_project import MultiProjectConfig, MultiProjectOrchestrator
config = MultiProjectConfig(projects=["proj_a", "proj_b"])
orchestrator = MultiProjectOrchestrator(config)
result = orchestrator.run()
```

## Health Checks (`health_check.py`)

```python
from infrastructure.core import SystemHealthChecker
checker = SystemHealthChecker()
status = checker.get_health_status()
```
