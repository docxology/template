#!/usr/bin/env python3
"""04_seal.py — seal the most-recently materialized child project."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
# `scripts` is not a package here (no __init__.py), and the repo root's own
# top-level `scripts/` package shadows it on sys.path — `from scripts.seal_child
# import ...` silently resolves to the wrong package. Import this project's
# scripts/ directory directly instead.
sys.path.insert(0, str(Path(__file__).parent))

from seal_child import seal_child
from src.project_paths import project_output_dirs
from src.realize import select_full_child

PROJECT_ROOT = Path(__file__).parent.parent


def main():
    """CLI entry point."""
    dirs = project_output_dirs(PROJECT_ROOT)
    child_dir = dirs["children"]
    if not child_dir.exists():
        print("No children found. Run realize_child_full.py first.", file=sys.stderr)
        sys.exit(1)
    try:
        full_child = select_full_child(PROJECT_ROOT, child_dir)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    seal_child(full_child)


if __name__ == "__main__":
    main()
