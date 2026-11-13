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
    assert "fallback lanes: health, tests, precommit, public-readiness" in result.stdout


@pytest.mark.parametrize(
    "lane", ("lint", "health", "verify-no-mocks", "security", "tests", "precommit", "confid", "public-readiness")
)
def test_no_act_named_dry_run_preserves_each_existing_lane(tmp_path: Path, lane: str) -> None:
    result = _run("--no-act", "--job", lane, "--dry-run", cwd=tmp_path)

    assert result.returncode == 0, result.stderr
    plans = [line for line in result.stdout.splitlines() if "DRYRUN" in line]
    assert plans == [f"[ci_local] DRYRUN — would run direct-command fallback lane: {lane}"]


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
    assert "uv run python scripts/audit/check_mirror_symlinks.py" in source


def test_fallback_scope_arrays_match_the_actual_public_helpers(tmp_path: Path) -> None:
    """The real combined CLI supplies the unchanged lint and type scopes."""
    import os
    import sys

    from infrastructure.project.public_scope import public_ci_lint_paths, public_ci_source_paths

    source = SCRIPT.read_text(encoding="utf-8")
    scope = source.split('  echo "[ci_local] === CI lint job ==="\n', 1)[1].split("  uv run ruff check ", 1)[0]
    environment = dict(
        os.environ,
        UV_CACHE_DIR=str(tmp_path / "uv-cache"),
        UV_NO_SYNC="1",
        UV_OFFLINE="1",
        UV_PYTHON=sys.executable,
        UV_PROJECT_ENVIRONMENT=sys.prefix,
        UV_PYTHON_DOWNLOADS="never",
    )
    environment.pop("UV_NO_PROJECT", None)
    result = subprocess.run(
        [
            "bash",
            "-c",
            "set -euo pipefail\n"
            + scope
            + 'printf "lint=%s\nsource=%s\n" "${PUBLIC_CI_LINT_PATHS[*]}" "${PUBLIC_CI_SOURCE_PATHS[*]}"',
        ],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "lint=" + " ".join(path.as_posix() for path in public_ci_lint_paths(REPO_ROOT)),
        "source=" + " ".join(path.as_posix() for path in public_ci_source_paths(REPO_ROOT)),
    ]


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
