"""Core module — most-used symbols for cross-module convenience.

Only symbols frequently imported via ``from infrastructure.core import X``
appear here. Specialist or rarely-used symbols should be imported directly
from their submodules:

    infrastructure.core.exceptions    — full exception hierarchy
    infrastructure.core.config_loader — load_config, get_config_as_dict
    infrastructure.core.environment   — check_python_version, setup_directories
    infrastructure.core.performance   — CodeProfiler, ProfilingMetrics, etc.
    infrastructure.core.checkpoint    — PipelineCheckpoint, StageResult
    infrastructure.core.pipeline      — PipelineConfig, PipelineExecutor
    infrastructure.core.multi_project — MultiProjectConfig, MultiProjectResult
    infrastructure.core.health_check  — quick_health_check, get_health_status
"""

from __future__ import annotations

# Checkpoint (used by orchestrator scripts)
from .checkpoint import CheckpointManager

# Health (used by analysis scripts)
from .health_check import SystemHealthChecker

# Logging (primary cross-cutting concern — all callers need these)
from .logging_utils import (
    format_duration,
    get_logger,
    log_operation,
    log_stage,
    log_success,
)

# Performance (decorator used by analysis scripts)
from .function_profiler import monitor_performance

# Progress (used by long-running scripts)
from .progress import ProgressBar

__all__ = [
    # Checkpoint
    "CheckpointManager",
    # Health
    "SystemHealthChecker",
    # Logging
    "get_logger",
    "log_operation",
    "log_stage",
    "log_success",
    "format_duration",
    # Performance
    "monitor_performance",
    # Progress
    "ProgressBar",
]
