"""Composable publication-readiness audit for public exemplars."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.pipeline.artifacts import validate_artifact_manifest
from infrastructure.methods import build_methods_orchestration_plan, validate_methods_orchestration_plan
from infrastructure.project.drift import run_drift_checks
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.validation.content.figure_validator import validate_figure_registry
from infrastructure.validation.evidence_registry import (
    build_project_evidence_registry,
    validate_text_against_registry,
)
from infrastructure.validation.output.artifacts import read_artifact_manifest
from infrastructure.validation.output.no_mock_enforcer import validate_no_mocks
from infrastructure.validation.publication.models import PublicationAuditReport, PublicationFinding

SCHEMA_VERSION = "template-publication-audit-v1"

_REQUIRED_RENDER_REPORTS = (
    "output/reports/artifact_manifest.json",
    "output/reports/evidence_registry.json",
    "output/reports/validation_report.json",
)

Checker = Callable[["AuditContext"], Iterable[PublicationFinding]]


@dataclass(frozen=True)
class AuditContext:
    """Inputs shared by publication audit checkers."""

    repo_root: Path
    project: str
    project_root: Path
    rendered: bool
    include_drift: bool


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _finding(
    ctx: AuditContext,
    *,
    path: str,
    code: str,
    severity: str,
    status: str,
    message: str,
    evidence: str = "",
    remediation: str = "",
    line: int = 0,
) -> PublicationFinding:
    return PublicationFinding(
        project=ctx.project,
        path=path,
        diagnostic_code=code,
        severity=severity,
        status=status,
        message=message,
        evidence=evidence,
        remediation=remediation,
        line=line,
    )


def check_project_presence(ctx: AuditContext) -> Iterable[PublicationFinding]:
    """Yield a finding if the declared public project directory is missing from the checkout."""
    if ctx.project_root.is_dir():
        return
    yield _finding(
        ctx,
        path=f"projects/{ctx.project}",
        code="PUBLICATION.PROJECT_MISSING",
        severity="error",
        status="fail",
        message="public project is missing from the checkout",
        remediation="Restore the canonical public exemplar or remove it from PUBLIC_PROJECT_NAMES.",
    )


def check_project_skill(ctx: AuditContext) -> Iterable[PublicationFinding]:
    """Yield a finding if the project's routable ``SKILL.md`` bundle is absent."""
    skill_name = ctx.project.removeprefix("templates/").replace("_", "-")
    skill_path = ctx.project_root / ".agents" / "skills" / skill_name / "SKILL.md"
    if skill_path.exists():
        return
    yield _finding(
        ctx,
        path=_relative(skill_path, ctx.repo_root),
        code="PUBLICATION.PROJECT_SKILL_MISSING",
        severity="error",
        status="fail",
        message="public exemplar has no routable project-local SKILL.md",
        remediation="Add the project skill bundle and regenerate the skill manifest/index.",
    )


def check_drift(ctx: AuditContext) -> Iterable[PublicationFinding]:
    """Run template-drift checks for the project and yield findings (skipped unless ``include_drift``)."""
    if not ctx.include_drift:
        return
    drift = run_drift_checks(ctx.repo_root, [ctx.project], include_repo_checks=False)
    for finding in drift.findings:
        status = "fail" if finding.severity == "ERROR" else "review_required"
        severity = "error" if finding.severity == "ERROR" else "warning"
        yield _finding(
            ctx,
            path=f"projects/{ctx.project}",
            code=f"DRIFT.{finding.rule}",
            severity=severity,
            status=status,
            message=finding.message,
            remediation="Resolve the template-drift finding and rerun the publication audit.",
        )


def check_no_mocks(ctx: AuditContext) -> Iterable[PublicationFinding]:
    """Run the no-mock enforcement scan over the project ``tests`` directory and yield findings."""
    tests_dir = ctx.project_root / "tests"
    if not tests_dir.is_dir():
        return
    for violation in validate_no_mocks(tests_dir, ctx.project_root):
        yield _finding(
            ctx,
            path=f"projects/{ctx.project}/tests",
            code="PUBLICATION.NO_MOCKS",
            severity="error",
            status="fail",
            message=violation,
            remediation="Exercise a real dependency, local HTTP service, fixture, or subprocess instead.",
        )


def check_methods(ctx: AuditContext) -> Iterable[PublicationFinding]:
    """Build and validate the methods orchestration plan, yielding findings for any issues."""
    try:
        plan = build_methods_orchestration_plan(ctx.repo_root, ctx.project)
        methods_issues = validate_methods_orchestration_plan(
            plan,
            repo_root=ctx.repo_root,
            require_generated_artifacts=ctx.rendered,
        )
    except (OSError, ValueError) as exc:
        yield _finding(
            ctx,
            path=f"projects/{ctx.project}/methods_pipeline.yaml",
            code="PUBLICATION.METHODS_AUDIT_CRASHED",
            severity="error",
            status="fail",
            message=str(exc),
            remediation="Make the methods pipeline and its contracts parseable.",
        )
        return
    for issue in methods_issues:
        status = "fail" if issue.severity == "error" else "review_required"
        severity = "error" if issue.severity == "error" else "warning"
        yield _finding(
            ctx,
            path=issue.path,
            code=issue.code,
            severity=severity,
            status=status,
            message=issue.message,
            remediation=issue.suggestion,
        )


def check_evidence(ctx: AuditContext) -> Iterable[PublicationFinding]:
    """Validate manuscript Markdown against the project evidence registry and yield review findings."""
    manuscript_dir = ctx.project_root / "manuscript"
    if not manuscript_dir.is_dir():
        return
    registry = build_project_evidence_registry(ctx.project_root)
    for markdown_path in sorted(manuscript_dir.glob("*.md")):
        if markdown_path.name in {"AGENTS.md", "README.md", "SYNTAX.md"}:
            continue
        text = markdown_path.read_text(encoding="utf-8")
        evidence_report = validate_text_against_registry(text, registry, strict=False)
        for evidence_issue in (*evidence_report.errors, *evidence_report.warnings):
            yield _finding(
                ctx,
                path=f"projects/{ctx.project}/manuscript/{markdown_path.name}",
                code="PUBLICATION.EVIDENCE_REVIEW",
                severity="warning",
                status="review_required",
                message=f"unsupported {evidence_issue.kind} token {evidence_issue.value!r}",
                evidence=f"line {evidence_issue.line_number}",
                remediation=(
                    "Register the source-backed fact or label the statement as methodological/fixture-derived."
                ),
                line=evidence_issue.line_number,
            )


def check_rendered_output_dir(ctx: AuditContext) -> Iterable[PublicationFinding]:
    """Yield a finding if the rendered ``output`` directory is missing for the project."""
    if (ctx.project_root / "output").is_dir():
        return
    yield _finding(
        ctx,
        path=f"projects/{ctx.project}/output",
        code="PUBLICATION.RENDERED_OUTPUT_MISSING",
        severity="error",
        status="fail",
        message="rendered output directory is missing",
        remediation="Run the canonical analysis, render, and validation stages.",
    )


def check_render_reports(ctx: AuditContext) -> Iterable[PublicationFinding]:
    """Yield a finding for each required generated publication report that is missing."""
    for relative in _REQUIRED_RENDER_REPORTS:
        if (ctx.project_root / relative).is_file():
            continue
        yield _finding(
            ctx,
            path=f"projects/{ctx.project}/{relative}",
            code="PUBLICATION.RENDER_REPORT_MISSING",
            severity="error",
            status="fail",
            message="required generated publication report is missing",
            remediation="Regenerate the project output through the canonical validation pipeline.",
        )


def check_artifact_manifest(ctx: AuditContext) -> Iterable[PublicationFinding]:
    """Read and validate the artifact manifest, yielding findings for parse errors or drift."""
    manifest_path = ctx.project_root / "output" / "reports" / "artifact_manifest.json"
    if not manifest_path.is_file():
        return
    try:
        manifest = read_artifact_manifest(manifest_path)
        manifest_report = validate_artifact_manifest(manifest, project_dir=ctx.project_root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        yield _finding(
            ctx,
            path=f"projects/{ctx.project}/output/reports/artifact_manifest.json",
            code="PUBLICATION.ARTIFACT_MANIFEST_INVALID",
            severity="error",
            status="fail",
            message=str(exc),
            remediation="Regenerate the artifact manifest from the current output tree.",
        )
        return
    for manifest_issue in manifest_report.issues:
        yield _finding(
            ctx,
            path=f"projects/{ctx.project}/output/reports/artifact_manifest.json",
            code="PUBLICATION.ARTIFACT_MANIFEST_DRIFT",
            severity="error",
            status="fail",
            message=manifest_issue,
            remediation="Regenerate outputs and the aggregate artifact manifest together.",
        )


def check_figure_registry(ctx: AuditContext) -> Iterable[PublicationFinding]:
    """Validate the figure registry against manuscript sources and yield findings."""
    figure_path = ctx.project_root / "output" / "figures" / "figure_registry.json"
    manuscript_dir = ctx.project_root / "manuscript"
    if not figure_path.exists():
        return
    figure_ok, figure_issues = validate_figure_registry(figure_path, manuscript_dir)
    for figure_issue in figure_issues:
        yield _finding(
            ctx,
            path=f"projects/{ctx.project}/output/figures/figure_registry.json",
            code="PUBLICATION.FIGURE_REGISTRY",
            severity="error",
            status="fail",
            message=figure_issue,
            remediation="Regenerate the figure and registry, including caption, label, and source metadata.",
        )
    if not figure_ok and not figure_issues:
        yield _finding(
            ctx,
            path=f"projects/{ctx.project}/output/figures/figure_registry.json",
            code="PUBLICATION.FIGURE_REGISTRY_INVALID",
            severity="error",
            status="fail",
            message="figure registry validation failed without a diagnostic",
            remediation="Inspect the figure registry JSON and rerun validation.",
        )


SOURCE_CHECKERS: tuple[Checker, ...] = (
    check_project_skill,
    check_drift,
    check_no_mocks,
    check_methods,
    check_evidence,
)

RENDERED_CHECKERS: tuple[Checker, ...] = (
    check_rendered_output_dir,
    check_render_reports,
    check_artifact_manifest,
    check_figure_registry,
)


def _audit_project(
    repo_root: Path,
    project: str,
    *,
    rendered: bool,
    include_drift: bool,
) -> list[PublicationFinding]:
    project_root = (repo_root / "projects" / project).resolve()
    ctx = AuditContext(
        repo_root=repo_root,
        project=project,
        project_root=project_root,
        rendered=rendered,
        include_drift=include_drift,
    )
    findings: list[PublicationFinding] = []
    findings.extend(check_project_presence(ctx))
    if not project_root.is_dir():
        return findings
    for checker in SOURCE_CHECKERS:
        findings.extend(checker(ctx))
    if rendered:
        for checker in RENDERED_CHECKERS:
            findings.extend(checker(ctx))
    return findings


def build_publication_audit(
    repo_root: Path | str,
    projects: Iterable[str] | None = None,
    *,
    rendered: bool = False,
    include_drift: bool = True,
) -> PublicationAuditReport:
    """Build a deterministic audit for one or all public projects."""
    root = Path(repo_root).resolve()
    names = tuple(projects) if projects is not None else tuple(PUBLIC_PROJECT_NAMES)
    findings: list[PublicationFinding] = []
    for project in names:
        findings.extend(_audit_project(root, project, rendered=rendered, include_drift=include_drift))
    findings.sort(
        key=lambda finding: (
            finding.project,
            finding.path,
            finding.diagnostic_code,
            finding.line,
            finding.message,
        )
    )
    return PublicationAuditReport(schema_version=SCHEMA_VERSION, projects=names, findings=tuple(findings))


def validate_publication_audit(report: PublicationAuditReport, *, strict: bool = False) -> int:
    """Return a process exit code.

    Deterministic ``fail`` findings always block. When ``strict`` is true,
    ``review_required`` findings also block.
    """
    if report.blocking_findings:
        return 1
    if strict and report.review_findings:
        return 1
    return 0


def format_publication_audit_json(report: PublicationAuditReport) -> str:
    """Serialize the audit as stable, sorted JSON."""
    return json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"


def format_publication_audit_markdown(report: PublicationAuditReport) -> str:
    """Serialize the audit as a concise human-readable Markdown report."""
    lines = [
        "# Publication audit",
        "",
        f"Status: **{report.status}**",
        "",
        f"Projects audited: {len(report.projects)}",
        f"Blocking findings: {len(report.blocking_findings)}",
        f"Review-required findings: {len(report.review_findings)}",
        "",
        "| Status | Severity | Project | Code | Path | Message |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for finding in report.findings:
        message = finding.message.replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| `{finding.status}` | `{finding.severity}` | `{finding.project}` | "
            f"`{finding.diagnostic_code}` | `{finding.path}` | {message} |"
        )
    lines.append("")
    return "\n".join(lines)
