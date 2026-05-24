#!/usr/bin/env python3
"""Run eval harness: skill-guided vs baseline responses + grading."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR.parents[3]))
sys.path.insert(0, str(_SCRIPTS_DIR))

from skill_eval.runner import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
