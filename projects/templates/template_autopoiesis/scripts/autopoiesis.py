#!/usr/bin/env python3
"""CLI wrapper — delegates to src/template_autopoiesis/core/cli.py::main."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from template_autopoiesis.core.cli import main

if __name__ == "__main__":
    main()
