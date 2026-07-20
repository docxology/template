"""Real-file tests for the private-project promotion security gate."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest
import yaml

from infrastructure.project.promotion import (
    PROMOTION_CHECKS,
    check_private_project_promotion,
    evaluate_promotion_candidate,
    main,
    render_promotion_report,
    scan_security_todos,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
AS_OF = date(2026, 7, 15)


def _write_candidate(tmp_path: Path, *, source: str = "def ok() -> bool:\n    return True\n") -> Path:
    project = tmp_path / "private_candidate"
    source_path = project / "src/service.py"
    source_path.parent.mkdir(parents=True)
    source_path.write_text(source, encoding="utf-8")
    return project


def _commit_candidate(project: Path, *, git_root: Path | None = None) -> str:
    repository = git_root or project
    subprocess.run(["git", "init", "-q"], cwd=repository, check=True, timeout=30)
    source_path = (project / "src").relative_to(repository)
    subprocess.run(["git", "add", source_path.as_posix()], cwd=repository, check=True, timeout=30)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Template Tests",
            "-c",
            "user.email=template-tests@example.test",
            "commit",
            "-qm",
            "candidate source",
        ],
        cwd=repository,
        check=True,
        timeout=30,
    )
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repository, capture_output=True, text=True, check=True, timeout=30
    ).stdout.strip()


def _orchestration_payload(*, source_commit: str, project: str = "working/private_candidate") -> dict[str, object]:
    return {
        "promotion": {
            "project": project,
            "source_commit": source_commit,
            "reviewer": "reviewer@example.test",
            "identity_verified": True,
            "authorization_verified": True,
            "redaction_reviewed": True,
            "secrets_externalized": True,
            "routes_reviewed": True,
            "mcp_boundaries_reviewed": True,
            "export_tests_passed": True,
            "risk_acceptance": None,
        }
    }


def _resolution(status: str = "closed") -> dict[str, str]:
    result = {"status": status, "evidence": "reviewed by the accountable maintainer"}
    if status == "risk-accepted":
        result.update(
            {
                "rationale": "bounded local-only exposure until the named follow-up",
                "accepted_by": "security-owner",
                "expires": "2026-12-31",
            }
        )
    return result


def _write_attestation(
    project: Path,
    *,
    checks: dict[str, object] | None = None,
    security_findings: dict[str, object] | None = None,
) -> Path:
    payload = {
        "schema_version": 1,
        "project": project.name,
        "review": {"reviewed_by": "security-owner", "reviewed_at": "2026-07-15"},
        "checks": checks if checks is not None else {name: _resolution() for name in PROMOTION_CHECKS},
        "security_findings": security_findings or {},
    }
    path = project / "promotion-security.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def test_complete_attestation_passes_without_source_disclosure(tmp_path: Path) -> None:
    project = _write_candidate(tmp_path)
    _write_attestation(project)

    report = check_private_project_promotion(project, as_of=AS_OF)

    assert report.eligible
    assert report.errors == ()
    assert report.findings == ()
    assert render_promotion_report(report).startswith("PASS private-project promotion gate")


def test_missing_boundary_check_fails_closed(tmp_path: Path) -> None:
    project = _write_candidate(tmp_path)
    checks = {name: _resolution() for name in PROMOTION_CHECKS if name != "authorization"}
    _write_attestation(project, checks=checks)

    report = check_private_project_promotion(project, as_of=AS_OF)

    assert not report.eligible
    assert "promotion attestation is missing checks: authorization" in report.errors


def test_risk_acceptance_requires_owner_rationale_and_fresh_expiry(tmp_path: Path) -> None:
    project = _write_candidate(tmp_path)
    checks = {name: _resolution() for name in PROMOTION_CHECKS}
    checks["authentication"] = {
        "status": "risk-accepted",
        "evidence": "bounded review",
        "expires": "2026-07-14",
    }
    _write_attestation(project, checks=checks)

    report = check_private_project_promotion(project, as_of=AS_OF)

    assert not report.eligible
    joined = "\n".join(report.errors)
    assert "rationale is required" in joined
    assert "accepted_by is required" in joined
    assert "expires is stale" in joined


def test_live_security_todo_requires_explicit_risk_acceptance(tmp_path: Path) -> None:
    secret_text = "# TODO: replace hard-coded authentication secret before release"
    project = _write_candidate(tmp_path, source=secret_text + "\n")
    _write_attestation(project)

    report = check_private_project_promotion(project, as_of=AS_OF)

    assert not report.eligible
    assert [finding.finding_id for finding in report.findings] == ["src/service.py:1"]
    rendered = render_promotion_report(report)
    assert "src/service.py:1" in rendered
    assert secret_text not in rendered


def test_live_security_todo_can_be_time_bounded_and_risk_accepted(tmp_path: Path) -> None:
    project = _write_candidate(tmp_path, source="# FIXME: authorization route handler gap\n")
    _write_attestation(project, security_findings={"src/service.py:1": _resolution("risk-accepted")})

    report = check_private_project_promotion(project, as_of=AS_OF)

    assert report.eligible
    assert len(report.findings) == 1


def test_stale_security_finding_attestation_is_rejected(tmp_path: Path) -> None:
    project = _write_candidate(tmp_path)
    _write_attestation(project, security_findings={"src/removed.py:7": _resolution("risk-accepted")})

    report = check_private_project_promotion(project, as_of=AS_OF)

    assert not report.eligible
    assert "stale security findings: src/removed.py:7" in "\n".join(report.errors)


def test_attestation_must_stay_inside_candidate(tmp_path: Path) -> None:
    project = _write_candidate(tmp_path)
    external = tmp_path / "promotion-security.yaml"
    internal = _write_attestation(project)
    external.write_text(internal.read_text(encoding="utf-8"), encoding="utf-8")

    report = check_private_project_promotion(project, attestation_path=external, as_of=AS_OF)

    assert not report.eligible
    assert "must live inside the candidate project" in "\n".join(report.errors)


def test_scanner_ignores_generated_output_and_attestation(tmp_path: Path) -> None:
    project = _write_candidate(tmp_path)
    attestation = _write_attestation(project)
    generated = project / "output/report.md"
    generated.parent.mkdir()
    generated.write_text("TODO: security secret", encoding="utf-8")
    attestation.write_text(attestation.read_text(encoding="utf-8") + "# TODO: security review\n", encoding="utf-8")

    findings, errors = scan_security_todos(project, attestation_path=attestation)

    assert findings == ()
    assert errors == ()


def test_thin_cli_returns_machine_readable_pass_and_failure(tmp_path: Path) -> None:
    project = _write_candidate(tmp_path)
    attestation = _write_attestation(project)
    command = [
        sys.executable,
        "scripts/gates/check_private_project_promotion.py",
        "--project-root",
        str(project),
        "--attestation",
        str(attestation),
        "--as-of",
        AS_OF.isoformat(),
        "--json",
    ]

    passed = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False, timeout=30)
    assert passed.returncode == 0, passed.stderr
    assert json.loads(passed.stdout)["eligible"] is True

    (project / "src/service.py").write_text("# TODO: redact secret export route\n", encoding="utf-8")
    failed = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False, timeout=30)
    assert failed.returncode == 1
    payload = json.loads(failed.stdout)
    assert payload["eligible"] is False
    assert payload["findings"][0]["finding_id"] == "src/service.py:1"


def test_explicit_candidate_cli_and_composite_report(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = _write_candidate(tmp_path)
    security = _write_attestation(project)
    source_commit = _commit_candidate(project)
    orchestration = project / "promotion.yaml"
    orchestration.write_text(
        f"""promotion:
  project: working/private_candidate
  source_commit: {source_commit}
  reviewer: reviewer@example.test
  identity_verified: true
  authorization_verified: true
  redaction_reviewed: true
  secrets_externalized: true
  routes_reviewed: true
  mcp_boundaries_reviewed: true
  export_tests_passed: true
  risk_acceptance: null
""",
        encoding="utf-8",
    )

    assert (
        main(
            [
                "candidate",
                "--project-root",
                str(project),
                "--attestation",
                str(security),
                "--as-of",
                AS_OF.isoformat(),
                "--json",
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["eligible"] is True

    composite = evaluate_promotion_candidate(
        project,
        project_name="working/private_candidate",
        orchestration_attestation=orchestration,
        as_of=AS_OF,
    )
    assert composite.eligible
    payload = composite.to_dict()
    security_payload = payload["security"]
    assert isinstance(security_payload, dict)
    assert security_payload["eligible"] is True


def test_composite_rejects_attestation_for_another_project(tmp_path: Path) -> None:
    project = _write_candidate(tmp_path)
    security = _write_attestation(project)
    source_commit = _commit_candidate(project)
    orchestration = project / "promotion.yaml"
    orchestration.write_text(
        yaml.safe_dump(
            {
                "promotion": {
                    "project": "working/another_project",
                    "source_commit": source_commit,
                    "reviewer": "reviewer@example.test",
                    "identity_verified": True,
                    "authorization_verified": True,
                    "redaction_reviewed": True,
                    "secrets_externalized": True,
                    "routes_reviewed": True,
                    "mcp_boundaries_reviewed": True,
                    "export_tests_passed": True,
                    "risk_acceptance": None,
                }
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="project does not match candidate"):
        evaluate_promotion_candidate(
            project,
            project_name="working/private_candidate",
            orchestration_attestation=orchestration,
            security_attestation=security,
            as_of=AS_OF,
        )


def test_composite_requires_qualified_project_name(tmp_path: Path) -> None:
    project = _write_candidate(tmp_path)
    security = _write_attestation(project)
    source_commit = _commit_candidate(project)
    orchestration = project / "promotion.yaml"
    orchestration.write_text(yaml.safe_dump(_orchestration_payload(source_commit=source_commit)), encoding="utf-8")

    with pytest.raises(ValueError, match="qualified and non-absolute"):
        evaluate_promotion_candidate(
            project,
            project_name="private_candidate",
            orchestration_attestation=orchestration,
            security_attestation=security,
            as_of=AS_OF,
        )


def test_composite_accepts_candidate_nested_in_sidecar_checkout(tmp_path: Path) -> None:
    sidecar = tmp_path / "sidecar"
    project = _write_candidate(sidecar / "working")
    security = _write_attestation(project)
    source_commit = _commit_candidate(project, git_root=sidecar)
    orchestration = project / "promotion.yaml"
    orchestration.write_text(yaml.safe_dump(_orchestration_payload(source_commit=source_commit)), encoding="utf-8")

    report = evaluate_promotion_candidate(
        project,
        project_name="working/private_candidate",
        orchestration_attestation=orchestration,
        security_attestation=security,
        as_of=AS_OF,
    )

    assert report.eligible is True


def test_composite_rejects_attestation_for_another_commit(tmp_path: Path) -> None:
    project = _write_candidate(tmp_path)
    security = _write_attestation(project)
    _commit_candidate(project)
    orchestration = project / "promotion.yaml"
    orchestration.write_text(yaml.safe_dump(_orchestration_payload(source_commit="b" * 40)), encoding="utf-8")

    with pytest.raises(ValueError, match="source_commit does not match candidate HEAD"):
        evaluate_promotion_candidate(
            project,
            project_name="working/private_candidate",
            orchestration_attestation=orchestration,
            security_attestation=security,
            as_of=AS_OF,
        )


def test_composite_rejects_uncommitted_candidate_source(tmp_path: Path) -> None:
    project = _write_candidate(tmp_path)
    security = _write_attestation(project)
    source_commit = _commit_candidate(project)
    orchestration = project / "promotion.yaml"
    orchestration.write_text(yaml.safe_dump(_orchestration_payload(source_commit=source_commit)), encoding="utf-8")
    (project / "src/service.py").write_text("def changed() -> bool:\n    return False\n", encoding="utf-8")

    with pytest.raises(ValueError, match="uncommitted changes outside attestation files"):
        evaluate_promotion_candidate(
            project,
            project_name="working/private_candidate",
            orchestration_attestation=orchestration,
            security_attestation=security,
            as_of=AS_OF,
        )


def test_composite_rejects_rename_into_allowlisted_attestation_path(tmp_path: Path) -> None:
    project = _write_candidate(tmp_path)
    security = project / "xxxpromotion-security.yaml"
    security.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "project": project.name,
                "review": {"reviewed_by": "security-owner", "reviewed_at": "2026-07-15"},
                "checks": {name: _resolution() for name in PROMOTION_CHECKS},
                "security_findings": {},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    _commit_candidate(project)
    subprocess.run(["git", "add", security.name], cwd=project, check=True, timeout=30)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Template Tests",
            "-c",
            "user.email=template-tests@example.test",
            "commit",
            "-qm",
            "candidate attestation",
        ],
        cwd=project,
        check=True,
        timeout=30,
    )
    source_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=project, capture_output=True, text=True, check=True, timeout=30
    ).stdout.strip()
    subprocess.run(
        ["git", "mv", security.name, "promotion-security.yaml"],
        cwd=project,
        check=True,
        timeout=30,
    )
    orchestration = project / "promotion.yaml"
    orchestration.write_text(yaml.safe_dump(_orchestration_payload(source_commit=source_commit)), encoding="utf-8")

    with pytest.raises(ValueError, match="uncommitted changes"):
        evaluate_promotion_candidate(
            project,
            project_name="working/private_candidate",
            orchestration_attestation=orchestration,
            security_attestation=project / "promotion-security.yaml",
            as_of=AS_OF,
        )
