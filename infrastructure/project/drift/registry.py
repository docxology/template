"""Registry of drift check callables — single import surface for runners."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from infrastructure.project.drift.models import Report

ProjectCheckFn = Callable[[Path, Report, str], None]
RepoCheckFn = Callable[[Path, Report], None]

from infrastructure.project.drift.checks import (  # noqa: E402 — registry aggregates checks module
    check_all_export_drift,
    check_config_author_placeholders,
    check_config_example_parity,
    check_coverage_floor_consistency,
    check_docs_hardcoded_counts,
    check_function_name_drift,
    check_metadata_export_current,
    check_mocks_absent_from_tests,
    check_no_blanket_except_in_src,
    check_no_oversize_src_files,
    check_project_src_infrastructure_boundary,
    check_publication_index_completeness,
    check_publication_metadata_consistency,
    check_publishing_status_block_current,
    check_referenced_files_exist,
    check_required_files_exist,
    check_shared_template_design_contract,
    check_shared_template_truth_contract,
    check_template_signpost_contract,
    check_test_class_drift,
)
from infrastructure.project.drift.checks_forkability import check_forkability_contract  # noqa: E402
from infrastructure.project.drift.orchestrator import (  # noqa: E402
    check_project_scripts,
    check_repo_scripts,
)

PROJECT_CHECKS: tuple[ProjectCheckFn, ...] = (
    check_required_files_exist,
    check_template_signpost_contract,
    check_config_example_parity,
    check_forkability_contract,
    check_function_name_drift,
    check_test_class_drift,
    check_all_export_drift,
    check_coverage_floor_consistency,
    check_referenced_files_exist,
    check_no_oversize_src_files,
    check_no_blanket_except_in_src,
    check_mocks_absent_from_tests,
    check_publication_index_completeness,
    check_publication_metadata_consistency,
    check_config_author_placeholders,
    check_metadata_export_current,
    check_publishing_status_block_current,
    check_project_src_infrastructure_boundary,
)

REPO_CHECKS: tuple[RepoCheckFn, ...] = (
    check_docs_hardcoded_counts,
    check_shared_template_design_contract,
    check_shared_template_truth_contract,
    check_repo_scripts,
)


def run_project_checks(project_root: Path, repo_root: Path, report: Report, project: str) -> None:
    """Run all registered per-project drift checks."""
    for check_fn in PROJECT_CHECKS:
        check_fn(project_root, report, project)
    check_project_scripts(project_root, repo_root, report, project)


def run_repo_checks(repo_root: Path, report: Report) -> None:
    """Run repository-wide drift checks."""
    for check_fn in REPO_CHECKS:
        check_fn(repo_root, report)


__all__ = [
    "PROJECT_CHECKS",
    "REPO_CHECKS",
    "ProjectCheckFn",
    "RepoCheckFn",
    "run_project_checks",
    "run_repo_checks",
]
