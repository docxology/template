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

**credentials.py** (`infrastructure/core/credentials.py`, not under `config/`)
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

**cli.py**
- Command-line interface utilities
- CLI argument parsing and validation

**config/config_cli.py**
- Configuration CLI commands
- Config file management from command line

**menu.py**
- Interactive menu system
- Menu-driven user interfaces

**logging/logging_formatters.py**
- Logging formatter utilities
- Custom log format definitions

**logging/logging_helpers.py**
- Logging helper functions
- Additional logging utilities

**logging/logging_progress.py**
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

**files/file_inventory.py**
- File inventory generation and management
- Directory scanning and categorization
- File size calculation and formatting
- Inventory reporting for pipeline summaries

**pipeline/pipeline.py**
- PipelineExecutor class for single project execution
- Pipeline configuration management
- Stage execution orchestration
- Checkpoint and logging integration

**pipeline/multi_project.py**
- MultiProjectOrchestrator class for cross-project execution
- Infrastructure test consolidation
- Parallel project pipeline execution
- Executive reporting integration

**pipeline/pipeline_summary.py**
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
- 10 stages with dependency graph (DAG)
- Tag-based filtering for `--core-only` vs full pipeline
- Stage metadata: name, script, description, dependencies, tags
- Optional `telemetry:` configuration block

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

### Source of truth

Long signature blocks below are historical reference; they can drift. For **current** types and behavior, read the Python modules (and [`runtime/AGENTS.md`](runtime/AGENTS.md), [`pipeline/AGENTS.md`](pipeline/AGENTS.md), [`telemetry/AGENTS.md`](telemetry/AGENTS.md), [`logging/AGENTS.md`](logging/AGENTS.md) where present). `progress`, `runtime/checkpoint`, and `runtime/retry` are summarized concisely inline; avoid duplicating full class listings elsewhere in this file.

## Function Signatures

### exceptions.py

#### TemplateError (class)
```python
class TemplateError(Exception):
    def __init__(
        self,
        message: str,
        context: Optional[dict[str, Any]] = None,
        suggestions: Optional[list[str]] = None,
        recovery_commands: Optional[list[str]] = None
    ) -> None:
        """Base exception for all template-related errors.

        Args:
            message: Human-readable error description
            context: Additional context about the error
            suggestions: List of actionable recovery suggestions
            recovery_commands: List of command-line commands to fix the issue
        """
```

#### ConfigurationError (class)
```python
class ConfigurationError(TemplateError):
    """Raised when configuration is invalid or missing."""
    pass
```

#### MissingConfigurationError (class)
```python
class MissingConfigurationError(ConfigurationError):
    """Raised when required configuration is missing."""
    pass
```

#### InvalidConfigurationError (class)
```python
class InvalidConfigurationError(ConfigurationError):
    """Raised when configuration values are invalid."""
    pass
```

#### ValidationError (class)
```python
class ValidationError(TemplateError):
    """Raised when validation fails."""
    pass
```

#### MarkdownValidationError (class)
```python
class MarkdownValidationError(ValidationError):
    """Raised when markdown validation fails."""
    pass
```

#### PDFValidationError (class)
```python
class PDFValidationError(ValidationError):
    """Raised when PDF validation fails."""
    pass
```

#### DataValidationError (class)
```python
class DataValidationError(ValidationError):
    """Raised when data validation fails."""
    pass
```

#### BuildError (class)
```python
class BuildError(TemplateError):
    """Raised when build process fails."""
    pass
```

#### CompilationError (class)
```python
class CompilationError(BuildError):
    """Raised when compilation (LaTeX, etc.) fails."""
    pass
```

#### ScriptExecutionError (class)
```python
class ScriptExecutionError(BuildError):
    """Raised when script execution fails."""
    pass
```

#### PipelineError (class)
```python
class PipelineError(BuildError):
    """Raised when pipeline orchestration fails."""
    pass
```

#### FileOperationError (class)
```python
class FileOperationError(TemplateError):
    """Raised when file operations fail."""
    pass
```

#### FileNotFoundError (class)
```python
class FileNotFoundError(FileOperationError):
    """Raised when a required file is not found.

    Note: This shadows Python's built-in FileNotFoundError, but provides
    better context for template-specific file errors.

    Automatically generates recovery commands based on file path.
    """

    def __init__(
        self,
        message: str,
        context: Optional[dict[str, Any]] = None,
        suggestions: Optional[list[str]] = None,
        recovery_commands: Optional[list[str]] = None
    ) -> None:
        """Initialize file not found error with automatic recovery commands.

        Args:
            message: Error message
            context: Error context (should include 'file' key)
            suggestions: Optional suggestions (auto-generated if None)
            recovery_commands: Optional commands (auto-generated if None)
        """
```

#### InvalidFileFormatError (class)
```python
class InvalidFileFormatError(FileOperationError):
    """Raised when file format is invalid or unexpected."""
    pass
```

#### DependencyError (class)
```python
class DependencyError(TemplateError):
    """Raised when dependencies are missing or invalid."""
    pass
```

#### MissingDependencyError (class)
```python
class MissingDependencyError(DependencyError):
    """Raised when a required dependency is missing.

    Automatically generates installation commands based on dependency name.
    """

    def __init__(
        self,
        message: str,
        context: Optional[dict[str, Any]] = None,
        suggestions: Optional[list[str]] = None,
        recovery_commands: Optional[list[str]] = None
    ) -> None:
        """Initialize missing dependency error with automatic installation commands.

        Args:
            message: Error message
            context: Error context (should include 'dependency' key)
            suggestions: Optional suggestions (auto-generated if None)
            recovery_commands: Optional commands (auto-generated if None)
        """
```

#### VersionMismatchError (class)
```python
class VersionMismatchError(DependencyError):
    """Raised when dependency version is incompatible."""
    pass
```

#### TestError (class)
```python
class TestError(TemplateError):
    """Raised when test execution or validation fails."""
    pass
```

#### InsufficientCoverageError (class)
```python
class InsufficientCoverageError(TestError):
    """Raised when test coverage is insufficient."""
    pass
```

#### IntegrationError (class)
```python
class IntegrationError(TemplateError):
    """Raised when component integration fails."""
    pass
```

#### LiteratureSearchError (class)
```python
class LiteratureSearchError(TemplateError):
    """Raised when literature search operations fail."""
    pass
```

#### APIRateLimitError (class)
```python
class APIRateLimitError(LiteratureSearchError):
    """Raised when API rate limits are exceeded."""
    pass
```

#### InvalidQueryError (class)
```python
class InvalidQueryError(LiteratureSearchError):
    """Raised when search query is invalid."""
    pass
```

#### LLMError (class)
```python
class LLMError(TemplateError):
    """Base exception for LLM operations."""
    pass
```

#### LLMConnectionError (class)
```python
class LLMConnectionError(LLMError):
    """Raised when connecting to LLM provider fails."""
    pass
```

#### LLMTemplateError (class)
```python
class LLMTemplateError(LLMError):
    """Raised when template processing fails."""
    pass
```

#### ContextLimitError (class)
```python
class ContextLimitError(LLMError):
    """Raised when token limit is exceeded."""
    pass
```

#### RenderingError (class)
```python
class RenderingError(TemplateError):
    """Base exception for rendering operations."""
    pass
```

#### FormatError (class)
```python
class FormatError(RenderingError):
    """Raised when output format is invalid or unsupported."""
    pass
```

#### TemplateRenderingError (class)
```python
class TemplateRenderingError(RenderingError):
    """Raised when rendering a template fails."""
    pass
```

#### PublishingError (class)
```python
class PublishingError(TemplateError):
    """Base exception for publishing operations."""
    pass
```

#### UploadError (class)
```python
class UploadError(PublishingError):
    """Raised when file upload fails."""
    pass
```

#### MetadataError (class)
```python
class MetadataError(PublishingError):
    """Raised when metadata validation fails."""
    pass
```

#### raise_with_context (function)
```python
def raise_with_context(
    exception_class: type[TemplateError],
    message: str,
    **context: Any
) -> None:
    """Raise an exception with context information.

    Args:
        exception_class: Exception class to raise
        message: Error message
        **context: Context information as keyword arguments

    Raises:
        exception_class: The specified exception with context
    """
```

#### format_file_context (function)
```python
def format_file_context(file_path: Path | str, line: Optional[int] = None) -> dict[str, Any]:
    """Format file path and optional line number as error context.

    Args:
        file_path: Path to file
        line: Optional line number

    Returns:
        Context dictionary with file and line information
    """
```

#### chain_exceptions (function)
```python
def chain_exceptions(
    new_exception: TemplateError,
    original: Exception
) -> TemplateError:
    """Chain a new exception with the original exception's context.

    Args:
        new_exception: New exception to raise
        original: Original exception that was caught

    Returns:
        New exception with chained context
    """
```

### logging/utils.py

#### get_log_level_from_env (function)
```python
def get_log_level_from_env() -> int:
    """Get log level from LOG_LEVEL environment variable.

    Returns:
        Python logging level (DEBUG, INFO, WARNING, ERROR)
    """
```

#### setup_logger (function)
```python
def setup_logger(
    name: str,
    level: Optional[int] = None,
    log_file: Optional[Path | str] = None
) -> logging.Logger:
    """Set up a logger with consistent formatting.

    Args:
        name: Logger name (usually __name__)
        level: Logging level (None = use environment)
        log_file: Optional file to write logs to

    Returns:
        Configured logger instance
    """
```

#### get_logger (function)
```python
def get_logger(name: str) -> logging.Logger:
    """Get or create a logger with standard configuration.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
```

#### set_global_log_level (function)
```python
def set_global_log_level(level: int) -> None:
    """Set log level for all template loggers.

    Args:
        level: Python logging level (DEBUG, INFO, WARNING, ERROR)
    """
```

#### log_operation (function)
```python
@contextmanager
def log_operation(
    operation: str,
    logger: Optional[logging.Logger] = None,
    level: int = logging.INFO,
    min_duration_to_log: float = 0.1
) -> Iterator[None]:
    """Context manager for logging operation start and completion.

    Args:
        operation: Description of the operation
        logger: Logger instance (creates one if None)
        level: Log level for messages
        min_duration_to_log: Minimum duration (seconds) to log completion message

    Yields:
        None
    """
```

#### log_operation_silent (function)
```python
@contextmanager
def log_operation_silent(
    operation: str,
    logger: Optional[logging.Logger] = None,
    level: int = logging.DEBUG
) -> Iterator[None]:
    """Context manager for logging operation start only (no completion message).

    Args:
        operation: Description of the operation
        logger: Logger instance (creates one if None)
        level: Log level for messages

    Yields:
        None
    """
```

#### log_timing (function)
```python
@contextmanager
def log_timing(
    label: str,
    logger: Optional[logging.Logger] = None
) -> Iterator[None]:
    """Context manager for timing operations.

    Args:
        label: Label for the timed operation
        logger: Logger instance (creates one if None)

    Yields:
        None
    """
```

#### log_function_call (function)
```python
def log_function_call(logger: Optional[logging.Logger] = None) -> Callable:
    """Decorator to log function calls with timing.

    Args:
        logger: Logger instance (creates one if None)

    Returns:
        Decorator function
    """
```

#### log_success (function)
```python
def log_success(message: str, logger: Optional[logging.Logger] = None) -> None:
    """Log a success message with success emoji.

    Args:
        message: Success message
        logger: Logger instance (creates one if None)
    """
```

#### log_header (function)
```python
def log_header(message: str, logger: Optional[logging.Logger] = None) -> None:
    """Log a section header with visual emphasis.

    Args:
        message: Header message
        logger: Logger instance (creates one if None)
    """
```

#### log_progress (function)
```python
def log_progress(
    current: int,
    total: int,
    task: str,
    logger: Optional[logging.Logger] = None
) -> None:
    """Log progress with percentage.

    Args:
        current: Current item number
        total: Total number of items
        task: Task description
        logger: Logger instance (creates one if None)
    """
```

#### log_stage (function)
```python
def log_stage(
    stage_num: int,
    total_stages: int,
    stage_name: str,
    logger: Optional[logging.Logger] = None
) -> None:
    """Log a pipeline stage header with consistent formatting.

    Args:
        stage_num: Current stage number (1-based)
        total_stages: Total number of stages
        stage_name: Name of the stage
        logger: Logger instance (creates one if None)
    """
```

#### log_substep (function)
```python
def log_substep(
    message: str,
    logger: Optional[logging.Logger] = None
) -> None:
    """Log a substep within a stage with consistent indentation.

    Args:
        message: Substep description
        logger: Logger instance (creates one if None)
    """
```

#### log_stage_with_eta (function)
```python
def log_stage_with_eta(
    stage_num: int,
    total_stages: int,
    stage_name: str,
    pipeline_start: Optional[float] = None,
    logger: Optional[logging.Logger] = None
) -> None:
    """Log a pipeline stage header with ETA calculation.

    Args:
        stage_num: Current stage number (1-based)
        total_stages: Total number of stages
        stage_name: Name of the stage
        pipeline_start: Pipeline start time (for ETA calculation)
        logger: Logger instance (creates one if None)
    """
```

#### log_resource_usage (function)
```python
def log_resource_usage(
    stage_name: str = "",
    logger: Optional[logging.Logger] = None
) -> None:
    """Log current resource usage (if psutil available).

    Args:
        stage_name: Name of the stage (for context)
        logger: Logger instance (creates one if None)
    """
```

### config/loader.py

#### load_config (function)
```python
def load_config(config_path: Path | str) -> Optional[Dict[str, Any]]:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config.yaml file

    Returns:
        Dictionary of configuration data, or None if file doesn't exist or can't be loaded
    """
```

#### format_author_details (function)
```python
def format_author_details(authors: List[Dict[str, Any]], doi: str = "") -> str:
    """Format author details string for LaTeX.

    Args:
        authors: List of author dictionaries (name, orcid, email, etc.)
        doi: Optional DOI string to include

    Returns:
        Formatted string with LaTeX line breaks
    """
```

#### format_author_name (function)
```python
def format_author_name(authors: List[Dict[str, Any]]) -> str:
    """Format author name(s) for display.

    Args:
        authors: List of author dictionaries

    Returns:
        Primary author name or "Project Author" if empty
    """
```

#### get_config_as_dict (function)
```python
def get_config_as_dict(repo_root: Path | str) -> Dict[str, str]:
    """Get configuration as a dictionary of key-value pairs.

    Loads configuration from projects/{name}/manuscript/config.yaml.

    Args:
        repo_root: Root directory of the repository

    Returns:
        Dictionary of configuration values (PROJECT_TITLE, AUTHOR_NAME, etc.)
    """
```

#### get_config_as_env_vars (function)
```python
def get_config_as_env_vars(repo_root: Path | str, respect_existing: bool = True) -> Dict[str, str]:
    """Get configuration as environment variables.

    Args:
        repo_root: Root directory of the repository
        respect_existing: If True, don't override existing environment variables

    Returns:
        Dictionary of environment variable assignments
    """
```

#### find_config_file (function)
```python
def find_config_file(repo_root: Path | str) -> Optional[Path]:
    """Find the manuscript config file at the standard location.

    Args:
        repo_root: Root directory of the repository

    Returns:
        Path to config.yaml if found at projects/{name}/manuscript/config.yaml, None otherwise
    """
```

#### get_translation_languages (function)
```python
def get_translation_languages(repo_root: Path | str) -> List[str]:
    """Get list of enabled translation languages from config.

    Reads the llm.translations section from config.yaml and returns
    the list of enabled language codes.

    Args:
        repo_root: Root directory of the repository

    Returns:
        List of language codes (e.g., ['zh', 'hi', 'ru']) if translations
        are enabled, empty list otherwise
    """
```

#### get_testing_config (function)
```python
def get_testing_config(repo_root: Path | str) -> Dict[str, Any]:
    """Get testing configuration from config.yaml.

    Reads the testing section from config.yaml and returns
    configuration values for test failure tolerance.

    Args:
        repo_root: Root directory of the repository

    Returns:
        Dictionary with testing configuration values:
        - max_test_failures: Maximum acceptable test failures (default: 0)
        - max_infra_test_failures: Maximum acceptable infrastructure test failures (default: 0)
        - max_project_test_failures: Maximum acceptable project test failures (default: 0)
        Returns empty dict if config file not found or invalid
    """
```

### credentials.py

`CredentialManager` loads optional `.env` (via `python-dotenv` when installed) and optional YAML with `${VAR}` substitution. Public methods: `get_zenodo_credentials`, `get_github_credentials`, `get_arxiv_credentials`, `has_*_credentials`. Module helpers: `make_bearer_auth_headers`, `make_token_auth_headers`.

### progress.py

Authoritative API: [`progress.py`](progress.py) — `ProgressBar` (`task`, `update(value, force=...)`, `finish`), `LLMProgressTracker`, `SubStageProgress` (`start_substage`, `complete_substage`, ETA helpers).

### runtime/checkpoint.py

Authoritative API: [`runtime/checkpoint.py`](runtime/checkpoint.py).

- `StageResult` — per-stage `name`, `exit_code`, `duration`, `timestamp`, `completed`, `status`.
- `PipelineCheckpoint` — `pipeline_start_time`, `last_stage_completed`, `stage_results`, `total_stages`, `checkpoint_time`; `to_dict()` / `from_dict()`.
- `CheckpointManager` — resolves `checkpoint_dir` from an explicit path, from `project_dir/output/.checkpoints`, or from `repo_root/projects/{project_name}/output/.checkpoints`; JSON file `pipeline_checkpoint.json`; `save_checkpoint`, `load_checkpoint`, `clear_checkpoint`, `checkpoint_exists`, `validate_checkpoint`.

### runtime/retry.py

Authoritative API: [`runtime/retry.py`](runtime/retry.py).

- `retry_with_backoff(...)` — **decorator factory** (`max_attempts`, `initial_delay`, `max_delay`, `exponential_base`, `jitter`, `exceptions`, `on_retry`).
- `retry_on_transient_failure` — shorthand using `TRANSIENT_EXCEPTIONS` (`ConnectionError`, `TimeoutError`, `OSError`) and capped `max_delay`.
- `RetryableOperation` — context manager / iterator for manual per-attempt control; `succeed()`, `retry(exception)`.

### pipeline/stage_monitor.py

#### PerformanceMonitor (class)
```python
class PerformanceMonitor:
    """Monitor system performance during operations.

    Tracks CPU usage, memory usage, and other system metrics.
    """

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """Initialize performance monitor.

        Args:
            logger: Logger instance for performance messages
        """

    def start_monitoring(self) -> None:
        """Start performance monitoring."""

    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring and return performance statistics.

        Returns:
            Dictionary with performance metrics
        """

    def get_current_stats(self) -> Dict[str, Any]:
        """Get current performance statistics.

        Returns:
            Dictionary with current performance metrics
        """
```

#### get_system_resources (function)
```python
def get_system_resources() -> Dict[str, Any]:
    """Get current system resource usage.

    Returns:
        Dictionary with system resource information:
        - cpu_percent: CPU usage percentage
        - memory_percent: Memory usage percentage
        - memory_used: Memory used in bytes
        - memory_available: Available memory in bytes
        - disk_usage: Disk usage information
    """
```

### runtime/environment.py

#### check_python_version (function)
```python
def check_python_version(min_version: Tuple[int, int] = (3, 8)) -> bool:
    """Check if current Python version meets minimum requirements.

    Args:
        min_version: Minimum required Python version as (major, minor) tuple

    Returns:
        True if version requirement is met
    """
```

#### check_dependencies (function)
```python
def check_dependencies(requirements: List[str]) -> Dict[str, bool]:
    """Check if required Python packages are installed.

    Args:
        requirements: List of package names to check

    Returns:
        Dictionary mapping package names to installation status
    """
```

#### check_build_tools (function)
```python
def check_build_tools(tools: List[str]) -> Dict[str, bool]:
    """Check if required build tools are available in PATH.

    Args:
        tools: List of tool names to check (e.g., ['pandoc', 'xelatex'])

    Returns:
        Dictionary mapping tool names to availability status
    """
```

#### setup_environment (function)
```python
def setup_environment(
    repo_root: Path,
    check_python: bool = True,
    check_deps: bool = True,
    check_tools: bool = True,
    create_dirs: bool = True
) -> Dict[str, Any]:
    """Perform environment setup and validation.

    Args:
        repo_root: Repository root directory
        check_python: Whether to check Python version
        check_deps: Whether to check dependencies
        check_tools: Whether to check build tools
        create_dirs: Whether to create required directories

    Returns:
        Dictionary with setup results and status
    """
```

### script_discovery.py

#### discover_analysis_scripts (function)
```python
def discover_analysis_scripts(project_dir: Path) -> List[Path]:
    """Discover analysis scripts in project scripts directory.

    Args:
        project_dir: Project directory to search

    Returns:
        List of script file paths
    """
```

#### discover_orchestrators (function)
```python
def discover_orchestrators(repo_root: Path) -> List[Path]:
    """Discover orchestrator scripts in repository.

    Args:
        repo_root: Repository root directory

    Returns:
        List of orchestrator script paths
    """
```

#### validate_script (function)
```python
def validate_script(script_path: Path) -> Dict[str, Any]:
    """Validate that a script file is executable and properly structured.

    Args:
        script_path: Path to script file

    Returns:
        Dictionary with validation results
    """
```

### files/operations.py

#### clean_output_directory (function)
```python
def clean_output_directory(output_dir: Path) -> None:
    """Clean an output directory by removing all files and subdirectories.

    Args:
        output_dir: Directory to clean

    Returns:
        True if cleaning was successful
    """
```

#### clean_output_directories (function)
```python
def clean_output_directories(
    repo_root: Path,
    project_names: List[str]
) -> Dict[str, bool]:
    """Clean output directories for multiple projects.

    Args:
        repo_root: Repository root directory
        project_names: List of project names

    Returns:
        Dictionary mapping project names to cleaning success status
    """
```

#### copy_final_deliverables (function)
```python
def copy_final_deliverables(
    repo_root: Path,
    project_name: str,
    output_dir: Optional[Path] = None
) -> List[Path]:
    """Copy final deliverables from project output to main output directory.

    Args:
        repo_root: Repository root directory
        project_name: Name of the project
        output_dir: Target output directory (default: repo_root/output/project_name)

    Returns:
        List of copied file paths
    """
```

### files/file_inventory.py

#### generate_file_inventory (function)
```python
def generate_file_inventory(directory: Path) -> Dict[str, Any]:
    """Generate file inventory for a directory.

    Args:
        directory: Directory to inventory

    Returns:
        Dictionary with file inventory information
    """
```

#### calculate_directory_size (function)
```python
def calculate_directory_size(directory: Path) -> Dict[str, Any]:
    """Calculate total size and file counts for a directory.

    Args:
        directory: Directory to analyze

    Returns:
        Dictionary with size and count information
    """
```

#### format_file_size (function)
```python
def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., '1.5 MB')
    """
```

### pipeline/pipeline.py

#### PipelineExecutor (class)
```python
class PipelineExecutor:
    """Execute pipeline stages for a single project.

    Orchestrates the execution of pipeline stages with checkpointing and logging.
    """

    def __init__(
        self,
        repo_root: Path,
        project_name: str,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """Initialize pipeline executor.

        Args:
            repo_root: Repository root directory
            project_name: Name of the project to execute
            logger: Logger instance for pipeline messages
        """

    def execute_stage(self, stage_name: str) -> Tuple[bool, Dict[str, Any]]:
        """Execute a specific pipeline stage.

        Args:
            stage_name: Name of the stage to execute

        Returns:
            Tuple of (success, result_dict)
        """

    def execute_pipeline(
        self,
        start_stage: Optional[str] = None,
        resume: bool = False
    ) -> Dict[str, Any]:
        """Execute pipeline with optional resume capability.

        Args:
            start_stage: Stage to start execution from
            resume: Whether to resume from checkpoint

        Returns:
            Dictionary with pipeline execution results
        """

    def save_checkpoint(self) -> Path:
        """Save current pipeline state to checkpoint.

        Returns:
            Path to saved checkpoint file
        """

    def load_checkpoint(self) -> Optional[PipelineCheckpoint]:
        """Load pipeline checkpoint if available.

        Returns:
            Checkpoint data or None if not found
        """
```

### pipeline/multi_project.py

#### MultiProjectOrchestrator (class)
```python
class MultiProjectOrchestrator:
    """Orchestrate pipeline execution across multiple projects.

    Manages execution of multiple projects with shared infrastructure testing.
    """

    def __init__(
        self,
        repo_root: Path,
        project_names: List[str],
        logger: Optional[logging.Logger] = None
    ) -> None:
        """Initialize multi-project orchestrator.

        Args:
            repo_root: Repository root directory
            project_names: List of project names to execute
            logger: Logger instance for orchestration messages
        """

    def execute_all_projects(
        self,
        core_only: bool = False,
        resume: bool = False
    ) -> Dict[str, Any]:
        """Execute pipelines for all specified projects.

        Args:
            core_only: Whether to run core pipeline only
            resume: Whether to resume from checkpoints

        Returns:
            Dictionary with execution results for all projects
        """

    def execute_infrastructure_tests(self) -> Tuple[bool, Dict[str, Any]]:
        """Execute infrastructure tests once for all projects.

        Returns:
            Tuple of (success, test_results)
        """

    def generate_executive_report(
        self,
        output_dir: Path
    ) -> List[Path]:
        """Generate executive report across all projects.

        Args:
            output_dir: Directory to save executive reports

        Returns:
            List of generated report files
        """
```

### pipeline/pipeline_summary.py

#### generate_pipeline_summary (function)
```python
def generate_pipeline_summary(
    pipeline_results: Dict[str, Any],
    repo_root: Path
) -> Dict[str, Any]:
    """Generate pipeline summary with metrics.

    Args:
        pipeline_results: Results from pipeline execution
        repo_root: Repository root directory

    Returns:
        Dictionary with pipeline summary information
    """
```

#### calculate_performance_metrics (function)
```python
def calculate_performance_metrics(
    stage_durations: Dict[str, float],
    total_duration: float
) -> Dict[str, Any]:
    """Calculate performance metrics from stage timing data.

    Args:
        stage_durations: Dictionary mapping stage names to durations
        total_duration: Total pipeline duration

    Returns:
        Dictionary with performance metrics
    """
```

#### generate_executive_summary (function)
```python
def generate_executive_summary(
    multi_project_results: Dict[str, Any],
    repo_root: Path
) -> Dict[str, Any]:
    """Generate executive summary across multiple projects.

    Args:
        multi_project_results: Results from multi-project execution
        repo_root: Repository root directory

    Returns:
        Dictionary with executive summary information
    """
```

## Usage Examples

### Basic Logging Setup
```python
from infrastructure.core import get_logger, setup_logger

# Get default logger
logger = get_logger(__name__)
logger.info("Starting operation")

# Setup custom logger with file output
from infrastructure.core.logging.utils import setup_logger

logger = setup_logger("my_module", log_file="logs/my_module.log")
logger.debug("Debug message")
```

### Exception Handling
```python
from infrastructure.core import TemplateError
from infrastructure.core.exceptions import raise_with_context

try:
    # Some operation
    result = risky_operation()
except Exception as e:
    # Raise with context
    raise_with_context(
        TemplateError,
        "Operation failed",
        operation="risky_operation",
        input_data=data
    )
```

### Configuration Management
```python
from pathlib import Path

from infrastructure.core.config.loader import load_config, get_config_as_env_vars

config = load_config(Path("projects/my_project/manuscript/config.yaml"))
env_vars = get_config_as_env_vars(Path("."))
for key, value in env_vars.items():
    os.environ[key] = value
```

### Pipeline Execution
```python
from pathlib import Path

from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.types import PipelineConfig

config = PipelineConfig(project_name="my_project", repo_root=Path("."), skip_llm=True)
executor = PipelineExecutor(config)
results = executor.execute_core_pipeline()
```

### Multi-Project Orchestration
```python
from pathlib import Path

from infrastructure.core.pipeline.multi_project import MultiProjectConfig, MultiProjectOrchestrator
from infrastructure.project.discovery import discover_projects

projects = discover_projects(Path("."))
mp_config = MultiProjectConfig(
    repo_root=Path("."),
    projects=projects,
    run_infra_tests=True,
    run_llm=False,
)
orchestrator = MultiProjectOrchestrator(mp_config)
result = orchestrator.execute_all_projects_core()
```

### runtime/health_check.py

#### SystemHealthChecker (class)
```python
class SystemHealthChecker:
    """Check system health and component status."""

    def __init__(self, check_interval: float = 30.0):
        """Initialize health checker.

        Args:
            check_interval: How often to perform checks (seconds)
        """
```

#### get_health_api (function)
```python
def get_health_api() -> HealthCheckAPI:
    """Get health check API instance.

    Returns:
        HealthCheckAPI instance
    """
```

#### quick_health_check (function)
```python
def quick_health_check() -> bool:
    """Perform quick system health check.

    Returns:
        True if all critical systems are healthy
    """
```

#### get_health_status (function)
```python
def get_health_status() -> Dict[str, Any]:
    """Get detailed health status.

    Returns:
        Dictionary with health status information
    """
```

#### get_health_metrics (function)
```python
def get_health_metrics() -> Dict[str, Any]:
    """Get health metrics.

    Returns:
        Dictionary with health metrics
    """
```

### security.py

#### SecurityValidator (class)
```python
class SecurityValidator:
    """Validate input for security threats."""

    def __init__(self, max_length: int = 10000):
        """Initialize security validator.

        Args:
            max_length: Maximum allowed input length
        """
```

#### SecurityHeaders (class)
```python
class SecurityHeaders:
    """Generate security headers for HTTP responses."""
```

#### RateLimiter (class)
```python
class RateLimiter:
    """Rate limiting for API requests."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
```

#### SecurityMonitor (class)
```python
class SecurityMonitor:
    """Monitor security events and violations."""
```

#### SecurityViolation (class)
```python
class SecurityViolation(Exception):
    """Raised when security violation is detected."""
    pass
```

#### get_security_validator (function)
```python
def get_security_validator() -> SecurityValidator:
    """Get security validator instance.

    Returns:
        SecurityValidator instance
    """
```

#### get_security_headers (function)
```python
def get_security_headers() -> Dict[str, str]:
    """Get security headers.

    Returns:
        Dictionary of security headers
    """
```

#### get_rate_limiter (function)
```python
def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance.

    Returns:
        RateLimiter instance
    """
```

#### get_security_monitor (function)
```python
def get_security_monitor() -> SecurityMonitor:
    """Get security monitor instance.

    Returns:
        SecurityMonitor instance
    """
```

#### validate_llm_input (function)
```python
def validate_llm_input(prompt: str) -> str:
    """Validate LLM input for security.

    Args:
        prompt: Input prompt to validate

    Returns:
        Sanitized prompt

    Raises:
        SecurityViolation: If input contains security threats
    """
```

#### rate_limit (function)
```python
@rate_limit(max_requests=100, window_seconds=60)
def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """Rate limiting decorator.

    Args:
        max_requests: Maximum requests per window
        window_seconds: Time window in seconds

    Returns:
        Decorator function
    """
```

### logging/logging_formatters.py

#### JSONFormatter (class)
```python
class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        """Initialize JSON formatter.

        Args:
            fmt: Format string
            datefmt: Date format string
        """
```

#### TemplateFormatter (class)
```python
class TemplateFormatter(logging.Formatter):
    """Template-aware formatter for logging."""
```

### logging/logging_progress.py

#### calculate_eta (function)
```python
def calculate_eta(
    current: int,
    total: int,
    start_time: float,
    use_ema: bool = True,
    alpha: float = 0.1
) -> Optional[float]:
    """Calculate estimated time remaining.

    Args:
        current: Current progress value
        total: Total progress value
        start_time: Start time
        use_ema: Whether to use exponential moving average
        alpha: EMA smoothing factor

    Returns:
        Estimated seconds remaining, or None if cannot calculate
    """
```

#### calculate_eta_ema (function)
```python
def calculate_eta_ema(
    current: int,
    total: int,
    start_time: float,
    alpha: float = 0.1
) -> Optional[float]:
    """Calculate ETA using exponential moving average.

    Args:
        current: Current progress value
        total: Total progress value
        start_time: Start time
        alpha: EMA smoothing factor

    Returns:
        Estimated seconds remaining
    """
```

#### calculate_eta_with_confidence (function)
```python
def calculate_eta_with_confidence(
    current: int,
    total: int,
    start_time: float,
    alpha: float = 0.1
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """Calculate ETA with confidence intervals.

    Args:
        current: Current progress value
        total: Total progress value
        start_time: Start time
        alpha: EMA smoothing factor

    Returns:
        Tuple of (realistic_eta, optimistic_eta, pessimistic_eta)
    """
```

#### log_progress_bar (function)
```python
def log_progress_bar(
    current: int,
    total: int,
    width: int = 30,
    task: str = "",
    logger: Optional[logging.Logger] = None
) -> None:
    """Log a progress bar.

    Args:
        current: Current progress value
        total: Total progress value
        width: Width of progress bar
        task: Task description
        logger: Logger instance
    """
```

#### Spinner (class)
```python
class Spinner:
    """Simple spinner for progress indication."""

    def __init__(self, message: str = "Processing...", spinner_chars: str = "|/-\\"):
        """Initialize spinner.

        Args:
            message: Spinner message
            spinner_chars: Spinner character sequence
        """
```

#### log_with_spinner (function)
```python
def log_with_spinner(
    message: str,
    logger: Optional[logging.Logger] = None,
    spinner_chars: str = "|/-\\"
) -> Iterator[None]:
    """Context manager for logging with spinner.

    Args:
        message: Spinner message
        logger: Logger instance
        spinner_chars: Spinner characters

    Yields:
        None
    """
```

#### StreamingProgress (class)
```python
class StreamingProgress:
    """Progress tracker for streaming operations."""

    def __init__(self, total: Optional[int] = None, task: str = "Streaming"):
        """Initialize streaming progress tracker.

        Args:
            total: Total expected items
            task: Task description
        """
```

#### log_progress_streaming (function)
```python
def log_progress_streaming(
    task: str = "Streaming",
    logger: Optional[logging.Logger] = None
) -> Iterator[StreamingProgress]:
    """Context manager for streaming progress.

    Args:
        task: Task description
        logger: Logger instance

    Yields:
        StreamingProgress instance
    """
```

#### log_stage_with_eta (function)
```python
def log_stage_with_eta(
    stage_num: int,
    total_stages: int,
    stage_name: str,
    pipeline_start: Optional[float] = None,
    logger: Optional[logging.Logger] = None
) -> None:
    """Log stage with ETA.

    Args:
        stage_num: Current stage number
        total_stages: Total number of stages
        stage_name: Stage name
        pipeline_start: Pipeline start time
        logger: Logger instance
    """
```

### runtime/function_profiler.py

#### PerformanceMonitor (class)
```python
class PerformanceMonitor:
    """Monitor performance metrics for operations."""

    def __init__(self):
        """Initialize performance monitor."""
```

#### monitor_performance (function)
```python
@contextmanager
def monitor_performance(operation_name: str, track_memory: bool = True):
    """Context manager for monitoring operation performance.

    Args:
        operation_name: Name of the operation being monitored
        track_memory: Whether to track memory usage

    Yields:
        PerformanceMonitor instance
    """
```

#### benchmark_llm_query (function)
```python
def benchmark_llm_query(client, prompt: str, iterations: int = 3) -> Dict[str, Union[float, List[float]]]:
    """Benchmark LLM query performance.

    Args:
        client: LLM client instance
        prompt: Query prompt
        iterations: Number of benchmark iterations

    Returns:
        Dictionary with performance metrics
    """
```

#### profile_memory_usage (function)
```python
def profile_memory_usage(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """Profile memory usage of a function.

    Args:
        func: Function to profile
        *args: Function arguments
        **kwargs: Function keyword arguments

    Returns:
        Dictionary with memory usage data
    """
```

#### main (function)
```python
def main():
    """Main function for performance monitoring CLI."""
```

#### benchmark_function (function)
```python
def benchmark_function(
    func: Callable,
    *args,
    iterations: int = 10,
    warmup_iterations: int = 2,
    **kwargs
) -> Dict[str, Any]:
    """Benchmark function performance.

    Args:
        func: Function to benchmark
        *args: Function arguments
        iterations: Number of benchmark iterations
        warmup_iterations: Number of warmup iterations
        **kwargs: Function keyword arguments

    Returns:
        Dictionary with benchmark results
    """
```

### config/config_cli.py

#### main (function)
```python
def main():
    """Main function for config CLI."""
```

### pipeline/stage_monitor.py

#### ResourceUsage (class)
```python
@dataclass
class ResourceUsage:
    """Resource usage metrics for a stage or operation."""
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    peak_memory_mb: float = 0.0
    io_read_mb: float = 0.0
    io_write_mb: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
```

#### PerformanceMetrics (class)
```python
@dataclass
class PerformanceMetrics:
    """Performance metrics for a stage or operation."""
    duration: float
    resource_usage: ResourceUsage = field(default_factory=ResourceUsage)
    operations_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
```

#### PerformanceMonitor (class)
```python
class PerformanceMonitor:
    """Monitor performance metrics for operations."""

    def __init__(self):
        """Initialize performance monitor."""
```

#### start (method)
```python
def start(self) -> None:
    """Start monitoring."""
```

#### stop (method)
```python
def stop(self) -> PerformanceMetrics:
    """Stop monitoring and return metrics.

    Returns:
        PerformanceMetrics with collected data
    """
```

#### record_operation (method)
```python
def record_operation(self) -> None:
    """Record an operation."""
```

#### record_cache_hit (method)
```python
def record_cache_hit(self) -> None:
    """Record a cache hit."""
```

#### record_cache_miss (method)
```python
def record_cache_miss(self) -> None:
    """Record a cache miss."""
```

#### update_memory (method)
```python
def update_memory(self) -> None:
    """Update peak memory tracking."""
```

#### monitor_performance (function)
```python
@contextmanager
def monitor_performance(operation_name: str = "Operation"):
    """Context manager for monitoring operation performance.

    Args:
        operation_name: Name of the operation being monitored

    Yields:
        PerformanceMonitor instance
    """
```

#### get_system_resources (function)
```python
def get_system_resources() -> dict[str, Any]:
    """Get current system resource information.

    Returns:
        Dictionary with system resource information
    """
```

#### StagePerformanceTracker (class)
```python
class StagePerformanceTracker:
    """Track performance metrics for pipeline stages."""

    def __init__(self):
        """Initialize stage performance tracker."""
```

#### start_stage (method)
```python
def start_stage(self, stage_name: str) -> None:
    """Start tracking a stage.

    Args:
        stage_name: Name of the stage
    """
```

#### end_stage (method)
```python
def end_stage(self, stage_name: str, exit_code: int) -> dict[str, Any]:
    """End tracking a stage and return metrics.

    Args:
        stage_name: Name of the stage
        exit_code: Exit code from the stage

    Returns:
        Dictionary with stage performance metrics
    """
```

#### get_performance_warnings (method)
```python
def get_performance_warnings(self) -> list[dict[str, Any]]:
    """Get performance warnings for stages.

    Returns:
        List of warning dictionaries
    """
```

#### get_summary (method)
```python
def get_summary(self) -> dict[str, Any]:
    """Get performance summary.

    Returns:
        Dictionary with performance summary
    """
```

### runtime/environment.py

#### check_python_version (function)
```python
def check_python_version() -> bool:
    """Verify Python 3.8+ is available.

    Checks the current Python version against the minimum requirement (3.8+)
    for the research template. Uses sys.version_info for reliable version detection.

    Returns:
        True if Python version is 3.8 or higher, False otherwise

    Example:
        >>> result = check_python_version()
        >>> assert result is True  # Requires Python 3.8+
    """
```

#### check_dependencies (function)
```python
def check_dependencies(required_packages: List[str] | None = None) -> Tuple[bool, List[str]]:
    """Verify required packages are installed.

    Attempts to import each package to verify availability. Distinguishes between
    required packages (must be present) and optional packages (warns but doesn't fail).

    Args:
        required_packages: List of package names to check. If None, uses default list
                          of core packages (numpy, matplotlib, pytest, requests).

    Returns:
        Tuple of (all_present: bool, missing_packages: List[str])

    Example:
        >>> all_present, missing = check_dependencies(['numpy', 'matplotlib'])
        >>> if not all_present:
        ...     print(f"Missing packages: {missing}")
    """
```

#### install_missing_packages (function)
```python
def install_missing_packages(packages: List[str]) -> bool:
    """Install missing packages using uv with fallback to pip.

    Attempts to install packages using uv package manager for speed and reliability.
    If uv is not available, provides guidance for manual installation.

    The function uses 'uv add' to properly manage dependencies through pyproject.toml,
    then runs 'uv sync' to install all dependencies. This ensures consistent
    dependency resolution and lock file generation.

    Args:
        packages: List of package names to install

    Returns:
        True if installation successful, False otherwise

    Example:
        >>> success = install_missing_packages(['numpy', 'matplotlib'])
        >>> if success:
        ...     print("Packages installed successfully")
        ... else:
        ...     print("Installation failed - check uv availability")
    """
```

#### check_build_tools (function)
```python
def check_build_tools(required_tools: dict[str, str] | None = None) -> bool:
    """Verify build tools are available.

    Uses shutil.which() to check if each tool is available in the system PATH.
    Provides descriptive error messages indicating the purpose of each tool.

    Args:
        required_tools: Dictionary mapping tool names to descriptions.
                       If None, uses default tools (pandoc, xelatex).

    Returns:
        True if all tools are available, False otherwise

    Example:
        >>> tools = {'pandoc': 'Document conversion', 'xelatex': 'LaTeX compilation'}
        >>> available = check_build_tools(tools)
        >>> assert available is True
    """
```

#### setup_directories (function)
```python
def setup_directories(repo_root: Path, project_name: str = "project", directories: List[str] | None = None) -> bool:
    """Create required directory structure for multi-project workflow.

    Creates both repository-level and project-specific output directories.
    Handles multi-project structure where each project has its own output area
    alongside a shared repository-level output structure.

    Args:
        repo_root: Repository root directory
        project_name: Name of project in projects/ directory (default: "project")
        directories: List of directory paths to create (relative to repo_root).
                    If None, uses default multi-project directories.

    Returns:
        True if all directories created successfully, False otherwise

    Example:
        >>> success = setup_directories(Path("."), "my_project")
        >>> assert success is True
    """
```

#### check_uv_available (function)
```python
def check_uv_available() -> bool:
    """Check if uv package manager is available and working.

    Tests uv availability by running 'uv --version' command. uv is a fast
    Python package manager that provides reliable dependency resolution and
    virtual environment management.

    Returns:
        True if uv is available and functional, False otherwise

    Example:
        >>> if check_uv_available():
        ...     print("Using uv for fast dependency management")
        ... else:
        ...     print("Falling back to pip - consider installing uv")
    """
```

#### get_python_command (function)
```python
def get_python_command() -> list[str]:
    """Get the appropriate Python command for subprocess execution.

    Returns the optimal Python command based on available tools:
    - ['uv', 'run', 'python'] if uv is available (preferred for managed environments)
    - [sys.executable] otherwise (uses current Python interpreter)

    This ensures consistent Python execution across different environments and
    respects uv-managed virtual environments when available.

    Returns:
        List of command arguments suitable for subprocess.run()

    Example:
        >>> cmd = get_python_command()
        >>> result = subprocess.run(cmd + ['-c', 'print("hello")'], ...)
    """
```

#### get_subprocess_env (function)
```python
def get_subprocess_env(base_env: dict = None) -> dict:
    """Get environment dict for subprocess with uv compatibility.

    Creates a clean environment dictionary for subprocess execution that handles
    VIRTUAL_ENV warnings when using uv. When uv is available and VIRTUAL_ENV is set,
    it removes VIRTUAL_ENV from the environment to prevent uv warnings about absolute paths.

    Args:
        base_env: Base environment dictionary (defaults to os.environ if None)

    Returns:
        Environment dictionary suitable for subprocess.run(env=...)

    Example:
        >>> env = get_subprocess_env()
        >>> result = subprocess.run(cmd, env=env, ...)
    """
```

#### verify_source_structure (function)
```python
def verify_source_structure(repo_root: Path, project_name: str = "project") -> bool:
    """Verify source code structure exists for multi-project template.

    For multi-project template, checks:
    - infrastructure/ - Generic reusable build tools
    - projects/{name}/ - Specified project structure
    - projects/{name}/src/ - Source code
    - projects/{name}/tests/ - Tests

    Args:
        repo_root: Repository root directory
        project_name: Name of project in projects/ directory (default: "project")

    Returns:
        True if required directories exist, False otherwise

    Example:
        >>> valid = verify_source_structure(Path("."), "my_project")
        >>> assert valid is True
    """
```

#### set_environment_variables (function)
```python
def set_environment_variables(repo_root: Path) -> bool:
    """Configure environment variables for pipeline.

    Sets critical environment variables needed for the research template pipeline:
    - MPLBACKEND=Agg: Ensures matplotlib runs in headless mode for server environments
    - PYTHONIOENCODING=utf-8: Ensures consistent text encoding across platforms
    - PROJECT_ROOT: Points to repository root for relative path calculations

    Args:
        repo_root: Repository root directory

    Returns:
        True if environment variables set successfully, False otherwise

    Example:
        >>> from pathlib import Path
        >>> repo_root = Path("/path/to/template")
        >>> success = set_environment_variables(repo_root)
        >>> assert success is True
    """
```

#### validate_uv_sync_result (function)
```python
def validate_uv_sync_result(repo_root: Path) -> tuple[bool, str]:
    """Validate that uv sync completed successfully.

    Checks for the presence of expected artifacts after a uv sync operation:
    - .venv/ directory: Virtual environment created
    - uv.lock file: Dependency lock file generated

    Args:
        repo_root: Repository root directory where uv sync was run

    Returns:
        Tuple of (success: bool, message: str) describing validation result

    Example:
        >>> success, msg = validate_uv_sync_result(Path("."))
        >>> if success:
        ...     print("uv sync completed successfully")
        ... else:
        ...     print(f"uv sync validation failed: {msg}")
    """
```

#### validate_directory_structure (function)
```python
def validate_directory_structure(repo_root: Path, project_name: str = "project") -> list[str]:
    """Validate that required directory structure exists.

    Checks for the presence of all directories created by setup_directories().
    This is useful for post-setup validation to ensure the environment is ready.

    Args:
        repo_root: Repository root directory
        project_name: Name of project in projects/ directory (default: "project")

    Returns:
        List of missing directory paths (empty list if all directories exist)

    Example:
        >>> missing = validate_directory_structure(Path("."), "my_project")
        >>> if missing:
        ...     print(f"Missing directories: {missing}")
        ... else:
        ...     print("All directories present")
    """
```

### script_discovery.py

#### discover_analysis_scripts (function)
```python
def discover_analysis_scripts(repo_root: Path) -> List[Path]:
    """Discover all analysis scripts in project/scripts/ to execute.

    Args:
        repo_root: Repository root directory

    Returns:
        List of Python script paths from project/scripts/ directory

    Raises:
        PipelineError: If project scripts directory not found
    """
```

#### discover_orchestrators (function)
```python
def discover_orchestrators(repo_root: Path) -> List[Path]:
    """Discover orchestrator scripts in scripts/ directory.

    Args:
        repo_root: Repository root directory

    Returns:
        List of available orchestrator script paths in execution order

    Raises:
        PipelineError: If scripts directory not found
    """
```

#### verify_analysis_outputs (function)
```python
def verify_analysis_outputs(repo_root: Path) -> bool:
    """Verify that analysis generated expected outputs.

    Args:
        repo_root: Repository root directory

    Returns:
        True if outputs are valid, False otherwise
    """
```

### files/operations.py

#### clean_output_directory (function)
```python
def clean_output_directory(output_dir: Path) -> None:
    """Clean top-level output directory before copying.

    Args:
        output_dir: Path to top-level output directory

    Returns:
        True if cleanup successful, False otherwise
    """
```

#### clean_output_directories (function)
```python
def clean_output_directories(repo_root: Path, subdirs: List[str] | None = None) -> None:
    """Clean output directories for a fresh pipeline start.

    Removes all contents from both project/output/ and output/ directories,
    then recreates the expected subdirectory structure.

    Args:
        repo_root: Repository root directory
        subdirs: List of subdirectories to recreate. If None, uses default list.
    """
```

#### copy_final_deliverables (function)
```python
def copy_final_deliverables(project_root: Path, output_dir: Path) -> Dict:
    """Copy all project outputs to top-level output directory.

    Recursively copies entire project/output/ directory structure, preserving:
    - pdf/ - PDF directory with manuscript and metadata
    - web/ - HTML web outputs
    - slides/ - Beamer slides and metadata
    - figures/ - Generated figures and visualizations
    - data/ - Data files (CSV, NPZ, etc.)
    - reports/ - Generated analysis and simulation reports
    - simulations/ - Simulation outputs and checkpoints
    - llm/ - LLM-generated manuscript reviews
    - logs/ - Pipeline execution logs

    Also copies combined PDF to root for convenient access.

    Args:
        project_root: Path to repository root
        output_dir: Path to top-level output directory

    Returns:
        Dictionary with copy statistics
    """
```

### files/file_inventory.py

#### FileInventoryManager (class)
```python
class FileInventoryManager:
    """Manages file inventory generation and reporting for pipeline outputs."""

    def __init__(self, base_dir: Path):
        """Initialize file inventory manager.

        Args:
            base_dir: Base directory to scan for files
        """

    def collect_files(self) -> bool:
        """Collect all files from the base directory.

        Returns:
            True if files were found, False otherwise
        """

    def generate_inventory_output(self, log_file: Optional[Path | str] = None) -> None:
        """Generate and display file inventory.

        Args:
            log_file: Optional log file to append inventory to
        """
```

### pipeline/pipeline.py

#### PipelineConfig (class)
```python
@dataclass
class PipelineConfig:
    """Configuration for pipeline execution."""

    project_name: str
    repo_root: Path
    skip_infra: bool = False
    skip_llm: bool = False
    resume: bool = False
    run_core_only: bool = False
```

#### PipelineExecutor (class)
```python
class PipelineExecutor:
    """Executes pipeline stages for a single project."""

    def __init__(self, config: PipelineConfig):
        """Initialize pipeline executor.

        Args:
            config: Pipeline configuration
        """

    def execute_full_pipeline(self) -> List[StageResult]:
        """Execute pipeline with all stages.

        Returns:
            List of stage results
        """

    def execute_core_pipeline(self) -> List[StageResult]:
        """Execute core pipeline without LLM stages.

        Returns:
            List of stage results
        """
```

### pipeline/multi_project.py

#### MultiProjectConfig (class)
```python
@dataclass
class MultiProjectConfig:
    """Configuration for multi-project execution."""

    repo_root: Path
    projects: List[Project]
    run_infra_tests: bool = True
    run_llm: bool = False
    run_executive_report: bool = True
```

#### MultiProjectResult (class)
```python
@dataclass
class MultiProjectResult:
    """Result of multi-project execution."""

    successful_projects: int
    failed_projects: int
    total_duration: float
    infra_test_duration: float = 0.0
```

#### MultiProjectOrchestrator (class)
```python
class MultiProjectOrchestrator:
    """Orchestrates pipeline execution across multiple projects."""

    def __init__(self, config: MultiProjectConfig):
        """Initialize multi-project orchestrator.

        Args:
            config: Multi-project configuration
        """

    def execute_all_projects_full(self) -> MultiProjectResult:
        """Execute full pipeline for all projects.

        Returns:
            Multi-project execution result
        """

    def execute_all_projects_core(self) -> MultiProjectResult:
        """Execute core pipeline for all projects.

        Returns:
            Multi-project execution result
        """
```

## Key Features

### Exception Handling
```python
from infrastructure.core import TemplateError
from infrastructure.core.exceptions import chain_exceptions

try:
    risky_operation()
except ValueError as e:
    raise chain_exceptions(TemplateError("Operation failed"), e)
```

### Logging
```python
from infrastructure.core.logging.utils import get_logger, log_operation, log_timing

logger = get_logger(__name__)
logger.info("Starting process")

with log_operation("Data processing", logger):
    process_data()

with log_timing("Algorithm execution", logger):
    run_algorithm()
```

### Configuration
```python
from pathlib import Path

from infrastructure.core.config.loader import (
    load_config,
    get_config_as_dict,
    get_translation_languages,
    find_config_file,
)

config = load_config(Path("projects/code_project/manuscript/config.yaml"))
env_dict = get_config_as_dict(Path("."))
config_path = find_config_file(Path("."))
languages = get_translation_languages(Path("."))
```

### Credential Management
```python
from pathlib import Path

from infrastructure.core.credentials import CredentialManager

manager = CredentialManager(env_file=Path(".env"), config_file=Path("config.yaml"))
zenodo = manager.get_zenodo_credentials(use_sandbox=True)
github = manager.get_github_credentials()
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

bar = ProgressBar(total=100, task="Processing")
for i in range(1, 101):
    bar.update(i)
bar.finish()
```

### Checkpoint Management
```python
from infrastructure.core import CheckpointManager
from infrastructure.core.runtime.checkpoint import StageResult

cm = CheckpointManager(project_name="code_project", repo_root=Path("."))
if cm.checkpoint_exists():
    state = cm.load_checkpoint()
# … after stages …
cm.save_checkpoint(
    pipeline_start_time=start,
    last_stage_completed=n,
    stage_results=[StageResult(name="tests", exit_code=0, duration=1.0)],
    total_stages=10,
)
```

### Retry Logic
```python
from infrastructure.core.runtime.retry import retry_with_backoff

@retry_with_backoff(max_attempts=3, initial_delay=1.0)
def risky_operation():
    ...
```

### Performance monitoring
```python
from infrastructure.core.runtime.function_profiler import monitor_performance

with monitor_performance("heavy_step"):
    ...
```

### Environment setup
```python
from pathlib import Path

from infrastructure.core.runtime.environment import (
    check_python_version,
    check_dependencies,
    setup_directories,
)

check_python_version()
check_dependencies(["numpy"])
setup_directories(Path("."), "code_project")
```

### Script discovery
```python
from pathlib import Path

from infrastructure.core.script_discovery import discover_analysis_scripts, discover_orchestrators

scripts = discover_analysis_scripts(Path("."), "code_project")
orchestrators = discover_orchestrators(Path("."))
```

### File operations
```python
from pathlib import Path

from infrastructure.core.files.cleanup import clean_output_directory
from infrastructure.core.files.operations import copy_final_deliverables

clean_output_directory(Path("output/code_project"))
copy_final_deliverables(Path("projects/code_project"), Path("output/code_project"), "code_project")
```

### File inventory
```python
from pathlib import Path

from infrastructure.core.files.inventory import FileInventoryManager

manager = FileInventoryManager(Path("projects/code_project/output"))
if manager.collect_files():
    manager.generate_inventory_output()
```

### Pipeline execution
```python
from pathlib import Path

from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.types import PipelineConfig

config = PipelineConfig(project_name="my_project", repo_root=Path("."), skip_llm=True)
executor = PipelineExecutor(config)
results = executor.execute_core_pipeline()
for r in results:
    print(f"{r.stage_name}: exit {r.exit_code} ({r.duration:.1f}s)")
```

### Multi-project orchestration
```python
from pathlib import Path

from infrastructure.core.pipeline.multi_project import MultiProjectConfig, MultiProjectOrchestrator
from infrastructure.project.discovery import discover_projects

projects = discover_projects(Path("."))
mp = MultiProjectConfig(repo_root=Path("."), projects=projects, run_llm=False)
result = MultiProjectOrchestrator(mp).execute_all_projects_core()
print(result.successful_projects, result.failed_projects)
```

### Pipeline summary
```python
from pathlib import Path

from infrastructure.core.pipeline.summary import generate_pipeline_summary

text = generate_pipeline_summary(
    stage_results=results,
    total_duration=123.45,
    output_dir=Path("output/code_project"),
    output_format="text",
)
print(text)
```

## Testing

Run core tests with:
```bash
pytest tests/infra_tests/test_core/
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
- `ProgressBar` writes to stderr; ensure the terminal is interactive when expecting live updates
- Call `update(value)` with the current absolute progress value, then `finish()`
- Throttling uses `update_interval`; pass `force=True` to bypass

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

## See Also

- [README.md](README.md) - Quick reference guide
- [`validation/`](../validation/) - Validation & quality assurance

