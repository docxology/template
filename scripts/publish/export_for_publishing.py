#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from infrastructure.publishing.export_bundle import export_for_publishing, main

__all__ = ["export_for_publishing", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
