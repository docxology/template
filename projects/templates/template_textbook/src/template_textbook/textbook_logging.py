"""Minimal, dependency-free logging helper shared across the project.

The ``LOG_LEVEL`` environment variable controls verbosity across all project
loggers:

* ``"0"`` → ``DEBUG``
* ``"1"`` → ``INFO``  (default)
* ``"2"`` → ``WARNING``
* ``"3"`` → ``ERROR``

Any other value (or absence of the variable) falls back to ``INFO``.
"""

from __future__ import annotations

import logging
import os

_LEVELS = {"0": logging.DEBUG, "1": logging.INFO, "2": logging.WARNING, "3": logging.ERROR}


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger honouring the ``LOG_LEVEL`` env var (0–3).

    A ``StreamHandler`` is attached the first time the logger is retrieved.
    Subsequent calls for the same ``name`` reuse the existing logger without
    adding duplicate handlers.

    Args:
        name: Logger name — typically ``__name__`` of the calling module.

    Returns:
        A :class:`logging.Logger` configured with the project's style.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(_LEVELS.get(os.environ.get("LOG_LEVEL", "1"), logging.INFO))
    logger.propagate = False
    return logger


__all__ = ["get_logger"]
