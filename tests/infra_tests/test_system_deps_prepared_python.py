"""Real shell selection without dependency acquisition or fake executables."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _copy_helper(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    root = tmp_path / "repo"
    shell = root / "scripts" / "shell"
    shell.mkdir(parents=True)
    helper = shell / "setup-system-deps.sh"
    shutil.copy2(ROOT / "scripts" / "shell" / helper.name, helper)
    tools = tmp_path / "tools"
    tools.mkdir()
    # Retain actual basic shell tools while deliberately withholding native
    # prerequisites and uv. No executable is replaced with simulated behavior.
    for name in ("dirname", "uname"):
        executable = shutil.which(name)
        assert executable is not None
        (tools / name).symlink_to(executable)
    env = dict(os.environ)
    env["PATH"] = str(tools)
    env["UV_CACHE_DIR"] = str(root / "must-not-create-cache")
    env["UV_PROJECT_ENVIRONMENT"] = str(root / "must-not-create-environment")
    return helper, env


@pytest.mark.parametrize(
    "nomination", ["missing", "empty", "missing-value", "not-executable", "not-python", "duplicate"]
)
def test_invalid_prepared_python_refuses_before_any_install(tmp_path: Path, nomination: str) -> None:
    helper, env = _copy_helper(tmp_path)
    args = ["/bin/bash", str(helper), "--prepared-python"]
    if nomination == "missing":
        args.append(str(tmp_path / "missing-python"))
    elif nomination == "empty":
        args.append("")
    elif nomination == "not-executable":
        path = tmp_path / "not-executable"
        path.write_text("not an executable")
        path.chmod(0o600)
        args.append(str(path))
    elif nomination == "duplicate":
        args.extend([sys.executable, "--prepared-python", sys.executable])
    elif nomination == "not-python":
        actual_true = shutil.which("true")
        assert actual_true is not None
        args.append(actual_true)
    result = subprocess.run(args, cwd=tmp_path, env=env, capture_output=True, text=True, timeout=10, check=False)
    assert result.returncode == 1, (result.stdout, result.stderr)
    assert "prepared Python" in result.stderr or "--prepared-python" in result.stderr
    assert not Path(env["UV_CACHE_DIR"]).exists()
    assert not Path(env["UV_PROJECT_ENVIRONMENT"]).exists()
    assert not (helper.parents[2] / "uv.lock").exists()


@pytest.mark.parametrize("selection", ["absolute", "relative"])
def test_real_prepared_python_reaches_native_check_without_uv(tmp_path: Path, selection: str) -> None:
    helper, env = _copy_helper(tmp_path)
    nomination = sys.executable
    if selection == "relative":
        (tmp_path / "prepared-python").symlink_to(sys.executable)
        nomination = "prepared-python"
    result = subprocess.run(
        ["/bin/bash", str(helper), "--check", "--prepared-python", nomination],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 1, (result.stdout, result.stderr)
    assert "pandoc not found" in result.stderr
    assert "xelatex not found" in result.stderr
    assert "verification failed" in result.stderr
    assert "uv not found" not in result.stderr
    assert not Path(env["UV_CACHE_DIR"]).exists()
    assert not Path(env["UV_PROJECT_ENVIRONMENT"]).exists()
    assert not (helper.parents[2] / "uv.lock").exists()
