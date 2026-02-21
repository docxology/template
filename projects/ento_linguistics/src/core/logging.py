"""Simple logging utilities for the Ento-Linguistic Research Project.

This module provides basic logging functionality using Python's standard logging module.
"""

import logging
import os
from typing import Optional

__all__ = [
    "get_logger",
    "log_substep",
    "log_progress_bar",
    "log_stage",
]


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger with standard configuration.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        # Set level from environment or default to INFO
        level_str = os.getenv("LOG_LEVEL", "1")
        level_map = {
            "0": logging.DEBUG,
            "1": logging.INFO,
            "2": logging.WARNING,
            "3": logging.ERROR,
        }
        level = level_map.get(level_str, logging.INFO)

        logger.setLevel(level)

        # Create console handler
        handler = logging.StreamHandler()
        handler.setLevel(level)

        # Create formatter
        formatter = logging.Formatter("%(levelname)s - %(name)s - %(message)s")
        handler.setFormatter(formatter)

        logger.addHandler(handler)

    return logger


def log_substep(message: str, logger: Optional[logging.Logger] = None) -> None:
    """Log a substep with indentation.

    Args:
        message: Message to log
        logger: Logger instance (creates default if None)
    """
    if logger is None:
        logger = get_logger(__name__)
    logger.info(f"  {message}")


def log_progress_bar(
    current: int, total: int, task: str, logger: Optional[logging.Logger] = None
) -> None:
    """Log progress with a simple bar.

    Args:
        current: Current progress
        total: Total items
        task: Task description
        logger: Logger instance (creates default if None)
    """
    if logger is None:
        logger = get_logger(__name__)

    percentage = int(100 * current / total) if total > 0 else 0
    bar = "=" * (percentage // 5) + " " * (20 - percentage // 5)
    logger.info(f"[{bar}] {percentage}% - {task}")


def log_stage(
    stage_num: int,
    total_stages: int,
    stage_name: str,
    logger: Optional[logging.Logger] = None,
) -> None:
    """Log a pipeline stage header.

    Args:
        stage_num: Current stage number (1-based)
        total_stages: Total number of stages
        stage_name: Name of the stage
        logger: Logger instance (creates default if None)
    """
    if logger is None:
        logger = get_logger(__name__)
    logger.info(f"Stage {stage_num}/{total_stages}: {stage_name}")
