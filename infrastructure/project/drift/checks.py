"""Template drift check implementations — barrel re-exports."""

from __future__ import annotations

from pathlib import Path

from infrastructure.project.drift.checks_boundary import (  # noqa: F401
    check_project_src_infrastructure_boundary,
)
from infrastructure.project.drift.checks_docs_counts import (  # noqa: F401
    check_docs_hardcoded_counts,
)
from infrastructure.project.drift.checks_exemplar import (  # noqa: F401
    check_all_export_drift,
    check_coverage_floor_consistency,
    check_function_name_drift,
    check_mocks_absent_from_tests,
    check_no_blanket_except_in_src,
    check_no_oversize_src_files,
    check_publication_metadata_consistency,
    check_referenced_files_exist,
    check_required_files_exist,
    check_test_class_drift,
)
from infrastructure.project.drift.models import Report
from infrastructure.project.drift.orchestrator import check_repo_scripts

__all__ = [
    "check_all_export_drift",
    "check_coverage_floor_consistency",
    "check_docs_hardcoded_counts",
    "check_function_name_drift",
    "check_mocks_absent_from_tests",
    "check_no_blanket_except_in_src",
    "check_no_oversize_src_files",
    "check_project",
    "check_project_src_infrastructure_boundary",
    "check_publication_metadata_consistency",
    "check_referenced_files_exist",
    "check_repo_thin_orchestrator_scripts",
    "check_required_files_exist",
    "check_test_class_drift",
]


def check_project(repo_root: Path, project: str, report: Report) -> None:
    from infrastructure.project.drift.registry import run_project_checks

    project_root = repo_root / "projects" / project
    if not project_root.is_dir():
        report.add("WARNING", project, "project_missing", f"{project_root} does not exist; skipping")
        return
    run_project_checks(project_root, repo_root, report, project)


def check_repo_thin_orchestrator_scripts(repo_root: Path, report: Report) -> None:
    check_repo_scripts(repo_root, report)
