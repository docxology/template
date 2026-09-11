"""Project analysis and reporting: quality audits, review reports, and the
final reading-report assembly."""

from template_search_project.analysis.analysis import (
    StageResult,
    audit_infrastructure_imports,
    check_determinism_artifacts,
    run_project_tests,
    validate_bibliography_completeness,
    validate_variables_resolved,
)
from template_search_project.analysis.report import write_reading_report
from template_search_project.analysis.review_report import generate_review_report

__all__ = [
    "StageResult",
    "audit_infrastructure_imports",
    "check_determinism_artifacts",
    "run_project_tests",
    "validate_bibliography_completeness",
    "validate_variables_resolved",
    "generate_review_report",
    "write_reading_report",
]
