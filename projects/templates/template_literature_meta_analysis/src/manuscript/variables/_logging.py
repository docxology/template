"""Shared logger for the variables package."""

from __future__ import annotations

try:
    from infrastructure.core.logging.utils import get_logger
except ImportError:
    import logging as _logging

    def get_logger(name: str):  # type: ignore[misc]
        return _logging.getLogger(name)


logger = get_logger(__name__)
