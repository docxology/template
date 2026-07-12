# Core Module

## Purpose

The Core module provides fundamental foundation utilities used across the entire infrastructure layer. It includes configuration management, unified logging, and a exception hierarchy with context preservation.

## Architecture

### Core Components

**exceptions.py**
- Base exception hierarchy (TemplateError and subclasses)
- Context preservation with exception chaining
- Module-specific exceptions (Literature, LLM, Rendering, Publishing)
- Exception utility functions for context formatting

**logging/utils.py**
- Unified Python logging with consistent formatting
- Environment-based configuration (LOG_LEVEL 0-3)
- Context managers for operation tracking and timing
- Decorators for function call logging
- Integration with bash logging.sh format
- Emoji support for TTY output

**config/loader.py**
- YAML configuration file loading
- Environment variable support with priority
- Author and metadata formatting
- Configuration file discovery at `projects/{name}/manuscript/config.yaml`
- Environment variable export
- Translation language configuration

**text_slug.py**
- Shared ASCII slug helpers: `slugify_token`, `extract_surname`, `title_key_word`, `pascal_case_token`
- Used by citation-key generation (`infrastructure/reference/citation/converter.py`) and deposit upload filenames (`infrastructure/publishing/deposit_filename.py`)
- `TITLE_STOP_WORDS` — stop-word set for title tokenization

**credentials.py**
- Credential management from .env and YAML config files
- Environment variable loading
- YAML configuration with environment variable substitution
- **Optional dependency**: `python-dotenv` (graceful fallback if not installed)
- Supports credential access from multiple sources

**progress.py**
- Progress bar utilities for long-running operations
- Sub-stage progress tracking
- Visual progress indicators

**runtime/checkpoint.py**
- Pipeline checkpoint management
- Save/restore pipeline state
- Stage result tracking

**runtime/retry.py**
- Retry logic with exponential backoff
- Transient failure handling
- Retryable operation wrappers

**pipeline/stage_monitor.py**
- Stage-level performance monitoring and resource tracking
- Timing, memory, CPU, and IO metrics (psutil optional)

**runtime/function_profiler.py**
- Function-level profiling utilities
- Decorators/context managers for targeted profiling

**security.py**
- Security utilities and input sanitization
- Security event monitoring
- Rate limiting and health checks

**runtime/health_check.py**
- System health monitoring
- Component status checking
- Health status reporting

**health.py**
- Unified repository health check entry point (`uv run python -m infrastructure.core.health`)
- Aggregates every per-CLI quality gate (mypy, ruff, ruff-format, bandit, no-mocks, `__all__` audit, docs-lint, stage-table & api-reference idempotence, architecture-overview presence) into a single typed `HealthReport`
- Subprocess-only orchestrator — exit code is the sole pass/fail signal; stdout/stderr captured for diagnostics only
- `--json` for machine-readable output (consumed by CI artefact upload), `--gates=<names>` for subset runs, `--quiet`, `--repo-root`, `--no-color`
- Public API: `GateResult`, `HealthReport`, `GATE_NAMES`, `build_gate_specs`, `run_health_checks`, `format_report_table`, `main`

**agent_memory.py**
- Load/save gitignored continual-learning agent memory at `.cursor/hooks/state/continual-learning-memory.json`
- Schema example (tracked): `.cursor/hooks/state/continual-learning-memory.example.json` — see [`.cursor/hooks/state/README.md`](../../.cursor/hooks/state/README.md)
- `audit_memory_payload()` returns advisory warnings when local memory hard-codes public project rosters or measured counts; see [`docs/rules/memory_and_decision_records.md`](../../docs/rules/memory_and_decision_records.md)
- Constants: `MEMORY_REL_PATH`, `EXAMPLE_REL_PATH`, `MAX_BULLETS` (12)
- Public API: `MemoryAdvisory`, `memory_path(repo_root)`, `example_path(repo_root)`, `empty_memory_payload()`, `normalize_bullets(items, *, max_items=MAX_BULLETS)`, `audit_memory_payload(payload)`, `load_memory(repo_root)`, `save_memory(repo_root, payload)`
- Tests: `tests/infra_tests/core/test_agent_memory.py`

**pytest_marker_exprs.py**
- ``build_pytest_marker_expression(...)`` returns one ``pytest -m`` string for subprocess runners (`pipeline_test_runner`, ``run_per_project_pytest``) so benchmarks and slow/Ollama-gated tests stay opt-in outside defaults.

**pytest_orchestration.py**
- Canonical Stage-01 / union-gate pytest subprocess policy: discovery logging, coverage datafile pinning, declared project ``fail_under``, and project-suite guards. Project subprocesses inject pytest/pytest-cov/pytest-timeout and pin `coverage==<workspace coverage version>` so `--cov-append` writes a single readable SQLite trace across mixed project environments. Consumed by ``infrastructure.reporting.pipeline_test_runner`` and ``infrastructure.core.test_runner``.
- ``resolve_xdist_args(parallel=None) -> list[str]`` centralizes **opt-in** pytest-xdist parallelism. Parallel argv uses work-stealing distribution and disables pytest-benchmark timing under xdist; project subprocesses inject both plugins. Resolution order: explicit ``parallel`` arg → ``PYTEST_XDIST_WORKERS`` env var → serial. ``0``/``1``/``none``/``off``/unparseable collapse to serial (one xdist worker is pure overhead). Threaded through ``build_union_pytest_command(..., parallel=...)``, ``run_per_project_pytest(..., parallel=...)``, and ``pipeline_test_runner`` (infra + project + ``execute_test_pipeline``), surfaced as the ``-n/--parallel`` flag on ``scripts/01_run_tests.py`` and ``scripts/pipeline/stage_01_test.py``. Default stays **serial** to preserve the load-contention safety documented in the root ``CLAUDE.md`` Testing section; coverage is unaffected because pytest-cov combines per-worker data before the datafile is written. Mirrors the ``MULTI_PROJECT_MAX_WORKERS`` opt-in convention of ``infrastructure.core.pipeline.multi_project_parallel``.

**analysis_pipeline.py**
- Stage-02 analysis-script runner: executes the discovered scripts under the standard subprocess contract (project-preferred interpreter, per-script timeout, sub-stage progress with EMA-based ETA), keeping `scripts/pipeline/stage_02_analysis.py` a thin orchestrator
- Public API: `run_analysis_script(script_path, repo_root, project_name)`, `run_analysis_pipeline(scripts, repo_root, project_name)`

**analysis_timeout.py**
- Resolves the per-script Stage-02 subprocess timeout from `ANALYSIS_SCRIPT_TIMEOUT_SEC` (default 7200s; `0`/`none`/`unlimited`/`inf` disables it; invalid/negative falls back to the default)
- Public API: `parse_analysis_script_timeout_sec(environ=None) -> float | None`

**coverage_policy.py**
- Coverage-plugin capability probe with no reporting imports (Layer 1)
- `check_cov_datafile_support() -> bool` — True when the installed pytest-cov supports the `--cov-datafile` flag

**determinism.py**
- Build-time reproducibility resolution around the `SOURCE_DATE_EPOCH` standard; precedence is an already-set `SOURCE_DATE_EPOCH` env var, then deterministic mode (author-date epoch of `HEAD` via git), then wall clock
- Public API: `is_deterministic_requested`, `resolve_source_date_epoch`, `resolve_build_timestamp`, `deterministic_subprocess_env`, constant `TEMPLATE_DETERMINISTIC_ENV`

**install_commands.py**
- OS-appropriate installation command generation; standalone with no infrastructure dependencies so it is import-safe from `exceptions.py`
- `build_install_commands(dependency) -> list[str]`

**lifecycle_discovery.py**
- Discovers top-level entries under `projects/` for pipeline discovery, classifying each directory as `standalone` (valid project) or `program`, skipping non-rendered lifecycle subdirs and dot-prefixed names
- Public API: `discover_program_entries(projects_dir, config=None)`, dataclasses `ProgramEntry` and `LifecycleDiscoveryConfig`, type `EntryKind`

**project_paths.py**
- Pure `pathlib` project-path primitives with no dependency on `infrastructure.project`, avoiding a `core ↔ project` layering cycle (re-exported by `infrastructure.project.discovery`)
- Public API: `find_repo_root()`, `resolve_project_root(repo_root, project_name)`, constant `NON_RENDERED_SUBDIRS`

**project_pyproject.py**
- Cached single-read accessors for a project `pyproject.toml`'s test/coverage settings
- Public API: `load_project_pyproject`, `project_declared_coverage_floor`, `resolve_project_cov_config`, `project_declares_dev_extra`, dataclass `ProjectPyprojectConfig`

**sidecar_linking.py**
- Generic sidecar lifecycle symlink sync for template checkouts: creates/updates/prunes managed symlinks under `projects/` from a resolved private root, honoring per-pool env/config overrides
- Public API: `sync_private_links`, `resolve_private_root`, `is_managed_symlink`, dataclasses `SidecarLinkConfig` and `LinkSyncResult`

**cli.py**
- Command-line interface utilities
- CLI argument parsing and validation

**cli_parser.py**
- `create_parser()` builds the argparse parser and the `pipeline`, `multi-project`, `inventory`, and `discover` subcommands for `python -m infrastructure.core.cli`

**cli_handlers.py**
- Command handlers dispatched from the CLI entry point; each takes a parsed `argparse.Namespace` and returns an exit code
- Public API: `handle_pipeline_command`, `handle_multi_project_command`, `handle_inventory_command`, `handle_discover_command`

**cli_scaffold.py**
- Shared CLI flag definitions and argparse schema introspection — an opt-in convergence point so adopting CLIs name flags identically and can emit a machine-readable parameter contract
- Public API: `add_repo_root_arg`, `add_project_arg`, `add_format_arg`, `add_verbose_arg`, `add_schema_flag`, `parser_schema`, `emit_schema`

**config/cli.py**
- Configuration CLI commands
- Config file management from command line

**menu.py**
- Interactive menu system
- Menu-driven user interfaces

**logging/formatters.py**
- Logging formatter utilities
- Custom log format definitions

**logging/helpers.py**
- Logging helper functions
- Additional logging utilities

**logging/progress.py**
- Progress logging utilities
- Progress tracking with logging integration

**runtime/environment.py**
- Environment setup and validation
- Dependency checking and installation
- Build tool verification
- Directory structure setup

**script_discovery.py**
- Script discovery and execution
- Analysis script finding
- Orchestrator script discovery

**files/operations.py**
- File management utilities
- Output directory cleanup
- Final deliverable copying

**files/inventory.py**
- File inventory generation and management
- Directory scanning and categorization
- File size calculation and formatting
- Inventory reporting for pipeline summaries

**files/project_lock.py**
- Per-project POSIX advisory lock for pipeline and test runner
- Env-marker re-entrancy for subprocess test stages

**pipeline/executor.py**
- PipelineExecutor class for single project execution
- Pipeline configuration management
- Stage execution orchestration
- Checkpoint and logging integration

**pipeline/multi_project.py**
- MultiProjectOrchestrator class for cross-project execution
- Infrastructure test consolidation
- Parallel project pipeline execution
- Executive reporting integration

**pipeline/summary.py**
- Pipeline summary generation and reporting
- Performance metrics calculation
- File inventory integration
- Executive reporting for multi-project runs

**pipeline/dag.py**
- Declarative pipeline DAG engine
- YAML-based stage definition parsing from `pipeline.yaml`
- Topological sorting via Kahn's algorithm
- Tag-based stage filtering (`core`, `optional`, `llm`)
- Project-specific `pipeline.yaml` override support

**pipeline/pipeline.yaml**
- Default declarative pipeline stage definitions
- 14 declared pipeline stages (8 core + 2 LLM + 2 opt-in ebook/metadata + 2 opt-in bundle/archival); default full runs execute 10 core+LLM stages; `--core-only` runs 8
- Tag-based filtering for `--core-only` vs full pipeline
- Stage metadata: name, script, description, dependencies, tags
- Optional `telemetry:` configuration block

**pipeline/stage_vocabulary.py**
- Canonical stage names and aliases loaded from `pipeline.yaml`
- Shared by menu progress banners (`orchestration/menu.py`) and eval grader stage heuristics

**telemetry/collector.py**
- `TelemetryCollector` — unified stage-level metrics + diagnostic aggregation
- Bridges `StagePerformanceTracker` and `DiagnosticReporter`
- Context-managed `start_stage()` / `end_stage()` lifecycle
- Performance warning detection (slow stage, high memory, high CPU)
- JSON + text report persistence

**telemetry/config.py**
- `TelemetryConfig` dataclass (YAML-loadable via `from_dict()`)
- Configurable thresholds: `slow_stage_multiplier`, `high_memory_mb`, `high_cpu_percent`
- Output format selection: `json`, `text`

**telemetry/models.py**
- `StageTelemetry` — per-stage timing, resource usage, diagnostic counts
- `PipelineTelemetry` — full pipeline report with warnings and system info
- `PerformanceWarning` — individual anomaly record

**telemetry/retention.py**
- `rotate(reports_dir, *, keep=10, archive_subdir=".history") -> RotationResult` — moves any previous `telemetry.json` into `<reports_dir>/<archive_subdir>/telemetry-<unix_ts>.json` and prunes archived files beyond `keep` (oldest first). Idempotent; honors `TELEMETRY_KEEP` env var when invoked from `TelemetryCollector._persist_report()`.
- `RotationResult` — frozen dataclass (`archived`, `pruned`, `kept`) describing a single rotation call.

## Function Signatures

Detailed reference moved to [`References/function-signatures.md`](References/function-signatures.md).

## Usage Examples

Detailed reference moved to [`References/usage-examples.md`](References/usage-examples.md).

## Key Features

### Exception Handling
```python
from infrastructure.core import TemplateError
from infrastructure.core.exceptions import raise_with_context, chain_exceptions

try:
    risky_operation()
except ValueError as e:
    raise chain_exceptions(
        TemplateError("Operation failed"),
        e
    )
```

### Logging
```python
from infrastructure.core import get_logger, log_operation
from infrastructure.core.logging.utils import log_timing

logger = get_logger(__name__)
logger.info("Starting process")

with log_operation("Data processing", logger):
    process_data()

with log_timing("Algorithm execution", logger):
    run_algorithm()
```

### Configuration
```python
from infrastructure.core.config.loader import load_config, get_config_as_dict, find_config_file
from infrastructure.core.config.queries import get_translation_languages

config = load_config(Path("projects/{project_name}/manuscript/config.yaml"))
env_dict = get_config_as_dict(Path("."))  # Loads from projects/{project_name}/manuscript/config.yaml
config_path = find_config_file(Path("."))  # Returns projects/{project_name}/manuscript/config.yaml if found
languages = get_translation_languages(Path("."))
```

### Credential Management
```python
from infrastructure.core.credentials import CredentialManager

# Initialize with optional .env and YAML config files
# Note: python-dotenv is optional - system works without it
manager = CredentialManager(
    env_file=Path(".env"),
    config_file=Path("config.yaml")
)

# Get credentials from environment or config
api_key = manager.get("API_KEY", default="default_key")
```

**Optional Dependency**: The `CredentialManager` uses `python-dotenv` for `.env` file support, but gracefully falls back if not installed. Install with:
```bash
pip install python-dotenv
# or
uv add python-dotenv
```

### Progress Tracking
```python
from infrastructure.core import ProgressBar
from infrastructure.core.progress import SubStageProgress

with ProgressBar(total=100, desc="Processing") as pbar:
    for i in range(100):
        pbar.update(1)
```

### Checkpoint Management
```python
from infrastructure.core import CheckpointManager
from infrastructure.core.runtime.checkpoint import StageResult

checkpoint = CheckpointManager()
if checkpoint.checkpoint_exists():
    state = checkpoint.load_checkpoint()
else:
    # Run pipeline stages
    checkpoint.save_checkpoint(stage_results)
```

### Retry Logic
```python
from infrastructure.core.runtime import retry_with_backoff

@retry_with_backoff(max_attempts=3, base_delay=1.0)
def risky_operation():
    # Operation that may fail
    pass
```

### Performance Monitoring
```python
from infrastructure.core.pipeline import PerformanceMonitor, get_system_resources

with PerformanceMonitor() as monitor:
    # Your code here
    pass

resources = get_system_resources()
print(f"CPU: {resources.cpu_percent}%, Memory: {resources.memory_percent}%")
```

### Environment Setup
```python
from infrastructure.core.runtime.environment import check_python_version, check_dependencies, setup_directories

check_python_version(min_version=(3, 8))
check_dependencies(["pandas", "numpy"])
setup_directories(["output", "output/figures"])
```

### Script Discovery
```python
from infrastructure.core.script_discovery import discover_analysis_scripts, discover_orchestrators

scripts = discover_analysis_scripts(Path("projects/project/scripts"))
orchestrators = discover_orchestrators(Path("scripts"))
```

### File Operations
```python
from infrastructure.core.files.cleanup import clean_output_directory
from infrastructure.core.files.operations import copy_final_deliverables

clean_output_directory(Path("output"))
copy_final_deliverables(Path("projects/project/output"), Path("output/project"))
```

### File Inventory
```python
from infrastructure.core.files.inventory import FileInventoryManager

manager = FileInventoryManager(Path("projects/project/output"))
if manager.collect_files():
    manager.generate_inventory_output()
```

### Pipeline Execution
```python
from infrastructure.core.pipeline import PipelineExecutor, PipelineConfig

config = PipelineConfig(
    project_name="my_project",
    repo_root=Path("."),
    skip_infra=False,
    skip_llm=True
)

executor = PipelineExecutor(config)
results = executor.execute_core_pipeline()

for result in results:
    print(f"{result.name}: {result.exit_code} ({result.duration:.1f}s)")
```

### Multi-Project Orchestration
```python
from infrastructure.core.pipeline.multi_project import MultiProjectConfig, MultiProjectOrchestrator
from infrastructure.project.discovery import discover_projects

projects = discover_projects(Path("."))
config = MultiProjectConfig(
    repo_root=Path("."),
    projects=projects,
    run_infra_tests=True,
    run_llm=False
)

orchestrator = MultiProjectOrchestrator(config)
result = orchestrator.execute_all_projects_core()

print(f"Successful: {result.successful_projects}, Failed: {result.failed_projects}")
```

### Pipeline Summary
```python
from infrastructure.core.pipeline.summary import generate_pipeline_summary

summary = generate_pipeline_summary(
    stage_results=results,
    total_duration=123.45,
    output_dir=Path("output"),
    format="text"
)
print(summary)
```

## Testing

Run core tests with:
```bash
uv run pytest tests/infra_tests/test_core/
```

## Configuration

Environment variables:
- `LOG_LEVEL` - 0=DEBUG, 1=INFO, 2=WARNING, 3=ERROR (default: 1)
- `NO_EMOJI` - Disable emoji output (default: enabled for TTY)

**Optional Dependencies:**
- `python-dotenv` - For `.env` file support in `credentials.py` (graceful fallback if not installed)

## Integration

Core module is imported by all other infrastructure modules for:
- Exception handling and context preservation
- Logging and progress tracking
- Configuration loading and management

## Troubleshooting

### Configuration Not Loading

**Issue**: `load_config()` returns None or empty configuration.

**Solutions**:
- Verify `projects/{project_name}/manuscript/config.yaml` exists and is valid YAML
- Check file permissions (read access required)
- Review YAML syntax for errors
- Use `find_config_file()` to locate config file
- Fall back to environment variables if config file missing

### Logging Not Appearing

**Issue**: Log messages not visible or formatted incorrectly.

**Solutions**:
- Check `LOG_LEVEL` environment variable (0=DEBUG, 1=INFO, 2=WARN, 3=ERROR)
- Verify logger is initialized with `get_logger(__name__)`
- Check if output is redirected (TTY detection)
- Disable emoji with `NO_EMOJI=1` if terminal doesn't support them

### Exception Context Lost

**Issue**: Exception chaining doesn't preserve context.

**Solutions**:
- Use `chain_exceptions()` for proper chaining
- Use `raise_with_context()` to add context
- Check that original exception is passed as `from_exception`
- Review exception hierarchy (use TemplateError subclasses)

### Credential Loading Fails

**Issue**: `CredentialManager` can't load credentials.

**Solutions**:
- Verify `.env` file exists and is readable (if using)
- Check YAML config file format and syntax
- Ensure `python-dotenv` is installed for `.env` support (optional)
- Check environment variable names match expected keys
- Review credential file paths are correct

### Progress Bar Not Displaying

**Issue**: Progress bars don't appear or update.

**Solutions**:
- Verify `tqdm` is installed (required dependency)
- Check if output is redirected (progress bars need TTY)
- Ensure `update()` is called with correct increment
- Use context manager (`with ProgressBar(...)`) for proper cleanup

### Checkpoint Corruption

**Issue**: Checkpoint file is corrupted or unreadable.

**Solutions**:
- Verify checkpoint file path is writable
- Check disk space availability
- Review JSON syntax in checkpoint file
- Use `checkpoint_exists()` before loading
- Handle `JSONDecodeError` gracefully

## Best Practices

### Exception Handling

- **Use TemplateError Hierarchy**: Use appropriate exception types
- **Preserve Context**: Always chain exceptions with context
- **Provide Details**: Include file paths, line numbers, and operation context
- **Fail Gracefully**: Handle errors without crashing entire pipeline

### Logging

- **Use Appropriate Levels**: DEBUG for details, INFO for progress, WARN for issues, ERROR for failures
- **Include Context**: Log operation names, file paths, and relevant data
- **Use Decorators**: `@log_operation` and `@log_timing` for automatic logging
- **Consistent Format**: Use structured logging for parsing

### Configuration

- **Version Control**: Commit `config.yaml.example` but not `config.yaml` (may contain secrets)
- **Environment Variables**: Use for sensitive data (tokens, keys)
- **Defaults**: Provide sensible defaults for all configuration options
- **Validation**: Validate configuration on load

### Credential Management

- **Never Commit Secrets**: Use `.env` or environment variables
- **Use CredentialManager**: Centralized credential access
- **Graceful Fallback**: Handle missing credentials gracefully
- **Document Requirements**: Document required credentials clearly

### Performance

- **Monitor Resources**: Use `PerformanceMonitor` for long operations
- **Track Timing**: Use `log_timing` for performance-critical sections
- **Optimize Hot Paths**: Profile and optimize frequently called functions
- **Resource Limits**: Check system resources before heavy operations

### Checkpointing

- **Save Frequently**: Checkpoint after each successful stage
- **Validate Before Resume**: Always validate checkpoint integrity
- **Handle Corruption**: Gracefully handle corrupted checkpoints
- **Clean Up**: Remove checkpoints after successful completion

## Opt-in modules (not default pipeline)

| Module | Entry | Notes |
| --- | --- | --- |
| [`cache_gate.py`](cache_gate.py) | `scripts/gates/gate_cache.py` | Hermes cache validation; requires `HERMES_HOME` |
| [`source_improve.py`](source_improve.py) | `scripts/maintenance/batch_cogsec_improve.py` | AST-based mechanical Python hygiene fixes |

## See Also

- [README.md](README.md) - Quick reference guide
- [`validation/`](../validation/) - Validation & quality assurance
- [`../scripts/gates/AGENTS.md`](../../scripts/gates/AGENTS.md) - Opt-in gate scripts
