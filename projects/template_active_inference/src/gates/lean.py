"""Lean toolchain validation helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path


def lean_project_present(project_root: Path) -> bool:
    """True when this project ships a Lake root (``lean/lakefile.lean``)."""
    return (project_root.resolve() / "lean" / "lakefile.lean").is_file()


def build_lean(project_root: Path) -> tuple[int, str]:
    """Build the Lean package when present; skip cleanly when absent."""
    if not lean_project_present(project_root):
        return 0, "lean project absent — skipped"
    lean_dir = project_root.resolve() / "lean"
    proc = subprocess.run(
        ["lake", "build"],
        cwd=lean_dir,
        capture_output=True,
        text=True,
    )
    output = proc.stdout + proc.stderr
    if proc.returncode != 0:
        return proc.returncode, output
    return 0, output
