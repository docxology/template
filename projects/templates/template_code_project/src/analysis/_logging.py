"""Shared logging helpers for analysis submodules."""

from __future__ import annotations

import logging

from ._infra import get_logger as _infra_get_logger


def _infra_available() -> bool:
    from . import INFRASTRUCTURE_AVAILABLE

    return bool(INFRASTRUCTURE_AVAILABLE)


_FALLBACK_LOGGER_NAME = "template_code_project.optimization_analysis"


def _setup_fallback_logging() -> logging.Logger:
    logger = logging.getLogger(_FALLBACK_LOGGER_NAME)
    if logger.handlers:
        return logger
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def get_logger() -> logging.Logger:
    """Get logger."""
    if _infra_available() and _infra_get_logger is not None:
        return _infra_get_logger(__name__)
    return _setup_fallback_logging()


__all__ = ["_setup_fallback_logging", "get_logger"]
