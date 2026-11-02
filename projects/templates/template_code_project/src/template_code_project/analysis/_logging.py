"""Shared logging helpers for analysis submodules."""

from __future__ import annotations

import logging

from ._infra import get_logger as _infra_get_logger


def get_logger() -> logging.Logger:
    """Get logger."""
    return _infra_get_logger(__name__)


__all__ = ["get_logger"]
