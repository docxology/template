#!/usr/bin/env python3
"""CLI for the code-project optimization analysis pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _template_repo_root(project_root: Path) -> Path | None:
    """Return the template repository root when this project is inside one."""
    for parent in project_root.parents:
        if (parent / "infrastructure").is_dir() and (parent / "pyproject.toml").is_file():
            return parent
    return None


for _path in (PROJECT_ROOT, PROJECT_ROOT / "src", *[_p for _p in [_template_repo_root(PROJECT_ROOT)] if _p]):
    path_text = str(_path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

from src.analysis.workflow import main, run_analysis_pipeline  # noqa: E402

__all__ = [
    "main",
    "run_analysis_pipeline",
]


if __name__ == "__main__":
    main()
