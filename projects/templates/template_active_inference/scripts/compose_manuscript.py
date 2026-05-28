#!/usr/bin/env python3
"""Thin orchestrator: compose sheaf sections into flat manuscript markdown."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from manuscript.sheaf.cli import run_compose_cli


def main(argv: list[str] | None = None) -> int:
    return run_compose_cli(argv, project_root=PROJECT_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
