"""Core logging subpackage — formatters, helpers, constants, and utilities.

Re-exports primary symbols for ``from infrastructure.core.logging import …`` usage.
"""

from __future__ import annotations

from infrastructure.core.logging.constants import EMOJIS, get_emoji_enabled, get_structured_logging_enabled
from infrastructure.core.logging.formatters import JSONFormatter, TemplateFormatter
from infrastructure.core.logging.helpers import format_duration, format_error_with_suggestions
from infrastructure.core.logging.progress import (
    Spinner,
    StreamingProgress,
    log_progress_bar,
    log_progress_streaming,
    log_stage_with_eta,
    log_with_spinner,
)
from infrastructure.core.logging.utils import (
    get_logger,
    log_operation,
    log_stage,
    log_success,
    setup_logger,
)

__all__ = [
    "EMOJIS",
    "JSONFormatter",
    "Spinner",
    "StreamingProgress",
    "TemplateFormatter",
    "format_duration",
    "format_error_with_suggestions",
    "get_emoji_enabled",
    "get_logger",
    "get_structured_logging_enabled",
    "log_operation",
    "log_progress_bar",
    "log_progress_streaming",
    "log_stage",
    "log_stage_with_eta",
    "log_success",
    "log_with_spinner",
    "setup_logger",
]

