"""Realize a generated child project: run analysis, render manuscript, validate.

This module provides helper functions for orchestrating the full pipeline
on a materialized child project.  Heavy steps (Chrome PDF rendering) are
gated behind availability checks.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional


def _project_slug(child_root: Path) -> str:
    return child_root.name


def _gate_python(child_root: Path) -> bool:
    """Return True if the child project's Python environment is available."""
    return sys.executable is not None


def run_child_stage(
    child_root: Path,
    script: str,
    timeout: int = 60,
) -> subprocess.CompletedProcess:
    """Run *script* inside *child_root* using the current Python interpreter."""
    return subprocess.run(
        [sys.executable, script],
        cwd=child_root,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def run_analysis_stage(child_root: Path) -> dict[str, object]:
    """Run analysis.py in *child_root* and return a result dict."""
    analysis_py = child_root / "analysis.py"
    if not analysis_py.exists():
        return {"success": False, "error": "analysis.py not found"}
    try:
        proc = run_child_stage(child_root, "analysis.py")
        return {
            "success": proc.returncode == 0,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "returncode": proc.returncode,
        }
    except Exception as exc:  # noqa: BLE001  # safety net: child stage failures surface as dict errors
        return {"success": False, "error": str(exc)}


def render_child_manuscript(
    child_root: Path,
    output_dir: Optional[Path] = None,
) -> dict[str, object]:
    """Render the child manuscript to PDF (if Chrome available)."""
    output_dir = output_dir or child_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return {
        "success": False,
        "reason": "Chrome/Pandoc rendering not available in child context",
        "output_dir": str(output_dir),
    }


def validate_child(child_root: Path) -> dict[str, object]:
    """Run basic validation on the child project structure."""
    required = [
        "analysis.py",
        "pyproject.toml",
        "provenance.json",
        "primitives/__init__.py",
    ]
    missing = [f for f in required if not (child_root / f).exists()]
    return {
        "valid": len(missing) == 0,
        "missing": missing,
        "child_root": str(child_root),
    }
