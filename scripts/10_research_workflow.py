#!/usr/bin/env python3
"""Backward-compatible shim — script moved to scripts/pipeline/stage_10_research_workflow.py.

This file is kept for compatibility with callers that reference the old path
directly. It prints a deprecation warning and delegates to the real implementation.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

warnings.warn(
    "scripts/10_research_workflow.py is deprecated. "
    "Use scripts/pipeline/stage_10_research_workflow.py instead.",
    DeprecationWarning,
    stacklevel=1,
)
print(
    "DEPRECATION: scripts/10_research_workflow.py has moved to scripts/pipeline/stage_10_research_workflow.py",
    file=sys.stderr,
)

# Add repo root to path so scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import ensure_repo_root_on_path  # noqa: E402
ensure_repo_root_on_path()

from scripts.pipeline.stage_10_research_workflow import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
