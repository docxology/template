"""Simple logging utilities for the Active Inference Meta-Pragmatic Framework.

This module provides basic logging functionality using Python's standard logging module.
"""

import logging
import os
from typing import Optional


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
