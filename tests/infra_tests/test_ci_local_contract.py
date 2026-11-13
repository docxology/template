"""Executable contracts for the local CI shell entry point."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

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


def test_no_act_dry_run_resolves_repository_root_from_any_cwd(tmp_path: Path) -> None:
    result = _run("--no-act", "--dry-run", cwd=tmp_path)

    assert result.returncode == 0, result.stderr
    assert f"Repository root: {REPO_ROOT}" in result.stdout
    assert "fallback lanes: health, tests, precommit, public-readiness" in result.stdout


def test_no_act_rejects_unknown_lane_instead_of_vacuous_success(tmp_path: Path) -> None:
    result = _run("--no-act", "--job", "not-a-real-lane", cwd=tmp_path)

    assert result.returncode == 2
    assert "Unsupported direct-command fallback lane" in result.stderr


def test_no_act_lists_fail_closed_policy_lanes(tmp_path: Path) -> None:
    result = _run("--no-act", "--list", cwd=tmp_path)

    assert result.returncode == 0, result.stderr
    for lane in ("health", "verify-no-mocks", "precommit", "confid"):
        assert f"- {lane}" in result.stdout


@pytest.mark.parametrize(
    ("arguments", "missing_module"),
    [(("--job", "lint"), "infrastructure.project.public_scope"), ((), "infrastructure.core.health")],
    ids=("named-lint", "default-health"),
)
def test_fallback_scope_producer_failure_stops_before_lint(
    tmp_path: Path, arguments: tuple[str, ...], missing_module: str
) -> None:
    """A genuine missing-package CLI failure cannot yield empty successful scopes."""
    import os
    import sys

    runtime = tmp_path / "empty-runtime"
    environment = dict(os.environ, UV_CACHE_DIR=str(tmp_path / "uv-cache"), UV_OFFLINE="1", UV_PYTHON_DOWNLOADS="never")
    for name in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT", "UV_PYTHON"):
        environment.pop(name, None)
    prepared = subprocess.run(
        ["uv", "venv", "--no-project", "--no-python-downloads", "--python", sys.executable, str(runtime)],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert prepared.returncode == 0, prepared.stderr
    owned_script = tmp_path / "owned-checkout/scripts/shell/ci_local.sh"
    owned_script.parent.mkdir(parents=True)
    owned_script.write_bytes(SCRIPT.read_bytes())
    python = runtime / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    environment.update(UV_NO_PROJECT="1", UV_NO_SYNC="1", UV_PYTHON=str(python))
    result = subprocess.run(
        ["bash", str(owned_script), "--no-act", *arguments],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode != 0
    assert missing_module in result.stderr
    assert "No module named" in result.stderr
    assert "ruff" not in result.stderr
    assert "All requested direct-command checks passed" not in result.stdout
