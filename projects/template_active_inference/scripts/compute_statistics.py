#!/usr/bin/env python3
"""Write combined analytical + simulation statistics JSON."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from analysis import write_analysis_statistics


def main() -> int:
    path = write_analysis_statistics(PROJECT_ROOT)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
