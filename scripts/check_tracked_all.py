#!/usr/bin/env python3
"""Confidentiality guards for all top-level resource directories.

Runs all confidentiality checks (projects, fonds, tools, rules) in one pass.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.project.git_guards import (
    offending_tracked_fonds,
    offending_tracked_projects,
    offending_tracked_rules,
    offending_tracked_tools,
)


def main() -> int:
    repo_root = REPO_ROOT.resolve()
    total_offenders = 0

    checks = [
        ("projects", offending_tracked_projects),
        ("fonds", offending_tracked_fonds),
        ("tools", offending_tracked_tools),
        ("rules", offending_tracked_rules),
    ]

    for name, func in checks:
        offenders = func(repo_root)
        if offenders:
            total_offenders += len(offenders)
            print(f"CONFIDENTIALITY VIOLATION: {name}")
            for path in offenders:
                print(f"  {path}")
        else:
            print(f"{name}: clean")

    if total_offenders:
        print(f"\n{total_offenders} total confidentiality violation(s).")
        print("Untrack them with: git rm -r --cached <path>")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())