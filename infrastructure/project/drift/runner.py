"""Run template drift checks and format reports."""

from __future__ import annotations

from pathlib import Path

from infrastructure.project.drift.checks import (
    check_project,
    check_repo_docs_hardcoded_counts,
    check_repo_thin_orchestrator_scripts,
)
from infrastructure.project.drift.models import Report
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

DEFAULT_PROJECT_NAMES: tuple[str, ...] = PUBLIC_PROJECT_NAMES


def run_drift_checks(
    repo_root: Path,
    projects: tuple[str, ...] | list[str] | None = None,
    *,
    include_repo_checks: bool = True,
) -> Report:
    """Run drift checks for the given exemplar projects."""
    report = Report()
    names = tuple(projects) if projects is not None else DEFAULT_PROJECT_NAMES
    for project in names:
        check_project(repo_root, project, report)
    if include_repo_checks:
        check_repo_docs_hardcoded_counts(repo_root, report)
        check_repo_thin_orchestrator_scripts(repo_root, report)
    return report


def print_human_report(report: Report) -> None:
    if not report.findings:
        print("template_drift: no drift detected.")
        return
    errors = report.errors()
    warnings = report.warnings()
    if errors:
        print(f"template_drift: {len(errors)} ERROR(S):")
        for finding in errors:
            print(f"  [ERROR] {finding.project}/{finding.rule}: {finding.message}")
    if warnings:
        print(f"template_drift: {len(warnings)} WARNING(S):")
        for finding in warnings:
            print(f"  [warn]  {finding.project}/{finding.rule}: {finding.message}")


def print_github_report(report: Report) -> None:
    for finding in report.findings:
        prefix = "::error" if finding.severity == "ERROR" else "::warning"
        print(f"{prefix} title={finding.project}/{finding.rule}::{finding.message}")


def exit_code_for_report(report: Report, *, strict: bool = False) -> int:
    if report.errors():
        return 1
    if strict and report.warnings():
        return 1
    return 0
