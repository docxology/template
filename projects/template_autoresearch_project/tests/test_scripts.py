"""Smoke tests for thin project scripts."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_run_autoresearch_loop_script(project_root: Path) -> None:
    script = project_root / "scripts" / "run_autoresearch_loop.py"
    result = subprocess.run([sys.executable, str(script)], cwd=project_root, text=True, capture_output=True)

    assert result.returncode == 0, result.stderr
    assert "autoresearch_loop.md" in result.stdout
