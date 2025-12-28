# Core Module

## Purpose

The Core module provides fundamental foundation utilities used across the entire infrastructure layer. It includes configuration management, unified logging, and a comprehensive exception hierarchy with context preservation.

## Architecture

### Core Components

**exceptions.py**
- Base exception hierarchy (TemplateError and subclasses)
- Context preservation with exception chaining
- Module-specific exceptions (Literature, LLM, Rendering, Publishing)
- Exception utility functions for context formatting

**logging_utils.py**
- Unified Python logging with consistent formatting
- Environment-based configuration (LOG_LEVEL 0-3)
- Context managers for operation tracking and timing
- Decorators for function call logging
- Integration with bash logging.sh format
- Emoji support for TTY output

**config_loader.py**
- YAML configuration file loading
- Environment variable support with priority
- Author and metadata formatting
- Configuration file discovery at `projects/{name}/manuscript/config.yaml`
- Environment variable export
- Translation language configuration

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

**checkpoint.py**
- Pipeline checkpoint management
- Save/restore pipeline state
- Stage result tracking

**retry.py**
- Retry logic with exponential backoff
- Transient failure handling
- Retryable operation wrappers

**performance.py**
- Performance monitoring and resource tracking
- System resource queries
- Performance metrics collection

**environment.py**
- Environment setup and validation
- Dependency checking and installation
- Build tool verification
- Directory structure setup

**script_discovery.py**
- Script discovery and execution
- Analysis script finding
- Orchestrator script discovery

**file_operations.py**
- File management utilities
- Output directory cleanup
- Final deliverable copying

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

### logging_utils.py

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

### config_loader.py

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
        Returns empty dict if config file not found or testing section missing
    """
```

### credentials.py

#### CredentialManager (class)
```python
class CredentialManager:
    """Manage credentials from .env and YAML config files.

    Supports loading credentials from:
    - Environment variables directly
    - .env files
    - YAML configuration files with environment variable substitution
    """

    def __init__(self, env_file: Optional[Path] = None,
                 config_file: Optional[Path] = None):
        """Initialize credential manager.

        Args:
            env_file: Path to .env file (optional, defaults to .env in root)
            config_file: Path to YAML config file (optional)
        """
```

#### get_zenodo_credentials (method)
```python
def get_zenodo_credentials(self, use_sandbox: bool = True) -> Dict[str, str]:
    """Get Zenodo API credentials.

    Args:
        use_sandbox: Whether to use sandbox environment (default: True)

    Returns:
        Dictionary with token and environment info
    """
```

#### get_github_credentials (method)
```python
def get_github_credentials(self) -> Dict[str, str]:
    """Get GitHub API credentials.

    Returns:
        Dictionary with token and repository info
    """
```

#### get_arxiv_credentials (method)
```python
def get_arxiv_credentials(self) -> Dict[str, Optional[str]]:
    """Get arXiv SWORD API credentials (optional).

    Returns:
        Dictionary with username and password (may be None)
    """
```

#### has_zenodo_credentials (method)
```python
def has_zenodo_credentials(self, use_sandbox: bool = True) -> bool:
    """Check if Zenodo credentials are available."""
```

#### has_github_credentials (method)
```python
def has_github_credentials(self) -> bool:
    """Check if GitHub credentials are available."""
```

#### has_arxiv_credentials (method)
```python
def has_arxiv_credentials(self) -> bool:
    """Check if arXiv credentials are available."""
```

### progress.py

#### ProgressBar (class)
```python
class ProgressBar:
    """Simple text-based progress bar for terminal output.

    Provides visual progress indication with percentage and optional ETA.
    Supports both item-based and token-based progress tracking.

    Example:
        >>> bar = ProgressBar(total=100, task="Processing files")
        >>> for i in range(100):
        ...     bar.update(i + 1)
        >>> bar.finish()
    """

    def __init__(
        self,
        total: int,
        task: str = "",
        width: int = 30,
        show_eta: bool = True,
        update_interval: float = 0.1,
        use_ema: bool = True
    ):
        """Initialize progress bar.

        Args:
            total: Total number of items to process
            task: Task description
            width: Width of progress bar in characters
            show_eta: Whether to show ETA
            update_interval: Minimum time between updates (seconds)
            use_ema: Whether to use exponential moving average for ETA
        """
```

#### update (method)
```python
def update(self, value: int, force: bool = False) -> None:
    """Update progress bar.

    Args:
        value: Current progress value
        force: Force update even if interval hasn't passed
    """
```

#### finish (method)
```python
def finish(self) -> None:
    """Finish progress bar and print final status."""
```

#### LLMProgressTracker (class)
```python
class LLMProgressTracker:
    """Progress tracker for LLM operations with token-based progress.

    Tracks token generation progress, throughput, and provides real-time updates.

    Example:
        >>> tracker = LLMProgressTracker(total_tokens=1000, task="Generating review")
        >>> for chunk in llm_stream:
        ...     tokens = estimate_tokens(chunk)
        ...     tracker.update_tokens(tokens)
        >>> tracker.finish()
    """

    def __init__(
        self,
        total_tokens: Optional[int] = None,
        task: str = "LLM Generation",
        show_throughput: bool = True
    ):
        """Initialize LLM progress tracker.

        Args:
            total_tokens: Total expected tokens (None for unknown)
            task: Task description
            show_throughput: Whether to show tokens/sec throughput
        """
```

#### update_tokens (method)
```python
def update_tokens(self, tokens: int) -> None:
    """Update token count.

    Args:
        tokens: Number of tokens generated in this chunk
    """
```

#### finish (method)
```python
def finish(self) -> None:
    """Finish tracking and display final stats."""
```

#### SubStageProgress (class)
```python
class SubStageProgress:
    """Track progress across multiple sub-stages within a main stage.

    Useful for operations with multiple steps (e.g., rendering multiple files).
    Uses EMA for improved ETA accuracy.

    Example:
        >>> progress = SubStageProgress(total=5, stage_name="Rendering PDFs")
        >>> for i, file in enumerate(files):
        ...     progress.start_substage(i + 1, file.name)
        ...     render_file(file)
        ...     progress.complete_substage()
    """

    def __init__(self, total: int, stage_name: str = "", use_ema: bool = True):
        """Initialize sub-stage progress tracker.

        Args:
            total: Total number of sub-stages
            stage_name: Name of the main stage
            use_ema: Whether to use exponential moving average for ETA (default: True)
        """
```

#### start_substage (method)
```python
def start_substage(self, substage_num: int, substage_name: str = "") -> None:
    """Start a new sub-stage.

    Args:
        substage_num: Sub-stage number (1-based)
        substage_name: Name of the sub-stage
    """
```

#### complete_substage (method)
```python
def complete_substage(self) -> None:
    """Mark current sub-stage as complete."""
```

#### get_eta (method)
```python
def get_eta(self) -> Optional[float]:
    """Get estimated time remaining.

    Returns:
        Estimated seconds remaining, or None if cannot calculate
    """
```

#### get_eta_with_confidence (method)
```python
def get_eta_with_confidence(self) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """Get ETA with confidence intervals.

    Returns:
        Tuple of (realistic_eta, optimistic_eta, pessimistic_eta)
    """
```

#### log_progress (method)
```python
def log_progress(self) -> None:
    """Log current progress with ETA."""
```

### checkpoint.py

#### StageResult (class)
```python
@dataclass
class StageResult:
    """Result of a pipeline stage execution."""
    name: str
    exit_code: int
    duration: float
    timestamp: str
    completed: bool = True
```

#### PipelineCheckpoint (class)
```python
@dataclass
class PipelineCheckpoint:
    """Pipeline checkpoint state."""
    pipeline_start_time: float
    last_stage_completed: int
    stage_results: list[StageResult]
    total_stages: int
    checkpoint_time: float

    def to_dict(self) -> dict[str, Any]:
        """Convert checkpoint to dictionary for serialization."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'PipelineCheckpoint':
        """Create checkpoint from dictionary."""
```

#### CheckpointManager (class)
```python
class CheckpointManager:
    """Manages pipeline checkpoints for resume capability."""

    def __init__(self, checkpoint_dir: Optional[Path] = None):
        """Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory for checkpoint files (default: projects/{name}/output/.checkpoints)
        """
```

#### save_checkpoint (method)
```python
def save_checkpoint(
    self,
    pipeline_start_time: float,
    last_stage_completed: int,
    stage_results: list[StageResult],
    total_stages: int
) -> None:
    """Save pipeline checkpoint.

    Args:
        pipeline_start_time: Pipeline start timestamp
        last_stage_completed: Last successfully completed stage number
        stage_results: List of stage results
        total_stages: Total number of stages
    """
```

#### load_checkpoint (method)
```python
def load_checkpoint(self) -> Optional[PipelineCheckpoint]:
    """Load pipeline checkpoint.

    Returns:
        PipelineCheckpoint if found and valid, None otherwise
    """
```

#### clear_checkpoint (method)
```python
def clear_checkpoint(self) -> None:
    """Clear saved checkpoint."""
```

#### checkpoint_exists (method)
```python
def checkpoint_exists(self) -> bool:
    """Check if checkpoint exists.

    Returns:
        True if checkpoint file exists and is valid
    """
```

#### validate_checkpoint (method)
```python
def validate_checkpoint(self) -> Tuple[bool, Optional[str]]:
    """Validate checkpoint integrity and consistency.

    Returns:
        Tuple of (is_valid, error_message)
        is_valid: True if checkpoint is valid and can be used
        error_message: None if valid, error description if invalid
    """
```

### retry.py

#### retry_with_backoff (function)
```python
def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to retry a function with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        exponential_base: Base for exponential backoff (default: 2.0)
        jitter: Add random jitter to prevent thundering herd (default: True)
        exceptions: Tuple of exception types to catch and retry (default: Exception)
        on_retry: Optional callback function(attempt_num, exception) called before retry

    Returns:
        Decorator function
    """
```

#### retry_on_transient_failure (function)
```python
def retry_on_transient_failure(
    max_attempts: int = 3,
    initial_delay: float = 1.0
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for retrying on common transient failures.

    Args:
        max_attempts: Maximum number of attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)

    Returns:
        Decorator function
    """
```

#### RetryableOperation (class)
```python
class RetryableOperation:
    """Context manager for retryable operations with manual control.

    Useful when you need more control over retry logic than a decorator provides.

    Example:
        >>> with RetryableOperation(max_attempts=3) as op:
        ...     for attempt in op:
        ...         try:
        ...             result = risky_operation()
        ...             op.succeed(result)
        ...         except TransientError as e:
        ...             op.retry(e)
    """

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0
    ):
        """Initialize retryable operation.

        Args:
            max_attempts: Maximum number of attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
        """
```

#### succeed (method)
```python
def succeed(self, result: Any = None) -> None:
    """Mark operation as successful.

    Args:
        result: Result value to store
    """
```

#### retry (method)
```python
def retry(self, exception: Exception) -> None:
    """Retry operation after delay.

    Args:
        exception: Exception that triggered the retry
    """
```

### performance.py

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

### environment.py

#### check_python_version (function)
```python
def check_python_version() -> bool:
    """Verify Python 3.8+ is available.

    Returns:
        True if Python version is 3.8 or higher, False otherwise
    """
```

#### check_dependencies (function)
```python
def check_dependencies(required_packages: List[str] | None = None) -> Tuple[bool, List[str]]:
    """Verify required packages are installed.

    Args:
        required_packages: List of package names to check. If None, uses default list.

    Returns:
        Tuple of (all_present, missing_packages)
    """
```

#### install_missing_packages (function)
```python
def install_missing_packages(packages: List[str]) -> bool:
    """Install missing packages using uv.

    Args:
        packages: List of package names to install

    Returns:
        True if installation successful, False otherwise
    """
```

#### check_build_tools (function)
```python
def check_build_tools(required_tools: dict[str, str] | None = None) -> bool:
    """Verify build tools are available.

    Args:
        required_tools: Dictionary mapping tool names to descriptions.
                       If None, uses default tools.

    Returns:
        True if all tools are available, False otherwise
    """
```

#### setup_directories (function)
```python
def setup_directories(repo_root: Path, directories: List[str] | None = None) -> bool:
    """Create required directory structure.

    Args:
        repo_root: Repository root directory
        directories: List of directory paths to create (relative to repo_root).
                    If None, uses default directories.

    Returns:
        True if all directories created successfully, False otherwise
    """
```

#### verify_source_structure (function)
```python
def verify_source_structure(repo_root: Path) -> bool:
    """Verify source code structure exists.

    Checks for the core components of the repository architecture:
    - infrastructure/ - Generic reusable build tools
    - project/ - Standalone research project

    Args:
        repo_root: Repository root directory

    Returns:
        True if required directories exist, False otherwise
    """
```

#### set_environment_variables (function)
```python
def set_environment_variables(repo_root: Path) -> bool:
    """Configure environment variables for pipeline.

    Args:
        repo_root: Repository root directory

    Returns:
        True if environment variables set successfully, False otherwise
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

### file_operations.py

#### clean_output_directory (function)
```python
def clean_output_directory(output_dir: Path) -> bool:
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
    - pdf/ - Complete PDF directory with manuscript and metadata
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

## Key Features

### Exception Handling
```python
from infrastructure.core import (
    TemplateError,
    raise_with_context,
    chain_exceptions
)

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
from infrastructure.core import get_logger, log_operation, log_timing

logger = get_logger(__name__)
logger.info("Starting process")

with log_operation("Data processing", logger):
    process_data()

with log_timing("Algorithm execution", logger):
    run_algorithm()
```

### Configuration
```python
from infrastructure.core import load_config, get_config_as_dict, get_translation_languages, find_config_file

config = load_config(Path("project/manuscript/config.yaml"))
env_dict = get_config_as_dict(Path("."))  # Loads from project/manuscript/config.yaml
config_path = find_config_file(Path("."))  # Returns project/manuscript/config.yaml if found
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
from infrastructure.core import ProgressBar, SubStageProgress

with ProgressBar(total=100, desc="Processing") as pbar:
    for i in range(100):
        pbar.update(1)
```

### Checkpoint Management
```python
from infrastructure.core import CheckpointManager, StageResult

checkpoint = CheckpointManager()
if checkpoint.checkpoint_exists():
    state = checkpoint.load_checkpoint()
else:
    # Run pipeline stages
    checkpoint.save_checkpoint(stage_results)
```

### Retry Logic
```python
from infrastructure.core import retry_with_backoff

@retry_with_backoff(max_attempts=3, base_delay=1.0)
def risky_operation():
    # Operation that may fail
    pass
```

### Performance Monitoring
```python
from infrastructure.core import PerformanceMonitor, get_system_resources

with PerformanceMonitor() as monitor:
    # Your code here
    pass

resources = get_system_resources()
print(f"CPU: {resources.cpu_percent}%, Memory: {resources.memory_percent}%")
```

### Environment Setup
```python
from infrastructure.core import check_python_version, check_dependencies, setup_directories

check_python_version(min_version=(3, 8))
check_dependencies(["pandas", "numpy"])
setup_directories(["output", "output/figures"])
```

### Script Discovery
```python
from infrastructure.core import discover_analysis_scripts, discover_orchestrators

scripts = discover_analysis_scripts(Path("projects/project/scripts"))
orchestrators = discover_orchestrators(Path("scripts"))
```

### File Operations
```python
from infrastructure.core import clean_output_directory, copy_final_deliverables

clean_output_directory(Path("output"))
copy_final_deliverables(Path("projects/project/output"), Path("output/project"))
```

## Testing

Run core tests with:
```bash
pytest tests/infrastructure/test_core/
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
- Verify `project/manuscript/config.yaml` exists and is valid YAML
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

## See Also

- [README.md](README.md) - Quick reference guide
- [`validation/`](../validation/) - Validation & quality assurance

