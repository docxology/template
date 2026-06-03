#!/usr/bin/env python3
"""Write deterministic toy sweep artifacts for promoted sheaf tracks."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from roadmap_tracks import write_toy_sweep_artifacts


def main() -> int:
    for name, path in write_toy_sweep_artifacts(PROJECT_ROOT).items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
