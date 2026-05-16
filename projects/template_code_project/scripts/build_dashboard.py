#!/usr/bin/env python3
"""Compatibility wrapper for the code-project dashboard builder.

Dashboard payload and rendering behavior lives in ``src/dashboard.py``. This
script keeps the historical CLI stable while remaining a thin orchestrator.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
for _path in (PROJECT_ROOT, PROJECT_ROOT / "src", PROJECT_ROOT.parent.parent):
    path_text = str(_path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

from src.dashboard import (  # noqa: E402,F401
    CFG_DEFAULT,
    DATA_DIR,
    OUTPUT,
    REP_DIR,
    WEB_DIR,
    _build_dashboard,
    _compute_payload,
    _load_yaml_defaults,
    _parse_args,
    _to_dashboard_invariant,
    _to_diagonal_A,
    main,
)

__all__ = [
    "CFG_DEFAULT",
    "DATA_DIR",
    "OUTPUT",
    "REP_DIR",
    "WEB_DIR",
    "_build_dashboard",
    "_compute_payload",
    "_load_yaml_defaults",
    "_parse_args",
    "_to_dashboard_invariant",
    "_to_diagonal_A",
    "main",
]


if __name__ == "__main__":
    main()
