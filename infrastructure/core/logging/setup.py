"""Logger setup and configuration — handler management, root logger, file handlers.

Extracted from utils.py to keep each module under 300 LOC.
Callers should continue to import from ``infrastructure.core.logging.utils``
which re-exports everything defined here.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from infrastructure.core.logging.formatters import JSONFormatter, TemplateFormatter
from infrastructure.core.logging.constants import get_structured_logging_enabled


def _is_test_environment() -> bool:
    """Return True if running inside pytest.

    Evaluated on every call (not cached) so that late pytest imports and
    PYTEST_CURRENT_TEST set after module import are correctly detected.
    """
    return bool(os.getenv("PYTEST_CURRENT_TEST") or "pytest" in sys.modules)


# Map environment LOG_LEVEL (0-3) to Python logging levels
LOG_LEVEL_MAP = {
    "0": logging.DEBUG,  # Most verbose
    "1": logging.INFO,  # Default
    "2": logging.WARNING,  # Warnings only
    "3": logging.ERROR,  # Errors only
}


def get_log_level_from_env() -> int:
    """Get log level from LOG_LEVEL environment variable (0=DEBUG, 1=INFO, 2=WARN, 3=ERROR)."""
    env_level = os.getenv("LOG_LEVEL", "1")  # Default to INFO
    return LOG_LEVEL_MAP.get(env_level, logging.INFO)


def setup_logger(
    name: str, level: int | None = None, log_file: Path | str | None = None
) -> logging.Logger:
    """Configure and return a logger with console handler and optional file handler."""
    logger = logging.getLogger(name)

    if level is None:
        level = get_log_level_from_env()
    logger.setLevel(level)

    logger.handlers.clear()

    is_test_env = _is_test_environment()

    console_handler = logging.StreamHandler(sys.stdout)
    if get_structured_logging_enabled():
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(TemplateFormatter())
    logger.addHandler(console_handler)

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    logger.propagate = is_test_env

    # caplog requires propagation: clean root logger handlers that would double-emit
    if is_test_env:
        root_logger = logging.getLogger()
        if root_logger.level > logger.level:
            root_logger.setLevel(logger.level)
        root_handlers_to_remove = [
            h
            for h in root_logger.handlers
            if isinstance(h, logging.StreamHandler)
            and (h.stream is sys.stdout or h.stream is sys.stderr)
        ]
        for h in root_handlers_to_remove:
            root_logger.removeHandler(h)
        if root_logger.level == logging.NOTSET:
            root_logger.setLevel(logging.WARNING)

    return logger


def setup_root_log_file_handler(log_file: Path) -> logging.FileHandler:
    """Add a file handler to the root logger, replacing any existing one for this path.

    Intended for pipeline-level log capture where all loggers (including third-party)
    should write to a single project log file.

    Args:
        log_file: Path to log file (parent directory must already exist)

    Returns:
        The newly created FileHandler (caller should store it for later close/remove)
    """
    root_logger = logging.getLogger()

    # Remove any existing handler for this exact log file
    for h in list(root_logger.handlers):
        if (
            isinstance(h, logging.FileHandler)
            and hasattr(h, "baseFilename")
            and Path(h.baseFilename).resolve() == log_file.resolve()
        ):
            h.close()
            root_logger.removeHandler(h)

    handler = logging.FileHandler(log_file)
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"))
    root_logger.addHandler(handler)
    return handler


def flush_file_handlers() -> None:
    """Flush all FileHandlers on the root logger and all named loggers.

    Call this before copying or archiving log files to ensure all buffered
    writes are flushed to disk.
    """
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.flush()

    for logger_name in logging.Logger.manager.loggerDict:
        logger_obj = logging.getLogger(logger_name)
        for handler in logger_obj.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.flush()


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured with standard handlers for the given name."""
    logger = logging.getLogger(name)

    # New or unconfigured logger: let setup_logger handle _is_test_environment internally.
    if not logger.handlers:
        return setup_logger(name)

    # Already-configured logger: check environment once for the two remaining branches.
    is_test_env = _is_test_environment()

    # If in test environment and logger hasn't been configured for propagation,
    # force reconfiguration to enable propagation.
    if is_test_env:
        if not logger.propagate:
            logger.handlers.clear()
            return setup_logger(name)
    else:
        # Non-test environment: always ensure propagate=False.
        # Python's default is propagate=True, which means messages fire once via
        # the module's own handler AND again via every ancestor logger that also
        # has handlers — this causes doubled (or more) console output.
        # setup_logger sets propagate=False, but get_logger must reinforce this
        # each time it returns an already-configured logger.
        logger.propagate = False

    return logger


def set_global_log_level(level: int) -> None:
    """Set log level on the root logger and all named loggers."""
    logging.getLogger().setLevel(level)
    for logger_name in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
