# 📚 Infrastructure Core API Reference

> Auto-generated module inventory for `infrastructure/core/` (26 modules).
> Last updated: 2026-02-21

## Module Index

| Module | Description |
|--------|-------------|
| [`checkpoint`](#checkpoint) | Pipeline checkpoint system for resume capability |
| [`cli`](#cli) | CLI interface for core infrastructure modules |
| [`config_cli`](#config_cli) | Load manuscript configuration script - THIN ORCHESTRATOR

This script reads project/manuscript/config |
| [`config_loader`](#config_loader) | Configuration loader for manuscript metadata |
| [`credentials`](#credentials) | Secure credential management for testing and operations |
| [`environment`](#environment) | Environment setup and validation utilities |
| [`errors`](#errors) | Typed error constants for consistent error messaging |
| [`exceptions`](#exceptions) | Custom exception hierarchy for the Research Project Template |
| [`file_inventory`](#file_inventory) | File inventory and collection utilities |
| [`file_operations`](#file_operations) | File and directory operation utilities |
| [`health_check`](#health_check) | System health monitoring and status checks |
| [`logging_formatters`](#logging_formatters) | Logging formatters for structured and template-based output |
| [`logging_helpers`](#logging_helpers) | Helper functions for logging utilities |
| [`logging_progress`](#logging_progress) | Progress bars, spinners, and ETA calculations for logging |
| [`logging_utils`](#logging_utils) | Unified Python logging module for the Research Project Template |
| [`menu`](#menu) | Interactive menu utilities (pure helpers) |
| [`multi_project`](#multi_project) | Multi-project orchestration system |
| [`performance`](#performance) | Performance monitoring and resource tracking utilities |
| [`performance_monitor`](#performance_monitor) | Performance monitoring and profiling utilities for research workflows |
| [`pipeline`](#pipeline) | Pipeline execution system for research projects |
| [`pipeline_summary`](#pipeline_summary) | Pipeline summary generation and reporting |
| [`progress`](#progress) | Progress reporting utilities for pipeline operations |
| [`retry`](#retry) | Retry utilities for handling transient failures |
| [`script_discovery`](#script_discovery) | Script discovery and execution utilities |
| [`security`](#security) | Security utilities and input validation for the research template system |

---

## checkpoint

*Pipeline checkpoint system for resume capability*

| Class | Description |
|-------|-------------|
| `StageResult` | Result of a pipeline stage execution |
| `PipelineCheckpoint` | Pipeline checkpoint state |
| `CheckpointManager` | Manages pipeline checkpoints for resume capability |

---

## cli

*CLI interface for core infrastructure modules*

| Function | Description |
|----------|-------------|
| `create_parser()` | Create the main argument parser for core CLI commands |
| `main()` | Main CLI entry point |
| `handle_pipeline_command()` | Handle pipeline execution command |
| `handle_multi_project_command()` | Handle multi-project execution command |
| `handle_inventory_command()` | Handle file inventory command |
| `handle_summary_command()` | Handle summary generation command |
| `handle_discover_command()` | Handle project discovery command |

---

## config_cli

*Load manuscript configuration script - THIN ORCHESTRATOR

This script reads project/manuscript/config*

| Function | Description |
|----------|-------------|
| `main()` | Main function to load and export configuration |

---

## config_loader

*Configuration loader for manuscript metadata*

| Class | Description |
|-------|-------------|
| `AuthorConfig` |  |
| `PaperConfig` |  |
| `PublicationConfig` |  |
| `TranslationsConfig` |  |
| `ReviewsConfig` |  |
| `LLMConfig` |  |
| `TestingConfig` |  |
| `ResolvedTestingConfig` | Immutable, fully-resolved testing configuration with defaults applied |
| `ManuscriptConfig` |  |

| Function | Description |
|----------|-------------|
| `load_config()` | Load configuration from YAML file |
| `format_author_details()` | Format author details string for LaTeX |
| `format_author_name()` | Format author name(s) for display |
| `get_config_as_dict()` | Get configuration as a dictionary of key-value pairs |
| `get_config_as_env_vars()` | Get configuration as environment variables |
| `find_config_file()` | Find the manuscript config file at the standard location |
| `get_translation_languages()` | Get list of enabled translation languages from config |
| `get_review_types()` | Get list of enabled review types from config |
| `get_testing_config()` | Get testing configuration from config |

---

## credentials

*Secure credential management for testing and operations*

| Class | Description |
|-------|-------------|
| `CredentialManager` | Manage credentials from |

---

## environment

*Environment setup and validation utilities*

| Function | Description |
|----------|-------------|
| `check_python_version()` | Verify Python 3 |
| `check_dependencies()` | Verify required packages are installed |
| `install_missing_packages()` | Install missing packages using uv with fallback to pip |
| `check_build_tools()` | Verify build tools are available |
| `setup_directories()` | Create required directory structure |
| `check_uv_available()` | Check if uv package manager is available and working |
| `get_python_command()` | Get the appropriate Python command for subprocess execution |
| `validate_interpreter()` | Validate that sys |
| `get_subprocess_env()` | Get environment dict for subprocess with uv compatibility |
| `verify_source_structure()` | Verify source code structure exists |
| `set_environment_variables()` | Configure environment variables for pipeline |
| `validate_uv_sync_result()` | Validate that uv sync completed successfully |
| `validate_directory_structure()` | Validate that required directory structure exists |

---

## errors

*Typed error constants for consistent error messaging*

| Class | Description |
|-------|-------------|
| `InfraError` | Typed error constant with code, message, and actionable suggestion |

**Constants:** `PIPELINE_STAGE_FAILED`, `PIPELINE_STAGES_INCOMPLETE`, `PIPELINE_EXECUTION_FAILED`, `STAGE_FAILED`, `STAGE_EXCEPTION`, `SCRIPT_EXECUTION_FAILED`, `CLI_UNKNOWN_COMMAND`, `CLI_COMMAND_FAILED`
  *...and 14 more*

---

## exceptions

*Custom exception hierarchy for the Research Project Template*

| Class | Description |
|-------|-------------|
| `TemplateError` | Base exception for all template-related errors |
| `ConfigurationError` | Raised when configuration is invalid or missing |
| `MissingConfigurationError` | Raised when required configuration is missing |
| `InvalidConfigurationError` | Raised when configuration values are invalid |
| `ValidationError` | Raised when validation fails |
| `MarkdownValidationError` | Raised when markdown validation fails |
| `PDFValidationError` | Raised when PDF validation fails |
| `DataValidationError` | Raised when data validation fails |
| `BuildError` | Raised when build process fails |
| `CompilationError` | Raised when compilation (LaTeX, etc |
| `ScriptExecutionError` | Raised when script execution fails |
| `PipelineError` | Raised when pipeline orchestration fails |
| `FileOperationError` | Raised when file operations fail |
| `FileNotFoundError` | Raised when a required file is not found |
| `NotADirectoryError` | Raised when a path is not a directory when a directory is expected |
| `InvalidFileFormatError` | Raised when file format is invalid or unexpected |
| `DependencyError` | Raised when dependencies are missing or invalid |
| `MissingDependencyError` | Raised when a required dependency is missing |
| `VersionMismatchError` | Raised when dependency version is incompatible |
| `TestError` | Raised when test execution or validation fails |
| `InsufficientCoverageError` | Raised when test coverage is insufficient |
| `IntegrationError` | Raised when component integration fails |
| `LiteratureSearchError` | Raised when literature search operations fail |
| `APIRateLimitError` | Raised when API rate limits are exceeded |
| `InvalidQueryError` | Raised when search query is invalid |
| `LLMError` | Base exception for LLM operations |
| `LLMConnectionError` | Raised when connecting to LLM provider fails |
| `LLMTemplateError` | Raised when template processing fails |
| `ContextLimitError` | Raised when token limit is exceeded |
| `RenderingError` | Base exception for rendering operations |
| `FormatError` | Raised when output format is invalid or unsupported |
| `TemplateRenderingError` | Raised when rendering a template fails |
| `PublishingError` | Base exception for publishing operations |
| `UploadError` | Raised when file upload fails |
| `MetadataError` | Raised when metadata validation fails |

| Function | Description |
|----------|-------------|
| `raise_with_context()` | Raise an exception with context information |
| `format_file_context()` | Format file path and optional line number as error context |
| `chain_exceptions()` | Chain a new exception with the original exception's context |

---

## file_inventory

*File inventory and collection utilities*

| Class | Description |
|-------|-------------|
| `FileInventoryEntry` | Entry in file inventory |
| `FileInventoryManager` | Manage file inventory and reports |

| Function | Description |
|----------|-------------|
| `format_file_size()` | Convert bytes to human-readable format |
| `collect_output_files()` | Convenience function to collect output files |
| `generate_inventory_report()` | Convenience function to generate inventory report |

---

## file_operations

*File and directory operation utilities*

| Function | Description |
|----------|-------------|
| `clean_output_directory()` | Clean top-level output directory before copying |
| `clean_output_directories()` | Clean output directories for a fresh pipeline start |
| `clean_root_output_directory()` | Clean root-level directories from output/ directory |
| `clean_coverage_files()` | Clean coverage database files to prevent corruption |
| `copy_final_deliverables()` | Copy all project outputs to top-level output directory |

---

## health_check

*System health monitoring and status checks*

| Class | Description |
|-------|-------------|
| `SystemHealthChecker` | Comprehensive system health monitoring |
| `HealthCheckAPI` | REST-like API for health check endpoints |

| Function | Description |
|----------|-------------|
| `get_health_api()` | Get the global health check API instance |
| `quick_health_check()` | Perform a quick health check |
| `get_health_status()` | Get detailed health status |
| `get_health_metrics()` | Get health metrics for monitoring systems |

---

## logging_formatters

*Logging formatters for structured and template-based output*

| Class | Description |
|-------|-------------|
| `JSONFormatter` | JSON formatter for structured logging |
| `TemplateFormatter` | Custom formatter matching bash logging |

**Constants:** `EMOJIS`, `USE_EMOJIS`, `USE_STRUCTURED_LOGGING`

---

## logging_helpers

*Helper functions for logging utilities*

| Function | Description |
|----------|-------------|
| `format_error_with_suggestions()` | Format error message with context, recovery suggestions, and commands |
| `format_duration()` | Format duration in seconds to human-readable string |

---

## logging_progress

*Progress bars, spinners, and ETA calculations for logging*

| Class | Description |
|-------|-------------|
| `Spinner` | Animated spinner for long-running operations |
| `StreamingProgress` | Real-time progress indicator for streaming operations |

| Function | Description |
|----------|-------------|
| `calculate_eta()` | Calculate estimated time remaining based on current progress |
| `calculate_eta_ema()` | Calculate ETA using exponential moving average for better accuracy |
| `calculate_eta_with_confidence()` | Calculate ETA with confidence intervals (optimistic/pessimistic) |
| `log_progress_bar()` | Display a progress bar in the console |
| `log_with_spinner()` | Context manager for operations with spinner indicator |
| `log_progress_streaming()` | Log streaming progress with real-time updates |
| `log_stage_with_eta()` | Log stage progress with ETA calculation |
| `log_resource_usage()` | Log current resource usage |

---

## logging_utils

*Unified Python logging module for the Research Project Template*

| Class | Description |
|-------|-------------|
| `ProjectLogger` | Standardized logging interface for research projects |
| `LogAggregator` | Aggregate and analyze log messages for summary reporting |

| Function | Description |
|----------|-------------|
| `get_project_logger()` | Get a standardized project logger |
| `setup_project_logging()` | Set up project logging with optional file output |
| `get_log_level_from_env()` | Get log level from LOG_LEVEL environment variable |
| `setup_logger()` | Set up a logger with consistent formatting |
| `get_logger()` | Get or create a logger with standard configuration |
| `log_operation()` | Context manager for logging operation start and completion |
| `log_operation_silent()` | Context manager for logging operation start only (no completion message) |
| `log_timing()` | Context manager for timing operations |
| `log_function_call()` | Decorator to log function calls with timing |
| `log_success()` | Log a success message with success emoji |
| `log_header()` | Log a section header with visual emphasis |
| `log_progress()` | Log progress with percentage |
| `log_stage()` | Log a pipeline stage header with consistent formatting |
| `log_substep()` | Log a substep within a stage with consistent indentation |
| `set_global_log_level()` | Set log level for all template loggers |
| `log_stage_with_eta()` | Log a pipeline stage header with ETA calculation |
| `log_resource_usage()` | Log current resource usage (if psutil available) |
| `collect_log_statistics()` | Collect statistics from a log file |
| `generate_log_summary()` | Generate summary report from log file |

**Constants:** `T`, `LOG_LEVEL_MAP`, `EMOJIS`, `USE_EMOJIS`, `USE_STRUCTURED_LOGGING`

---

## menu

*Interactive menu utilities (pure helpers)*

| Class | Description |
|-------|-------------|
| `MenuOption` | Single menu option descriptor |

| Function | Description |
|----------|-------------|
| `parse_choice_sequence()` | Parse a user-entered menu choice sequence |
| `format_menu()` | Return a plain-text menu representation |

---

## multi_project

*Multi-project orchestration system*

| Class | Description |
|-------|-------------|
| `MultiProjectConfig` | Configuration for multi-project execution |
| `MultiProjectResult` | Result of multi-project execution |
| `MultiProjectOrchestrator` | Orchestrate pipeline execution across multiple projects |

---

## performance

*Performance monitoring and resource tracking utilities*

| Class | Description |
|-------|-------------|
| `ResourceUsage` | Resource usage metrics for a stage or operation |
| `PerformanceMetrics` | Performance metrics for a stage or operation |
| `PerformanceMonitor` | Monitor performance metrics for operations |
| `StagePerformanceTracker` | Track performance metrics for pipeline stages |

| Function | Description |
|----------|-------------|
| `monitor_performance()` | Context manager for monitoring operation performance |
| `get_system_resources()` | Get current system resource information |

---

## performance_monitor

*Performance monitoring and profiling utilities for research workflows*

| Class | Description |
|-------|-------------|
| `PerformanceMetrics` | Container for performance measurement results |
| `PerformanceMonitor` | Comprehensive performance monitoring and profiling |

| Function | Description |
|----------|-------------|
| `get_performance_monitor()` | Get the global performance monitor instance |
| `monitor_performance()` | Decorator for monitoring function performance |
| `benchmark_llm_query()` | Benchmark LLM query performance |
| `profile_memory_usage()` | Profile memory usage of a function |
| `main()` | CLI entry point for performance monitoring |
| `benchmark_function()` | Convenience function to benchmark a function using PerformanceMonitor |

---

## pipeline

*Pipeline execution system for research projects*

| Class | Description |
|-------|-------------|
| `PipelineConfig` | Configuration for pipeline execution |
| `PipelineStageResult` | Result from a pipeline stage execution |
| `PipelineExecutor` | Execute research project pipeline stages |

---

## pipeline_summary

*Pipeline summary generation and reporting*

| Class | Description |
|-------|-------------|
| `PipelineSummary` | Summary of pipeline execution |
| `PipelineSummaryGenerator` | Generate pipeline execution summaries |

| Function | Description |
|----------|-------------|
| `generate_pipeline_summary()` | Convenience function to generate and format pipeline summary |

---

## progress

*Progress reporting utilities for pipeline operations*

| Class | Description |
|-------|-------------|
| `ProgressBar` | Simple text-based progress bar for terminal output |
| `LLMProgressTracker` | Progress tracker for LLM operations with token-based progress |
| `SubStageProgress` | Track progress across multiple sub-stages within a main stage |

---

## retry

*Retry utilities for handling transient failures*

| Class | Description |
|-------|-------------|
| `RetryableOperation` | Context manager for retryable operations with manual control |

| Function | Description |
|----------|-------------|
| `retry_with_backoff()` | Decorator to retry a function with exponential backoff |
| `retry_on_transient_failure()` | Decorator for retrying on common transient failures |

**Constants:** `T`

---

## script_discovery

*Script discovery and execution utilities*

| Function | Description |
|----------|-------------|
| `discover_analysis_scripts()` | Discover all analysis scripts in projects/{project_name}/scripts/ to execute |
| `discover_orchestrators()` | Discover orchestrator scripts in scripts/ directory |
| `verify_analysis_outputs()` | Verify that analysis generated expected outputs |

---

## security

*Security utilities and input validation for the research template system*

| Class | Description |
|-------|-------------|
| `SecurityValidator` | Comprehensive input validation and security checks |
| `SecurityHeaders` | Security headers for HTTP responses and requests |
| `RateLimiter` | Simple in-memory rate limiter |
| `SecurityMonitor` | Monitor security events and anomalies |
| `SecurityViolation` | Exception raised for security violations |

| Function | Description |
|----------|-------------|
| `get_security_validator()` | Get the global security validator instance |
| `get_security_headers()` | Get security headers |
| `get_rate_limiter()` | Get the global rate limiter instance |
| `get_security_monitor()` | Get the global security monitor instance |
| `validate_llm_input()` | Convenience function for LLM input validation |
| `rate_limit()` | Decorator for rate limiting functions |

---
