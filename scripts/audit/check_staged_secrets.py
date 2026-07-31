#!/usr/bin/env python3
"""Fail closed when high-confidence credentials are present in staged blobs.

Pre-commit companion to ``check_tracked_secrets.py``. Scans added, copied,
modified, and renamed blobs directly from Git's index so partial staging cannot
hide a credential or report an unstaged value. Reports ``path:line:kind``
metadata only and never prints the matched value.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.project.git_guards import staged_diff_secret_findings  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Run the staged-diff secret scan without printing secret values."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)

    findings = staged_diff_secret_findings(args.repo_root.resolve())
    if not findings:
        print("No high-confidence credentials found in staged files.")
        return 0

    print("Staged files contain high-confidence credentials; rotate and remove them:")
    for finding in findings:
        print(f"  {finding}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
