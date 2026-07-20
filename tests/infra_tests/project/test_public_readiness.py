"""Tests for the public exemplar readiness gate."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.project.public_readiness import (
    PublicReadinessReport,
    PublicReadinessResult,
    run_public_readiness,
)
from scripts.gates.public_readiness import main as public_readiness_main
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES


def test_public_readiness_fails_closed_when_expected_roster_is_absent(tmp_path: Path) -> None:
    report = run_public_readiness(tmp_path)

    assert report.counts == {"fail": len(PUBLIC_PROJECT_NAMES), "pass": 0, "skip": 0}
    assert report.missing_projects == tuple(sorted(PUBLIC_PROJECT_NAMES))
    assert report.exit_code() == 1


def test_public_readiness_does_not_execute_a_symlinked_public_path(tmp_path: Path) -> None:
    """The public lane must not turn a private symlink into executable scope."""
    target = tmp_path / "private-sidecar" / "template_active_inference"
    target.mkdir(parents=True)
    public_path = tmp_path / "projects" / "templates" / "template_active_inference"
    public_path.parent.mkdir(parents=True)
    public_path.symlink_to(target, target_is_directory=True)

    report = run_public_readiness(tmp_path)

    assert "templates/template_active_inference" in report.missing_projects


def test_public_readiness_fails_on_skips_unless_the_optional_lane_allows_them() -> None:
    result = PublicReadinessResult("templates/example", "skip", 2, 0.1, ())
    report = PublicReadinessReport((result,), (result.project,))

    assert report.counts == {"fail": 0, "pass": 0, "skip": 1}
    assert report.exit_code() == 1
    assert report.exit_code(allow_skips=True) == 0


def test_public_readiness_fails_closed_on_unknown_status() -> None:
    result = PublicReadinessResult("templates/example", "unexpected", 0, 0.1, ())
    report = PublicReadinessReport((result,), (result.project,))

    assert report.exit_code() == 1


def test_public_readiness_rejects_non_positive_timeout(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="timeout_seconds must be positive"):
        run_public_readiness(tmp_path, timeout_seconds=0)


def test_public_readiness_cli_rejects_non_positive_timeout() -> None:
    with pytest.raises(SystemExit, match="2"):
        public_readiness_main(["--timeout", "0"])
