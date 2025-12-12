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
    format_duration,
    calculate_eta,
    log_stage_with_eta,
    log_progress_bar,
    format_error_with_suggestions,
)
from .progress import (
    ProgressBar,
    SubStageProgress,
)
from .retry import (
    retry_with_backoff,
    retry_on_transient_failure,
    RetryableOperation,
)
from .checkpoint import (
    CheckpointManager,
    PipelineCheckpoint,
    StageResult,
)
from .performance import (
    PerformanceMonitor,
    PerformanceMetrics,
    ResourceUsage,
    monitor_performance,
    get_system_resources,
)
from .config_loader import (
    load_config,
    get_config_as_dict,
    get_config_as_env_vars,
    find_config_file,
    get_translation_languages,
)
from .environment import (
    check_python_version,
    check_dependencies,
    install_missing_packages,
    check_build_tools,
    setup_directories,
    verify_source_structure,
    set_environment_variables,
)
from .script_discovery import (
    discover_analysis_scripts,
    discover_orchestrators,
    verify_analysis_outputs,
)
from .file_operations import (
    clean_output_directory,
    clean_output_directories,
    copy_final_deliverables,
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
    "format_duration",
    "calculate_eta",
    "log_stage_with_eta",
    "log_progress_bar",
    "format_error_with_suggestions",
    # Progress
    "ProgressBar",
    "SubStageProgress",
    # Retry
    "retry_with_backoff",
    "retry_on_transient_failure",
    "RetryableOperation",
    # Checkpoint
    "CheckpointManager",
    "PipelineCheckpoint",
    "StageResult",
    # Performance
    "PerformanceMonitor",
    "PerformanceMetrics",
    "ResourceUsage",
    "monitor_performance",
    "get_system_resources",
    # Configuration
    "load_config",
    "get_config_as_dict",
    "get_config_as_env_vars",
    "find_config_file",
    "get_translation_languages",
    # Environment
    "check_python_version",
    "check_dependencies",
    "install_missing_packages",
    "check_build_tools",
    "setup_directories",
    "verify_source_structure",
    "set_environment_variables",
    # Script Discovery
    "discover_analysis_scripts",
    "discover_orchestrators",
    "verify_analysis_outputs",
    # File Operations
    "clean_output_directory",
    "clean_output_directories",
    "copy_final_deliverables",
]

