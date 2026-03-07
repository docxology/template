"""Shared logging constants with no infrastructure imports.

This module defines emoji and feature-flag constants shared between
logging_utils and logging_formatters, avoiding duplicate definitions
and circular import issues.
"""

from __future__ import annotations

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

# Check if emojis should be used (NO_EMOJI env var or not a TTY)
USE_EMOJIS = not os.getenv("NO_EMOJI") and sys.stdout.isatty()

# Check if structured logging (JSON) should be used
USE_STRUCTURED_LOGGING = os.getenv("STRUCTURED_LOGGING", "false").lower() == "true"
