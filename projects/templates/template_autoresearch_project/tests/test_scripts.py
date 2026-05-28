"""Smoke tests for thin project scripts."""

from __future__ import annotations

import os
import py_compile
import subprocess
import sys
from pathlib import Path


def test_run_autoresearch_loop_script_is_thin_orchestrator(project_root: Path) -> None:
    script = project_root / "scripts" / "run_autoresearch_loop.py"
    py_compile.compile(str(script), doraise=True)

    source = script.read_text(encoding="utf-8")
    assert "from src.loop import run_autoresearch_loop" in source
    assert "run_autoresearch_loop(PROJECT_ROOT, REPO_ROOT)" in source


def test_manuscript_variable_script_writes_resolved_sources(project_root: Path) -> None:
    script = project_root / "scripts" / "z_generate_manuscript_variables.py"
    env = {
        key: value
        for key, value in os.environ.items()
        if not (key.startswith("COV_CORE_") or key.startswith("COVERAGE_"))
    }
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=project_root,
        text=True,
        capture_output=True,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert "manuscript_variables.json" in result.stdout
