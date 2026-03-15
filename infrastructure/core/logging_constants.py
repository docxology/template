"""Shared logging constants with no infrastructure imports.

This module defines emoji and feature-flag constants shared between
logging_utils and logging_formatters, avoiding duplicate definitions
and circular import issues.
"""

from __future__ import annotations

import functools
import os
import sys

EMOJIS = {
    "info": "ℹ️",
    "success": "✅",
    "warning": "⚠️",
    "error": "❌",
    "rocket": "🚀",
    "sparkles": "✨",
    "folder": "📁",
    "book": "📖",
    "clean": "🧹",
    "gear": "⚙️",
    "chart": "📊",
}

@functools.lru_cache(maxsize=None)
def get_emoji_enabled() -> bool:
    """Return True if emoji output is enabled (NO_EMOJI unset and stdout is a TTY)."""
    return not os.getenv("NO_EMOJI") and sys.stdout.isatty()


@functools.lru_cache(maxsize=None)
def get_structured_logging_enabled() -> bool:
    """Return True if structured (JSON) logging is enabled via STRUCTURED_LOGGING env var."""
    return os.getenv("STRUCTURED_LOGGING", "false").lower() == "true"
