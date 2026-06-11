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

#### NotADirectoryError (class)
```python
class NotADirectoryError(FileOperationError, builtins.NotADirectoryError):
    """Raised when a path is not a directory when a directory is expected."""
    pass
```

#### SecurityError (class)
```python
class SecurityError(SecurityViolation):
    """Security violation in LLM input sanitization.

    Subclass of SecurityViolation kept for backwards compatibility with call
    sites that catch SecurityError. Re-exported from
    infrastructure.core._exceptions_domains via exceptions.py.
    """
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

### config/queries.py

#### get_translation_languages (function)
```python
def get_translation_languages(repo_root: Path | str, project_name: str = "project") -> List[str]:
    """Get list of enabled translation languages from config.

    Reads the llm.translations section from config.yaml and returns
    the list of enabled language codes.

    Args:
        repo_root: Root directory of the repository
        project_name: Name of the project whose config.yaml to read

    Returns:
        List of language codes (e.g., ['zh', 'hi', 'ru']) if translations
        are enabled, empty list otherwise
    """
```

#### get_testing_config (function)
```python
def get_testing_config(repo_root: Path | str) -> ResolvedTestingConfig:
    """Get testing configuration from config.yaml.

    Reads the testing section from config.yaml and returns
    configuration values for test failure tolerance.

    Args:
        repo_root: Root directory of the repository

    Returns:
        ResolvedTestingConfig with testing configuration values:
        - max_test_failures: Maximum acceptable test failures (default: 0)
        - max_infra_test_failures: Maximum acceptable infrastructure test failures (default: 0)
        - max_project_test_failures: Maximum acceptable project test failures (default: 0)
    """
```

### credentials.py

#### CredentialManager (class)
```python
class CredentialManager:
    """Manage credentials from .env and YAML config files.

    Loads credentials from environment variables, .env files (when
    python-dotenv is installed), and YAML config files with env-var
    substitution.
    """

    def __init__(self, env_file: Path | None = None, config_file: Path | None = None): ...

    def get_zenodo_credentials(self, use_sandbox: bool = True) -> dict[str, Any]: ...
    def get_github_credentials(self) -> dict[str, Any]: ...
    def get_arxiv_credentials(self) -> dict[str, Any]: ...
    def has_zenodo_credentials(self, use_sandbox: bool = True) -> bool: ...
    def has_github_credentials(self) -> bool: ...
    def has_arxiv_credentials(self) -> bool: ...
```

#### make_bearer_auth_headers (function)
```python
def make_bearer_auth_headers(token: str) -> dict[str, str]:
    """Return Authorization header dict using OAuth2 Bearer scheme."""
```

#### make_token_auth_headers (function)
```python
def make_token_auth_headers(token: str) -> dict[str, str]:
    """Return Authorization header dict using GitHub token scheme."""
```

### progress.py

#### ProgressBar (class)
```python
class ProgressBar:
    """Visual progress indicator for long-running operations.

    Provides a progress bar with percentage completion, ETA, and customizable formatting.
    """

    def __init__(
        self,
        total: int,
        description: str = "",
        width: int = 50,
        show_eta: bool = True,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """Initialize progress bar.

        Args:
            total: Total number of items to process
            description: Description of the operation
            width: Width of the progress bar in characters
            show_eta: Whether to show estimated time of arrival
            logger: Logger instance for output
        """

    def update(self, increment: int = 1) -> None:
        """Update progress by specified increment.

        Args:
            increment: Number of items completed
        """

    def finish(self) -> None:
        """Mark progress as and finalize display."""
```

#### SubStageProgress (class)
```python
class SubStageProgress:
    """Progress tracking for nested operations with substages.

    Manages progress through multiple substages within a larger operation.
    """

    def __init__(
        self,
        total_stages: int,
        stage_names: List[str],
        logger: Optional[logging.Logger] = None
    ) -> None:
        """Initialize substage progress tracker.

        Args:
            total_stages: Total number of substages
            stage_names: Names of each substage
            logger: Logger instance for output
        """

    def start_stage(self, stage_index: int) -> None:
        """Start a specific substage.

        Args:
            stage_index: Index of the stage to start (0-based)
        """

    def update_progress(self, completed: int, total: int) -> None:
        """Update progress within current substage.

        Args:
            completed: Number of items completed in current stage
            total: Total number of items in current stage
        """

    def finish_stage(self) -> None:
        """Mark current substage as."""
```

### runtime/checkpoint.py

#### PipelineCheckpoint (class)
```python
class PipelineCheckpoint:
    """Data structure for pipeline checkpoint state.

    Contains information about completed stages, timing, and pipeline state.
    """

    def __init__(
        self,
        pipeline_name: str,
        start_time: float,
        completed_stages: List[str],
        stage_results: Dict[str, Any],
        current_stage: Optional[str] = None
    ) -> None:
        """Initialize pipeline checkpoint.

        Args:
            pipeline_name: Name of the pipeline
            start_time: Pipeline start timestamp
            completed_stages: List of completed stage names
            stage_results: Results from completed stages
            current_stage: Currently executing stage (if any)
        """
```

#### CheckpointManager (class)
```python
class CheckpointManager:
    """Manages pipeline checkpoint save/load operations.

    Provides functionality to save and restore pipeline execution state.
    """

    def __init__(self, checkpoint_dir: Path) -> None:
        """Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory to store checkpoint files
        """

    def save_checkpoint(self, checkpoint: PipelineCheckpoint) -> Path:
        """Save pipeline checkpoint to file.

        Args:
            checkpoint: Checkpoint data to save

        Returns:
            Path to saved checkpoint file
        """

    def load_checkpoint(self, pipeline_name: str) -> Optional[PipelineCheckpoint]:
        """Load most recent checkpoint for pipeline.

        Args:
            pipeline_name: Name of the pipeline

        Returns:
            Most recent checkpoint or None if not found
        """

    def list_checkpoints(self, pipeline_name: str) -> List[Path]:
        """List all checkpoint files for a pipeline.

        Args:
            pipeline_name: Name of the pipeline

        Returns:
            List of checkpoint file paths
        """

    def cleanup_old_checkpoints(
        self,
        pipeline_name: str,
        keep_recent: int = 5
    ) -> None:
        """Clean up old checkpoint files, keeping only recent ones.

        Args:
            pipeline_name: Name of the pipeline
            keep_recent: Number of recent checkpoints to keep
        """
```

### runtime/retry.py

#### retry_with_backoff (function)
```python
def retry_with_backoff(
    func: Callable,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    exceptions_to_retry: Tuple[type, ...] = (Exception,),
    logger: Optional[logging.Logger] = None
) -> Any:
    """Execute function with exponential backoff retry logic.

    Args:
        func: Function to execute
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay between retries (seconds)
        backoff_factor: Factor by which delay increases each retry
        max_delay: Maximum delay between retries (seconds)
        exceptions_to_retry: Tuple of exception types to retry on
        logger: Logger instance for retry messages

    Returns:
        Result of successful function execution

    Raises:
        Last exception encountered if all retries exhausted
    """
```

#### RetryableOperation (class)
```python
class RetryableOperation:
    """Wrapper for operations that should be retried with backoff.

    Provides a class-based interface for retryable operations.
    """

    def __init__(
        self,
        operation: Callable,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0,
        exceptions_to_retry: Tuple[type, ...] = (Exception,),
        logger: Optional[logging.Logger] = None
    ) -> None:
        """Initialize retryable operation.

        Args:
            operation: Operation function to wrap
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay between retries (seconds)
            backoff_factor: Factor by which delay increases each retry
            max_delay: Maximum delay between retries (seconds)
            exceptions_to_retry: Tuple of exception types to retry on
            logger: Logger instance for retry messages
        """

    def execute(self, *args, **kwargs) -> Any:
        """Execute the operation with retry logic.

        Args:
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation

        Returns:
            Result of successful operation execution
        """
```

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

### analysis_timeout.py

- ``parse_analysis_script_timeout_sec(environ=None) -> float | None`` — resolves ``ANALYSIS_SCRIPT_TIMEOUT_SEC`` for Stage 02 ``subprocess.run`` (default ``7200.0`` seconds = 2 hours; ``0`` / ``none`` / ``unlimited`` / ``inf`` → ``None``, no per-script timeout).

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

### files/operations.py

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

### files/inventory.py

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

### files/project_lock.py

#### project_output_lock (function)
```python
def project_output_lock(
    project_root: Path,
    *,
    timeout: float | None = None,
) -> Iterator[None]:
    """Advisory lock serializing pipeline/test runs for one project output tree."""
```

### pipeline/executor.py

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

### pipeline/summary.py

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
