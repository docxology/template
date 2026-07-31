#!/usr/bin/env python3
"""Fail closed when high-confidence credentials are present in tracked files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.project.git_guards import tracked_secret_findings  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Run the tracked-index secret scan without printing secret values."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)

    findings = tracked_secret_findings(args.repo_root.resolve())
    if not findings:
        print("No high-confidence credentials found in tracked files.")
        return 0

    print("Tracked files contain high-confidence credentials; rotate and remove them:")
    for finding in findings:
        print(f"  {finding}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
