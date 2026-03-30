"""Core runtime subpackage — environment, checkpoints, health checks, profiling.

Re-exports primary symbols for ``from infrastructure.core.runtime import …`` usage.
"""

from __future__ import annotations

from infrastructure.core.runtime.checkpoint import CheckpointManager, StageResult
from infrastructure.core.runtime.environment import (
    check_python_version,
    get_python_command,
    get_subprocess_env,
    setup_directories,
)
from infrastructure.core.runtime.eta import ETAEstimate, calculate_eta
from infrastructure.core.runtime.function_profiler import (
    CodeProfiler,
    ProfilingMetrics,
    monitor_performance,
)
from infrastructure.core.runtime.health_check import SystemHealthChecker
from infrastructure.core.runtime.retry import retry_with_backoff

__all__ = [
    "CheckpointManager",
    "CodeProfiler",
    "ETAEstimate",
    "ProfilingMetrics",
    "StageResult",
    "SystemHealthChecker",
    "calculate_eta",
    "check_python_version",
    "get_python_command",
    "get_subprocess_env",
    "monitor_performance",
    "retry_with_backoff",
    "setup_directories",
]
