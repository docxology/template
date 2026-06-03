#!/usr/bin/env python3
"""Write provenance, replay, and counterexample validation artifacts."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from validation_spine import write_validation_spine_artifacts


def main() -> int:
    for name, path in write_validation_spine_artifacts(PROJECT_ROOT).items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
