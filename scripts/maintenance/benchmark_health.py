#!/usr/bin/env python3
"""Create clean-checkout serial/parallel health benchmark evidence."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from infrastructure.core.health_benchmark import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
