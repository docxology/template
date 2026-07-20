"""Core pipeline APIs with lazy compatibility re-exports.

Import leaf modules for new code (for example
``infrastructure.core.pipeline.types``).  Package-level names remain available
during the compatibility window, but loading this package no longer imports
reporting or scientific/visualization dependencies eagerly.
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from infrastructure.core.pipeline.definition import (
        PipelinePurpose,
        PipelineSource,
        PipelineSourceOrigin,
        PipelineSourceResolutionError,
        resolve_pipeline_source,
    )
    from infrastructure.core.pipeline.dag import stage_label
    from infrastructure.core.pipeline.executor import PipelineExecutor
    from infrastructure.core.pipeline.multi_project import (
        MultiProjectConfig,
        MultiProjectOrchestrator,
        MultiProjectResult,
        format_multi_project_outcome_lines,
    )
    from infrastructure.core.pipeline.stage_monitor import (
        PerformanceMetrics,
        PerformanceMonitor,
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
    from infrastructure.reporting.multi_project_report import format_multi_project_detailed_report

_EXPORTS: dict[str, tuple[str, str]] = {
    "PipelinePurpose": ("infrastructure.core.pipeline.definition", "PipelinePurpose"),
    "PipelineSource": ("infrastructure.core.pipeline.definition", "PipelineSource"),
    "PipelineSourceOrigin": ("infrastructure.core.pipeline.definition", "PipelineSourceOrigin"),
    "PipelineSourceResolutionError": (
        "infrastructure.core.pipeline.definition",
        "PipelineSourceResolutionError",
    ),
    "resolve_pipeline_source": ("infrastructure.core.pipeline.definition", "resolve_pipeline_source"),
    "PipelineConfig": ("infrastructure.core.pipeline.types", "PipelineConfig"),
    "PipelineExecutor": ("infrastructure.core.pipeline.executor", "PipelineExecutor"),
    "stage_label": ("infrastructure.core.pipeline.dag", "stage_label"),
    "MultiProjectConfig": ("infrastructure.core.pipeline.multi_project", "MultiProjectConfig"),
    "MultiProjectOrchestrator": ("infrastructure.core.pipeline.multi_project", "MultiProjectOrchestrator"),
    "MultiProjectResult": ("infrastructure.core.pipeline.multi_project", "MultiProjectResult"),
    "format_multi_project_outcome_lines": (
        "infrastructure.core.pipeline.multi_project",
        "format_multi_project_outcome_lines",
    ),
    "format_multi_project_detailed_report": (
        "infrastructure.reporting.multi_project_report",
        "format_multi_project_detailed_report",
    ),
    "PerformanceMetrics": ("infrastructure.core.pipeline.stage_monitor", "PerformanceMetrics"),
    "PerformanceMonitor": ("infrastructure.core.pipeline.stage_monitor", "PerformanceMonitor"),
    "StagePerformanceTracker": ("infrastructure.core.pipeline.stage_monitor", "StagePerformanceTracker"),
    "get_system_resources": ("infrastructure.core.pipeline.stage_monitor", "get_system_resources"),
    "generate_pipeline_summary": ("infrastructure.core.pipeline.summary", "generate_pipeline_summary"),
    "PipelineControlConfig": ("infrastructure.core.pipeline.types", "PipelineControlConfig"),
    "PipelineStageResult": ("infrastructure.core.pipeline.types", "PipelineStageResult"),
    "StageContract": ("infrastructure.core.pipeline.types", "StageContract"),
    "StageHooks": ("infrastructure.core.pipeline.types", "StageHooks"),
    "StagePolicy": ("infrastructure.core.pipeline.types", "StagePolicy"),
    "StageSpec": ("infrastructure.core.pipeline.types", "StageSpec"),
    "TelemetryCollector": ("infrastructure.core.telemetry", "TelemetryCollector"),
    "TelemetryConfig": ("infrastructure.core.telemetry", "TelemetryConfig"),
}

__all__ = [
    "PipelinePurpose",
    "PipelineSource",
    "PipelineSourceOrigin",
    "PipelineSourceResolutionError",
    "resolve_pipeline_source",
    "PipelineConfig",
    "PipelineExecutor",
    "stage_label",
    "MultiProjectConfig",
    "MultiProjectOrchestrator",
    "MultiProjectResult",
    "format_multi_project_outcome_lines",
    "format_multi_project_detailed_report",
    "PerformanceMetrics",
    "PerformanceMonitor",
    "StagePerformanceTracker",
    "get_system_resources",
    "generate_pipeline_summary",
    "PipelineControlConfig",
    "PipelineStageResult",
    "StageContract",
    "StageHooks",
    "StagePolicy",
    "StageSpec",
    "TelemetryCollector",
    "TelemetryConfig",
]


def __getattr__(name: str) -> Any:
    """Load a compatibility export only when it is requested."""
    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(name) from exc
    value = getattr(import_module(module_name), attribute)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Expose lazy names to interactive help and introspection."""
    return sorted((*globals(), *__all__))
