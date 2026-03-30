"""Template meta-project — repository introspection and metrics injection.

Introspection API:
    discover_infrastructure_modules — scan infrastructure/ subpackages
    discover_projects — scan projects/ workspaces
    count_pipeline_stages — enumerate numbered pipeline scripts
    analyze_test_coverage_config — extract testing thresholds
    build_infrastructure_report — aggregate all above into one report

Injection API:
    load_metrics          — deserialise output/data/metrics.json
    render_chapter        — substitute ${vars} in one chapter file
    render_all_chapters   — process all chapters into output/manuscript/

Data classes:
    ModuleInfo, ProjectAnalysis, PipelineStage, CoverageConfig, InfrastructureReport
"""

from __future__ import annotations

from .inject_metrics import load_metrics, render_all_chapters, render_chapter
from .introspection import (
    CoverageConfig,
    InfrastructureReport,
    ModuleInfo,
    PipelineStage,
    ProjectAnalysis,
    analyze_test_coverage_config,
    build_infrastructure_report,
    count_pipeline_stages,
    discover_infrastructure_modules,
    discover_projects,
)
from .architecture_viz import (
    comparative_feature_matrix_data,
    generate_all_architecture_figures,
    generate_architecture_overview,
    generate_comparative_feature_matrix,
    generate_module_inventory,
    generate_pipeline_stages,
)
from .metrics import (
    build_manuscript_metrics_dict,
    count_docs_markdown_files,
    count_docs_subdirs,
    count_test_functions,
    format_count,
    save_metrics_json,
)

__all__ = [
    # Introspection data classes
    "ModuleInfo",
    "ProjectAnalysis",
    "PipelineStage",
    "CoverageConfig",
    "InfrastructureReport",
    # Introspection functions
    "discover_infrastructure_modules",
    "discover_projects",
    "count_pipeline_stages",
    "analyze_test_coverage_config",
    "build_infrastructure_report",
    # Injection functions
    "load_metrics",
    "render_chapter",
    "render_all_chapters",
    # Metrics functions
    "count_test_functions",
    "count_docs_markdown_files",
    "count_docs_subdirs",
    "format_count",
    "build_manuscript_metrics_dict",
    "save_metrics_json",
    # Architecture visualization functions
    "comparative_feature_matrix_data",
    "generate_architecture_overview",
    "generate_pipeline_stages",
    "generate_module_inventory",
    "generate_comparative_feature_matrix",
    "generate_all_architecture_figures",
]
