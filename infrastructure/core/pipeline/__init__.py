"""Core pipeline subpackage — execution, monitoring, multi-project orchestration.

Re-exports primary symbols for ``from infrastructure.core.pipeline import …`` usage.
"""

from infrastructure.core.pipeline.dag import stage_label
from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.multi_project import (
    MultiProjectConfig,
    MultiProjectOrchestrator,
    MultiProjectResult,
    format_multi_project_detailed_report,
    format_multi_project_outcome_lines,
)
from infrastructure.core.pipeline.stage_monitor import (
    PerformanceMonitor,
    PerformanceMetrics,
    StagePerformanceTracker,
    get_system_resources,
)
from infrastructure.core.pipeline.summary import generate_pipeline_summary
from infrastructure.core.pipeline.types import (
    PipelineControlConfig,
    PipelineConfig,
    PipelineStageResult,
    StageContract,
    StageHooks,
    StagePolicy,
    StageSpec,
)
from infrastructure.core.telemetry import TelemetryCollector, TelemetryConfig

__all__ = [
    "MultiProjectConfig",
    "MultiProjectOrchestrator",
    "MultiProjectResult",
    "format_multi_project_detailed_report",
    "format_multi_project_outcome_lines",
    "PerformanceMetrics",
    "PerformanceMonitor",
    "PipelineConfig",
    "PipelineExecutor",
    "PipelineStageResult",
    "PipelineControlConfig",
    "StagePerformanceTracker",
    "StageContract",
    "StageHooks",
    "StagePolicy",
    "StageSpec",
    "TelemetryCollector",
    "TelemetryConfig",
    "generate_pipeline_summary",
    "get_system_resources",
    "stage_label",
]
