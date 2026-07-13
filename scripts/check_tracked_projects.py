#!/usr/bin/env python3
"""Confidentiality guard — thin CLI over infrastructure.project.git_guards."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.project.git_guards import offending_tracked_projects  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Path to repository root (default: auto-detected from script location)",
    )
    args = parser.parse_args(argv)

    offenders = offending_tracked_projects(args.repo_root.resolve())
    if not offenders:
        print("Confidentiality guard: only public canonical template projects are tracked.")
        return 0

    print(
        "CONFIDENTIALITY VIOLATION: non-template project paths are tracked by git.\n"
        "This is a PUBLIC repo — untrack them immediately with:\n"
        "  git rm -r --cached <path>\n"
        "Offending tracked paths:"
    )
    for path in offenders:
        print(f"  {path}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
