"""Logging formatters for structured and template-based output."""

import json
import logging
from datetime import datetime
from typing import ClassVar

from infrastructure.core.logging.constants import EMOJIS, get_emoji_enabled, get_terminal_verbose_enabled


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging.

    Outputs log records as JSON for machine parsing.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


class TemplateFormatter(logging.Formatter):
    """Custom formatter matching bash logging.sh format.

    Format: [YYYY-MM-DD HH:MM:SS] [LEVEL] message
    Adds emojis when appropriate and running in a TTY.
    """

    _LEVEL_EMOJI_KEYS: ClassVar[dict[int, str]] = {
        logging.DEBUG: "",
        logging.INFO: "info",
        logging.WARNING: "warning",
        logging.ERROR: "error",
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with timestamp and emoji."""
        # Create timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

        # Get emoji for level (evaluated at format time so env changes are respected)
        emoji_key = self._LEVEL_EMOJI_KEYS.get(record.levelno, "")
        emoji = EMOJIS[emoji_key] if (emoji_key and get_emoji_enabled()) else ""
        emoji_str = f"{emoji} " if emoji else ""

        # Format message
        level_name = record.levelname
        message = record.getMessage()

        return f"{emoji_str}[{timestamp}] [{level_name}] {message}"


class ConsoleFormatter(logging.Formatter):
    """Terminal-oriented formatter: clean messages, no timestamp/level chrome.

    Returns just the message for INFO/DEBUG and an emoji-prefixed message for
    warnings/errors. Reverts to the verbose TemplateFormatter format when the
    env var LOG_TERMINAL_VERBOSE=1.

    The verbose path is the existing TemplateFormatter behavior, preserved for
    operators who depend on per-line timestamps in the terminal.
    """

    _LEVEL_EMOJI_KEYS: ClassVar[dict[int, str]] = {
        logging.DEBUG: "",
        logging.INFO: "",  # no emoji on info — keep terminal calm
        logging.WARNING: "warning",
        logging.ERROR: "error",
        logging.CRITICAL: "error",
    }

    def format(self, record: logging.LogRecord) -> str:
        # Honour LOG_TERMINAL_VERBOSE=1 → full prefix (rollback path)
        if get_terminal_verbose_enabled():
            return TemplateFormatter().format(record)

        message = record.getMessage()
        emoji_key = self._LEVEL_EMOJI_KEYS.get(record.levelno, "")
        if emoji_key and get_emoji_enabled():
            return f"{EMOJIS[emoji_key]} {message}"
        return message
