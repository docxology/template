"""Core module - Foundation utilities.

This module contains fundamental utilities used across the infrastructure layer,
including configuration management, logging, and exception hierarchy.

Modules:
    config_loader: Configuration file and environment variable loading
    logging_utils: Unified Python logging system
    exceptions: Custom exception hierarchy with context preservation
"""

from .checkpoint import CheckpointManager, PipelineCheckpoint, StageResult
from .config_loader import (find_config_file, get_config_as_dict,
                            get_config_as_env_vars, get_translation_languages,
                            load_config)
from .environment import (check_build_tools, check_dependencies,
                          check_python_version, install_missing_packages,
                          set_environment_variables, setup_directories,
                          verify_source_structure)
from .exceptions import (APIRateLimitError, BuildError, ConfigurationError,
                         DependencyError, FileOperationError, FormatError,
                         IntegrationError, LiteratureSearchError,
                         LLMConnectionError, LLMError, LLMTemplateError,
                         PublishingError, RenderingError, TemplateError,
                         TestError, UploadError, ValidationError,
                         chain_exceptions, format_file_context,
                         raise_with_context)
from .file_inventory import (FileInventoryEntry, FileInventoryManager,
                             collect_output_files, format_file_size,
                             generate_inventory_report)
from .file_operations import (clean_output_directories, clean_output_directory,
                              copy_final_deliverables)
from .health_check import (HealthCheckAPI, SystemHealthChecker, get_health_api,
                           get_health_metrics, get_health_status,
                           quick_health_check)
from .logging_utils import (calculate_eta, format_duration,
                            format_error_with_suggestions, get_logger,
                            log_function_call, log_header, log_operation,
                            log_progress, log_progress_bar, log_stage,
                            log_stage_with_eta, log_substep, log_success,
                            log_timing, set_global_log_level, setup_logger)
from .multi_project import (MultiProjectConfig, MultiProjectOrchestrator,
                            MultiProjectResult)
from .performance import (PerformanceMetrics, PerformanceMonitor,
                          ResourceUsage, get_system_resources,
                          monitor_performance)
from .performance_monitor import \
    PerformanceMetrics as AdvancedPerformanceMetrics
from .performance_monitor import \
    PerformanceMonitor as AdvancedPerformanceMonitor
from .performance_monitor import (benchmark_function, benchmark_llm_query,
                                  get_performance_monitor)
from .performance_monitor import \
    monitor_performance as monitor_performance_decorator
from .performance_monitor import profile_memory_usage
from .pipeline import PipelineConfig, PipelineExecutor, PipelineStageResult
from .pipeline_summary import (PipelineSummary, PipelineSummaryGenerator,
                               generate_pipeline_summary)
from .progress import ProgressBar, SubStageProgress
from .retry import (RetryableOperation, retry_on_transient_failure,
                    retry_with_backoff)
from .script_discovery import (discover_analysis_scripts,
                               discover_orchestrators, verify_analysis_outputs)
from .security import (RateLimiter, SecurityHeaders, SecurityMonitor,
                       SecurityValidator, SecurityViolation, get_rate_limiter,
                       get_security_headers, get_security_monitor,
                       get_security_validator, rate_limit, validate_llm_input)

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
    "AdvancedPerformanceMonitor",
    "AdvancedPerformanceMetrics",
    "monitor_performance_decorator",
    "get_performance_monitor",
    "benchmark_function",
    "benchmark_llm_query",
    "profile_memory_usage",
    "SystemHealthChecker",
    "HealthCheckAPI",
    "get_health_api",
    "quick_health_check",
    "get_health_status",
    "get_health_metrics",
    "SecurityValidator",
    "SecurityHeaders",
    "RateLimiter",
    "SecurityMonitor",
    "SecurityViolation",
    "get_security_validator",
    "get_security_headers",
    "get_rate_limiter",
    "get_security_monitor",
    "validate_llm_input",
    "rate_limit",
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
    # Pipeline
    "PipelineConfig",
    "PipelineStageResult",
    "PipelineExecutor",
    # Multi-Project
    "MultiProjectConfig",
    "MultiProjectResult",
    "MultiProjectOrchestrator",
    # File Inventory
    "FileInventoryEntry",
    "FileInventoryManager",
    "collect_output_files",
    "generate_inventory_report",
    "format_file_size",
    # Pipeline Summary
    "PipelineSummary",
    "PipelineSummaryGenerator",
    "generate_pipeline_summary",
]
