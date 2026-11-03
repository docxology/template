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

**health.py** / **health_gates.py**
- Unified repository health check entry point (`uv run python -m infrastructure.core.health`)
- `health_gates.build_gate_specs` owns the gate argv table; `health.py` re-exports it and runs the CLI
- Aggregates every per-CLI quality gate (mypy, ruff, ruff-format, bandit, no-mocks, `__all__` audit, docs-lint, stage-table & api-reference idempotence, architecture-overview presence) into a single typed `HealthReport`
- Subprocess-only orchestrator — exit code is the sole pass/fail signal; stdout/stderr captured for diagnostics only
- `--json` for machine-readable output (consumed by CI artefact upload), `--gates=<names>` for subset runs, `--quiet`, `--repo-root`, `--no-color`, and bounded `--workers` concurrency (`1` keeps serial diagnostics)
- Includes the executable methods-plan and public-capability gates so static health covers both infrastructure contracts and the canonical public exemplar roster.
- Public API: `GateResult`, `HealthReport`, `GATE_NAMES`, `build_gate_specs`, `run_health_checks`, `format_report_table`, `main`

**health_benchmark.py**
- Validates serial and parallel health JSON reports from the same clean checkout
- Fails closed unless commit, clean-tree state, worker count, and exact gate-argv digest match; both runs execute the complete canonical gate registry, pass, and improve wall time by the declared threshold
- Public API: `HealthRunSummary`, `HealthBenchmarkManifest`, `HealthBenchmarkError`, `load_health_report`, `build_health_benchmark_manifest`, `main`

**ci_policy.py**
- Derives the CI Gate's required job identities from the current workflow and rejects missing, duplicate, or incomplete dependencies.
- The thin `scripts/gates/ci_policy.py` entrypoint emits this set for the workflow; the Gate admits only its exact observed set and the documented conditional skips.
- Public API: `required_ci_jobs(repo_root)`

**agent_memory.py**
- Load/save gitignored continual-learning agent memory at `.agents/state/continual-learning-memory.json`
- Schema example (tracked): `.agents/state/continual-learning-memory.example.json` — see [`.agents/state/README.md`](../../.agents/state/README.md)
- `audit_memory_payload()` returns advisory warnings when local memory hard-codes public project rosters or measured counts; see [`docs/rules/memory_and_decision_records.md`](../../docs/rules/memory_and_decision_records.md)
- Constants: `MEMORY_REL_PATH`, `EXAMPLE_REL_PATH`, `MAX_BULLETS` (12)
- Public API: `MemoryAdvisory`, `memory_path(repo_root)`, `example_path(repo_root)`, `empty_memory_payload()`, `normalize_bullets(items, *, max_items=MAX_BULLETS)`, `audit_memory_payload(payload)`, `load_memory(repo_root)`, `save_memory(repo_root, payload)`
- Tests: `tests/infra_tests/core/test_agent_memory.py`

**Testing cluster — re-homed to [`testing/`](testing/AGENTS.md) (`CORE-TESTING-REHOME-1`)**

The pytest/testing modules below moved to the
[`infrastructure/core/testing/`](testing/README.md) subpackage. **Flat shims
are gone:** their old flat `infrastructure/core/<module>.py` back-compat shims
were deleted, and every historical import path now fails fast with
`ModuleNotFoundError` instead of silently resolving. Import the real homes
(`infrastructure.core.testing.*`) directly. The per-module documentation below
still applies verbatim:
`pytest_marker_exprs.py`, `pytest_orchestration.py`, `pytest_profiles.py`,
`public_matrix_receipt.py`, `project_test_matrix.py`,
`test_impact.py`, `test_performance.py`, `test_runner.py`,
`test_runner_cache.py`, `test_runner_outputs.py`, `coverage_policy.py`.

**pytest_marker_exprs.py**
- ``build_pytest_marker_expression(...)`` returns one ``pytest -m`` string for subprocess runners (`pipeline_test_runner`, ``run_per_project_pytest``) so benchmarks and slow/Ollama-gated tests stay opt-in outside defaults.

**pytest_orchestration.py**
- Canonical Stage-01 / union-gate pytest subprocess policy: discovery logging, isolated coverage datafile pinning, declared project ``fail_under``, and project-suite guards. Each project subprocess injects pytest/pytest-cov/pytest-timeout and pins `coverage==<workspace coverage version>` to its own readable SQLite trace; the runner combines those files only after all project floors pass, preventing parent-suite coverage contamination. Consumed by ``infrastructure.reporting.pipeline_test_runner`` and ``infrastructure.core.test_runner``.
- ``resolve_xdist_args(parallel=None) -> list[str]`` centralizes inner pytest-xdist parallelism. Parallel argv uses scope-based distribution to keep subprocess-heavy modules together and disables pytest-benchmark timing under xdist; project subprocesses inject both plugins. Resolution order: explicit ``parallel`` arg → ``PYTEST_XDIST_WORKERS`` env var → serial. ``0``/``1``/``none``/``off``/unparseable collapse to serial. ``parse_project_workers('auto')`` resolves a bounded outer matrix (default cap four, overridable with ``TEMPLATE_PROJECT_WORKERS``). Outer project workers and inner pytest-xdist remain mutually exclusive. Coverage data remains isolated per worker, and full coverage runs on macOS fail early above two workers because the supported developer lane has reproduced scheduler replacement failures at higher counts; Linux retains explicit higher-worker opt-in.

**test_performance.py**
- Owns matched serial/parallel Stage-01 test commands and fail-closed performance manifests for the fast `pipeline-smoke` lane, the full infrastructure lane, or the public project matrix.
- `scripts/maintenance/benchmark_tests.py` writes provenance-bound JSON evidence; it refuses dirty checkouts and requires both lanes to pass with identical selection and commit.

**test_runner_outputs.py**
- Owns the Git-visible output-tree inventory and content digest used by the
  isolated public-project test runner; ignored caches and runtime logs remain
  outside the receipt boundary, while tracked or non-ignored output changes
  fail the output-isolation contract.

**worker_policy.py**
- Shared bounded worker resolution for the outer public-project matrix and inner pytest-xdist lanes.
- `resolve_bounded_workers` applies explicit values, environment overrides, CPU-aware defaults, and a hard safety cap without allowing invalid or oversubscribed counts.
- Environment controls: `TEMPLATE_PROJECT_WORKERS` / `MULTI_PROJECT_MAX_WORKERS` for outer project concurrency and `PYTEST_XDIST_WORKERS` for inner test workers.

**project_test_matrix.py**
- Shared bounded subprocess service for public readiness, per-project union coverage, and parallel documentation counts. ``run_project_test_matrix(tasks, workers=...)`` isolates each task, applies a hard timeout, continues after failure/timeout, captures bounded diagnostics when requested, and returns results in canonical input order regardless of completion order. Outer project workers must not be combined with inner pytest-xdist workers; the higher-level orchestration validators enforce that boundary.

**subprocess_policy.py**
- Source-owned typed policy inventory for intentional subprocess wrappers. `SubprocessPolicy` requires positive finite numeric whole-operation and guardian-startup budgets (booleans are invalid), an existing source declaration, and a process-group boundary. The shared guardian defaults to a 60-second startup phase from source admission through READY and ARM; the original run deadline always takes precedence, and each handshake consumes that same phase clock. Source-admission and READY timeout precede command launch and are not descendant-cleanup evidence; ARM failure occurs after child launch, cleans actual token holders, and preserves observed interruption. Serialized policy records include the startup budget; `run_with_policy` delegates to the shared bounded executor and can fail closed on non-zero exits. `INTENTIONAL_SUBPROCESS_POLICIES` covers the project matrix, renderer, git metadata, validation, and optional formal-spec lanes.

**test_impact.py**
- Read-only changed-surface classifier. `scripts/audit/test_impact.py` unions staged, unstaged, deleted, and non-ignored untracked paths before `classify_changed_paths()` reports infrastructure, documentation, public-exemplar, and local-only impacts, recommends the smallest safe lanes, and explicitly prohibits nested outer-project parallelism with inner pytest-xdist.

**public_matrix_receipt.py**
- Deterministic public-matrix receipt for per-project release lanes: records one bounded public-matrix run (per-project coverage floors, pass/fail, duration, resource profile, collection count, cache identity, and explicit skip reason) into a versioned contract, and fails closed when the on-disk output tree would drift from the receipt after the run. `write_public_matrix_receipt` lives here and is called from `test_runner.py`. Backs the `--receipt` public-matrix mode and the scheduled `public-matrix-receipt` CI job.

**analysis_pipeline.py**
- Stage-02 runs admitted producers through the audited held-source launcher with a positive finite deadline and the existing nominated interpreter. It does not resolve or acquire dependencies while executing. Original leaf outcomes remain typed; interruption, timeout, or runtime/source blockage stops later producers. Paths remain confined to the project's `scripts/` tree. Credential-like environment variables are redacted by default; set `ANALYSIS_ALLOW_SECRETS=1` only for an explicitly reviewed live integration.
- Configured `analysis.scripts` entries are required: malformed configuration, missing producers, duplicates, non-Python utilities, and escapes refuse before execution. An explicit empty list declares no analysis; projects without an allowlist retain lexicographic discovery.
- Public API: `run_analysis_script_outcome(script_path, repo_root, project_name)`, `run_analysis_script(script_path, repo_root, project_name)`, `run_analysis_pipeline(scripts, repo_root, project_name)`

**execution_boundary.py**
- Bounded subprocess execution for project hooks and analysis scripts (SECURE-RUN-1 / PROJECT-EXECUTION-BOUNDARY-1): `run_bounded_subprocess` launches a command in a fresh process group so a timeout can `killpg` the whole tree (no orphaned descendants); `build_bounded_env` strips credential-like env vars unless explicitly allow-listed; `validate_hook_root` enforces root confinement; `classify_lifecycle_link` distinguishes intentional lifecycle links from escapes. Wired into `infrastructure.project.setup_hook.run_project_setup_hook` and `infrastructure.core.pipeline.hooks.run_stage_hooks`.
- Public API: `run_bounded_subprocess`, `build_bounded_env`, `validate_hook_root`, `classify_lifecycle_link`, `LinkClassification`, `BoundedSubprocessResult`

**analysis_timeout.py**
- Resolves a positive finite Stage-02 deadline from `ANALYSIS_SCRIPT_TIMEOUT_SEC` (default 7200s). Invalid, nonpositive, nonfinite, and retired unlimited values fail configuration admission before producers run.
- Public API: `parse_analysis_script_timeout_sec(environ=None) -> float`

**coverage_policy.py**
- Coverage-plugin capability probe with no reporting imports (Layer 1)
- `check_cov_datafile_support() -> bool` — True when the installed pytest-cov supports the `--cov-datafile` flag
- `PYTEST_HELP_PROBE_TIMEOUT_SECONDS` — bounded 30-second startup budget; it is deliberately longer than the ordinary test timeout because xdist workers can contend during pytest import on macOS

**determinism.py**
- Canonical execution admits `core` or explicitly selected `live` and pins `SOURCE_DATE_EPOCH` before computing the effective environment identity. An explicit nonnegative epoch wins; otherwise the nominated Git candidate supplies its committer epoch and revision. Non-Git exports require an explicit candidate epoch. Invalid epochs and clock-disable settings refuse instead of falling back to wall clock. Operation timestamps remain actual observation times.
- `execution_policy.apply_execution_policy` defines this admission. Direct timestamp utilities retain an explicit wall-clock API outside canonical execution; deterministic requests fail when their epoch is unavailable.
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
- Public API: `load_project_pyproject`, `project_declared_coverage_floor`, `project_declared_test_command`, `resolve_project_cov_config`, `project_declares_dev_extra`, dataclass `ProjectPyprojectConfig`
- `[tool.template].project_test_command` is an explicit, default-off argv contract for the single-project Stage-01 lane; malformed declarations fail closed. Stage 01 admits one existing selected interpreter against the workspace's exact pytest/Coverage runner versions without acquisition, requires project-local coverage evidence plus real warning/discovery/outcome counts, and gives the verifier a 6,900-second deadline inside the tree-killing 7,200-second stage boundary. The `--all-projects --public-projects` union runner honors the same source-declared verifier contract, retains independently admitted isolated coverage bytes, and runs declared lanes serially after the bounded ordinary pytest matrix. GitHub's per-project public matrix also invokes the single-project Stage-01 contract.

**sidecar_linking.py**
- Generic sidecar lifecycle symlink sync for template checkouts: creates/updates/prunes managed symlinks under any top-level resource tree (`projects/`, `fonds/`, `rules/`, `tools/`) from a resolved private root, honoring per-pool env/config overrides
- Owns the one `linking` CLI those four trees share: `build_link_sync_parser` (the `--repo-root`/`--private-root`/`--dry-run`/`--no-prune` contract) and `run_link_sync_cli` (parse, resolve, sync, report, return 0), so each tree's `linking.py` keeps only its `SidecarLinkConfig` and thin named wrappers
- Owns the result printer too: `print_link_sync_result` (summary + deltas on stdout) and `write_link_sync_deltas` (deltas only, for callers that prefix their own summary)
- Public API: `sync_private_links`, `resolve_private_root`, `is_managed_symlink`, `unmanaged_mirror_entries`, `build_link_sync_parser`, `run_link_sync_cli`, `print_link_sync_result`, `write_link_sync_deltas`, dataclasses `SidecarLinkConfig` and `LinkSyncResult`
- Characterization tests: [`tests/infra_tests/core/test_sidecar_linking.py`](../../tests/infra_tests/core/test_sidecar_linking.py) and [`tests/infra_tests/core/test_sidecar_linking_cli.py`](../../tests/infra_tests/core/test_sidecar_linking_cli.py) (the latter pins all four tree CLIs against one contract)

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
- Declared / default-full / `--mode core` counts come from `pipeline.yaml` via `STAGE_SUMMARY` (see root `AGENTS.md`); `opt_in_tags` is the single exclude set for default and `--mode core` runs
- Tag-based filtering for `--mode core` vs full pipeline
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
config_path = find_config_file(Path("."), project_name="templates/template_code_project")
# Unqualified lookup returns a path only when exactly one manuscript config exists.
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
    mode="core"
)

executor = PipelineExecutor(config)
results = executor.execute_pipeline()

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
    mode="core"
)

orchestrator = MultiProjectOrchestrator(config)
result = orchestrator.execute_all_projects()

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

## Release acceptance modules

| Module | Role |
| --- | --- |
| `analysis_data_custody.py` | Retain actual boundary data bytes around supervised analysis execution. |
| `analysis_evidence.py` | Private, source-bound aggregate evidence for supervised analysis producers. |
| `analysis_figure_custody.py` | Observe the existing six plotted figures inside the actual analysis scope. |
| `analysis_launch.py` | Analysis adapter for the canonical audited Python stage supervisor. |
| `analysis_read_custody.py` | Observe exact bytes returned by the real Source-owned project read API. |
| `analysis_write_custody.py` | Observe actual completed Source API writes inside the genuine script scope. |
| `bytecode_audit.py` | Stdlib-only pre-import audit of executed public code and its cache bytes. |
| `implementation_custody.py` | Actual public implementation and installed-distribution custody. |
