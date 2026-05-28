#!/usr/bin/env python3
"""Run analytical parameter sweep and invariant report."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from analysis import run_analysis


def main() -> int:
    paths = run_analysis(PROJECT_ROOT)
    for name, path in paths.items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
