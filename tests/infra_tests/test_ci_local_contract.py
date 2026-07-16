"""Executable contracts for the local CI shell entry point."""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts/shell/ci_local.sh"


def _run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def test_ci_local_shell_syntax_is_valid() -> None:
    result = subprocess.run(
        ["bash", "-n", str(SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr


def test_no_act_dry_run_resolves_repository_root_from_any_cwd(tmp_path: Path) -> None:
    result = _run("--no-act", "--dry-run", cwd=tmp_path)

    assert result.returncode == 0, result.stderr
    assert f"Repository root: {REPO_ROOT}" in result.stdout
    assert "lint, health, verify-no-mocks" in result.stdout


def test_no_act_rejects_unknown_lane_instead_of_vacuous_success(tmp_path: Path) -> None:
    result = _run("--no-act", "--job", "not-a-real-lane", cwd=tmp_path)

    assert result.returncode == 2
    assert "Unsupported direct-command fallback lane" in result.stderr


def test_no_act_lists_fail_closed_policy_lanes(tmp_path: Path) -> None:
    result = _run("--no-act", "--list", cwd=tmp_path)

    assert result.returncode == 0, result.stderr
    for lane in ("health", "verify-no-mocks", "precommit", "confid"):
        assert f"- {lane}" in result.stdout


def test_fallback_invokes_uv_precommit_and_full_confidentiality_guard() -> None:
    source = SCRIPT.read_text(encoding="utf-8")

    assert "uv run pre-commit run --all-files" in source
    assert "uv run pre-commit run --hook-stage pre-push --all-files" in source
    assert "uv run python scripts/audit/check_tracked_all.py" in source
    assert "check_tracked_projects.py" not in source
