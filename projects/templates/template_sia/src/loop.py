"""Compatibility re-exports — harness orchestration lives in scripts/sia_loop_impl.py."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from sia_loop_impl import (  # noqa: E402
    SiaLoopResult,
    build_run_config,
    fixtures_dir,
    run_sia_loop_project,
)

__all__ = [
    "SiaLoopResult",
    "build_run_config",
    "fixtures_dir",
    "run_sia_loop_project",
]
