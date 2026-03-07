"""Core module - Foundation utilities.

This module re-exports the most commonly needed symbols from infrastructure.core
submodules. Specialist symbols (security, profiling, file inventory, etc.) should
be imported directly from their submodules.

Commonly used submodules for direct import:
    infrastructure.core.security       — SecurityValidator, RateLimiter, etc.
    infrastructure.core.performance    — CodeProfiler, ProfilingMetrics, etc.
    infrastructure.core.exceptions     — full exception hierarchy
    infrastructure.core.file_inventory — FileInventoryManager, etc.
"""

from __future__ import annotations

# Checkpoint
from .checkpoint import CheckpointManager, PipelineCheckpoint, StageResult

# Configuration
from .config_loader import get_config_as_dict, load_config

# Environment
from .environment import check_dependencies, check_python_version, set_environment_variables, setup_directories

# Core exceptions (commonly caught/raised across modules)
from .exceptions import (
    BuildError,
    ConfigurationError,
    DependencyError,
    FileOperationError,
    IntegrationError,
    TemplateError,
    TestError,
    ValidationError,
    chain_exceptions,
    format_file_context,
    raise_with_context,
)

# Health
from .health_check import SystemHealthChecker, get_health_status, quick_health_check

# Logging (primary API surface — used everywhere)
from .logging_utils import (
    calculate_eta,
    format_duration,
    format_error_with_suggestions,
    get_logger,
    log_header,
    log_operation,
    log_stage,
    log_stage_with_eta,
    log_substep,
    log_success,
    log_timing,
    set_global_log_level,
    setup_logger,
)

# Multi-Project
from .multi_project import MultiProjectConfig, MultiProjectOrchestrator, MultiProjectResult

# Performance (decorator/context manager — commonly used)
from .performance import get_system_resources, monitor_performance, performance_context

# Pipeline
from .pipeline import PipelineConfig, PipelineExecutor, PipelineStageResult

# Progress
from .progress import ProgressBar, SubStageProgress

__all__ = [
    # Checkpoint
    "CheckpointManager",
    "PipelineCheckpoint",
    "StageResult",
    # Configuration
    "load_config",
    "get_config_as_dict",
    # Environment
    "check_python_version",
    "check_dependencies",
    "setup_directories",
    "set_environment_variables",
    # Exceptions
    "TemplateError",
    "ConfigurationError",
    "ValidationError",
    "BuildError",
    "FileOperationError",
    "DependencyError",
    "TestError",
    "IntegrationError",
    "raise_with_context",
    "format_file_context",
    "chain_exceptions",
    # Health
    "SystemHealthChecker",
    "quick_health_check",
    "get_health_status",
    # Logging
    "setup_logger",
    "get_logger",
    "log_operation",
    "log_timing",
    "log_success",
    "log_header",
    "log_stage",
    "log_substep",
    "set_global_log_level",
    "format_duration",
    "calculate_eta",
    "log_stage_with_eta",
    "format_error_with_suggestions",
    # Multi-Project
    "MultiProjectConfig",
    "MultiProjectResult",
    "MultiProjectOrchestrator",
    # Performance
    "monitor_performance",
    "performance_context",
    "get_system_resources",
    # Pipeline
    "PipelineConfig",
    "PipelineStageResult",
    "PipelineExecutor",
    # Progress
    "ProgressBar",
    "SubStageProgress",
]
