#!/usr/bin/env python3
"""Generate publication figures."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from visualizations.figures import generate_all_figures


def main() -> int:
    for path in generate_all_figures(PROJECT_ROOT):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
