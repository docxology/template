"""Tests for offline private-project promotion attestations."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
import yaml

from infrastructure.project.promotion import load_promotion_attestation, main, validate_promotion_attestation


def _payload(**overrides: object) -> dict[str, object]:
    promotion: dict[str, object] = {
        "project": "working/private_example",
        "source_commit": "a" * 40,
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
    promotion.update(overrides)
    return {"promotion": promotion}


def test_complete_attestation_is_approved() -> None:
    result = validate_promotion_attestation(_payload())

    assert result.approved is True
    assert result.to_dict()["project"] == "working/private_example"


def test_incomplete_attestation_requires_explicit_risk_acceptance() -> None:
    with pytest.raises(ValueError, match="without risk acceptance"):
        validate_promotion_attestation(_payload(export_tests_passed=False))


def test_risk_acceptance_can_cover_incomplete_checks() -> None:
    result = validate_promotion_attestation(
        _payload(
            export_tests_passed=False,
            risk_acceptance={
                "owner": "security-owner",
                "rationale": "Promotion is limited to a review environment.",
                "expiry": "2099-01-01",
            },
        )
    )

    assert result.approved is True
    assert result.risk_acceptance is not None


@pytest.mark.parametrize("project", ["/private/project", "working/../project", "private_example"])
def test_project_path_escape_is_rejected(project: str) -> None:
    with pytest.raises(ValueError, match="qualified"):
        validate_promotion_attestation(_payload(project=project))


def test_expired_risk_acceptance_is_rejected() -> None:
    with pytest.raises(ValueError, match="must not be in the past"):
        validate_promotion_attestation(
            _payload(
                identity_verified=False,
                risk_acceptance={"owner": "owner", "rationale": "temporary", "expiry": "2000-01-01"},
            )
        )


def test_yaml_loader_and_cli_emit_secret_free_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "promotion.yaml"
    path.write_text(
        """promotion:\n  project: working/private_example\n  source_commit: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n  reviewer: reviewer@example.test\n  identity_verified: true\n  authorization_verified: true\n  redaction_reviewed: true\n  secrets_externalized: true\n  routes_reviewed: true\n  mcp_boundaries_reviewed: true\n  export_tests_passed: true\n  risk_acceptance: null\n""",
        encoding="utf-8",
    )

    assert load_promotion_attestation(path).approved is True
    assert main([str(path)]) == 0
    output = capsys.readouterr().out
    result = json.loads(output)
    assert result["approved"] is True
    assert "password" not in output.lower()


def test_explicit_attestation_command_uses_deterministic_audit_date(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = tmp_path / "promotion.yaml"
    payload = _payload(
        export_tests_passed=False,
        risk_acceptance={"owner": "owner", "rationale": "bounded", "expiry": "2026-07-20"},
    )
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    assert main(["attestation", str(path), "--as-of", "2026-07-20"]) == 0
    assert json.loads(capsys.readouterr().out)["approved"] is True
    assert main(["attestation", str(path), "--as-of", "2026-07-21"]) == 1
    assert "must not be in the past" in capsys.readouterr().out

    assert load_promotion_attestation(path, as_of=date(2026, 7, 20)).approved


def test_package_cli_rejects_bare_promotion_project(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "promotion.yaml"
    path.write_text(yaml.safe_dump(_payload(project="private_example")), encoding="utf-8")

    assert main(["attestation", str(path), "--as-of", "2026-07-20"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["approved"] is False
    assert "qualified" in payload["error"]
