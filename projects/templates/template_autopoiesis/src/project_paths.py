"""Project output directory helpers for template_autopoiesis."""

from __future__ import annotations

from pathlib import Path


def project_output_dirs(project_root: str | Path) -> dict[str, Path]:
    """Return standard output directories for the project, creating them if needed."""
    root = Path(project_root)
    dirs = {
        "output": root / "output",
        "figures": root / "output" / "figures",
        "data": root / "output" / "data",
        "manuscript": root / "output" / "manuscript",
        "children": root / "output" / "children",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs
