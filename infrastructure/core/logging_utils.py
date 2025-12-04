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
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, Iterator

# Import TemplateError for error formatting (imported at function level to avoid circular import)

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


# =============================================================================
# CUSTOM FORMATTER
# =============================================================================

class TemplateFormatter(logging.Formatter):
    """Custom formatter matching bash logging.sh format.
    
    Format: [YYYY-MM-DD HH:MM:SS] [LEVEL] message
    Adds emojis when appropriate and running in a TTY.
    """
    
    LEVEL_EMOJIS = {
        logging.DEBUG: '',
        logging.INFO: EMOJIS['info'] if USE_EMOJIS else '',
        logging.WARNING: EMOJIS['warning'] if USE_EMOJIS else '',
        logging.ERROR: EMOJIS['error'] if USE_EMOJIS else '',
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with timestamp and emoji.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted log message
        """
        # Create timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Get emoji for level
        emoji = self.LEVEL_EMOJIS.get(record.levelno, '')
        emoji_str = f"{emoji} " if emoji else ""
        
        # Format message
        level_name = record.levelname
        message = record.getMessage()
        
        return f"{emoji_str}[{timestamp}] [{level_name}] {message}"


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
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(TemplateFormatter())
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        # File logs without emojis
        file_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Don't propagate to root logger
    logger.propagate = False
    
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
    
    # If not configured, set up with defaults
    if not logger.handlers:
        return setup_logger(name)
    
    return logger


# =============================================================================
# CONTEXT MANAGERS
# =============================================================================

@contextmanager
def log_operation(
    operation: str,
    logger: Optional[logging.Logger] = None,
    level: int = logging.INFO
) -> Iterator[None]:
    """Context manager for logging operation start and completion.
    
    Args:
        operation: Description of the operation
        logger: Logger instance (creates one if None)
        level: Log level for messages
        
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
        logger.log(level, f"Completed: {operation} ({duration:.1f}s)")
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


# =============================================================================
# DECORATORS
# =============================================================================

def log_function_call(logger: Optional[logging.Logger] = None) -> Callable:
    """Decorator to log function calls with arguments and timing.
    
    Args:
        logger: Logger instance (creates one if None)
        
    Returns:
        Decorator function
        
    Example:
        >>> @log_function_call(logger)
        ... def process_file(filename: str) -> bool:
        ...     return True
        >>> process_file("data.csv")
        ℹ️ [2025-11-21 12:00:00] [INFO] Calling: process_file(filename='data.csv')
        ℹ️ [2025-11-21 12:00:01] [INFO] Returned: process_file -> True (1.0s)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)
            
            # Log function call
            args_str = ', '.join(repr(a) for a in args)
            kwargs_str = ', '.join(f"{k}={v!r}" for k, v in kwargs.items())
            all_args = ', '.join(filter(None, [args_str, kwargs_str]))
            
            logger.debug(f"Calling: {func.__name__}({all_args})")
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.debug(f"Returned: {func.__name__} -> {result!r} ({duration:.1f}s)")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Exception in {func.__name__} after {duration:.1f}s: {e}",
                    exc_info=True
                )
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
        >>> import logging
        >>> set_global_log_level(logging.DEBUG)
    """
    for name in logging.Logger.manager.loggerDict:
        if 'infrastructure' in name or 'scripts' in name:
            logger = logging.getLogger(name)
            logger.setLevel(level)


def log_progress_bar(
    current: int, 
    total: int, 
    task: str = "", 
    width: int = 20,
    show_eta: bool = False,
    elapsed_time: Optional[float] = None
) -> None:
    """Display a simple text-based progress bar.

    Args:
        current: Current progress value
        total: Total progress value
        task: Task description to display
        width: Width of the progress bar in characters
        show_eta: Whether to show estimated time remaining
        elapsed_time: Elapsed time in seconds (for ETA calculation)

    Example:
        >>> log_progress_bar(15, 100, "Processing files")
        ℹ️ [████████░░░░░░░░] Processing files 15/100 (15%)
        >>> log_progress_bar(15, 100, "Processing files", show_eta=True, elapsed_time=30.0)
        ℹ️ [████████░░░░░░░░] Processing files 15/100 (15%) ETA: 2m 10s
    """
    # Get logger instance (avoiding scoping issues)
    progress_logger = get_logger(__name__)

    percent = (current * 100) // total if total > 0 else 0
    filled = (current * width) // total if total > 0 else 0
    bar = "█" * filled + "░" * (width - filled)

    task_str = f" {task}" if task else ""
    status = f"  [{bar}]{task_str} {current}/{total} ({percent}%)"
    
    # Add ETA if requested
    if show_eta and elapsed_time is not None and current > 0:
        eta_seconds = calculate_eta(elapsed_time, current, total)
        if eta_seconds is not None:
            status += f" ETA: {format_duration(eta_seconds)}"
    
    progress_logger.info(status)


def format_error_with_suggestions(error: Any) -> str:
    """Format error message with context and recovery suggestions.

    Args:
        error: TemplateError instance with context and suggestions

    Returns:
        Formatted error message string

    Example:
        >>> from infrastructure.core.exceptions import TemplateError
        >>> error = TemplateError("File not found", context={"file": "test.txt"}, suggestions=["Check file path", "Verify permissions"])
        >>> print(format_error_with_suggestions(error))
        ❌ File not found
        <BLANKLINE>
        📋 Context:
           • file: test.txt
        <BLANKLINE>
        🔧 Recovery Options:
           1. Check file path
           2. Verify permissions
    """
    # Import here to avoid circular import
    from infrastructure.core.exceptions import TemplateError
    
    if not isinstance(error, TemplateError):
        return str(error)
    
    lines = [f"❌ {error.message}"]

    if error.context:
        lines.append("\n📋 Context:")
        for key, value in error.context.items():
            lines.append(f"   • {key}: {value}")

    if error.suggestions:
        lines.append("\n🔧 Recovery Options:")
        for i, suggestion in enumerate(error.suggestions, 1):
            lines.append(f"   {i}. {suggestion}")

    return "\n".join(lines)


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string (e.g., "1m 23s", "45s")
        
    Example:
        >>> format_duration(83)
        '1m 23s'
        >>> format_duration(45)
        '45s'
    """
    if seconds < 60:
        return f"{int(seconds)}s"
    
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    
    if minutes < 60:
        return f"{minutes}m {secs}s"
    
    hours = minutes // 60
    mins = minutes % 60
    
    if hours < 24:
        return f"{hours}h {mins}m"
    
    days = hours // 24
    hrs = hours % 24
    return f"{days}d {hrs}h"


def calculate_eta(
    elapsed_time: float,
    completed_items: int,
    total_items: int
) -> Optional[float]:
    """Calculate estimated time remaining based on current progress.
    
    Args:
        elapsed_time: Time elapsed so far in seconds
        completed_items: Number of items completed
        total_items: Total number of items
        
    Returns:
        Estimated time remaining in seconds, or None if cannot calculate
        
    Example:
        >>> calculate_eta(30.0, 3, 10)
        70.0  # 30s for 3 items = 10s/item, 7 remaining = 70s
    """
    if completed_items <= 0 or total_items <= 0:
        return None
    
    if completed_items >= total_items:
        return 0.0
    
    avg_time_per_item = elapsed_time / completed_items
    remaining_items = total_items - completed_items
    return avg_time_per_item * remaining_items


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

