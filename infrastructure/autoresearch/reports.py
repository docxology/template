"""Report writers for AutoResearch readiness."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from infrastructure.autoresearch.models import AutoResearchPlan, AutoResearchReport


def write_autoresearch_report(project_root: Path, report: AutoResearchReport) -> tuple[Path, Path]:
    """Write portable JSON and Markdown AutoResearch readiness reports."""
    reports_dir = project_root / "output" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = reports_dir / "autoresearch_readiness.json"
    md_path = reports_dir / "autoresearch_readiness.md"
    portable_report = _release_safe_report(report)

    json_path.write_text(json.dumps(portable_report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(_to_markdown(portable_report), encoding="utf-8")
    return json_path, md_path


def _release_safe_report(report: AutoResearchReport) -> AutoResearchReport:
    """Replace validation-only absolute paths with stable public labels."""
    plan = report.plan
    repo_root = plan.repo_root if plan is not None else None
    issues = tuple(
        replace(issue, source_path=_release_safe_path(issue.source_path, repo_root)) for issue in report.issues
    )
    if plan is None:
        return replace(report, issues=issues)

    config = replace(
        plan.config,
        source_path=_release_safe_path(plan.config.source_path, plan.repo_root),
    )
    portable_plan = replace(
        plan,
        repo_root=Path("."),
        project_root=Path(_release_safe_path(plan.project_root, plan.repo_root)),
        config=config,
    )
    return replace(report, issues=issues, plan=portable_plan)


def _release_safe_path(value: str | Path, repo_root: Path | None) -> str:
    """Return a checkout-independent path without a machine-local prefix."""
    text = str(value)
    if not text:
        return ""
    path = Path(text)
    if not path.is_absolute():
        return path.as_posix()
    if repo_root is not None:
        try:
            return path.resolve().relative_to(repo_root.resolve()).as_posix()
        except ValueError:
            pass
    return path.name


def write_autoresearch_plan(project_root: Path, plan: AutoResearchPlan) -> Path:
    """Write the composed AutoResearch plan JSON."""
    path = project_root / "output" / "data" / "autoresearch_plan.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_autoresearch_review_packet(project_root: Path, report: AutoResearchReport) -> tuple[Path, Path]:
    """Write a generic readiness review packet."""
    reports_dir = project_root / "output" / "reports"
    data_dir = project_root / "output" / "data"
    reports_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    packet = {
        "project_name": report.project_name,
        "ready_for_review": report.valid,
        "summary": report.summary,
        "issues": [issue.to_dict() for issue in report.issues],
        "required_review_decision": "approve, revise, or block before publication",
    }
    json_path = data_dir / "autoresearch_review_packet.json"
    md_path = reports_dir / "autoresearch_review_packet.md"
    json_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(_review_packet_markdown(packet), encoding="utf-8")
    return json_path, md_path


def write_autoresearch_summary(project_root: Path, report: AutoResearchReport) -> Path:
    """Write a generic AutoResearch summary Markdown report."""
    reports_dir = project_root / "output" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / "autoresearch_summary.md"
    summary = report.summary
    path.write_text(
        "\n".join(
            [
                "# AutoResearch Summary",
                "",
                f"- Project: `{report.project_name}`",
                f"- Readiness valid: `{str(report.valid).lower()}`",
                f"- Issues: {summary['issues']}",
                f"- Errors: {summary['errors']}",
                f"- Warnings: {summary['warnings']}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def write_benchmark_scores(project_root: Path, plan: AutoResearchPlan) -> Path:
    """Write deterministic benchmark task status from configured grading outputs."""
    data_dir = project_root / "output" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    tasks = []
    for task in plan.config.benchmark_tasks:
        grading_path = _artifact_path(project_root, task.grading_output)
        tasks.append(
            {
                "id": task.identifier,
                "description": task.description,
                "grading_output_path": task.grading_output,
                "status": "graded" if grading_path.exists() else "missing",
            }
        )
    payload = {
        "project_name": plan.project_name,
        "tasks": tasks,
        "task_count": len(tasks),
    }
    path = data_dir / "benchmark_scores.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _to_markdown(report: AutoResearchReport) -> str:
    summary = report.summary
    lines = [
        "# AutoResearch Readiness",
        "",
        f"- Project: `{report.project_name}`",
        f"- Status: `{'pass' if report.valid else 'attention'}`",
        f"- Issues: {summary['issues']} ({summary['errors']} error(s), {summary['warnings']} warning(s))",
        "",
    ]
    if report.plan:
        lines.extend(
            [
                "## Plan",
                "",
                f"- Topic: `{report.plan.config.topic}`",
                f"- Domain: `{report.plan.domain}`",
                f"- Stages: {len(report.plan.stages)}",
                f"- Quality checks: {', '.join(report.plan.quality_checks) or 'none'}",
                "",
            ]
        )
    if not report.issues:
        lines.extend(["No readiness issues were found.", ""])
        return "\n".join(lines)

    lines.extend(["## Issues", ""])
    for issue in report.issues:
        lines.extend(
            [
                f"### {issue.code}",
                "",
                f"- Severity: `{issue.severity}`",
                f"- Source: `{issue.source_path}`",
                f"- Message: {issue.message}",
                f"- Suggested action: {issue.suggested_action}",
                "",
            ]
        )
    return "\n".join(lines)


def _review_packet_markdown(packet: dict[str, object]) -> str:
    lines = [
        "# AutoResearch Human Review Packet",
        "",
        f"- Project: `{packet['project_name']}`",
        f"- Ready for review: `{str(packet['ready_for_review']).lower()}`",
        f"- Required decision: {packet['required_review_decision']}",
        "",
    ]
    issues = packet.get("issues", [])
    if isinstance(issues, list) and issues:
        lines.extend(["## Issues", ""])
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            lines.append(f"- `{issue.get('code', 'AUTORESEARCH.UNKNOWN')}`: {issue.get('message', '')}")
        lines.append("")
    return "\n".join(lines)


def _artifact_path(project_root: Path, artifact: str) -> Path:
    path = Path(artifact)
    if path.is_absolute():
        return path
    return project_root / path
