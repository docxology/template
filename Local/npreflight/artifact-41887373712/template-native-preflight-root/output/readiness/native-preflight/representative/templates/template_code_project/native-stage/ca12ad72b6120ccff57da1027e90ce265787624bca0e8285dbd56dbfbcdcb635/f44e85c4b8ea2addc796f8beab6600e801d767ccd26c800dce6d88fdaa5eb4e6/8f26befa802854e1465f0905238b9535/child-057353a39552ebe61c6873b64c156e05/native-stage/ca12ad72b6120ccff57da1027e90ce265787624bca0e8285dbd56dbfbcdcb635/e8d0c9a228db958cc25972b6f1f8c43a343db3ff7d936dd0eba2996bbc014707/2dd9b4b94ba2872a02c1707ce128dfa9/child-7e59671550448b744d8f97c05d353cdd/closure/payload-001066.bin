"""Shared I/O helpers for documentation validation modules.

This module hosts the defensive markdown reader used across the docs validation
package so that both the ``consistency/`` submodule and the top-level linters can
import it from one stable location without reaching into ``consistency/_shared``.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


def read_markdown(path: Path) -> str | None:
    """Read a markdown file, returning None on I/O or decode failure."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        logger.debug("skipping %s: %s", path, exc)
        return None
