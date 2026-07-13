#!/usr/bin/env python3
"""Compatibility wrapper for ``scripts/pipeline/stage_06_llm_review.py``."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


if __name__ == "__main__":
    runpy.run_module("scripts.pipeline.stage_06_llm_review", run_name="__main__")
