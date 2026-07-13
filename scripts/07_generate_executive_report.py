#!/usr/bin/env python3
"""Compatibility wrapper for ``scripts/pipeline/stage_07_executive_report.py``."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.pipeline.stage_07_executive_report import main, verify_project_completion  # noqa: E402

__all__ = ["main", "verify_project_completion"]


if __name__ == "__main__":
    raise SystemExit(main())
