## Usage Examples

### Basic Logging Setup
```python
from infrastructure.core import get_logger
from infrastructure.core.logging.setup import setup_logger

# Get default logger
logger = get_logger(__name__)
logger.info("Starting operation")

# Setup custom logger with file output
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
from infrastructure.core.config.loader import load_config, get_config_as_dict

# Load from file
config = load_config("config.yaml")

# Get as environment variables
env_vars = get_config_as_dict(Path("."))
for key, value in env_vars.items():
    os.environ[key] = value
```

### Pipeline Execution
```python
from infrastructure.core.pipeline import PipelineExecutor

# Execute single project pipeline
executor = PipelineExecutor(Path("."), "my_project")
results = executor.execute_pipeline()

# Execute with resume capability
results = executor.execute_pipeline(resume=True)
```

### Multi-Project Orchestration
```python
from infrastructure.core.pipeline.multi_project import MultiProjectOrchestrator

# Execute multiple projects
orchestrator = MultiProjectOrchestrator(
    Path("."),
    ["project1", "project2", "project3"]
)
results = orchestrator.execute_all_projects(core_only=True)

# Generate executive report
reports = orchestrator.generate_executive_report(Path("output/executive"))
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

#### get_health_status (function)
```python
def get_health_status() -> Dict[str, Any]:
    """Get detailed health status.

    Returns:
        Dictionary with health status information
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

### logging/formatters.py

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

### logging/progress.py

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

### config/cli.py

#### main (function)
```python
def main():
    """Main function for config CLI."""
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
    """Mark current sub-stage as."""
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

### runtime/checkpoint.py

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

### runtime/retry.py

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
def verify_analysis_outputs(
    repo_root: Path,
    project_name: str = "project",
    project_dir: Path | None = None,
) -> bool:
    """Verify that analysis generated expected outputs.

    Probes ``output/figures`` and ``output/data`` under the resolved
    project directory in two passes:

    * **First pass** records ``(dir, exists, file_count)`` for each
      expected output directory.
    * **Second pass** logs the result. When at least one expected
      directory contains files, the "Output directory not yet created"
      and "Output directory is empty" lines for the *other* directories
      are downgraded from INFO to DEBUG. This keeps logs quiet for
      projects whose analysis legitimately produces only one output
      kind (figures-only, data-only) without hiding the warning when
      analysis produced nothing at all.

    Args:
        repo_root: Repository root directory.
        project_name: Project directory name (default: ``"project"``).
        project_dir: Absolute path to the project directory. Defaults
            to ``repo_root / "projects" / project_name``.

    Returns:
        ``True`` if outputs are present or no analysis scripts were
        expected to run; ``False`` only when scripts exist but every
        expected output directory is empty or absent.
    """
```

### files/operations.py

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

### files/inventory.py

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

### pipeline/executor.py

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

### security.py

#### SecurityValidator (class)
```python
class SecurityValidator:
    """Validates and sanitizes input for security.

    LLM-specific prompt sanitization lives in
    ``infrastructure.llm.core.sanitization.sanitize_llm_input``.
    """
```

#### get_security_headers (function)
```python
def get_security_headers() -> dict[str, str]:
    """Return comprehensive HTTP security headers."""
```

#### RateLimiter (class)
```python
class RateLimiter:
    """Rate limiting for API requests."""
    
    def check_rate_limit(self, identifier: str) -> bool:
        """Check if request is within rate limit.
        
        Args:
            identifier: Request identifier
            
        Returns:
            True if within limit, False otherwise
        """
```

#### SecurityMonitor (class)
```python
class SecurityMonitor:
    """Monitors security events and violations."""
    
    def log_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log a security event.
        
        Args:
            event_type: Type of security event
            details: Event details
        """
```

#### SecurityViolation (class)
```python
class SecurityViolation(Exception):
    """Raised when a security violation is detected."""
    pass
```

#### get_security_validator (function)
```python
def get_security_validator() -> SecurityValidator:
    """Get security validator instance."""
```

#### get_security_headers (function)
```python
def get_security_headers() -> Dict[str, str]:
    """Get security headers dictionary."""
```

#### get_rate_limiter (function)
```python
def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance."""
```

#### get_security_monitor (function)
```python
def get_security_monitor() -> SecurityMonitor:
    """Get security monitor instance."""
```

#### rate_limit (decorator)
```python
@rate_limit(max_requests: int = 100, window_seconds: int = 60)
def api_function():
    """Rate-limited function decorator."""
    pass
```

### runtime/health_check.py

#### SystemHealthChecker (class)
```python
class SystemHealthChecker:
    """Checks system health and component status."""
    
    def check_health(self) -> Dict[str, Any]:
        """Perform health check.
        
        Returns:
            Health status dictionary
        """
    
    def check_component(self, component: str) -> Dict[str, Any]:
        """Check health of specific component.
        
        Args:
            component: Component name to check
            
        Returns:
            Component health status
        """
```

#### get_health_status (function)
```python
def get_health_status() -> Dict[str, Any]:
    """Get current health status."""
```

### cli.py

#### create_parser (function)
```python
def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser.
    
    Returns:
        Configured argument parser
    """
```

#### main (function)
```python
def main() -> int:
    """Main CLI entry point.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
```

#### handle_pipeline_command (function)
```python
def handle_pipeline_command(args: argparse.Namespace) -> int:
    """Handle pipeline command.
    
    Args:
        args: Parsed command arguments
        
    Returns:
        Exit code
    """
```

#### handle_multi_project_command (function)
```python
def handle_multi_project_command(args: argparse.Namespace) -> int:
    """Handle multi-project command.
    
    Args:
        args: Parsed command arguments
        
    Returns:
        Exit code
    """
```

#### handle_inventory_command (function)
```python
def handle_inventory_command(args: argparse.Namespace) -> int:
    """Handle inventory command.
    
    Args:
        args: Parsed command arguments
        
    Returns:
        Exit code
    """
```

#### handle_discover_command (function)
```python
def handle_discover_command(args: argparse.Namespace) -> int:
    """Handle discover command.
    
    Args:
        args: Parsed command arguments
        
    Returns:
        Exit code
    """
```

### config/cli.py

This module provides CLI commands for configuration management. See `cli.py` for integration.

### menu.py

This module provides interactive menu system utilities for menu-driven user interfaces.

### logging/formatters.py

This module provides logging formatter utilities and custom log format definitions.

### logging/helpers.py

This module provides additional logging helper functions beyond those in `logging/utils.py`.

### logging/progress.py

This module provides progress logging utilities that integrate progress tracking with logging.

### runtime/function_profiler.py

This module provides function-level profiling utilities (cProfile/tracemalloc) and benchmarking helpers. See `pipeline/stage_monitor.py` for stage-level resource monitoring.

### pipeline/summary.py

#### generate_pipeline_summary (function)
```python
def generate_pipeline_summary(
    stage_results: List[StageResult],
    total_duration: float,
    output_dir: Path,
    format: str = "text"
) -> str:
    """Generate pipeline execution summary.

    Args:
        stage_results: List of stage execution results
        total_duration: Total pipeline duration in seconds
        output_dir: Output directory path
        format: Output format ('text' or 'json')

    Returns:
        Formatted summary string
    """
```
