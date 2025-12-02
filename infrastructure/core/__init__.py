"""Core module - Foundation utilities.

This module contains fundamental utilities used across the infrastructure layer,
including configuration management, logging, and exception hierarchy.

Modules:
    config_loader: Configuration file and environment variable loading
    logging_utils: Unified Python logging system
    exceptions: Custom exception hierarchy with context preservation
"""

from .exceptions import (
    TemplateError,
    ConfigurationError,
    ValidationError,
    BuildError,
    FileOperationError,
    DependencyError,
    TestError,
    IntegrationError,
    LiteratureSearchError,
    APIRateLimitError,
    LLMError,
    LLMConnectionError,
    LLMTemplateError,
    RenderingError,
    FormatError,
    PublishingError,
    UploadError,
    raise_with_context,
    format_file_context,
    chain_exceptions,
)
from .logging_utils import (
    setup_logger,
    get_logger,
    log_operation,
    log_timing,
    log_function_call,
    log_success,
    log_header,
    log_progress,
    log_stage,
    log_substep,
    set_global_log_level,
)
from .config_loader import (
    load_config,
    get_config_as_dict,
    get_config_as_env_vars,
    find_config_file,
    get_translation_languages,
)

__all__ = [
    # Exceptions
    "TemplateError",
    "ConfigurationError",
    "ValidationError",
    "BuildError",
    "FileOperationError",
    "DependencyError",
    "TestError",
    "IntegrationError",
    "LiteratureSearchError",
    "APIRateLimitError",
    "LLMError",
    "LLMConnectionError",
    "LLMTemplateError",
    "RenderingError",
    "FormatError",
    "PublishingError",
    "UploadError",
    "raise_with_context",
    "format_file_context",
    "chain_exceptions",
    # Logging
    "setup_logger",
    "get_logger",
    "log_operation",
    "log_timing",
    "log_function_call",
    "log_success",
    "log_header",
    "log_progress",
    "log_stage",
    "log_substep",
    "set_global_log_level",
    # Configuration
    "load_config",
    "get_config_as_dict",
    "get_config_as_env_vars",
    "find_config_file",
    "get_translation_languages",
]

