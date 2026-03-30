"""Pipeline and convenience logging functions — stage headers, progress, resource usage.

Extracted from utils.py to keep each module under 300 LOC.
Callers should continue to import from ``infrastructure.core.logging.utils``
which re-exports everything defined here.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Iterator, ParamSpec, TypeVar

from infrastructure.core.logging.constants import EMOJIS, get_emoji_enabled
from infrastructure.core.logging.helpers import format_duration
from infrastructure.core.logging.setup import get_logger
from infrastructure.core.runtime.eta import calculate_eta
from infrastructure.core._optional_deps import psutil

# Type variables for generic decorator
T = TypeVar("T")
P = ParamSpec("P")

_HEADER_SEPARATOR_WIDTH = 50
_STAGE_SEPARATOR_WIDTH = 46


@contextmanager
def log_operation(
    operation: str,
    logger: logging.Logger | None = None,
    level: int = logging.INFO,
    min_duration_to_log: float = 0.1,
    log_completion: bool = True,
) -> Iterator[None]:
    """Context manager that logs operation start, completion, and failure.

    Args:
        operation: Human-readable name of the operation being performed.
        logger: Logger instance; defaults to module logger if None.
        level: Log level for start/completion messages (default INFO).
        min_duration_to_log: Completion is only logged when duration exceeds this (seconds).
        log_completion: When False, suppress the completion log even if duration exceeds threshold.
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
def log_timing(label: str, logger: logging.Logger | None = None) -> Iterator[None]:
    """Context manager that logs elapsed time for label on exit."""
    logger = logger or get_logger(__name__)

    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.info(f"{label}: {duration:.1f}s")


def log_function_call(logger: logging.Logger | None = None) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator that logs function calls at DEBUG level with elapsed time and error reporting."""

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        func_logger = logger or get_logger(func.__module__)

        @wraps(func)
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

        return wrapper

    return decorator


def log_success(message: str, logger: logging.Logger | None = None) -> None:
    """Log message at INFO level prefixed with the success emoji."""
    logger = logger or get_logger(__name__)

    if get_emoji_enabled():
        logger.info(f"{EMOJIS['success']} {message}")
    else:
        logger.info(message)


def log_header(message: str, logger: logging.Logger | None = None) -> None:
    """Log a section header with visual emphasis (separator + message + separator)."""
    logger = logger or get_logger(__name__)

    prefix = EMOJIS["rocket"] + " " if get_emoji_enabled() else ""
    separator = "=" * _HEADER_SEPARATOR_WIDTH

    logger.info("")
    logger.info(separator)
    logger.info(f"{prefix}{message}")
    logger.info(separator)


def log_progress(current: int, total: int, task: str, logger: logging.Logger | None = None) -> None:
    """Log a progress update with current position, total, and percentage."""
    logger = logger or get_logger(__name__)

    percent = (current * 100) // total if total > 0 else 0
    logger.info(f"[{current}/{total} - {percent}%] {task}")


def log_stage(
    stage_num: int,
    total_stages: int,
    stage_name: str,
    logger: logging.Logger | None = None,
) -> None:
    """Log a numbered pipeline stage header with a visual separator."""
    logger = logger or get_logger(__name__)

    separator = "\u2501" * _STAGE_SEPARATOR_WIDTH
    logger.info("")
    logger.info(f"[{stage_num}/{total_stages}] {stage_name}")
    logger.info(separator)


def log_substep(message: str, logger: logging.Logger | None = None) -> None:
    """Log a pipeline sub-step message with standard indentation."""
    logger = logger or get_logger(__name__)

    logger.info(f"\n  {message}")


def log_pipeline_stage_with_eta(
    stage_num: int,
    total_stages: int,
    stage_name: str,
    pipeline_start: float | None = None,
    logger: logging.Logger | None = None,
) -> None:
    """Log a pipeline stage header with ETA calculation."""
    logger = logger or get_logger(__name__)

    percentage = (stage_num * 100) // total_stages if total_stages > 0 else 0
    separator = "\u2501" * _STAGE_SEPARATOR_WIDTH

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


def log_live_resource_usage(stage_name: str = "", logger: logging.Logger | None = None) -> None:
    """Log current resource usage via live psutil sampling (if psutil available)."""
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
        logger.warning(f"Failed to get resource usage: {e}")
