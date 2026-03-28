"""Unified Python logging module for the Research Project Template.

This module provides structured logging with consistent formatting across all Python
scripts in the template. It integrates with the bash logging.sh format and provides:
- Consistent log levels (DEBUG, INFO, WARN, ERROR)
- Context managers for operation tracking
- Performance timing utilities
- Integration with environment-based configuration

Part of the infrastructure layer (Layer 1) - reusable across all projects.

## Logging module map (all modules are intentional — each has a distinct role):

| Module              | Import pattern                    | Purpose                                    |
|---------------------|-----------------------------------|--------------------------------------------|
| utils.py            | get_logger, log_substep, etc.     | **Primary entry point** — re-exports all   |
| setup.py            | setup_logger, get_logger, etc.    | Logger setup and configuration             |
| pipeline_logging.py | log_stage, log_header, etc.       | Pipeline logging and convenience functions |
| constants.py        | USE_EMOJIS, LOG_LEVEL, etc.       | Runtime env-var constants (internal use)   |
| helpers.py          | format_error_with_suggestions, ...| Formatting helpers used by logging_utils   |
| formatters.py       | JSONFormatter, TemplateFormatter  | Handler/formatter setup (called once)      |
| progress.py         | Spinner, StreamingProgress, etc.  | Progress display (animated output)         |

Callers should import from ``utils`` for all everyday logging needs.
Direct imports from the other modules are for specialised use only.

## Stability contract

The public API of this module (get_logger, log_substep, log_success, etc.) is frozen.
Adding or renaming public functions requires updating all callers — treat this as a
codebase-wide breaking change. Prefer adding optional kwargs over new functions.

Module-level ``logger = get_logger(__name__)`` is the approved pattern — get_logger()
initialises lazily and is safe to call at import time.
"""

from __future__ import annotations

# Re-export from setup.py — logger configuration and retrieval
from infrastructure.core.logging.setup import (  # noqa: F401
    LOG_LEVEL_MAP,
    flush_file_handlers,
    get_log_level_from_env,
    get_logger,
    set_global_log_level,
    setup_logger,
    setup_root_log_file_handler,
)

# Re-export from pipeline_logging.py — context managers, decorators, convenience functions
from infrastructure.core.logging.pipeline_logging import (  # noqa: F401
    log_function_call,
    log_header,
    log_live_resource_usage,
    log_operation,
    log_pipeline_stage_with_eta,
    log_progress,
    log_stage,
    log_substep,
    log_success,
    log_timing,
)

# Re-export from helpers (used by some callers via utils)
from infrastructure.core.logging.helpers import format_error_with_suggestions  # noqa: F401

# Re-export TemplateFormatter (test_logging_utils.py imports it from here)
from infrastructure.core.logging.formatters import TemplateFormatter  # noqa: F401

# Core logging API — progress utilities, formatters, and constants are
# importable directly from their respective submodules (logging_progress,
# logging_formatters, logging_constants).
__all__ = [
    "TemplateFormatter",
    "flush_file_handlers",
    "format_error_with_suggestions",
    "get_log_level_from_env",
    "get_logger",
    "log_function_call",
    "log_header",
    "log_live_resource_usage",
    "log_operation",
    "log_pipeline_stage_with_eta",
    "log_progress",
    "log_stage",
    "log_substep",
    "log_success",
    "log_timing",
    "LOG_LEVEL_MAP",
    "set_global_log_level",
    "setup_logger",
    "setup_root_log_file_handler",
]
