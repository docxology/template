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
from typing import Any, Callable, Iterator, Optional, TypeVar

# Import from split modules
from infrastructure.core.logging_formatters import JSONFormatter, TemplateFormatter
from infrastructure.core.logging_helpers import format_duration, format_error_with_suggestions
from infrastructure.core.logging_progress import (
    Spinner,
    StreamingProgress,
    calculate_eta,
    calculate_eta_ema,
    calculate_eta_with_confidence,
    log_progress_bar,
    log_progress_streaming,
)
from infrastructure.core.logging_progress import log_with_spinner
from infrastructure.core._optional_deps import psutil
from infrastructure.core.logging_constants import EMOJIS, USE_EMOJIS, USE_STRUCTURED_LOGGING

# Type variable for generic context manager
T = TypeVar("T")


def _is_test_environment() -> bool:
    """Return True if running inside pytest."""
    return (
        os.getenv("PYTEST_CURRENT_TEST") is not None
        or "pytest" in sys.modules
        or any("pytest" in str(v) for v in sys.modules.values() if hasattr(v, "__file__"))
    )


# =============================================================================
# LOG LEVEL CONFIGURATION
# =============================================================================

# Map environment LOG_LEVEL (0-3) to Python logging levels
LOG_LEVEL_MAP = {
    "0": logging.DEBUG,  # Most verbose
    "1": logging.INFO,  # Default
    "2": logging.WARNING,  # Warnings only
    "3": logging.ERROR,  # Errors only
}


# =============================================================================
# STANDARDIZED PROJECT LOGGING INTERFACE
# =============================================================================



def get_log_level_from_env() -> int:
    """Get log level from LOG_LEVEL environment variable (0=DEBUG, 1=INFO, 2=WARN, 3=ERROR)."""
    env_level = os.getenv("LOG_LEVEL", "1")  # Default to INFO
    return LOG_LEVEL_MAP.get(env_level, logging.INFO)


# =============================================================================
# LOGGER CONFIGURATION
# =============================================================================


def setup_logger(
    name: str, level: Optional[int] = None, log_file: Optional[Path | str] = None
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
    is_test_env = _is_test_environment()

    # In test environment: don't add console handler, enable propagation
    # so pytest's caplog can capture logs from root logger
    # In normal environment: add console handler, disable propagation
    # Always add Console handler so capsys can capture stdout
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
        file_formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Set propagation based on environment (caplog requires propagation)
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
            h
            for h in root_logger.handlers
            if isinstance(h, logging.StreamHandler)
            and (h.stream is sys.stdout or h.stream is sys.stderr)
        ]
        for h in root_handlers_to_remove:
            root_logger.removeHandler(h)
        # Ensure root logger has at least WARNING level to not filter out our logs
        if root_logger.level == logging.NOTSET:
            root_logger.setLevel(logging.WARNING)

    return logger


def setup_root_log_file_handler(log_file: Path) -> logging.FileHandler:
    """Add a file handler to the root logger, replacing any existing one for this path.

    Intended for pipeline-level log capture where all loggers (including third-party)
    should write to a single project log file.

    Args:
        log_file: Path to log file (parent directory must already exist)

    Returns:
        The newly created FileHandler (caller should store it for later close/remove)
    """
    root_logger = logging.getLogger()

    # Remove any existing handler for this exact log file
    for h in list(root_logger.handlers):
        if (
            isinstance(h, logging.FileHandler)
            and hasattr(h, "baseFilename")
            and Path(h.baseFilename).resolve() == log_file.resolve()
        ):
            h.close()
            root_logger.removeHandler(h)

    handler = logging.FileHandler(log_file)
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")
    )
    root_logger.addHandler(handler)
    return handler


def flush_file_handlers() -> None:
    """Flush all FileHandlers on the root logger and all named loggers.

    Call this before copying or archiving log files to ensure all buffered
    writes are flushed to disk.
    """
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.flush()

    for logger_name in logging.Logger.manager.loggerDict:
        logger_obj = logging.getLogger(logger_name)
        for handler in logger_obj.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.flush()


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured with standard handlers for the given name."""
    logger = logging.getLogger(name)

    # Check if we're in test environment (same detection as setup_logger)
    is_test_env = _is_test_environment()

    # If not configured, set up with defaults
    if not logger.handlers:
        return setup_logger(name)

    # If in test environment and logger hasn't been configured for propagation,
    # force reconfiguration to enable propagation
    if is_test_env:
        if not logger.propagate:
            # Force reconfiguration by clearing handlers and calling setup_logger
            logger.handlers.clear()
            return setup_logger(name)
        # Ensure propagation is enabled even if handlers exist
        logger.propagate = True
    else:
        # Non-test environment: always ensure propagate=False.
        # Python's default is propagate=True, which means messages fire once via
        # the module's own handler AND again via every ancestor logger that also
        # has handlers — this causes doubled (or more) console output.
        # setup_logger sets propagate=False, but get_logger must reinforce this
        # each time it returns an already-configured logger.
        logger.propagate = False

    return logger



# =============================================================================
# CONTEXT MANAGERS
# =============================================================================


@contextmanager
def log_operation(
    operation: str,
    logger: Optional[logging.Logger] = None,
    level: int = logging.INFO,
    min_duration_to_log: float = 0.1,
    log_completion: bool = True,
) -> Iterator[None]:
    """Context manager for logging operation start and optional completion.

    Args:
        operation: Description of the operation
        logger: Logger instance (creates one if None)
        level: Log level for messages
        min_duration_to_log: Minimum duration (seconds) to log completion message
        log_completion: Whether to log completion message (False = start only)
    """
    logger = logger or get_logger(__name__)

    logger.log(level, f"Starting: {operation}")
    start_time = time.time()

    try:
        yield
        if log_completion:
            duration = time.time() - start_time
            if duration >= min_duration_to_log:
                logger.log(level, f"Completed: {operation} ({duration:.1f}s)")
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Failed: {operation} after {duration:.1f}s - {e}")
        raise


@contextmanager
def log_timing(label: str, logger: Optional[logging.Logger] = None) -> Iterator[None]:
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
    logger = logger or get_logger(__name__)

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
            func_logger.debug(f"Calling: {func.__name__}")
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                func_logger.debug(f"Completed: {func.__name__} ({duration:.1f}s)")
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
    """Log message at INFO level prefixed with the success emoji."""
    logger = logger or get_logger(__name__)

    emoji = EMOJIS["success"] if USE_EMOJIS else "[SUCCESS]"
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
    logger = logger or get_logger(__name__)

    prefix = EMOJIS["rocket"] + " " if USE_EMOJIS else ""
    separator = "=" * 50

    logger.info("")
    logger.info(separator)
    logger.info("%s%s", prefix, message)
    logger.info(separator)


def log_progress(
    current: int, total: int, task: str, logger: Optional[logging.Logger] = None
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
    logger = logger or get_logger(__name__)

    percent = (current * 100) // total if total > 0 else 0
    logger.info(f"[{current}/{total} - {percent}%] {task}")


def log_stage(
    stage_num: int,
    total_stages: int,
    stage_name: str,
    logger: Optional[logging.Logger] = None,
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
    logger = logger or get_logger(__name__)

    separator = "━" * 46
    logger.info("")
    logger.info(f"[{stage_num}/{total_stages}] {stage_name}")
    logger.info(separator)


def log_substep(message: str, logger: Optional[logging.Logger] = None) -> None:
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
    logger = logger or get_logger(__name__)

    logger.info(f"\n  {message}")


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
        if hasattr(logger, "setLevel"):
            logger.setLevel(level)


def log_stage_with_eta(
    stage_num: int,
    total_stages: int,
    stage_name: str,
    pipeline_start: Optional[float] = None,
    logger: Optional[logging.Logger] = None,
) -> None:
    """Log a pipeline stage header with ETA calculation."""
    logger = logger or get_logger(__name__)

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


def log_resource_usage(stage_name: str = "", logger: Optional[logging.Logger] = None) -> None:
    """Log current resource usage (if psutil available)."""
    logger = logger or get_logger(__name__)

    if psutil is None:
        logger.debug("psutil not available, skipping resource usage reporting")
        return

    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)
        cpu_percent = process.cpu_percent(interval=0.1)

        resource_info = f"Memory: {memory_mb:.0f} MB"
        if cpu_percent > 0:
            resource_info += f", CPU: {cpu_percent:.1f}%"

        if stage_name:
            logger.info(f"  Resource usage ({stage_name}): {resource_info}")
        else:
            logger.info(f"  Resource usage: {resource_info}")

    except (OSError, AttributeError) as e:
        logger.debug(f"Failed to get resource usage: {e}")


# Public API exports
__all__ = [
    # Core functions
    "get_log_level_from_env",
    "setup_logger",
    "get_logger",
    "set_global_log_level",
    # Context managers
    "log_operation",
    "log_timing",
    "log_function_call",
    # Utility functions
    "log_success",
    "log_header",
    "log_progress",
    "log_stage",
    "log_substep",
    # Helpers
    "format_error_with_suggestions",
    "format_duration",
    # Progress utilities
    "calculate_eta",
    "calculate_eta_ema",
    "calculate_eta_with_confidence",
    "log_progress_bar",
    "log_stage_with_eta",
    "log_resource_usage",
    "Spinner",
    "log_with_spinner",
    "StreamingProgress",
    "log_progress_streaming",
    # Formatters
    "JSONFormatter",
    "TemplateFormatter",
    # Constants
    "EMOJIS",
    "USE_EMOJIS",
    "USE_STRUCTURED_LOGGING",
]


