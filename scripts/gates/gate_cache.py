#!/usr/bin/env python3
"""Cache validation gate — thin CLI over infrastructure.core.cache_gate."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.core.cache_gate import run_cache_gate  # noqa: E402

if __name__ == "__main__":
    sys.exit(run_cache_gate())
