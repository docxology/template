#!/usr/bin/env python3
"""Forward to z_generate_manuscript_variables (single hydration entry point)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    script = Path(__file__).resolve().parent / "z_generate_manuscript_variables.py"
    result = subprocess.run(
        [sys.executable, str(script), *(argv or [])],
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
