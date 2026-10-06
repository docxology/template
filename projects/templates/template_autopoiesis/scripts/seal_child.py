#!/usr/bin/env python3
"""Write a recompute-verified child seal; required failures exit nonzero."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
_BOOTSTRAP = importlib.util.spec_from_file_location(
    "autopoiesis_script_bootstrap", PROJECT_ROOT / "scripts/_bootstrap.py"
)
if _BOOTSTRAP is None or _BOOTSTRAP.loader is None:
    raise ImportError("actual project bootstrap is unavailable")
_bootstrap = importlib.util.module_from_spec(_BOOTSTRAP)
_BOOTSTRAP.loader.exec_module(_bootstrap)
_bootstrap.bootstrap_project(PROJECT_ROOT)

from template_autopoiesis.gates.sealing import seal_verified_child  # noqa: E402 - actual provider selection precedes own imports


def seal_child(child_root: Path) -> None:
    """Seal a verified child using its actual spec and current source bytes."""
    print(f"Sealed: {seal_verified_child(child_root)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("child_root", type=Path)
    args = parser.parse_args(argv)
    try:
        seal_child(args.child_root)
    except (OSError, ValueError, TypeError) as exc:
        print(f"Required child seal failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
