"""Logging formatters for structured and template-based output."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import ClassVar, Dict

from infrastructure.core.logging_constants import EMOJIS, USE_EMOJIS


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging.

    Outputs log records as JSON for machine parsing.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON formatted log message
        """
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

    LEVEL_EMOJIS: ClassVar[Dict[int, str]] = {
        logging.DEBUG: "",
        logging.INFO: EMOJIS["info"] if USE_EMOJIS else "",
        logging.WARNING: EMOJIS["warning"] if USE_EMOJIS else "",
        logging.ERROR: EMOJIS["error"] if USE_EMOJIS else "",
    }  # read-only lookup — do not mutate

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with timestamp and emoji.

        Args:
            record: Log record to format

        Returns:
            Formatted log message
        """
        # Create timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

        # Get emoji for level
        emoji = self.LEVEL_EMOJIS.get(record.levelno, "")
        emoji_str = f"{emoji} " if emoji else ""

        # Format message
        level_name = record.levelname
        message = record.getMessage()

        return f"{emoji_str}[{timestamp}] [{level_name}] {message}"
