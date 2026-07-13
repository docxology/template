#!/usr/bin/env python3
"""CLI wrapper — delegates to src/cli.py::main."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cli import main

if __name__ == "__main__":
    main()
