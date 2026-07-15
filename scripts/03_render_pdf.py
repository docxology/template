#!/usr/bin/env python3
"""Compatibility wrapper for ``scripts/pipeline/stage_03_render.py``."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.pipeline.stage_03_render import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
