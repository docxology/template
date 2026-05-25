"""Report writers for AutoResearch readiness."""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.autoresearch.models import AutoResearchReport


def write_autoresearch_report(project_root: Path, report: AutoResearchReport) -> tuple[Path, Path]:
    """Write JSON and Markdown AutoResearch readiness reports."""
    reports_dir = project_root / "output" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = reports_dir / "autoresearch_readiness.json"
    md_path = reports_dir / "autoresearch_readiness.md"

    json_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(_to_markdown(report), encoding="utf-8")
    return json_path, md_path


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
