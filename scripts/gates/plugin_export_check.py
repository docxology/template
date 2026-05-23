#!/usr/bin/env python3
"""Plugin export drift gate — thin CLI over infrastructure.validation.plugin_export."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.validation.plugin_export import run_plugin_export_check  # noqa: E402


if __name__ == "__main__":
    sys.exit(run_plugin_export_check())
