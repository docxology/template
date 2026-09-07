"""Tests for the public publication-readiness audit."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.core.pipeline.artifacts import snapshot_current_artifact_manifest
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.rendering.manuscript_composition import write_manuscript_composition
from infrastructure.validation.cli.main import build_parser, publication_audit_command
from infrastructure.validation.publication import (
    PublicationAuditReport,
    PublicationFinding,
    build_publication_audit,
    format_publication_audit_json,
    format_publication_audit_markdown,
    validate_publication_audit,
)
from infrastructure.validation.publication.rendered_provenance import write_rendered_provenance_receipt
from infrastructure.validation.rendered_snapshot import build_current_rendered_snapshot
from tests._support.projects import make_project, write_doc

REPO_ROOT = Path(__file__).resolve().parents[3]
SYNTHETIC_PROJECT = "templates/template_test"


def _write_snapshot_audit_fixture(root: Path) -> Path:
    """Write one real-file rendered project with a stage-zero integrity snapshot."""
    project = make_project(
        root,
        "template_test",
        program="templates",
        with_manuscript=True,
        with_scripts=True,
        with_output=True,
    )
    write_doc(
        project / ".agents" / "skills" / "template-test" / "SKILL.md",
        "---\nname: template-test\ndescription: Synthetic publication fixture.\n---\n",
    )
    write_doc(
        project / "methods_pipeline.yaml",
        """\
stages:
  - name: Project Analysis
    key: analysis
    script: scripts/pipeline/stage_02_analysis.py
    tags: [core]
    contract:
      input_artifacts: ["projects/{project}/src/"]
      output_artifacts: ["projects/{project}/output/data/result.json"]
      definition_of_done: "Analysis writes a source-bound result."
      failure_code: "PROJECT_ANALYSIS_FAILED"
      retry_policy: 0
""",
    )
    write_doc(root / "scripts" / "pipeline" / "stage_02_analysis.py", 'print("analysis")\n')
    write_doc(root / "scripts" / "runner" / "execute_pipeline.py", 'print("pipeline")\n')

    source = project / "manuscript" / "01_methods.md"
    hydrated = project / "output" / "manuscript" / source.name
    manuscript = "# Methods\n\nA deterministic procedure produces a source-bound artifact.\n"
    write_doc(source, manuscript)
    write_doc(hydrated, manuscript)
    combined = project / "output" / "web" / "_combined_manuscript.md"
    write_doc(combined, manuscript)
    write_manuscript_composition(project, SYNTHETIC_PROJECT, [hydrated], combined)
    write_doc(project / "output" / "data" / "result.json", '{"status": "complete"}\n')
    write_doc(project / "output" / "reports" / "evidence_registry.json", '{"claims": []}\n')
    snapshot_current_artifact_manifest(project / "output")

    snapshot = build_current_rendered_snapshot(root, SYNTHETIC_PROJECT)
    checks = {"Artifact manifest": True, "Rendered structure": True}
    validation_report = {
        "timestamp": "2026-01-01T00:00:00Z",
        "checks": checks,
        "figure_issues": [],
        "output_statistics": {"inventory_mode": "stable-shippable-output-v1"},
        "summary": {
            "total_checks": len(checks),
            "passed": len(checks),
            "failed": 0,
            "figure_issues_count": 0,
            "all_passed": True,
        },
        "recommendations": [],
        "validated_inputs": snapshot.validated_inputs_dict(),
    }
    write_doc(
        project / "output" / "reports" / "validation_report.json",
        json.dumps(validation_report, indent=2, sort_keys=True) + "\n",
    )
    return project


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


def test_publication_audit_requires_alt_for_tagged_pdf_cover(tmp_path: Path) -> None:
    project = make_project(tmp_path, "template_test", program="templates", with_manuscript=True)
    config_path = project / "manuscript" / "config.yaml"
    config_path.write_text(
        "paper:\n  title: Tagged paper\n  cover:\n    image: cover.png\nmetadata:\n  tagged_pdf: true\n",
        encoding="utf-8",
    )

    missing_alt = build_publication_audit(
        tmp_path,
        ["templates/template_test"],
        rendered=False,
        include_drift=False,
    )

    assert "PUBLICATION.COVER_ACCESSIBILITY" in {finding.diagnostic_code for finding in missing_alt.blocking_findings}

    with_alt = config_path.read_text(encoding="utf-8").replace(
        "    image: cover.png\n",
        "    image: cover.png\n    alt: A source-bound cover.\n",
    )
    config_path.write_text(with_alt, encoding="utf-8")
    complete = build_publication_audit(
        tmp_path,
        ["templates/template_test"],
        rendered=False,
        include_drift=False,
    )

    assert "PUBLICATION.COVER_ACCESSIBILITY" not in {finding.diagnostic_code for finding in complete.blocking_findings}


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


def test_strict_rendered_audit_accepts_stage_zero_snapshot_with_current_receipt(tmp_path: Path) -> None:
    project = _write_snapshot_audit_fixture(tmp_path)
    manifest_payload = json.loads(
        (project / "output" / "reports" / "artifact_manifest.json").read_text(encoding="utf-8")
    )
    write_rendered_provenance_receipt(tmp_path, SYNTHETIC_PROJECT)

    report = build_publication_audit(
        tmp_path,
        [SYNTHETIC_PROJECT],
        rendered=True,
        include_drift=False,
    )

    assert manifest_payload["entries"]
    assert {entry["stage_num"] for entry in manifest_payload["entries"]} == {0}
    assert {entry["stage_name"] for entry in manifest_payload["entries"]} == {"current-output-snapshot"}
    assert report.findings == ()
    assert validate_publication_audit(report, strict=True) == 0


@pytest.mark.parametrize(
    ("receipt_state", "expected_failure"),
    [
        ("missing", "PUBLICATION.RENDERED_PROVENANCE_MISSING"),
        ("stale", "PUBLICATION.RENDERED_PROVENANCE_VALIDATION_INPUTS_DRIFT"),
    ],
)
def test_strict_rendered_audit_rejects_stage_zero_snapshot_without_current_receipt(
    tmp_path: Path,
    receipt_state: str,
    expected_failure: str,
) -> None:
    project = _write_snapshot_audit_fixture(tmp_path)
    if receipt_state == "stale":
        write_rendered_provenance_receipt(tmp_path, SYNTHETIC_PROJECT)
        write_doc(project / "src" / "stub.py", '"""Source changed after validation."""\n')

    report = build_publication_audit(
        tmp_path,
        [SYNTHETIC_PROJECT],
        rendered=True,
        include_drift=False,
    )
    codes = {finding.diagnostic_code for finding in report.findings}

    assert codes == {"METHODS.STAGE_PROVENANCE_UNAVAILABLE", expected_failure}
    assert validate_publication_audit(report, strict=True) == 1


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


def test_publication_audit_checks_accessibility_for_hydrated_only_figure(tmp_path: Path) -> None:
    project = make_project(
        tmp_path,
        "template_test",
        program="templates",
        with_manuscript=True,
        with_output=True,
    )
    write_doc(project / "manuscript" / "00_abstract.md", "# Abstract\n\nNo source figure.\n")
    write_doc(
        project / "output" / "manuscript" / "03_results.md",
        "# Results\n\n![Injected result](../figures/injected.png){#fig:injected}\n",
    )
    figures = project / "output" / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    (figures / "injected.png").write_bytes(b"png")
    (figures / "figure_registry.json").write_text(
        json.dumps(
            {
                "figures": [
                    {
                        "label": "fig:injected",
                        "filename": "injected.png",
                        "generated_by": "tests.injected",
                        "metadata": {"alt_text": ""},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = build_publication_audit(
        tmp_path,
        ["templates/template_test"],
        rendered=True,
        include_drift=False,
        require_figure_accessibility=True,
    )

    matching = [
        finding for finding in report.blocking_findings if finding.diagnostic_code == "PUBLICATION.FIGURE_REGISTRY"
    ]
    assert len(matching) == 1
    assert "fig:injected" in matching[0].message


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
