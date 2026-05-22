"""Shared logging constants with no infrastructure imports.

This module defines emoji and feature-flag constants shared between
logging_utils and logging_formatters, avoiding duplicate definitions
and circular import issues.
"""

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


BANNER_WIDTH = 60  # top-level banner separators (== bar)
STAGE_WIDTH = 46  # per-stage section header (━ bar)
SUBSECTION_WIDTH = 50  # in-stage subsection (== bar)
TABLE_WIDTH = 80  # data-table containers (- bar)


def get_emoji_enabled() -> bool:
    """Return True if emoji output is enabled (NO_EMOJI unset and stdout is a TTY).

    Not cached: sys.stdout.isatty() and os.getenv("NO_EMOJI") are both legitimately
    changed between tests (stdout capture, env patching), so caching would cause
    test-order-dependent failures.
    """
    return not os.getenv("NO_EMOJI") and sys.stdout.isatty()


def get_structured_logging_enabled() -> bool:
    """Return True if structured (JSON) logging is enabled via STRUCTURED_LOGGING env var.

    Not cached: os.getenv() can be legitimately patched between tests.
    """
    return os.getenv("STRUCTURED_LOGGING", "false").lower() == "true"


def get_terminal_verbose_enabled() -> bool:
    """Return True if LOG_TERMINAL_VERBOSE=1 — restore full timestamp/[INFO] prefix on console.

    Not cached: env legitimately patched between tests.
    """
    return os.getenv("LOG_TERMINAL_VERBOSE", "").lower() in ("1", "true", "yes")
