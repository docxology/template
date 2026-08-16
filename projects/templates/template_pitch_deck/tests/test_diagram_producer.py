"""Real-process negative control for the required Mermaid producer."""

from __future__ import annotations

import os
import runpy
import subprocess
import sys

from paths import locate_repo_root, project_root


def test_diagram_sources_leave_newline_serialization_to_renderer():
    """Fresh sidecars must end in one newline without a blank trailing line."""
    script = project_root() / "scripts" / "15_generate_diagrams.py"
    diagrams = runpy.run_path(str(script))["DIAGRAMS"]
    assert isinstance(diagrams, dict)
    assert diagrams
    assert all(isinstance(source, str) and source == source.rstrip("\n") for source in diagrams.values())


def test_diagram_producer_fails_when_mmdc_is_unavailable():
    """Tracked PNGs must not turn a missing renderer into a successful Stage 02."""
    repo_root = locate_repo_root(project_root())
    script = project_root() / "scripts" / "15_generate_diagrams.py"
    env = os.environ.copy()
    env["PATH"] = ""
    env["SOURCE_DATE_EPOCH"] = "1786717253"
    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=repo_root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    combined = completed.stdout + completed.stderr
    assert completed.returncode == 1
    assert "Required Mermaid producer failed" in combined
    assert "mmdc" in combined
