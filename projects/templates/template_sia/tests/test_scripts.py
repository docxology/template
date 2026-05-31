"""Subprocess tests for project analysis scripts."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parents[2]


def _script_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    return env


def test_run_sia_loop_script(tmp_path: Path):
    import shutil

    project = tmp_path / "proj"
    shutil.copytree(PROJECT_ROOT, project)
    if (project / "output").exists():
        shutil.rmtree(project / "output")
    proc = subprocess.run(
        [
            sys.executable,
            str(project / "scripts" / "run_sia_loop.py"),
            "--project-root",
            str(project),
        ],
        cwd=str(REPO_ROOT),
        env=_script_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert (project / "output" / "runs" / "run_1" / "run_summary.json").is_file()


def test_generate_manuscript_variables_script():
    run_proc = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "run_sia_loop.py")],
        cwd=str(REPO_ROOT),
        env=_script_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert run_proc.returncode == 0, run_proc.stderr
    proc = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "z_generate_manuscript_variables.py")],
        cwd=str(REPO_ROOT),
        env=_script_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert (PROJECT_ROOT / "output" / "data" / "manuscript_variables.json").is_file()
