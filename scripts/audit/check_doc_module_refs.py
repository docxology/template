#!/usr/bin/env python3
"""Documentation module-reference guard — thin CLI over infrastructure.documentation.doc_module_refs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.documentation.doc_module_refs import scan_repo  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Run the documentation module-reference gate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)
    findings = scan_repo(args.repo_root.resolve())
    if not findings:
        print("All documented infrastructure.* module references resolve.")
        return 0
    print(f"{len(findings)} unresolved infrastructure module reference(s) in documentation:")
    for finding in findings:
        print(f"  {finding.format()}")
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
