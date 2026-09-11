"""Core domain modules for the template meta-project: repository
introspection, typed receipts and figure contracts, and repo-root discovery
for the thin orchestrator scripts."""

from .contracts import (
    MATRIX_SCHEMA_VERSION,
    METRICS_RECEIPT_SCHEMA_VERSION,
    METRICS_SCHEMA_VERSION,
    STEGANOGRAPHY_RECEIPT_SCHEMA_VERSION,
    build_metrics_receipt,
    build_steganography_defaults_receipt,
    validate_comparative_matrix_lockstep,
    validate_metrics_payload,
    validate_metrics_receipt,
    validate_steganography_defaults_receipt,
)
from .introspection import (
    META_PROJECT_DIR_NAME,
    META_PROJECT_PUBLIC_NAME,
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
    enumerate_numbered_scripts,
    load_pipeline_stages_from_yaml,
    resolve_template_repo_root,
)
from .paths import locate_repo_root

__all__ = [
    "META_PROJECT_DIR_NAME",
    "META_PROJECT_PUBLIC_NAME",
    "CoverageConfig",
    "InfrastructureReport",
    "ModuleInfo",
    "PipelineStage",
    "ProjectAnalysis",
    "MATRIX_SCHEMA_VERSION",
    "METRICS_RECEIPT_SCHEMA_VERSION",
    "METRICS_SCHEMA_VERSION",
    "STEGANOGRAPHY_RECEIPT_SCHEMA_VERSION",
    "analyze_test_coverage_config",
    "build_infrastructure_report",
    "build_metrics_receipt",
    "build_steganography_defaults_receipt",
    "count_pipeline_stages",
    "discover_infrastructure_modules",
    "discover_projects",
    "enumerate_numbered_scripts",
    "load_pipeline_stages_from_yaml",
    "locate_repo_root",
    "resolve_template_repo_root",
    "validate_comparative_matrix_lockstep",
    "validate_metrics_payload",
    "validate_metrics_receipt",
    "validate_steganography_defaults_receipt",
]
