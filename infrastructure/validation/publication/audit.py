"""Composable publication-readiness audit for public exemplars."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from markdown_it import MarkdownIt

from infrastructure.core.pipeline.artifacts import validate_artifact_manifest
from infrastructure.methods import build_methods_orchestration_plan, validate_methods_orchestration_plan
from infrastructure.project.drift import run_drift_checks
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.validation.content.figure_validator import validate_figure_registry
from infrastructure.validation.evidence_registry import (
    build_project_evidence_registry,
    missing_evidence_source_paths,
    validate_text_against_registry,
)
from infrastructure.validation.output.artifacts import read_artifact_manifest
from infrastructure.validation.output.no_mock_enforcer import validate_no_mocks
from infrastructure.validation.publication.models import PublicationAuditReport, PublicationFinding
from infrastructure.validation.publication.rendered_provenance import (
    RenderedProvenanceValidation,
    rendered_manuscript_paths,
    validate_rendered_provenance,
)

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
    require_figure_accessibility: bool = False
    rendered_provenance: RenderedProvenanceValidation | None = None


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
        if (
            issue.code == "METHODS.STAGE_PROVENANCE_UNAVAILABLE"
            and ctx.rendered_provenance is not None
            and ctx.rendered_provenance.valid
        ):
            # A current co-snapshot receipt is alternative evidence. It never
            # changes an integrity-only artifact manifest into stage lineage.
            continue
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
    for source_path in missing_evidence_source_paths(ctx.project_root, registry, repo_root=ctx.repo_root):
        yield _finding(
            ctx,
            path=f"projects/{ctx.project}/output/reports/evidence_registry.json",
            code="PUBLICATION.EVIDENCE_SOURCE_MISSING",
            severity="error",
            status="fail",
            message=f"evidence registry source path is missing or outside the project: {source_path}",
            remediation="Regenerate the evidence registry from current project artifacts and remove stale paths.",
        )
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
    figure_ok, figure_issues = validate_figure_registry(
        figure_path,
        manuscript_dir,
        require_accessibility=ctx.require_figure_accessibility,
    )
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


_PLACEHOLDER_TOKEN_RE = re.compile(
    r"""
    (?:
        \{\{\{?\s*
        (?:
            (?!\#(?:fig|tbl|sec|eq|def|prop|thm|lem|cor|rem|ax):)
            [\#/>^&!]\s*[A-Za-z_][A-Za-z0-9_.-]*(?:\s+[^{}\n]+)?
            |
            [A-Za-z_][A-Za-z0-9_.-]*
            (?:
                \.\*
                |
                :[^\s{}\n]+
                |
                \s*\([^{}\n]*\)
            )?
        )
        \s*\}\}\}?
        |
        \$\{\s*(?!\()[#!]?[A-Za-z_][A-Za-z0-9_.-]*(?:[^{}\n]*)?\}
    )
    """,
    re.VERBOSE,
)


def _mask_inline_code_spans(content: str) -> str:
    """Mask CommonMark code spans using exact maximal backtick-run matching."""
    masked = list(content)
    index = 0
    while index < len(content):
        opener = content.find("`", index)
        if opener < 0:
            break
        opener_end = opener
        while opener_end < len(content) and content[opener_end] == "`":
            opener_end += 1
        width = opener_end - opener
        cursor = opener_end
        closer_end = -1
        while cursor < len(content):
            closer = content.find("`", cursor)
            if closer < 0:
                break
            candidate_end = closer
            while candidate_end < len(content) and content[candidate_end] == "`":
                candidate_end += 1
            if candidate_end - closer == width:
                closer_end = candidate_end
                break
            cursor = candidate_end
        if closer_end < 0:
            index = opener_end
            continue
        for position in range(opener, closer_end):
            if masked[position] != "\n":
                masked[position] = " "
        index = closer_end
    return "".join(masked)


def _mask_markdown_code(content: str) -> str:
    """Mask only CommonMark-parsed code blocks/spans while preserving offsets."""
    lines = content.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    masked = list(content)
    for token in MarkdownIt("commonmark").parse(content):
        if token.map is None:
            continue
        start_line, end_line = token.map
        start = offsets[start_line]
        end = offsets[end_line]
        if token.type in {"fence", "code_block"}:
            for position in range(start, end):
                if masked[position] != "\n":
                    masked[position] = " "
            continue
        if token.type != "inline":
            continue
        inline_mask = _mask_inline_code_spans(content[start:end])
        for relative, character in enumerate(inline_mask):
            if character != content[start + relative]:
                masked[start + relative] = character
    return "".join(masked)


def check_placeholder_tokens(ctx: AuditContext) -> Iterable[PublicationFinding]:
    """Scan combined and hydrated manuscripts, reporting each unresolved token once."""
    seen_tokens: set[str] = set()
    for path in rendered_manuscript_paths(ctx.project_root):
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            yield _finding(
                ctx,
                path=f"projects/{ctx.project}/{_relative(path, ctx.project_root)}",
                code="PUBLICATION.PLACEHOLDER_SCAN_FAILED",
                severity="error",
                status="fail",
                message=f"cannot read rendered manuscript input: {exc}",
                remediation="Restore the rendered manuscript and rerun the canonical render.",
            )
            continue
        searchable = _mask_markdown_code(content)
        for match in _PLACEHOLDER_TOKEN_RE.finditer(searchable):
            token = match.group(0)
            if token in seen_tokens:
                continue
            seen_tokens.add(token)
            line = searchable[: match.start()].count("\n") + 1
            yield _finding(
                ctx,
                path=f"projects/{ctx.project}/{_relative(path, ctx.project_root)}",
                code="PUBLICATION.PLACEHOLDER_TOKEN",
                severity="error",
                status="fail",
                message=f"unresolved placeholder token in rendered output: {token}",
                remediation="Hydrate the declared token and regenerate rendered outputs.",
                line=line,
            )


def check_unconsumed_markdown(ctx: AuditContext) -> Iterable[PublicationFinding]:
    """Fail when explicit canonical source-to-render consumption is incomplete."""
    if ctx.rendered_provenance is None:
        return
    for issue in ctx.rendered_provenance.issues:
        if issue.code != "UNCONSUMED_MANUSCRIPT":
            continue
        yield _finding(
            ctx,
            path=f"projects/{ctx.project}/output/reports/rendered_provenance.json",
            code="PUBLICATION.UNCONSUMED_MANUSCRIPT",
            severity="error",
            status="fail",
            message=issue.message,
            remediation=(
                "Hydrate every canonical manuscript input and rerun render, validation, and receipt generation."
            ),
        )


def check_rendered_provenance(ctx: AuditContext) -> Iterable[PublicationFinding]:
    """Require a complete, well-formed, current rendered co-snapshot receipt."""
    if ctx.rendered_provenance is None:
        return
    for issue in ctx.rendered_provenance.issues:
        if issue.code == "UNCONSUMED_MANUSCRIPT":
            continue
        yield _finding(
            ctx,
            path=f"projects/{ctx.project}/output/reports/rendered_provenance.json",
            code=f"PUBLICATION.RENDERED_PROVENANCE_{issue.code}",
            severity="error",
            status="fail",
            message=issue.message,
            remediation="Regenerate outputs, pass validation, and write a new rendered provenance receipt.",
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
    check_rendered_provenance,
    check_placeholder_tokens,
    check_unconsumed_markdown,
)


def _audit_project(
    repo_root: Path,
    project: str,
    *,
    rendered: bool,
    include_drift: bool,
    require_figure_accessibility: bool,
) -> list[PublicationFinding]:
    project_root = (repo_root / "projects" / project).resolve()
    provenance = validate_rendered_provenance(repo_root, project) if rendered and project_root.is_dir() else None
    ctx = AuditContext(
        repo_root=repo_root,
        project=project,
        project_root=project_root,
        rendered=rendered,
        include_drift=include_drift,
        require_figure_accessibility=require_figure_accessibility,
        rendered_provenance=provenance,
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
    require_figure_accessibility: bool = False,
) -> PublicationAuditReport:
    """Build a deterministic audit for one or all public projects."""
    root = Path(repo_root).resolve()
    names = tuple(projects) if projects is not None else tuple(PUBLIC_PROJECT_NAMES)
    findings: list[PublicationFinding] = []
    for project in names:
        findings.extend(
            _audit_project(
                root,
                project,
                rendered=rendered,
                include_drift=include_drift,
                require_figure_accessibility=require_figure_accessibility,
            )
        )
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
