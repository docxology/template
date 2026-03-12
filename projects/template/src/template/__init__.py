"""Template meta-project — repository introspection utilities.

Public API:
    discover_infrastructure_modules — scan infrastructure/ subpackages
    discover_projects — scan projects/ workspaces
    count_pipeline_stages — enumerate numbered pipeline scripts
    analyze_test_coverage_config — extract testing thresholds
    build_infrastructure_report — aggregate all above into one report

Data classes:
    ModuleInfo, ProjectInfo, PipelineStage, CoverageConfig, InfrastructureReport
"""

from __future__ import annotations

from .introspection import (
    CoverageConfig,
    InfrastructureReport,
    ModuleInfo,
    PipelineStage,
    ProjectInfo,
    analyze_test_coverage_config,
    build_infrastructure_report,
    count_pipeline_stages,
    discover_infrastructure_modules,
    discover_projects,
)

__all__ = [
    "ModuleInfo",
    "ProjectInfo",
    "PipelineStage",
    "CoverageConfig",
    "InfrastructureReport",
    "discover_infrastructure_modules",
    "discover_projects",
    "count_pipeline_stages",
    "analyze_test_coverage_config",
    "build_infrastructure_report",
]
