#!/usr/bin/env python3
"""Compatibility wrapper for ``scripts/runner/bundle_executable.py``."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.runner.bundle_executable import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
