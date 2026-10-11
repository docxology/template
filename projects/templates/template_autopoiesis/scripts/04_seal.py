#!/usr/bin/env python3
"""Seal the manifest-selected current runtime export; preserve published children."""

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

from template_autopoiesis.gates.custody_paths import confined_path  # noqa: E402 - actual provider selection precedes own imports
from template_autopoiesis.gates.realize import select_full_child  # noqa: E402 - actual provider selection precedes own imports
from template_autopoiesis.gates.sealing import seal_verified_child  # noqa: E402 - actual provider selection precedes own imports


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args(argv)
    try:
        exports = confined_path(args.project_root, "output/.pipeline/child_realization/exports")
        child = select_full_child(args.project_root, exports)
        print(f"Sealed: {seal_verified_child(child)}")
    except (OSError, ValueError, TypeError) as exc:
        print(f"Required child seal failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
