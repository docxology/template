"""Resolve project root and standard output paths for the EDA exemplar."""

from __future__ import annotations

import sys
from pathlib import Path

_DEFAULT_ROOT = Path(__file__).resolve().parent.parent


def resolve_project_root(package_name: str) -> Path:
    mod = sys.modules.get(package_name)
    if mod is not None and hasattr(mod, "project_root"):
        return Path(mod.project_root)
    return _DEFAULT_ROOT


def project_output_dirs(project_root: Path | None = None) -> dict[str, Path]:
    """Return common output directories for the EDA exemplar."""
    root = project_root or _DEFAULT_ROOT
    output = root / "output"
    return {
        "output": output,
        "figures": output / "figures",
        "data": output / "data",
        "reports": output / "reports",
        "web": output / "web",
    }
