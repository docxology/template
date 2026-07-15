#!/usr/bin/env python3
"""Compatibility wrapper for :mod:`scripts.publish.publish_project_release`."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.publish.publish_project_release import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
