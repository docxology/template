"""Shared helpers for figure generators (shim)."""

from __future__ import annotations

from pathlib import Path

from .._runtime import experiment_config, get_logger, save_figure_data
from .._runtime import project_root as _project_root


def project_root() -> Path:
    """Process project root."""
    return _project_root("src.figures")


__all__ = ["experiment_config", "get_logger", "project_root", "save_figure_data"]
