"""Core pipeline subpackage — execution, monitoring, multi-project orchestration.

Re-exports primary symbols for ``from infrastructure.core.pipeline import …`` usage.
"""

from __future__ import annotations

from infrastructure.core.pipeline.executor import (
    PipelineConfig,
    PipelineExecutor,
    PipelineStageResult,
)
from infrastructure.core.pipeline.multi_project import (
    MultiProjectConfig,
    MultiProjectOrchestrator,
    MultiProjectResult,
)
from infrastructure.core.pipeline.stage_monitor import (
    PerformanceMonitor,
    PerformanceMetrics,
    StagePerformanceTracker,
    get_system_resources,
)
from infrastructure.core.pipeline.summary import generate_pipeline_summary
from infrastructure.core.pipeline.types import StageSpec
from infrastructure.core.telemetry import TelemetryCollector, TelemetryConfig

__all__ = [
    "MultiProjectConfig",
    "MultiProjectOrchestrator",
    "MultiProjectResult",
    "PerformanceMetrics",
    "PerformanceMonitor",
    "PipelineConfig",
    "PipelineExecutor",
    "PipelineStageResult",
    "StagePerformanceTracker",
    "StageSpec",
    "TelemetryCollector",
    "TelemetryConfig",
    "generate_pipeline_summary",
    "get_system_resources",
]
