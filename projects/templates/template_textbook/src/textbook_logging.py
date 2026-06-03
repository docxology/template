"""Minimal, dependency-free logging helper shared across the project."""

from __future__ import annotations

import logging
import os

_LEVELS = {"0": logging.DEBUG, "1": logging.INFO, "2": logging.WARNING, "3": logging.ERROR}


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger honouring the ``LOG_LEVEL`` env var (0-3)."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(_LEVELS.get(os.environ.get("LOG_LEVEL", "1"), logging.INFO))
    logger.propagate = False
    return logger
