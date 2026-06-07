#!/usr/bin/env python3
"""CLI for the code-project optimization analysis pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
for _path in (PROJECT_ROOT, PROJECT_ROOT / "src", PROJECT_ROOT.parents[2]):
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
