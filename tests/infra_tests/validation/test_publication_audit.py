"""Tests for the public publication-readiness audit."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.validation.cli.main import build_parser, publication_audit_command
from infrastructure.validation.publication import (
    PublicationAuditReport,
    PublicationFinding,
    build_publication_audit,
    format_publication_audit_json,
    format_publication_audit_markdown,
    validate_publication_audit,
)
from tests._support.projects import make_project, write_doc

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_advanced_literature_review_is_in_public_scope() -> None:
    assert "templates/template_advanced_literature_review" in PUBLIC_PROJECT_NAMES


def test_publication_audit_finding_serialization_is_stable() -> None:
    finding = PublicationFinding(
        project="templates/example",
        path="projects/templates/example/README.md",
        diagnostic_code="PUBLICATION.EXAMPLE",
        severity="warning",
        status="review_required",
        message="editorial review remains",
        evidence="line 4",
        remediation="review the sentence",
        line=4,
    )
    report = PublicationAuditReport("test-v1", (finding.project,), (finding,))

    assert report.status == "review"
    assert validate_publication_audit(report, strict=False) == 0
    assert validate_publication_audit(report, strict=True) == 1
    payload = json.loads(format_publication_audit_json(report))
    assert payload["findings"][0]["diagnostic_code"] == "PUBLICATION.EXAMPLE"
    assert "review_required" in format_publication_audit_markdown(report)


def test_publication_audit_blocks_deterministic_failures() -> None:
    finding = PublicationFinding(
        project="templates/example",
        path="projects/templates/example/tests",
        diagnostic_code="PUBLICATION.NO_MOCKS",
        severity="error",
        status="fail",
        message="prohibited mock framework",
    )
    report = PublicationAuditReport("test-v1", (finding.project,), (finding,))

    assert report.status == "fail"
    assert validate_publication_audit(report, strict=False) == 1
    assert validate_publication_audit(report, strict=True) == 1


def test_publication_audit_cli_exposes_rendered_and_format_flags() -> None:
    args = build_parser().parse_args(
        [
            "publication-audit",
            "--project",
            "templates/template_advanced_literature_review",
            "--rendered",
            "--strict",
            "--format",
            "json",
        ]
    )

    assert args.command == "publication-audit"
    assert args.rendered is True
    assert args.strict is True
    assert args.format == "json"


def test_publication_audit_cli_exposes_figure_accessibility_flag() -> None:
    args = build_parser().parse_args(
        [
            "publication-audit",
            "--project",
            "templates/template_advanced_literature_review",
            "--require-figure-accessibility",
        ]
    )

    assert args.require_figure_accessibility is True


def test_publication_audit_cli_exposes_all_public_selection() -> None:
    args = build_parser().parse_args(["publication-audit", "--all-public"])

    assert args.all_public is True
    assert args.project is None


def test_publication_audit_json_stream_is_machine_readable(capsys: pytest.CaptureFixture[str]) -> None:
    args = build_parser().parse_args(
        [
            "publication-audit",
            "--project",
            "templates/template_advanced_literature_review",
            "--format",
            "json",
        ]
    )
    with pytest.raises(SystemExit) as exc_info:
        publication_audit_command(args)
    assert exc_info.value.code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == "template-publication-audit-v1"


def test_advanced_audit_has_no_missing_static_contracts() -> None:
    report = build_publication_audit(
        REPO_ROOT,
        ["templates/template_advanced_literature_review"],
        rendered=False,
        include_drift=False,
    )
    codes = {finding.diagnostic_code for finding in report.blocking_findings}
    assert "PUBLICATION.PROJECT_SKILL_MISSING" not in codes


def test_publication_audit_flags_missing_project_skill(tmp_path: Path) -> None:
    make_project(tmp_path, "template_test", program="templates", with_manuscript=True)
    report = build_publication_audit(
        tmp_path,
        ["templates/template_test"],
        rendered=False,
        include_drift=False,
    )
    codes = {finding.diagnostic_code for finding in report.blocking_findings}
    assert "PUBLICATION.PROJECT_SKILL_MISSING" in codes


def test_publication_audit_flags_missing_project(tmp_path: Path) -> None:
    (tmp_path / "projects").mkdir()
    report = build_publication_audit(
        tmp_path,
        ["templates/missing_project"],
        rendered=False,
        include_drift=False,
    )
    assert any(finding.diagnostic_code == "PUBLICATION.PROJECT_MISSING" for finding in report.findings)


def test_publication_audit_rendered_mode_requires_reports(tmp_path: Path) -> None:
    project = make_project(
        tmp_path,
        "template_test",
        program="templates",
        with_manuscript=True,
        with_output=True,
    )
    write_doc(project / "manuscript" / "02_methods_overview.md", "# Methods\n\nProcedure.\n")
    write_doc(
        project / "methods_pipeline.yaml",
        """
stages:
  - name: Project Analysis
    script: projects/templates/template_test/scripts/run.py
    tags: [core]
    contract:
      input_artifacts: ["projects/templates/template_test/src/"]
      output_artifacts: ["projects/templates/template_test/output/data/result.json"]
      definition_of_done: "Analysis writes a result."
      failure_code: ANALYSIS_FAILED
""",
    )
    write_doc(project / "scripts" / "run.py", 'print("ok")\n')

    report = build_publication_audit(
        tmp_path,
        ["templates/template_test"],
        rendered=True,
        include_drift=False,
    )
    codes = {finding.diagnostic_code for finding in report.blocking_findings}
    assert "PUBLICATION.RENDER_REPORT_MISSING" in codes


def test_publication_audit_flags_missing_figure_registry_for_referenced_figure(tmp_path: Path) -> None:
    project = make_project(
        tmp_path,
        "template_test",
        program="templates",
        with_manuscript=True,
        with_output=True,
    )
    write_doc(
        project / "manuscript" / "03_results.md",
        "# Results\n\n![Result](../output/figures/result.png){#fig:result}\n",
    )
    report = build_publication_audit(
        tmp_path,
        ["templates/template_test"],
        rendered=True,
        include_drift=False,
    )
    codes = {finding.diagnostic_code for finding in report.blocking_findings}
    assert "PUBLICATION.FIGURE_REGISTRY" in codes


def test_publication_audit_flags_missing_evidence_source(tmp_path: Path) -> None:
    project = make_project(
        tmp_path,
        "template_test",
        program="templates",
        with_manuscript=True,
        with_output=True,
    )
    write_doc(
        project / "data" / "claim_ledger.yaml",
        "claims:\n  - claim_id: missing-source\n    kind: number\n    value: 42\n    artifact_path: missing.json\n",
    )
    report = build_publication_audit(
        tmp_path,
        ["templates/template_test"],
        rendered=False,
        include_drift=False,
    )
    codes = {finding.diagnostic_code for finding in report.blocking_findings}
    assert "PUBLICATION.EVIDENCE_SOURCE_MISSING" in codes


def test_publication_audit_findings_sort_deterministically(tmp_path: Path) -> None:
    (tmp_path / "projects").mkdir()
    report = build_publication_audit(
        tmp_path,
        ["templates/b", "templates/a"],
        rendered=False,
        include_drift=False,
    )
    codes = [finding.diagnostic_code for finding in report.findings]
    projects = [finding.project for finding in report.findings]
    assert codes == ["PUBLICATION.PROJECT_MISSING", "PUBLICATION.PROJECT_MISSING"]
    assert projects == ["templates/a", "templates/b"]
