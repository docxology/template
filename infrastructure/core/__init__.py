"""Core module — most-used symbols for cross-module convenience.

Only symbols frequently imported via ``from infrastructure.core import X``
appear here. Specialist or rarely-used symbols should be imported directly
from their submodules:

    infrastructure.core.exceptions    — full exception hierarchy
    infrastructure.core.config.loader — load_config, get_config_as_dict
    infrastructure.core.runtime.environment   — check_python_version, setup_directories
    infrastructure.core.runtime.function_profiler — CodeProfiler, ProfilingMetrics, etc.
    infrastructure.core.runtime.checkpoint    — PipelineCheckpoint, StageResult
    infrastructure.core.pipeline      — PipelineConfig, PipelineExecutor
    infrastructure.core.pipeline.multi_project — MultiProjectConfig, MultiProjectResult
    infrastructure.core.runtime.health_check  — quick_health_check, get_health_status
    infrastructure.core.telemetry     — TelemetryCollector, TelemetryConfig
"""

from __future__ import annotations

# Checkpoint (used by orchestrator scripts)
from infrastructure.core.runtime.checkpoint import CheckpointManager

# Health (used by analysis scripts)
from infrastructure.core.runtime.health_check import SystemHealthChecker

# Logging (primary cross-cutting concern — all callers need these)
from infrastructure.core.logging.helpers import format_duration
from infrastructure.core.logging.utils import (
    get_logger,
    log_operation,
    log_stage,
    log_success,
)

# Performance (decorator used by analysis scripts)
from infrastructure.core.runtime.function_profiler import monitor_performance

# Progress (used by long-running scripts)
from infrastructure.core.progress import ProgressBar

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
