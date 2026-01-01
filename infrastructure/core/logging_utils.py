"""Unified Python logging module for the Research Project Template.

This module provides structured logging with consistent formatting across all Python
scripts in the template. It integrates with the bash logging.sh format and provides:
- Consistent log levels (DEBUG, INFO, WARN, ERROR)
- Context managers for operation tracking
- Performance timing utilities
- Integration with environment-based configuration

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""
from __future__ import annotations

import logging
import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, Iterator

# Import from split modules
from infrastructure.core.logging_formatters import JSONFormatter, TemplateFormatter
from infrastructure.core.logging_helpers import format_error_with_suggestions, format_duration
from infrastructure.core.logging_progress import (
    calculate_eta,
    calculate_eta_ema,
    calculate_eta_with_confidence,
    log_progress_bar,
    log_stage_with_eta as _log_stage_with_eta,
    log_resource_usage as _log_resource_usage,
    Spinner,
    log_with_spinner,
    StreamingProgress,
    log_progress_streaming,
)

# Type variable for generic context manager
T = TypeVar('T')


# =============================================================================
# LOG LEVEL CONFIGURATION
# =============================================================================

# Map environment LOG_LEVEL (0-3) to Python logging levels
LOG_LEVEL_MAP = {
    '0': logging.DEBUG,    # Most verbose
    '1': logging.INFO,     # Default
    '2': logging.WARNING,  # Warnings only
    '3': logging.ERROR,    # Errors only
}


# =============================================================================
# STANDARDIZED PROJECT LOGGING INTERFACE
# =============================================================================

"""
Standardized Logging Interface for Research Projects

This module provides a unified logging interface that works across both
infrastructure and project layers. Projects can use the simple ProjectLogger
class for consistent logging throughout their codebase.

USAGE PATTERNS:

1. Basic Project Logging:
   ```python
   from utils.logging import get_logger
   log = get_logger(__name__)
   log.info("Starting analysis")
   log.success("Completed successfully")
   ```

2. Context Managers:
   ```python
   with log.operation("Running simulation"):
       # Your code here
       pass
   ```

3. Progress Tracking:
   ```python
   log.progress(50, 100, "Processing data")
   log.stage(2, 5, "Data Analysis")
   ```

4. File Logging:
   ```python
   from infrastructure.core.logging_utils import setup_project_logging
   log = setup_project_logging(__name__, log_file="analysis.log")
   ```

ENVIRONMENT VARIABLES:
- LOG_LEVEL: 0=DEBUG, 1=INFO, 2=WARNING, 3=ERROR
- NO_EMOJI: Disable emoji in output (for CI/CD)
- STRUCTURED_LOGGING: Enable JSON structured logging

LOGGING LEVELS:
- DEBUG: Detailed diagnostic information
- INFO: General information about program execution
- WARNING: Warning messages for potential issues
- ERROR: Error messages for failures
- SUCCESS: Success confirmations with emoji
- HEADER: Section headers with formatting
- PROGRESS: Progress indicators with percentages
- STAGE: Pipeline stage indicators
- SUBSTEP: Sub-operation indicators

BEST PRACTICES:
1. Use __name__ as logger name for proper hierarchy
2. Use context managers for operations that have clear start/end
3. Use appropriate log levels (don't spam INFO with DEBUG details)
4. Use progress/stage logging for long-running operations
5. Test logging in your code (don't assume it works)
"""

class ProjectLogger:
    """Standardized logging interface for research projects.

    This class provides a simple, consistent logging interface that all projects
    can use. It wraps the infrastructure logging utilities with a clean API.

    Example:
        >>> from infrastructure.core.logging_utils import ProjectLogger
        >>> log = ProjectLogger(__name__)
        >>> log.info("Starting analysis...")
        >>> log.success("Analysis completed!")
        >>> log.progress(50, 100, "Processing data")
    """

    def __init__(self, name: str, level: Optional[int] = None):
        """Initialize project logger.

        Args:
            name: Logger name (usually __name__)
            level: Optional logging level override
        """
        self.name = name
        self._logger = get_logger(name)
        if level is not None:
            self._logger.setLevel(level)

    def debug(self, message: str, *args, **kwargs) -> None:
        """Log debug message."""
        self._logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs) -> None:
        """Log info message."""
        self._logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        """Log warning message."""
        self._logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        """Log error message."""
        self._logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> None:
        """Log critical message."""
        self._logger.critical(message, *args, **kwargs)

    def success(self, message: str) -> None:
        """Log success message with emoji."""
        log_success(message, self._logger)

    def header(self, message: str) -> None:
        """Log section header."""
        log_header(message, self._logger)

    def progress(self, current: int, total: int, task: str = "") -> None:
        """Log progress with percentage."""
        log_progress(current, total, task, self._logger)

    def stage(self, stage_num: int, total_stages: int, stage_name: str) -> None:
        """Log pipeline stage header."""
        log_stage(stage_num, total_stages, stage_name, self._logger)

    def substep(self, message: str) -> None:
        """Log substep with indentation."""
        log_substep(message, self._logger)

    @contextmanager
    def operation(self, operation: str, level: int = logging.INFO):
        """Context manager for logging operation start/completion."""
        with log_operation(operation, self._logger, level):
            yield

    @contextmanager
    def timing(self, label: str):
        """Context manager for timing operations."""
        with log_timing(label, self._logger):
            yield

    def resource_usage(self, stage_name: str = "") -> None:
        """Log current resource usage."""
        log_resource_usage(stage_name, self._logger)


# =============================================================================
# CONVENIENCE FUNCTIONS FOR PROJECTS
# =============================================================================

def get_project_logger(name: str, level: Optional[int] = None) -> ProjectLogger:
    """Get a standardized project logger.

    This is the recommended way for projects to get logging functionality.
    It provides a clean, consistent interface that works across all projects.

    Args:
        name: Logger name (usually __name__)
        level: Optional logging level override

    Returns:
        ProjectLogger instance

    Example:
        >>> from infrastructure.core.logging_utils import get_project_logger
        >>> log = get_project_logger(__name__)
        >>> log.info("Starting analysis")
        >>> log.success("Analysis completed!")
    """
    return ProjectLogger(name, level)


def setup_project_logging(name: str, level: Optional[int] = None,
                         log_file: Optional[Path | str] = None) -> ProjectLogger:
    """Set up project logging with optional file output.

    Args:
        name: Logger name (usually __name__)
        level: Optional logging level override
        log_file: Optional file to write logs to

    Returns:
        Configured ProjectLogger instance

    Example:
        >>> log = setup_project_logging(__name__, log_file="analysis.log")
        >>> log.info("Analysis started")
    """
    if log_file:
        setup_logger(name, level, log_file)
    return get_project_logger(name, level)


def get_log_level_from_env() -> int:
    """Get log level from LOG_LEVEL environment variable.
    
    Returns:
        Python logging level (DEBUG, INFO, WARNING, ERROR)
        
    Example:
        >>> os.environ['LOG_LEVEL'] = '0'
        >>> get_log_level_from_env()
        10  # logging.DEBUG
    """
    env_level = os.getenv('LOG_LEVEL', '1')  # Default to INFO
    return LOG_LEVEL_MAP.get(env_level, logging.INFO)


# =============================================================================
# EMOJI SUPPORT (MATCHING BASH LOGGING)
# =============================================================================

EMOJIS = {
    'info': 'ℹ️',
    'success': '✅',
    'warning': '⚠️',
    'error': '❌',
    'rocket': '🚀',
    'sparkles': '✨',
    'folder': '📁',
    'book': '📖',
    'clean': '🧹',
    'gear': '⚙️',
    'chart': '📊',
}

# Check if emojis should be used (NO_EMOJI env var or not a TTY)
USE_EMOJIS = not os.getenv('NO_EMOJI') and sys.stdout.isatty()

# Check if structured logging (JSON) should be used
USE_STRUCTURED_LOGGING = os.getenv('STRUCTURED_LOGGING', 'false').lower() == 'true'


# =============================================================================
# LOGGER CONFIGURATION
# =============================================================================

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
        
    Example:
        >>> logger = setup_logger(__name__)
        >>> logger.info("Processing started")
        ℹ️ [2025-11-21 12:00:00] [INFO] Processing started
    """
    logger = logging.getLogger(name)
    
    # Set level from environment or parameter
    if level is None:
        level = get_log_level_from_env()
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Check if we're in test environment (pytest)
    # Check multiple indicators for pytest environment
    is_test_env = (
        os.getenv('PYTEST_CURRENT_TEST') is not None or
        'pytest' in sys.modules or
        any('pytest' in str(v) for v in sys.modules.values() if hasattr(v, '__file__'))
    )
    
    # In test environment: don't add console handler, enable propagation
    # so pytest's caplog can capture logs from root logger
    # In normal environment: add console handler, disable propagation
    if not is_test_env:
        # Console handler (only in non-test environment)
        console_handler = logging.StreamHandler(sys.stdout)
        if USE_STRUCTURED_LOGGING:
            console_handler.setFormatter(JSONFormatter())
        else:
            console_handler.setFormatter(TemplateFormatter())
        logger.addHandler(console_handler)
    
    # File handler (optional, works in both environments)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        # File logs without emojis
        file_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Set propagation based on environment
    logger.propagate = is_test_env
    
    # In test environment, ensure root logger is configured to receive propagated logs
    if is_test_env:
        root_logger = logging.getLogger()
        # Ensure root logger level allows the logs through
        if root_logger.level > logger.level:
            root_logger.setLevel(logger.level)
        # Remove any stdout/stderr handlers from root logger that might interfere with caplog
        # (pytest's caplog will add its own handler)
        root_handlers_to_remove = [
            h for h in root_logger.handlers
            if isinstance(h, logging.StreamHandler) and 
            (h.stream is sys.stdout or h.stream is sys.stderr)
        ]
        for h in root_handlers_to_remove:
            root_logger.removeHandler(h)
        # Ensure root logger has at least WARNING level to not filter out our logs
        if root_logger.level == logging.NOTSET:
            root_logger.setLevel(logging.WARNING)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger with standard configuration.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
        
    Example:
        >>> from logging_utils import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Task complete")
    """
    logger = logging.getLogger(name)
    
    # Check if we're in test environment (same detection as setup_logger)
    is_test_env = (
        os.getenv('PYTEST_CURRENT_TEST') is not None or
        'pytest' in sys.modules or
        any('pytest' in str(v) for v in sys.modules.values() if hasattr(v, '__file__'))
    )
    
    # If not configured, set up with defaults
    if not logger.handlers:
        return setup_logger(name)
    
    # If in test environment and logger was configured before test mode,
    # force reconfiguration to enable propagation and remove console handlers
    if is_test_env:
        # Check if logger needs reconfiguration (has console handlers or propagate is False)
        has_console_handler = any(
            isinstance(h, logging.StreamHandler) and 
            (h.stream is sys.stdout or h.stream is sys.stderr)
            for h in logger.handlers
        )
        
        if has_console_handler or not logger.propagate:
            # Force reconfiguration by clearing handlers and calling setup_logger
            logger.handlers.clear()
            return setup_logger(name)
        # Ensure propagation is enabled even if handlers exist
        logger.propagate = True
    
    return logger


# =============================================================================
# CONTEXT MANAGERS
# =============================================================================

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
        
    Example:
        >>> with log_operation("Processing data", logger):
        ...     process_data()
        ℹ️ [2025-11-21 12:00:00] [INFO] Starting: Processing data
        ℹ️ [2025-11-21 12:00:05] [INFO] Completed: Processing data (5.0s)
    """
    if logger is None:
        logger = get_logger(__name__)
    
    logger.log(level, f"Starting: {operation}")
    start_time = time.time()
    
    try:
        yield
        duration = time.time() - start_time
        # Only log completion if duration exceeds threshold
        if duration >= min_duration_to_log:
            logger.log(level, f"Completed: {operation} ({duration:.1f}s)")
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Failed: {operation} after {duration:.1f}s - {e}")
        raise


@contextmanager
def log_operation_silent(
    operation: str,
    logger: Optional[logging.Logger] = None,
    level: int = logging.DEBUG
) -> Iterator[None]:
    """Context manager for logging operation start only (no completion message).
    
    Useful for operations that complete very quickly or don't need completion logging.
    
    Args:
        operation: Description of the operation
        logger: Logger instance (creates one if None)
        level: Log level for messages
        
    Yields:
        None
        
    Example:
        >>> with log_operation_silent("Quick check", logger):
        ...     quick_check()
        ℹ️ [2025-11-21 12:00:00] [DEBUG] Starting: Quick check
    """
    if logger is None:
        logger = get_logger(__name__)
    
    logger.log(level, f"Starting: {operation}")
    start_time = time.time()
    
    try:
        yield
        # No completion message logged
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Failed: {operation} after {duration:.1f}s - {e}")
        raise


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
        
    Example:
        >>> with log_timing("Data processing", logger):
        ...     expensive_operation()
        ℹ️ [2025-11-21 12:00:05] [INFO] Data processing: 5.0s
    """
    if logger is None:
        logger = get_logger(__name__)
    
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.info(f"{label}: {duration:.1f}s")


def log_function_call(logger: Optional[logging.Logger] = None) -> Callable:
    """Decorator to log function calls with timing.
    
    Args:
        logger: Logger instance (creates one if None)
        
    Returns:
        Decorator function
        
    Example:
        >>> @log_function_call(logger)
        ... def process_data():
        ...     pass
        ℹ️ [2025-11-21 12:00:00] [INFO] Calling: process_data
        ℹ️ [2025-11-21 12:00:05] [INFO] Completed: process_data (5.0s)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        func_logger = logger or get_logger(func.__module__)
        
        def wrapper(*args: Any, **kwargs: Any) -> T:
            func_logger.info(f"Calling: {func.__name__}")
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                func_logger.info(f"Completed: {func.__name__} ({duration:.1f}s)")
                return result
            except Exception as e:
                duration = time.time() - start_time
                func_logger.error(f"Failed: {func.__name__} after {duration:.1f}s - {e}")
                raise
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    
    return decorator


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def log_success(message: str, logger: Optional[logging.Logger] = None) -> None:
    """Log a success message with success emoji.
    
    Args:
        message: Success message
        logger: Logger instance (creates one if None)
        
    Example:
        >>> log_success("Build completed successfully")
        ✅ [2025-11-21 12:00:00] [INFO] Build completed successfully
    """
    if logger is None:
        logger = get_logger(__name__)
    
    emoji = EMOJIS['success'] if USE_EMOJIS else '[SUCCESS]'
    logger.info(f"{emoji} {message}" if USE_EMOJIS else message)


def log_header(message: str, logger: Optional[logging.Logger] = None) -> None:
    """Log a section header with visual emphasis.
    
    Args:
        message: Header message
        logger: Logger instance (creates one if None)
        
    Example:
        >>> log_header("STAGE 01: Setup")
        🚀 [2025-11-21 12:00:00] [INFO]
        🚀 [2025-11-21 12:00:00] [INFO] ============================================================
        🚀 [2025-11-21 12:00:00] [INFO] STAGE 01: Setup
        🚀 [2025-11-21 12:00:00] [INFO] ============================================================
    """
    if logger is None:
        logger = get_logger(__name__)
    
    emoji = EMOJIS['rocket'] if USE_EMOJIS else ''
    separator = "=" * 50

    logger.info("")
    logger.info(separator)
    logger.info(message)
    logger.info(separator)


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
        
    Example:
        >>> log_progress(15, 100, "Processing files")
        ℹ️ [2025-11-21 12:00:00] [INFO] [15/100 - 15%] Processing files
    """
    if logger is None:
        logger = get_logger(__name__)
    
    percent = (current * 100) // total if total > 0 else 0
    logger.info(f"[{current}/{total} - {percent}%] {task}")


def log_stage(
    stage_num: int,
    total_stages: int,
    stage_name: str,
    logger: Optional[logging.Logger] = None
) -> None:
    """Log a pipeline stage header with consistent formatting.
    
    Provides standardized stage header formatting across all pipeline scripts.
    
    Args:
        stage_num: Current stage number (1-based)
        total_stages: Total number of stages
        stage_name: Name of the stage
        logger: Logger instance (creates one if None)
        
    Example:
        >>> log_stage(3, 7, "PDF Rendering")
        ℹ️ [2025-11-21 12:00:00] [INFO]
        ℹ️ [2025-11-21 12:00:00] [INFO] [3/7] PDF Rendering
        ℹ️ [2025-11-21 12:00:00] [INFO] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    if logger is None:
        logger = get_logger(__name__)
    
    separator = "━" * 46
    logger.info("")
    logger.info(f"[{stage_num}/{total_stages}] {stage_name}")
    logger.info(separator)


def log_substep(
    message: str,
    logger: Optional[logging.Logger] = None
) -> None:
    """Log a substep within a stage with consistent indentation.
    
    Adds a leading newline and indentation for visual separation.
    
    Args:
        message: Substep description
        logger: Logger instance (creates one if None)
        
    Example:
        >>> log_substep("Validating PDF files...")
        ℹ️ [2025-11-21 12:00:00] [INFO]
        ℹ️ [2025-11-21 12:00:00] [INFO]   Validating PDF files...
    """
    if logger is None:
        logger = get_logger(__name__)
    
    logger.info(f"\n  {message}")


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

# Create default logger for this module
_default_logger = setup_logger(__name__)


def set_global_log_level(level: int) -> None:
    """Set log level for all template loggers.
    
    Args:
        level: Python logging level (DEBUG, INFO, WARNING, ERROR)
        
    Example:
        >>> set_global_log_level(logging.DEBUG)
    """
    logging.getLogger().setLevel(level)
    for logger_name in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(logger_name)
        if hasattr(logger, 'setLevel'):
            logger.setLevel(level)


# Public API exports
__all__ = [
    # Core functions
    'get_log_level_from_env',
    'setup_logger',
    'get_logger',
    'set_global_log_level',
    # Context managers
    'log_operation',
    'log_operation_silent',
    'log_timing',
    'log_function_call',
    # Utility functions
    'log_success',
    'log_header',
    'log_progress',
    'log_stage',
    'log_substep',
    'log_file_generated',
    # Helpers
    'format_error_with_suggestions',
    'format_duration',
    # Progress utilities
    'calculate_eta',
    'calculate_eta_ema',
    'calculate_eta_with_confidence',
    'log_progress_bar',
    'log_stage_with_eta',
    'log_resource_usage',
    'Spinner',
    'log_with_spinner',
    'StreamingProgress',
    'log_progress_streaming',
    # Formatters
    'JSONFormatter',
    'TemplateFormatter',
    # Constants
    'EMOJIS',
    'USE_EMOJIS',
    'USE_STRUCTURED_LOGGING',
]


# Wrapper functions
def log_stage_with_eta(
    stage_num: int,
    total_stages: int,
    stage_name: str,
    pipeline_start: Optional[float] = None,
    logger: Optional[logging.Logger] = None
) -> None:
    """Log a pipeline stage header with ETA calculation.
    
    Provides standardized stage header formatting with ETA calculation
    similar to the bash script's log_stage function.
    
    Args:
        stage_num: Current stage number (1-based)
        total_stages: Total number of stages
        stage_name: Name of the stage
        pipeline_start: Pipeline start time (for ETA calculation)
        logger: Logger instance (creates one if None)
        
    Example:
        >>> import time
        >>> start = time.time()
        >>> time.sleep(5)
        >>> log_stage_with_eta(3, 7, "PDF Rendering", start)
        ℹ️ [2025-11-21 12:00:00] [INFO]
        ℹ️ [2025-11-21 12:00:00] [INFO] [3/7] PDF Rendering (42% complete)
        ℹ️ [2025-11-21 12:00:00] [INFO]   Elapsed: 5s | ETA: 6s
        ℹ️ [2025-11-21 12:00:00] [INFO] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    if logger is None:
        logger = get_logger(__name__)
    
    percentage = (stage_num * 100) // total_stages if total_stages > 0 else 0
    separator = "━" * 46
    
    logger.info("")
    logger.info(f"[{stage_num}/{total_stages}] {stage_name} ({percentage}% complete)")
    
    # Calculate and display ETA if pipeline start time provided
    if pipeline_start is not None and stage_num > 0:
        elapsed = time.time() - pipeline_start
        if elapsed > 0:
            eta_seconds = calculate_eta(elapsed, stage_num, total_stages)
            if eta_seconds is not None:
                elapsed_str = format_duration(elapsed)
                eta_str = format_duration(eta_seconds)
                logger.info(f"  Elapsed: {elapsed_str} | ETA: {eta_str}")
    
    logger.info(separator)


def log_resource_usage(
    stage_name: str = "",
    logger: Optional[logging.Logger] = None
) -> None:
    """Log current resource usage (if psutil available).
    
    Provides memory and CPU usage information when psutil is installed.
    Falls back gracefully if psutil is not available.
    
    Args:
        stage_name: Name of the stage (for context)
        logger: Logger instance (creates one if None)
        
    Example:
        >>> log_resource_usage("PDF Rendering")
        ℹ️ [2025-11-21 12:00:00] [INFO]   Resource usage: Memory: 512 MB, CPU: 15.2%
    """
    if logger is None:
        logger = get_logger(__name__)
    
    try:
        import psutil
        process = psutil.Process()
        
        # Get memory usage
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)
        
        # Get CPU usage (average over 0.1s)
        cpu_percent = process.cpu_percent(interval=0.1)
        
        # Format resource info
        resource_info = f"Memory: {memory_mb:.0f} MB"
        if cpu_percent > 0:
            resource_info += f", CPU: {cpu_percent:.1f}%"
        
        if stage_name:
            logger.info(f"  Resource usage ({stage_name}): {resource_info}")
        else:
            logger.info(f"  Resource usage: {resource_info}")
            
    except ImportError:
        # psutil not available - skip resource reporting
        pass
    except Exception as e:
        # Any other error - log at debug level
        logger.debug(f"Failed to get resource usage: {e}")


# =============================================================================
# LOG AGGREGATION AND ANALYSIS
# =============================================================================

class LogAggregator:
    """Aggregate and analyze log messages for summary reporting."""
    
    def __init__(self):
        """Initialize log aggregator."""
        self.messages = {
            'debug': [],
            'info': [],
            'warning': [],
            'error': [],
            'success': [],
        }
        self.start_time = None
        self.end_time = None
        
    def add_message(self, level: str, message: str, timestamp: Optional[float] = None):
        """Add a log message to the aggregator.
        
        Args:
            level: Log level (debug, info, warning, error, success)
            message: Log message text
            timestamp: Message timestamp (default: current time)
        """
        import time
        if timestamp is None:
            timestamp = time.time()
            
        if level.lower() in self.messages:
            self.messages[level.lower()].append({
                'message': message,
                'timestamp': timestamp
            })
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of aggregated logs.
        
        Returns:
            Dictionary with log statistics and key messages
        """
        summary = {
            'counts': {level: len(msgs) for level, msgs in self.messages.items()},
            'total_messages': sum(len(msgs) for msgs in self.messages.values()),
            'recent_errors': [m['message'] for m in self.messages['error'][-5:]],
            'recent_warnings': [m['message'] for m in self.messages['warning'][-5:]],
            'has_errors': len(self.messages['error']) > 0,
            'has_warnings': len(self.messages['warning']) > 0,
        }
        return summary
    
    def generate_report(self) -> str:
        """Generate human-readable log summary report.
        
        Returns:
            Formatted summary report string
        """
        summary = self.get_summary()
        
        lines = [
            "",
            "LOG SUMMARY",
            "=" * 60,
            "",
            "Message Counts:",
        ]
        
        for level, count in summary['counts'].items():
            if count > 0:
                lines.append(f"  {level.upper()}: {count}")
        
        lines.append(f"  TOTAL: {summary['total_messages']}")
        lines.append("")
        
        if summary['recent_errors']:
            lines.append("Recent Errors:")
            for err in summary['recent_errors']:
                lines.append(f"  • {err}")
            lines.append("")
        
        if summary['recent_warnings']:
            lines.append("Recent Warnings:")
            for warn in summary['recent_warnings']:
                lines.append(f"  • {warn}")
            lines.append("")
        
        return "\n".join(lines)
    
    def save_to_file(self, output_path: Path):
        """Save aggregated logs to file.
        
        Args:
            output_path: Path to save log summary
        """
        import json
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        summary = self.get_summary()
        summary['all_messages'] = self.messages
        
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)


def collect_log_statistics(log_file: Path) -> Dict[str, Any]:
    """Collect statistics from a log file.
    
    Args:
        log_file: Path to log file
        
    Returns:
        Dictionary with log statistics
    """
    if not log_file.exists():
        return {
            'error': 'Log file not found',
            'counts': {},
            'total_lines': 0
        }
    
    stats = {
        'counts': {
            'debug': 0,
            'info': 0,
            'warning': 0,
            'error': 0,
            'critical': 0
        },
        'total_lines': 0,
        'errors': [],
        'warnings': []
    }
    
    try:
        with open(log_file, 'r') as f:
            for line in f:
                stats['total_lines'] += 1
                line_lower = line.lower()
                
                if 'debug' in line_lower:
                    stats['counts']['debug'] += 1
                elif 'info' in line_lower:
                    stats['counts']['info'] += 1
                elif 'warning' in line_lower or 'warn' in line_lower:
                    stats['counts']['warning'] += 1
                    if len(stats['warnings']) < 10:  # Keep last 10
                        stats['warnings'].append(line.strip())
                elif 'error' in line_lower:
                    stats['counts']['error'] += 1
                    if len(stats['errors']) < 10:  # Keep last 10
                        stats['errors'].append(line.strip())
                elif 'critical' in line_lower:
                    stats['counts']['critical'] += 1
                    if len(stats['errors']) < 10:
                        stats['errors'].append(line.strip())
    
    except Exception as e:
        stats['error'] = f"Failed to parse log file: {e}"
    
    return stats


def generate_log_summary(log_file: Path, output_file: Optional[Path] = None) -> str:
    """Generate summary report from log file.
    
    Args:
        log_file: Path to log file to analyze
        output_file: Optional path to save summary (default: None)
        
    Returns:
        Formatted summary string
    """
    stats = collect_log_statistics(log_file)
    
    if 'error' in stats and stats.get('total_lines', 0) == 0:
        return f"Error: {stats['error']}"
    
    lines = [
        "",
        f"LOG ANALYSIS: {log_file.name}",
        "=" * 60,
        "",
        f"Total Lines: {stats['total_lines']}",
        "",
        "Message Breakdown:",
    ]
    
    for level, count in stats['counts'].items():
        if count > 0:
            lines.append(f"  {level.upper()}: {count}")
    
    if stats.get('errors'):
        lines.append("")
        lines.append(f"Recent Errors ({len(stats['errors'])}):")
        for err in stats['errors'][:5]:
            lines.append(f"  • {err[:100]}")  # Truncate long lines
    
    if stats.get('warnings'):
        lines.append("")
        lines.append(f"Recent Warnings ({len(stats['warnings'])}):")
        for warn in stats['warnings'][:5]:
            lines.append(f"  • {warn[:100]}")  # Truncate long lines
    
    lines.append("")
    
    summary_text = "\n".join(lines)
    
    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(summary_text)
    
    return summary_text

