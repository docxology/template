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

    assert report.profile == "release"
    assert report.project_workers == 1
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
    result = PublicReadinessResult("templates/example", "skip", 2, 0.1, (), reason_code="OPTIONAL_TOOL_MISSING")
    report = PublicReadinessReport((result,), (result.project,))

    assert report.counts == {"fail": 0, "pass": 0, "skip": 1}
    assert report.exit_code() == 1
    assert report.exit_code(allow_skips=True) == 0


def test_public_readiness_treats_unmarked_exit_two_as_failure() -> None:
    result = PublicReadinessResult("templates/example", "fail", 2, 0.1, (), reason_code="SUBPROCESS_EXIT_2")
    report = PublicReadinessReport((result,), (result.project,))

    assert report.exit_code(allow_skips=True) == 1


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


def test_public_readiness_cli_rejects_non_positive_project_workers() -> None:
    with pytest.raises(SystemExit, match="2"):
        public_readiness_main(["--project-workers", "0"])


def test_public_readiness_serializes_profile_and_worker_metadata() -> None:
    result = PublicReadinessResult("templates/example", "pass", 0, 0.1, ())
    report = PublicReadinessReport((result,), (result.project,), profile="quick", project_workers=2)

    payload = report.to_dict()

    assert payload["profile"] == "quick"
    assert payload["project_workers"] == 2


@pytest.mark.parametrize(
    "results,expected",
    [
        ((), ("templates/example",)),
        ((), ()),
        ((PublicReadinessResult("templates/example", "pass", 0, 0.1, ()),) * 2, ("templates/example",)),
        ((PublicReadinessResult("templates/other", "pass", 0, 0.1, ()),), ("templates/example",)),
        ((PublicReadinessResult("templates/example", "pass", 0, 0.1, ()),), ("templates/example",) * 2),
        ((PublicReadinessResult("templates/example", "pass", 1, 0.1, ()),), ("templates/example",)),
    ],
)
def test_readiness_rejects_incomplete_or_inconsistent_reports(results, expected) -> None:
    report = PublicReadinessReport(results, expected)
    assert report.exit_code(allow_skips=True) == 1


def test_readiness_reports_results_omitted_from_expected_roster() -> None:
    report = PublicReadinessReport((), ("templates/example",))
    assert report.missing_projects == ("templates/example",)


def test_readiness_default_encloses_single_project_timeout() -> None:
    from infrastructure.project.public_readiness import DEFAULT_TIMEOUT_SECONDS
    from infrastructure.reporting.suite_runner import DEFAULT_SINGLE_PROJECT_TEST_TIMEOUT_SECONDS

    assert DEFAULT_TIMEOUT_SECONDS >= DEFAULT_SINGLE_PROJECT_TEST_TIMEOUT_SECONDS + 300


@pytest.mark.parametrize("timeout", [True, -1, 1.5, float("inf"), float("nan")])
def test_readiness_rejects_invalid_runtime_timeout(tmp_path: Path, timeout) -> None:
    with pytest.raises(ValueError, match="timeout_seconds must be positive"):
        run_public_readiness(tmp_path, timeout_seconds=timeout)


def test_readiness_counts_identify_their_unit() -> None:
    from infrastructure.project.public_readiness import format_public_readiness

    result = PublicReadinessResult("templates/example", "pass", 0, 0.1, ())
    report = PublicReadinessReport((result,), (result.project,))
    assert report.to_dict()["counts_unit"] == "projects"
    assert "Project counts:" in format_public_readiness(report)


@pytest.mark.parametrize("timeout,delay,status", [(None, 0, "pass"), (1, 5, "fail")])
def test_readiness_default_and_explicit_caps_use_real_subprocesses(tmp_path: Path, timeout, delay, status) -> None:
    from infrastructure.project.public_readiness import DEFAULT_TIMEOUT_SECONDS

    project = sorted(PUBLIC_PROJECT_NAMES)[0]
    (tmp_path / "projects" / project).mkdir(parents=True)
    script = tmp_path / "scripts" / "pipeline" / "stage_01_test.py"
    script.parent.mkdir(parents=True)
    script.write_text(f"import time\ntime.sleep({delay})\nprint('real readiness probe completed')\n", encoding="utf-8")
    report = run_public_readiness(tmp_path, **({} if timeout is None else {"timeout_seconds": timeout}))
    result = next(result for result in report.results if result.project == project)
    assert result.status == status
    assert result.timeout_seconds == (DEFAULT_TIMEOUT_SECONDS if timeout is None else timeout)
    if timeout is None:
        assert result.returncode == 0
        assert "real readiness probe completed" in result.output_tail
    else:
        assert result.returncode == 124
        assert result.reason_code == "SUBPROCESS_EXIT_124"
