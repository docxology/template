#!/usr/bin/env python3
"""Generate the method inventory documentation report."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from gates.method_inventory import write_method_inventory


def main() -> int:
    path = write_method_inventory(PROJECT_ROOT)
    print(f"method_inventory: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
